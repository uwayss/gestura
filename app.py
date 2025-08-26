# ~/Code/gestura/app.py
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np

from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from renderer import Renderer

# --- Constants ---
PIP_WIDTH = 320
PIP_HEIGHT = 240

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Gestura PiP")
        self.overrideredirect(True)  # Create a borderless window
        self.wm_attributes("-topmost", True) # Keep it always on top

        # Position the window in the top-right corner
        screen_width = self.winfo_screenwidth()
        x_pos = screen_width - PIP_WIDTH - 20 # 20px margin
        y_pos = 20
        self.geometry(f"{PIP_WIDTH}x{PIP_HEIGHT}+{x_pos}+{y_pos}")

        # --- Gestura Setup ---
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")

        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.renderer = Renderer()

        # --- Tkinter UI ---
        self.canvas = tk.Label(self)
        self.canvas.pack()

        # Start the main loop
        self.update_frame()

    def update_frame(self):
        """The main application loop."""
        success, frame = self.cap.read()
        if not success:
            self.after(10, self.update_frame)
            return

        # --- Core Logic ---
        results, processed_frame = self.hand_tracker.process_frame(frame)
        
        # Create the small black background for our PiP window
        pip_background = np.zeros((PIP_HEIGHT, PIP_WIDTH, 3), dtype=np.uint8)
        
        # Scale landmarks to the PiP window size
        # (This is a simplified approach, MediaPipe drawing handles it)
        display_frame = self.renderer.draw(pip_background, results)

        # --- Display in Tkinter ---
        # Convert the OpenCV (BGR) image to a PIL (RGB) image
        img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        self.canvas.imgtk = img_tk
        self.canvas.configure(image=img_tk)

        # Schedule the next update
        self.after(10, self.update_frame)

    def run(self):
        """Starts the Tkinter main loop."""
        print("Starting Gestura PiP. Close the window or press Ctrl+C to quit.")
        self.mainloop()

    def _cleanup(self):
        print("Closing camera...")
        self.cap.release()
        self.hand_tracker.close()