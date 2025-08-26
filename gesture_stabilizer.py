# ~/Code/gestura/gesture_stabilizer.py

# How many consecutive frames a gesture must be detected before it's considered "stable".
# A higher number means less sensitivity but more delay. 5 is a good starting point.
CONFIRMATION_THRESHOLD = 1

class GestureStabilizer:
    def __init__(self):
        self.candidate_gesture = None
        self.stable_gesture = None
        self.confirmation_frames = 0

    def update(self, raw_gesture):
        """
        Processes a raw gesture from a single frame and returns a stable gesture
        only after it has been detected for a set number of consecutive frames.
        """
        if raw_gesture == self.candidate_gesture:
            # If we see the same gesture again, increment the confirmation counter.
            self.confirmation_frames += 1
        else:
            # If the gesture changes, reset the counter and set a new candidate.
            self.candidate_gesture = raw_gesture
            self.confirmation_frames = 1

        # If the confirmation count reaches our threshold...
        if self.confirmation_frames >= CONFIRMATION_THRESHOLD:
            # ...and the candidate is different from the current stable gesture...
            if self.candidate_gesture != self.stable_gesture:
                # ...then we have a new, confirmed stable gesture.
                self.stable_gesture = self.candidate_gesture
        
        return self.stable_gesture