# 🖐️ Hand Gesture Mouse Control for macOS

Control your Mac's cursor, clicks, drag, and scroll using a webcam and hand gestures. The app runs on your Mac and sends ordinary mouse actions to the desktop; no special receiver or companion app is needed.

This project is designed for **macOS desktop computers**. It is not a mobile app and is not currently documented or tested for Windows or Linux.

## 🎯 How It Works

1. **OpenCV** reads live frames from the selected camera.
2. **MediaPipe Hand Landmarker** detects up to one hand and returns 21 landmarks (fingertips, joints, and wrist).
3. The program uses distances and finger positions to recognize the gestures below.
4. **PyAutoGUI** moves the macOS pointer and sends clicks, drags, and scrolls.

Frames are analyzed locally. The program does not record or upload camera video. If the hand-landmarker model file is missing, the program downloads it from Google's MediaPipe model host.

## 💻 Device and Platform Support

| Device/setup | Support |
| --- | --- |
| Mac desktop or laptop running macOS | Target platform; requires a Python environment that can install the listed packages |
| Built-in Mac webcam | Supported when macOS grants camera access |
| USB/external webcam | Usually works if OpenCV can open it; change `CAM_INDEX` if it is not the default camera |
| Mac screen and mouse-driven apps | The app controls the system pointer, so it can operate standard mouse controls in most desktop apps |
| Windows or Linux computer | Not currently documented or tested by this project |
| iPhone, iPad, Android phone/tablet, smart TV, or game console | Not supported; this is a Python desktop program, not an installable mobile or embedded app |

### What you need

- A Mac with a working webcam (built-in or compatible USB camera).
- A display, keyboard, and macOS user session. The keyboard is used to quit the camera window.
- Python 3 and the packages in `requirements.txt`. Choose a Python release for which pip can install the current MediaPipe, OpenCV, and PyAutoGUI packages.
- macOS camera permission for the app used to launch Python, and Accessibility permission if macOS requests it for mouse control.
- An internet connection for package installation and, only if `hand_landmarker.task` is missing, the one-time model download.

This program does not emulate a touchscreen, type text, recognize speech, or control a device over the network. Gestures produce mouse actions on the Mac running the program.

---

## 🤚 Hand Gestures

### 1. **Point (Index Finger Only)**

- **Gesture**: Extend only your index finger, keep other fingers curled
- **Action**: Move the cursor
- **How it works**: The app tracks your index fingertip and moves the cursor to follow it in real-time

### 2. **Click (Thumb + Index Pinch)**

- **Gesture**: Pinch your thumb and index finger together (touch them)
- **Action**: Single left-click
- **Duration**: Quick pinch (less than 0.3 seconds)
- **Distance Setting**: Thumb-to-index must be closer than `CLICK_DISTANCE` (38px by default)

### 3. **Drag (Thumb + Index Hold)**

- **Gesture**: Pinch thumb and index finger together and hold
- **Action**: Click and drag
- **Duration**: Hold the pinch for more than 0.3 seconds (`DRAG_HOLD_SECONDS`)
- **How to use**:
  - Pinch and hold to start dragging
  - Move your hand to drag
  - Release the pinch to drop

### 4. **Right-Click (Thumb + Middle Pinch)**

- **Gesture**: Pinch your thumb and middle finger together
- **Action**: Right-click (context menu)
- **Edge-Triggered**: Fires once when you start the pinch
- **Distance Setting**: Thumb-to-middle must be closer than `CLICK_DISTANCE` (38px)

### 5. **Scroll (Index + Middle Up)**

- **Gesture**: Hold up your index and middle fingers together, close to each other
- **Action**: Scroll up/down
- **How to use**:
  - Point index and middle fingers up, keep them close together
  - Move your hand UP to scroll up
  - Move your hand DOWN to scroll down
- **Settings**:
  - `SCROLL_FINGERS_TOGETHER_DIST`: How close fingers must be (60px default)
  - `SCROLL_SENSITIVITY`: How far page scrolls per hand movement (2.0x default)
  - `SCROLL_DEAD_ZONE`: Ignore tiny tremors below this threshold (2px default)

### 6. **Pause/Resume (Fist)**

- **Gesture**: Make a closed fist with all fingers curled
- **Action**: Toggle pause/resume of gesture control
- **Duration**: Hold the fist for 0.8 seconds (`FIST_HOLD_SECONDS`)
- **Visual Indicator**: Status changes to "PAUSED" in red text
- **Safety**: Automatically releases any active drag when fist is made

### 7. **Quit**

- **Key**: Press **'q'** in the camera window to exit

---

## 📋 Gesture Summary Table

| Gesture              | Action       | Keys/Fingers       | Duration      |
| -------------------- | ------------ | ------------------ | ------------- |
| Index pointing       | Move cursor  | Index only         | Continuous    |
| Thumb + Index pinch  | Left-click   | Quick pinch        | < 0.3s        |
| Thumb + Index hold   | Drag         | Hold pinch         | > 0.3s        |
| Thumb + Middle pinch | Right-click  | Quick pinch        | Instant       |
| Index + Middle up    | Scroll       | Both up, close     | Hand movement |
| Closed Fist          | Toggle pause | All fingers curled | Hold 0.8s     |
| Press 'q'            | Quit         | Keyboard           | Once          |

---

## 🚀 Installation & Setup

The commands below are for macOS Terminal and assume Git and Python 3 are installed.

### 1. Clone the repository

```bash
git clone https://github.com/ShashankCodeX/Hand-Gesture-Control.git
cd Hand-Gesture-Control
```

Alternatively, download the repository as a ZIP and open Terminal in the extracted project folder.

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project includes `hand_landmarker.task`. If it is absent when you start the script, the script attempts to download it. The download requires internet access.

### 4. Grant macOS permissions

1. Open **System Settings → Privacy & Security → Camera** and allow the launcher you use (for example, Terminal or VS Code).
2. If macOS blocks pointer control, open **System Settings → Privacy & Security → Accessibility** and allow that same launcher.
3. Restart the program after changing permissions if the camera or pointer is still unavailable.

Permission names and prompts can differ slightly between macOS versions. Grant access only to the launcher you trust.

### 5. Run the application

```bash
python gesture_control.py
```

The camera preview opens in a window. Press **q** while that window is focused to quit. In the preview, the white rectangle is the active hand-position area; the cursor maps from that area to the full screen.

---

## ⚙️ Tuning Guide

Edit these values in `gesture_control.py` to customize how the app feels:

### Camera Settings

```python
CAM_INDEX = 0                  # 0 = default camera, 1 = external camera
CAM_WIDTH, CAM_HEIGHT = 640, 480   # Camera resolution
FRAME_MARGIN = 100             # Pixels from edge that are ignored (prevents edge artifacts)
```

### Cursor Smoothing

```python
SMOOTHING = 5                  # 1 = raw/jittery, higher = smoother but more lag
                               # Recommended: 3-8
```

### Click & Drag Settings

```python
CLICK_DISTANCE = 38            # Pixels: thumb-to-finger distance to trigger pinch
                               # Lower = must pinch tighter
                               # Higher = pinches easier (but may trigger accidentally)

DRAG_HOLD_SECONDS = 0.30       # How long to hold pinch before it becomes a drag
```

### Pause/Resume

```python
FIST_HOLD_SECONDS = 0.8        # How long to hold a fist to toggle pause
```

### Scroll Settings

```python
SCROLL_FINGERS_TOGETHER_DIST = 60   # Pixels: how close index+middle must be
SCROLL_SENSITIVITY = 2.0            # Higher = faster scrolling
SCROLL_DEAD_ZONE = 2                # Ignore tremors smaller than this
```

---

## 🎮 Usage Tips

### Best Practices

1. **Lighting**: Use good lighting for best hand detection
2. **Distance**: Position yourself 1-2 feet from the camera
3. **Background**: Plain backgrounds work better than busy scenes
4. **Hand Position**: Keep your hand clearly visible and not too close to the camera
5. **Pause When Not Using**: Make a fist to pause control and avoid accidental clicks

### Troubleshooting

#### "No hand detected"

- Move your hand closer to the camera
- Improve lighting
- Make sure your hand is fully visible
- Check that your camera is working

#### Cursor is jittery

- Increase `SMOOTHING` value (try 6-8 instead of 5)
- Improve lighting conditions
- Make sure you're not too close to the camera

#### Clicks are too sensitive/not sensitive enough

- Too sensitive? Increase `CLICK_DISTANCE` (try 45-50)
- Not sensitive enough? Decrease `CLICK_DISTANCE` (try 30-35)

#### Drag stops unexpectedly

- Increase `DRAG_HOLD_SECONDS` slightly (try 0.4 or 0.5)
- Make sure you're not accidentally opening/closing fingers

#### Scroll not working

- Make sure index and middle fingers are close together
- Adjust `SCROLL_FINGERS_TOGETHER_DIST` if needed
- Increase `SCROLL_SENSITIVITY` for faster scrolling

#### Camera permission denied

- macOS: System Settings → Privacy & Security → Camera
- Grant access to Terminal/VS Code
- Restart the application

---

## 🖥️ On-Screen Indicators

While the app is running, you'll see:

- **Status Text** (top-left): Current gesture/action being performed
- **FPS Counter** (top-right): Measured processing/display rate; it varies with the Mac, camera, lighting, and other running apps
- **White Rectangle**: The "active zone" - moves your cursor only within this area
- **Green Skeleton**: Hand landmarks and connections being tracked
- **Orange Points**: Thumb, index, and middle fingertips used for gesture detection

### Status Colors

- **Green**: Normal operation
- **Cyan/blue**: Scrolling
- **Orange**: Dragging
- **Red**: Paused

---

## 📊 Hand Anatomy (for reference)

The app tracks 21 precise points on your hand:

```
         8   12  16  20    (fingertips)
         |    |   |   |
         7   11  15  19    (middle joints)
     4   |    |   |   |
     |   6   10  14  18    (base joints)
     3   |    |   |   |
     |   5    9  13  17
     2    \   |   |  /
      \    \  |  | /
       1    \ | | /
        \    \||/
         0 -- WRIST         (wrist)
```

- **Thumb**: Points 1-4
- **Index**: Points 5-8
- **Middle**: Points 9-12
- **Ring**: Points 13-16
- **Pinky**: Points 17-20
- **Wrist**: Point 0

---

## 🔧 Technical Details

### Requirements

- **opencv-python**: Video capture and display
- **mediapipe**: Hand detection and landmark tracking
- **pyautogui**: Mouse control
- **numpy**: Numerical calculations

### Model

- Uses Google's **MediaPipe Hand Landmarker** (float16 version)
- The model is included in this repository; if it is missing, the script automatically downloads it (about 7 MB)
- Runs inference on the CPU; GPU acceleration is disabled by the script

### Performance

- Processing speed and cursor response depend on the Mac, camera, lighting, and background workload; no fixed frame-rate or latency is guaranteed
- Good lighting, a visible hand, and a steady camera generally improve tracking

---

## ⚠️ Safety

### PyAutoGUI Failsafe

PyAutoGUI's **failsafe** is enabled. Moving the pointer to a screen corner can raise its failsafe exception and stop the control loop. The program's cleanup code releases an active drag and closes the camera. This is a backup, not a substitute for keeping the quit key available.

### Always Remember

- Press **'q'** anytime to quit the application
- Make a **fist** to pause gesture control temporarily
- Keep your hand visible to the camera for best results
- Keep the camera window and your keyboard accessible; do not rely on gesture control for safety-critical or precision tasks

---

## 📝 Example Workflows

### Browsing the Web

1. **Point** with index finger to move cursor over links
2. **Click** (pinch thumb + index) to click links
3. **Scroll** (index + middle up together) to scroll up/down
4. **Right-click** (pinch thumb + middle) for context menu

### Dragging Files

1. **Point** to position cursor over file
2. **Hold pinch** (thumb + index) to start dragging
3. **Move hand** to drag file to new location
4. **Release pinch** to drop file

### Video Calling

1. **Point** to move cursor
2. **Pause** (make fist) when not needed to prevent accidental clicks
3. **Scroll** (index + middle) if needed during call

---

## 🐛 Known Limitations

- Works best with one hand at a time
- Requires good lighting conditions
- May have slight lag on older Macs
- Not recommended for high-precision work (e.g., photo editing)
- Best used at 1-2 feet distance from camera

---

## 📚 Learn More

See the source code in `gesture_control.py` for detailed comments explaining every part of the implementation.

---

## 🎉 Enjoy!

Have fun controlling your Mac with hand gestures! Experiment with the tuning settings to find what works best for you.

**Pro Tip**: The more you use it, the more natural the gestures will feel. Practice makes perfect! 🖐️
