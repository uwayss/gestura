# Gestura 🤌

A modular, real-time hand gesture recognition system for controlling your computer. Built with Python, OpenCV, and MediaPipe, Gestura runs silently in the background, mapping your hand gestures to custom shell commands and scripts.

## Features

- **State-Driven Gesture Recognition:** Define gestures based on a combination of hand properties: handedness, palm orientation (front/back), finger direction (up/down/left/right), and individual finger states (curled/extended).
- **Highly Expressive Configuration:** A simple `gestures.json` allows for creating specific, unambiguous gestures without changing any code.
- **Gesture Combos:** Chain gestures together (e.g., `volume_up-fist`) to trigger complex actions.
- **Headless by Default:** Runs silently, providing subtle, cross-platform desktop notifications on action triggers.
- **Advanced Visual Debug Mode:** A comprehensive debug view (`--debug`) shows the live camera feed, hand landmarks, and the real-time analysis of the hand's state (direction, orientation, etc.), making it easy to create new gestures.
- **Stable and Reliable:** A gesture "stabilizer" filters out noisy flickers, ensuring only deliberate poses trigger actions.

## Setup & Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/uwayss/gestura.git
    cd gestura
    ```

2.  **Create and Activate a Virtual Environment:**

    ```bash
    # Requires Python >= 3.8
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

#### 1. Headless Mode (Default)

Runs silently in the background, executing commands and sending a brief desktop notification for feedback.

```bash
python3 main.py
```

Press `Ctrl+C` to stop.

#### 2. Debug Mode

Launches a window showing the live camera feed with detailed state analysis for each hand. This mode is essential for defining and testing new gestures.

```bash
python3 main.py --debug
```

Press `q` while the window is active to quit.

## Configuration

Customizing Gestura is done entirely through JSON files. Gesture names are always lowercase.

#### 1. Defining Custom Gestures (`gestures.json`)

A gesture is defined by a set of `conditions` that the live hand state must match. You can omit any condition to make the gesture more general.

```json
{
  "volume_up": {
    "conditions": {
      "handedness": "right",
      "direction": "up",
      "fingers": {
        "index": "extended",
        "middle": "extended"
      }
    }
  },
  "fist": {
    "conditions": {
      "fingers": {
        "thumb": "curled",
        "index": "curled",
        "middle": "curled",
        "ring": "curled",
        "pinky": "curled"
      }
    }
  }
}
```

**Available Conditions:**

- `"handedness"`: `"left"` or `"right"`
- `"orientation"`: `"front"` (palm facing camera) or `"back"` (knuckles facing camera)
- `"direction"`: `"up"`, `"down"`, `"left"`, or `"right"` (based on the vector from wrist to knuckles)
- `"fingers"`: An object specifying the required state (`"extended"` or `"curled"`) for one or more fingers (`"thumb"`, `"index"`, `"middle"`, `"ring"`, `"pinky"`).

#### 2. Mapping Actions to Gestures (`actions.json`)

Link a recognized gesture name (or a combo) to a shell command.

```json
{
  "fist": "~/scripts/media-toggle.sh",
  "volume_down": "amixer -D pulse sset Master 5%-",
  "volume_up": "amixer -D pulse sset Master 5%+",
  "volume_up-fist": "xdotool key super+l"
}
```

#### 3. Tuning Sensitivity and Timing

You can fine-tune responsiveness by editing constants at the top of these files:

- `gesture_stabilizer.py`: `CONFIRMATION_THRESHOLD`
- `combo_manager.py`: `COMBO_TIMEOUT`
- `app.py`: `ACTION_COOLDOWN`
