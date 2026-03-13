"""
B-POINT — Virtual AI Mouse v3.0
Developer: Babar (BSSE Final Year Student)
Compatible: MediaPipe 0.10.30-0.10.32 | Python 3.12-3.14
Uses NEW MediaPipe Tasks API (no mp.solutions needed)
"""

import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from collections import deque
from typing import Optional, Tuple

# New MediaPipe Tasks API
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.vision import RunningMode
from mediapipe import Image, ImageFormat

# ─────────────────────────── SCREEN RESOLUTION ────────────────────────────────

def get_screen_resolution():
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h

SCREEN_W, SCREEN_H = get_screen_resolution()

# ─────────────────────────── CONFIG ───────────────────────────────────────────

CAMERA_INDEX        = 0
ZONE_MARGIN         = 0.20
EMA_ALPHA           = 0.25
CLICK_THRESHOLD     = 0.050
RCLICK_THRESHOLD    = 0.050
CLICK_COOLDOWN      = 0.30
DOUBLE_INTERVAL     = 0.35
SCROLL_SPEED        = 3
WINDOW_NAME         = "B-POINT v3.0  |  Press Q to quit"

# ─────────────────────────── EMA FILTER ───────────────────────────────────────

class EMAFilter:
    def __init__(self, alpha=EMA_ALPHA):
        self.alpha = alpha
        self._prev = None

    def update(self, point):
        if self._prev is None:
            self._prev = point.copy()
            return point
        s = self.alpha * point + (1.0 - self.alpha) * self._prev
        self._prev = s
        return s

    def reset(self):
        self._prev = None

# ─────────────────────────── COORDINATE MAPPER ────────────────────────────────

class CoordinateMapper:
    def __init__(self, margin=ZONE_MARGIN):
        self.x_src = [margin, 1.0 - margin]
        self.y_src = [margin, 1.0 - margin]

    def map(self, nx, ny):
        sx = int(np.interp(nx, self.x_src, [0, SCREEN_W]))
        sy = int(np.interp(ny, self.y_src, [0, SCREEN_H]))
        # mirror removed — cursor now moves naturally
        sx = int(np.clip(sx, 0, SCREEN_W - 1))
        sy = int(np.clip(sy, 0, SCREEN_H - 1))
        return sx, sy

# ─────────────────────────── GESTURE STATE ────────────────────────────────────

class GestureState:
    def __init__(self):
        self.left_click    = False
        self.right_click   = False
        self.double_click  = False
        self.scroll_up     = False
        self.scroll_down   = False
        self.pinch_left    = 1.0
        self.pinch_right   = 1.0
        self.last_lclick   = 0.0
        self.last_rclick   = 0.0
        self.prev_scroll_y = None

def dist(lm, a, b):
    return float(np.hypot(lm[a].x - lm[b].x, lm[a].y - lm[b].y))

def tip_above_pip(lm, tip, pip):
    return lm[tip].y < lm[pip].y

def detect_gestures(lm, state, now):
    state.pinch_left  = dist(lm, 8, 4)
    state.pinch_right = dist(lm, 12, 4)

    # Left click / double click
    if state.pinch_left < CLICK_THRESHOLD:
        elapsed = now - state.last_lclick
        if elapsed > CLICK_COOLDOWN:
            if elapsed < DOUBLE_INTERVAL:
                state.double_click = True
                state.left_click   = False
            else:
                state.left_click   = True
                state.double_click = False
            state.last_lclick = now
    else:
        state.left_click  = False
        state.double_click = False

    # Right click
    if state.pinch_right < RCLICK_THRESHOLD:
        if now - state.last_rclick > CLICK_COOLDOWN:
            state.right_click = True
            state.last_rclick = now
    else:
        state.right_click = False

    # Scroll: index + middle up, ring down
    i_up = tip_above_pip(lm, 8,  6)
    m_up = tip_above_pip(lm, 12, 10)
    r_up = tip_above_pip(lm, 16, 14)

    if i_up and m_up and not r_up:
        cy = lm[8].y
        if state.prev_scroll_y is not None:
            dy = cy - state.prev_scroll_y
            state.scroll_up   = dy < -0.015
            state.scroll_down = dy >  0.015
            if not state.scroll_up and not state.scroll_down:
                pass
        state.prev_scroll_y = cy
    else:
        state.scroll_up     = False
        state.scroll_down   = False
        state.prev_scroll_y = None

    return state

# ─────────────────────────── HUD ──────────────────────────────────────────────

def draw_hud(frame, state, fps, cursor_pos):
    h, w = frame.shape[:2]
    m = ZONE_MARGIN
    cv2.rectangle(frame,
                  (int(m*w), int(m*h)),
                  (int((1-m)*w), int((1-m)*h)),
                  (80,80,80), 1)
    cv2.putText(frame, "Active Zone",
                (int(m*w)+4, int(m*h)-6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80,80,80), 1)

    F = cv2.FONT_HERSHEY_SIMPLEX
    W = (240,240,240); G = (0,255,120); Y = (0,220,255); C = (255,220,0)

    lines = [
        (f"FPS: {fps:.1f}", G),
        (f"Screen {SCREEN_W}x{SCREEN_H}", W),
        (f"Cursor {cursor_pos[0]},{cursor_pos[1]}", C),
        ("", W),
        (f"L-Click  {'ON' if state.left_click   else '--'}", Y if state.left_click   else W),
        (f"R-Click  {'ON' if state.right_click  else '--'}", Y if state.right_click  else W),
        (f"DblClick {'ON' if state.double_click else '--'}", Y if state.double_click else W),
        (f"Scroll-Up {'ON' if state.scroll_up   else '--'}", Y if state.scroll_up    else W),
        (f"Scroll-Dn {'ON' if state.scroll_down else '--'}", Y if state.scroll_down  else W),
    ]
    for i, (txt, col) in enumerate(lines):
        cv2.putText(frame, txt, (10, 20+i*22), F, 0.5, col, 1, cv2.LINE_AA)

    legend = [
        "Move    : Index finger",
        "L-Click : Index+Thumb pinch",
        "R-Click : Middle+Thumb pinch",
        "Scroll  : Index+Middle raised",
        "DblClk  : Two quick pinches",
        "Quit    : Q key",
    ]
    for i, txt in enumerate(legend):
        cv2.putText(frame, txt, (w-265, 20+i*20), F, 0.42, W, 1, cv2.LINE_AA)
    return frame

# ─────────────────────────── DOWNLOAD MODEL ───────────────────────────────────

def get_model_path():
    import urllib.request, os
    model_path = "hand_landmarker.task"
    if not os.path.exists(model_path):
        print("Downloading hand landmark model (~8 MB)...")
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
        urllib.request.urlretrieve(url, model_path)
        print("Model downloaded!")
    return model_path

# ─────────────────────────── MAIN ─────────────────────────────────────────────

def main():
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0

    model_path = get_model_path()

    # New Tasks API setup
    base_options    = python.BaseOptions(model_asset_path=model_path)
    options         = HandLandmarkerOptions(
        base_options         = base_options,
        running_mode         = RunningMode.VIDEO,
        num_hands            = 1,
        min_hand_detection_confidence = 0.75,
        min_hand_presence_confidence  = 0.75,
        min_tracking_confidence       = 0.75,
    )
    detector = HandLandmarker.create_from_options(options)

    # Camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS,          60)

    if not cap.isOpened():
        print("[ERROR] Camera not found! Try changing CAMERA_INDEX to 1.")
        return

    smoother   = EMAFilter()
    mapper     = CoordinateMapper()
    state      = GestureState()
    fps_buf    = deque(maxlen=30)
    prev_time  = time.time()
    cursor_pos = (SCREEN_W // 2, SCREEN_H // 2)
    ts_ms      = 0

    print("=" * 52)
    print("  B-POINT v3.0 started! Show your hand.")
    print(f"  Screen: {SCREEN_W} x {SCREEN_H}")
    print("  Press Q in the camera window to quit.")
    print("=" * 52)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        now = time.time()
        fps_buf.append(1.0 / max(now - prev_time, 1e-6))
        prev_time = now
        fps = float(np.mean(fps_buf))

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts_ms += 1

        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        result   = detector.detect_for_video(mp_image, ts_ms)

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]   # first hand

            # Draw skeleton manually
            ih, iw = frame.shape[:2]
            connections = [
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (0,9),(9,10),(10,11),(11,12),
                (0,13),(13,14),(14,15),(15,16),
                (0,17),(17,18),(18,19),(19,20),
                (5,9),(9,13),(13,17),
            ]
            pts = [(int(p.x*iw), int(p.y*ih)) for p in lm]
            for a, b in connections:
                cv2.line(frame, pts[a], pts[b], (0, 200, 255), 2)
            for x, y in pts:
                cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)

            # Move cursor
            raw    = np.array([lm[8].x, lm[8].y])
            smooth = smoother.update(raw)
            cursor_pos = mapper.map(float(smooth[0]), float(smooth[1]))
            pyautogui.moveTo(*cursor_pos)

            # Gestures
            state = detect_gestures(lm, state, now)

            if state.double_click:
                pyautogui.doubleClick()
            elif state.left_click:
                pyautogui.click()
            if state.right_click:
                pyautogui.rightClick()
            if state.scroll_up:
                pyautogui.scroll(SCROLL_SPEED)
            if state.scroll_down:
                pyautogui.scroll(-SCROLL_SPEED)

            # Click indicator
            cx, cy_ = pts[8]
            color  = (0, 80, 255) if state.left_click else (0, 255, 100)
            radius = 14 if state.left_click else 10
            cv2.circle(frame, (cx, cy_), radius,     color, -1)
            cv2.circle(frame, (cx, cy_), radius + 3, color,  2)

            # Pinch bar
            bar = int(np.interp(state.pinch_left, [0, 0.15], [0, 120]))
            bc  = (0,80,255) if state.pinch_left < CLICK_THRESHOLD else (0,255,100)
            cv2.rectangle(frame, (iw-135, ih-32), (iw-15, ih-16),        (40,40,40), -1)
            cv2.rectangle(frame, (iw-135, ih-32), (iw-135+bar, ih-16),   bc,         -1)
            cv2.putText(frame, "Pinch", (iw-135, ih-38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180,180,180), 1)
        else:
            smoother.reset()

        frame = draw_hud(frame, state, fps, cursor_pos)
        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    print("B-POINT stopped.")


if __name__ == "__main__":
    main()