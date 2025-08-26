# Gestura 🤌

A modular, real-time hand gesture recognition system for controlling your computer. Built with Python, OpenCV, and MediaPipe, Gestura runs silently in the background, mapping your hand gestures to custom shell commands and scripts.

## Features

- **Robust Gesture Recognition:** Uses a rotation-invariant algorithm based on the hand's geometry, providing consistent detection regardless of hand orientation.
- **Highly Configurable:**
  - **Custom Gestures:** Define complex gestures like "SPIDERMAN" or "OKAY" in a simple `gestures.json` file without changing any code.
  - **Custom Actions:** Easily map single gestures or gesture combos (e.g., "ONE-FIST") to any shell command in `actions.json`.
  - **Tuning:** Adjust sensitivity, cooldowns, and combo timeouts via constants in the code.
- **Gesture Combos:** Chain simple gestures together to trigger complex actions, preventing accidental triggers.
- **Headless by Default:** Runs silently in the background, providing subtle, cross-platform desktop notifications on action triggers.
- **Visual Debug Mode:** A comprehensive debug view (`--debug`) shows the live camera feed, hand landmarks, and the real-time state of each finger.
- **Stable and Reliable:** A gesture "stabilizer" filters out noisy, instantaneous flickers, ensuring that only deliberate poses trigger actions.

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
    This single command installs everything needed, including the cross-platform notification library.
    ```bash
    pip install -r requirements.txt
    ```

## Usage

#### 1. Headless Mode (Default)

Runs silently in the background. It will print detected gestures to the terminal and execute their corresponding commands, sending a brief desktop notification for feedback.

```bash
python3 main.py
```

Press `Ctrl+C` to stop.

#### 2. Debug Mode

Launches a window showing the live camera feed with landmarks and detailed debug information.

```bash
python3 main.py --debug
```

Press `q` while the window is active to quit.

## Configuration

Customizing Gestura is done entirely through JSON files.

#### 1. Defining Custom Gestures (`gestures.json`)

Create new gestures by defining the state of each finger. States are `"Extended"` or `"Curled"`.

```json
{
  "SPIDERMAN": {
    "thumb": "Extended",
    "index": "Extended",
    "middle": "Curled",
    "ring": "Curled",
    "pinky": "Extended"
  },
  "OKAY": {
    "thumb": "Extended",
    "index": "Extended",
    "middle": "Curled",
    "ring": "Curled",
    "pinky": "Curled"
  }
}
```

**Note:** It's best to avoid using hyphens (`-`) in gesture names, as this character is used to define combos in `actions.json`.

#### 2. Mapping Actions to Gestures (`actions.json`)

Link a recognized gesture name (either a default, a custom one, or a combo) to a shell command. For combos, join gesture names with a hyphen.

```json
{
  "FIST": "~/scripts/media-toggle.sh",
  "ONE": "amixer -D pulse sset Master 5%-",
  "TWO": "amixer -D pulse sset Master 5%+",
  "SPIDERMAN": "gnome-screenshot",
  "ONE-FIST": "xdotool key super+l"
}
```

#### 3. Tuning Sensitivity and Timing

You can fine-tune responsiveness by editing constants at the top of these files:

- `gesture_stabilizer.py`: Change `CONFIRMATION_THRESHOLD` to control how long a gesture must be held.
- `combo_manager.py`: Change `COMBO_TIMEOUT` to set the max time between gestures in a combo.
- `app.py`: Change `ACTION_COOLDOWN` to set the minimum time between single gesture actions.
