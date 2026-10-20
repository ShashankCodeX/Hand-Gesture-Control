"""
================================================================================
 HAND GESTURE MOUSE CONTROL FOR MAC
================================================================================
Control your Mac's cursor, clicks, drag, and scroll using ONLY your webcam
and hand gestures. No mouse or trackpad needed.

HOW IT WORKS (big picture):
  1. OpenCV grabs live video frames from your webcam.
  2. Google's MediaPipe "Hand Landmarker" AI model looks at each frame and
     finds 21 precise points on your hand (fingertips, knuckles, wrist).
  3. We do simple geometry/math on those 21 points to figure out what
     gesture you're making (pointing, pinching, fist, etc).
  4. pyautogui translates that gesture into a real macOS mouse action
     (move the cursor, click, drag, scroll).

GESTURES:
  ☝️  Point with your INDEX finger only        -> move the cursor
  🤏  Pinch THUMB + INDEX finger                -> click (tap) / drag (hold)
  🤏  Pinch THUMB + MIDDLE finger               -> right-click
  ✌️  INDEX + MIDDLE fingers up, close together -> scroll (move hand up/down)
  ✊  Make a FIST and hold it ~0.8s             -> pause / resume control

Press 'q' in the camera window to quit at any time.
Throwing your cursor into a corner of the screen is a pyautogui "failsafe"
that instantly aborts control if anything ever misbehaves.

Full explanation of every part of this file is in README.md.
================================================================================
"""

import os
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'
os.environ['GLOG_minloglevel'] = '2'

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time
import urllib.request

# ==============================================================================
# 1. SETTINGS  -- tweak these numbers to change how the system feels.
#    Every value here is explained in README.md under "Tuning Guide".
# ==============================================================================

CAM_INDEX = 0                  # 0 = default webcam. Try 1 if you use an external cam.
CAM_WIDTH, CAM_HEIGHT = 640, 480

FRAME_MARGIN = 100              # px border inside the camera view that maps to
                                 # the FULL screen. Keeps you from needing to reach
                                 # to the literal edge of the camera frame.

SMOOTHING = 5                   # 1 = raw/no smoothing (jittery, instant).
                                 # Higher = smoother cursor but more lag. Try 3-8.

CLICK_DISTANCE = 38             # px. Thumb-to-finger distance below this = "pinching".
                                 # Lower = must pinch tighter. Higher = pinches easier
                                 # (but may trigger accidentally).

DRAG_HOLD_SECONDS = 0.30        # How long you must hold a pinch before it becomes a
                                 # drag instead of a click.

FIST_HOLD_SECONDS = 0.8         # How long you must hold a fist to toggle pause.

SCROLL_FINGERS_TOGETHER_DIST = 60   # px. How close index+middle tips must be to
                                     # count as "scroll gesture" and not something else.
SCROLL_SENSITIVITY = 2.0        # Higher = scrolling moves the page faster.
SCROLL_DEAD_ZONE = 2            # px. Ignore tiny hand tremor below this movement.

WINDOW_NAME = "Hand Gesture Control  (press q to quit)"

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

pyautogui.FAILSAFE = True       # fling cursor to a screen corner = instant abort
pyautogui.PAUSE = 0             # no artificial delay between pyautogui commands


# ==============================================================================
# 2. MAKE SURE THE AI MODEL FILE EXISTS  (auto-downloads ~7MB on first run)
# ==============================================================================

def ensure_model_downloaded():
    if os.path.exists(MODEL_PATH):
        return
    print(f"Hand-tracking model not found. Downloading it once from Google (~7MB)...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded successfully ->", MODEL_PATH)
    except Exception as e:
        raise SystemExit(
            "\nCouldn't auto-download the model file.\n"
            f"Error: {e}\n\n"
            "Fix: download it manually and place it next to this script:\n"
            f"  curl -L -o hand_landmarker.task \"{MODEL_URL}\"\n"
        )


# ==============================================================================
# 3. HAND LANDMARK INDEX MAP
#    MediaPipe always returns 21 points per hand, in this exact fixed order.
#    Naming them makes the rest of the code readable instead of "points[8]".
#
#         8   12  16  20
#         |    |   |   |
#         7   11  15  19
#     4   |    |   |   |
#     |   6   10  14  18
#     3   |    |   |   |
#     |   5    9  13  17
#     2    \   |   |  /
#      \    \  |  | /
#       1    \ | | /
#        \    \||/
#         0 -- WRIST
# ==============================================================================

WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

# The 21 bone connections, used only for drawing the skeleton on screen.
HAND_BONES = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm base
]


# ==============================================================================
# 4. SMALL MATH HELPERS
# ==============================================================================

def euclidean_distance(p1, p2):
    """Straight-line distance between two (x, y) pixel points. Pythagoras: c = sqrt(a^2+b^2)."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def fingers_up(points):
    """
    Returns which of the 4 non-thumb fingers are pointing straight up
    (extended), based on comparing each fingertip's height to its own
    knuckle (PIP joint). In image coordinates, y grows DOWNWARD, so a
    fingertip that is 'higher' on screen has a SMALLER y value.
    (Thumb is intentionally excluded here -- it moves sideways, not up/down,
    so this simple check doesn't apply to it. We handle thumb separately
    via direct pinch-distance instead.)
    """
    return {
        "index":  points[INDEX_TIP][1]  < points[INDEX_PIP][1],
        "middle": points[MIDDLE_TIP][1] < points[MIDDLE_PIP][1],
        "ring":   points[RING_TIP][1]   < points[RING_PIP][1],
        "pinky":  points[PINKY_TIP][1]  < points[PINKY_PIP][1],
    }


# ==============================================================================
# 5. THE GESTURE -> MOUSE STATE MACHINE
#    This class remembers what happened on the previous frame (e.g. "was I
#    already pinching?") so it can detect transitions like "pinch just
#    started" vs "pinch is being held", which is what makes click vs. drag
#    vs. scroll all feel natural instead of firing 30 times a second.
# ==============================================================================

class GestureMouseController:
    def __init__(self, screen_w, screen_h, cam_w, cam_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.cam_w = cam_w
        self.cam_h = cam_h

        self.prev_x = screen_w / 2
        self.prev_y = screen_h / 2

        self.is_dragging = False
        self.pinch_start_time = None
        self.was_right_pinching = False

        self.fist_start_time = None
        self.fist_triggered = False
        self.paused = False

        self.last_scroll_y = None
        self.status = "STARTING"

    def _release_drag_if_needed(self):
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False

    def map_to_screen(self, x, y):
        """Map a point from the 'active zone' inside the camera frame to full
        screen pixel coordinates. np.interp automatically clamps values
        outside the given range to the nearest edge, so your cursor can't
        fly off-screen even if your finger goes past the active zone."""
        screen_x = np.interp(x, (FRAME_MARGIN, self.cam_w - FRAME_MARGIN), (0, self.screen_w))
        screen_y = np.interp(y, (FRAME_MARGIN, self.cam_h - FRAME_MARGIN), (0, self.screen_h))
        return float(screen_x), float(screen_y)

    def smooth(self, x, y):
        """Exponential smoothing: move only part-way from the last cursor
        position toward the new target each frame. This is the classic
        trick that turns jittery raw tracking data into a calm cursor."""
        curr_x = self.prev_x + (x - self.prev_x) / SMOOTHING
        curr_y = self.prev_y + (y - self.prev_y) / SMOOTHING
        self.prev_x, self.prev_y = curr_x, curr_y
        return curr_x, curr_y

    def update(self, points, now):
        """Call this once per frame with the 21 (x, y) pixel points for one
        hand and the current time (seconds). It decides what's happening
        and drives the real mouse via pyautogui."""

        fingers = fingers_up(points)
        index_tip = points[INDEX_TIP]
        middle_tip = points[MIDDLE_TIP]
        thumb_tip = points[THUMB_TIP]

        is_fist = not any(fingers.values())

        # ---- FIST held -> toggle pause -------------------------------------
        if is_fist:
            # Safety first: release any in-progress drag the instant fingers
            # curl into a fist, even if the fist isn't held long enough to
            # toggle pause yet. Without this, a quick fist mid-drag could
            # leave the mouse button "stuck" down.
            self._release_drag_if_needed()
            if self.fist_start_time is None:
                self.fist_start_time = now
            if not self.fist_triggered and (now - self.fist_start_time) > FIST_HOLD_SECONDS:
                self.paused = not self.paused
                self.fist_triggered = True
            self.status = "PAUSED" if self.paused else "fist... hold to toggle"
            return
        else:
            self.fist_start_time = None
            self.fist_triggered = False

        if self.paused:
            self.status = "PAUSED  (hold a fist to resume)"
            return

        # ---- SCROLL: index + middle up together, ring & pinky down ---------
        if fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            if euclidean_distance(index_tip, middle_tip) < SCROLL_FINGERS_TOGETHER_DIST:
                avg_y = (index_tip[1] + middle_tip[1]) / 2
                if self.last_scroll_y is not None:
                    delta = self.last_scroll_y - avg_y  # hand moves UP -> scroll up
                    if abs(delta) > SCROLL_DEAD_ZONE:
                        pyautogui.scroll(int(delta * SCROLL_SENSITIVITY))
                self.last_scroll_y = avg_y
                self._release_drag_if_needed()
                self.status = "SCROLLING"
                return
        self.last_scroll_y = None

        # ---- Cursor always follows the index fingertip from here on --------
        raw_x, raw_y = self.map_to_screen(*index_tip)
        curr_x, curr_y = self.smooth(raw_x, raw_y)
        curr_x = min(max(curr_x, 0), self.screen_w - 1)
        curr_y = min(max(curr_y, 0), self.screen_h - 1)
        pyautogui.moveTo(curr_x, curr_y)

        # ---- LEFT pinch (thumb + index): click or drag ----------------------
        pinch_click_dist = euclidean_distance(thumb_tip, index_tip)
        is_click_pinching = pinch_click_dist < CLICK_DISTANCE

        if is_click_pinching:
            if self.pinch_start_time is None:
                self.pinch_start_time = now
            held = now - self.pinch_start_time
            if not self.is_dragging and held > DRAG_HOLD_SECONDS:
                pyautogui.mouseDown()
                self.is_dragging = True
            self.status = "DRAGGING" if self.is_dragging else "pinch... hold to drag"
            return

        # pinch just released this frame?
        if self.pinch_start_time is not None:
            held = now - self.pinch_start_time
            if self.is_dragging:
                pyautogui.mouseUp()
                self.is_dragging = False
                self.status = "dropped"
            elif held <= DRAG_HOLD_SECONDS:
                pyautogui.click()
                self.status = "CLICK!"
            self.pinch_start_time = None
            return

        # ---- RIGHT pinch (thumb + middle): right-click, edge-triggered -----
        pinch_right_dist = euclidean_distance(thumb_tip, middle_tip)
        if pinch_right_dist < CLICK_DISTANCE:
            if not self.was_right_pinching:
                pyautogui.rightClick()
                self.status = "RIGHT CLICK!"
            self.was_right_pinching = True
            return
        self.was_right_pinching = False

        self.status = "moving"


# ==============================================================================
# 6. DRAWING HELPERS  (the on-screen visual feedback window)
# ==============================================================================

def draw_hand_skeleton(frame, points):
    for a, b in HAND_BONES:
        cv2.line(frame, points[a], points[b], (0, 220, 0), 2)
    for i, p in enumerate(points):
        color = (0, 140, 255) if i in (THUMB_TIP, INDEX_TIP, MIDDLE_TIP) else (0, 220, 0)
        cv2.circle(frame, p, 5, color, -1)


def draw_overlay(frame, controller, fps):
    h, w = frame.shape[:2]

    cv2.rectangle(frame, (FRAME_MARGIN, FRAME_MARGIN),
                  (w - FRAME_MARGIN, h - FRAME_MARGIN), (255, 255, 255), 1)

    status_color = (0, 220, 0)
    if controller.paused:
        status_color = (0, 0, 255)
    elif controller.is_dragging:
        status_color = (0, 165, 255)
    elif "SCROLL" in controller.status:
        status_color = (255, 200, 0)

    cv2.putText(frame, controller.status, (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, status_color, 2)
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 200), 1)
    cv2.putText(frame, "q = quit", (12, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (150, 150, 150), 1)


# ==============================================================================
# 7. MAIN LOOP
# ==============================================================================

def main():
    ensure_model_downloaded()

    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    screen_w, screen_h = pyautogui.size()

    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    if not cap.isOpened():
        raise SystemExit(
            "\nCouldn't open the webcam.\n"
            "On macOS this is almost always a permissions issue:\n"
            "  System Settings -> Privacy & Security -> Camera\n"
            "  -> enable access for Terminal (or iTerm2 / VS Code, whichever you're running from).\n"
        )

    controller = GestureMouseController(screen_w, screen_h, CAM_WIDTH, CAM_HEIGHT)

    print("Hand Gesture Control is running.")
    print(f"Screen resolution detected: {screen_w}x{screen_h}")
    print("Show your hand to the camera. Press 'q' in the video window to quit.\n")

    prev_frame_time = time.time()

    try:
        with HandLandmarker.create_from_options(options) as landmarker:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Camera frame grab failed, stopping.")
                    break

                frame = cv2.flip(frame, 1)  # mirror, so hand-right = cursor-right
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int(time.time() * 1000)

                result = landmarker.detect_for_video(mp_image, timestamp_ms)

                if result.hand_landmarks:
                    hand = result.hand_landmarks[0]
                    points = [(int(lm.x * CAM_WIDTH), int(lm.y * CAM_HEIGHT)) for lm in hand]

                    draw_hand_skeleton(frame, points)
                    controller.update(points, time.time())
                else:
                    controller.status = "no hand detected"
                    controller._release_drag_if_needed()

                now = time.time()
                fps = 1.0 / max(now - prev_frame_time, 1e-6)
                prev_frame_time = now

                draw_overlay(frame, controller, fps)
                cv2.imshow(WINDOW_NAME, frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        controller._release_drag_if_needed()
        cap.release()
        cv2.destroyAllWindows()
        print("Stopped. Bye!")


if __name__ == "__main__":
    main()