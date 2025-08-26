# ~/Code/gestura/combo_manager.py
import time

# Max seconds between gestures to be considered part of a combo.
COMBO_TIMEOUT = 1.5

class ComboManager:
    def __init__(self):
        self.sequence = []
        self.last_gesture_time = 0

    def update(self, gesture_name):
        """
        Updates the current gesture sequence. Resets if timeout is exceeded.
        Returns the current combo string (e.g., "ONE-FIST").
        """
        current_time = time.time()

        if not gesture_name:
            return None
        
        # If the time since the last gesture is too long, start a new sequence.
        if current_time - self.last_gesture_time > COMBO_TIMEOUT:
            self.sequence = []

        self.sequence.append(gesture_name)
        self.last_gesture_time = current_time
        
        return "-".join(self.sequence)

    def reset(self):
        """Clears the current combo sequence."""
        self.sequence = []
        self.last_gesture_time = 0
        print("Combo sequence reset.")