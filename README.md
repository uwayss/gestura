# Gestura 🤌 (Go Version)

A modular, real-time hand gesture recognition system for controlling your computer. This version is built with **Go** for high performance and easy distribution, using a minimal Python helper for MediaPipe integration. Gestura runs silently in the background, mapping your hand gestures to custom shell commands.

## Architecture

The core application is a native Go binary. It spawns a small Python script as a child process. The Python script's only job is to access the webcam, run MediaPipe's hand detection model, and stream the raw landmark data as JSON to `stdout`. The Go application consumes this JSON stream and handles all logic: gesture recognition, state stabilization, combos, and action execution.

This provides the best of both worlds: native performance for the main app and easy access to the Python-exclusive MediaPipe library.

## Setup & Installation

#### 1. System Dependencies

You need Go, Python, and the OpenCV libraries installed.

```bash
# Install Go (e.g., version 1.21+)
sudo apt update
sudo apt install -y golang-go

# Install Python and venv
sudo apt install -y python3-pip python3-venv

# Install OpenCV library required by GoCV
sudo apt install -y libopencv-dev
```

#### 2. Project Setup

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/uwayss/gestura.git
cd gestura
```

#### 3. Setup Python Helper Environment

This creates a self-contained Python environment for MediaPipe inside the `mediapipe_helper` directory.

```bash
python3 -m venv mediapipe_helper/venv
source mediapipe_helper/venv/bin/activate
pip install -r mediapipe_helper/requirements.txt
deactivate
```

#### 4. Setup Go Dependencies

This will download the required Go packages (`gocv` and `beeep`).

```bash
go mod init github.com/uwayss/gestura
go mod tidy
```

## Usage

#### 1. Headless Mode (Default)

Runs silently, executing commands and sending desktop notifications.

```bash
go run .
```

Press `Ctrl+C` to stop.

#### 2. Debug Mode

Launches a window showing the live camera feed with detailed state analysis. Essential for creating and testing gestures.

```bash
go run . --debug
```

Press `q` while the window is active to quit.

## Building a Single Binary

One of the main advantages of Go is creating a single, distributable executable.

```bash
go build -o gestura
```

Now you have a single file named `gestura`. You can run it directly: `./gestura` or `./gestura --debug`.
The binary still depends on the `mediapipe_helper` directory and your JSON configs being in the same folder.

## Configuration

Configuration is identical to the original Python version, using `gestures.json` and `actions.json`. See the original README for details on defining gestures and actions.
