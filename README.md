# Gestura 🤌

A modular, real-time hand gesture recognition system built with Python, OpenCV, and MediaPipe. It displays a small, borderless, always-on-top "picture-in-picture" window, making it ideal for controlling your system without an intrusive UI.

## Features

- **Real-Time Performance:** Uses Google's MediaPipe for fast and accurate hand tracking.
- **Minimalist UI:** A small, borderless, picture-in-picture overlay keeps your screen clear.
- **Cross-Platform:** Built with Tkinter, it works on Linux, Windows, and macOS.
- **Extremely Modular:** Code is split into logical components (Tracker, Recognizer, Renderer), making it easy to modify.
- **Data-Driven Gestures:** Adding new gestures is as simple as defining them in a dictionary.

## Setup & Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/uwayss/gestura.git
    cd gestura
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Requires a Python version >= 3.8
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main application from the root of the project directory.

```bash
python3 main.py
```

A small window showing your hand landmarks will appear in the top-right corner of your screen. To close it, either bring the terminal into focus and press `Ctrl+C`, or you may need to kill the process via your system monitor.

## How to Add a New Gesture

1.  Open `gesture_recognizer.py`.
2.  Add a new entry to the `GESTURE_DEFINITIONS` dictionary, specifying the required state ("Extended" or "Curled") for all five fingers.
    ```python
    # gesture_recognizer.py
    "THUMBS_UP": {
        "thumb": "Extended", "index": "Curled", "middle": "Curled",
        "ring": "Curled", "pinky": "Curled"
    },
    ```
