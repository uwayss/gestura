# Gestura 🤌

A modular, real-time hand gesture recognition system for controlling your computer. Built with Python, OpenCV, and MediaPipe, Gestura runs silently in the background, mapping your hand gestures to custom shell commands and scripts.

## Features

- **Robust Gesture Recognition:** Uses a rotation-invariant algorithm based on the hand's geometry, providing consistent detection regardless of hand orientation or which palm is facing the camera.
- **Highly Configurable:**
  - **Actions:** Easily map gestures to any shell command or script in a simple `actions.json` file.
  - **Tuning:** Adjust sensitivity and cooldowns via constants in the code.
- **Headless by Default:** Designed to run silently in the background without any UI.
- **Visual Debug Mode:** A comprehensive debug view (`--debug`) shows the live camera feed, hand landmarks, and the real-time state of each finger for easy testing.
- **Stable and Reliable:** A gesture "stabilizer" filters out noisy, instantaneous flickers, ensuring that only deliberate, stable poses trigger actions.
- **Multi-Hand Support:** Tracks and displays data for up to two hands in debug mode.

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

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Gestura can be run in two modes from the project's root directory.

#### 1. Headless Mode (Default)

Runs silently in the background. It will print detected gestures to the terminal and execute their corresponding commands. This is the intended mode for daily use.

```bash
python3 main.py
```

Press `Ctrl+C` in the terminal to stop the application.

#### 2. Debug Mode

Launches a window showing the live camera feed with landmarks and detailed debug information for each hand. This is essential for testing gestures and tuning the recognizer.

```bash
python3 main.py --debug
```

Press `q` while the window is active to quit.

## Configuration

Customizing Gestura is simple and doesn't require changing the core application logic.

#### Mapping Actions to Gestures

Open the `actions.json` file to link a recognized gesture name to a command.

```json
{
  "FIST": "~/scripts/media-toggle.sh",
  "ONE": "amixer -D pulse sset Master 5%-",
  "TWO": "amixer -D pulse sset Master 5%+",
  "FIVE": "gnome-screenshot"
}
```

The key is the gesture name (e.g., `"FIST"`, `"ONE"`, `"TWO"`), and the value is the shell command to execute.

#### Tuning Sensitivity and Timing

You can fine-tune the application's responsiveness by editing the constants at the top of these files:

- `gesture_stabilizer.py`: Change `CONFIRMATION_THRESHOLD` to control how many consecutive frames a gesture must be seen before it's considered "stable". (Higher = less sensitive, more delay).
- `app.py`: Change `ACTION_COOLDOWN` to set the minimum time in seconds between two actions being executed.
