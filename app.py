# ~/Code/gestura/app.py
import cv2
import time
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from renderer import Renderer
from action_executor import ActionExecutor
from gesture_stabilizer import GestureStabilizer
from combo_manager import ComboManager

ACTION_COOLDOWN = 1.0 # seconds

class App:
    def __init__(self, debug=False):
        self.debug = debug
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")

        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.action_executor = ActionExecutor(is_headless=not self.debug)
        self.renderer = Renderer()
        self.combo_manager = ComboManager()
        
        # We need a separate stabilizer for each potential hand
        self.stabilizers = [GestureStabilizer(), GestureStabilizer()]
        
        # --- State Tracking ---
        # Tracks the last gesture that triggered an action to manage cooldown
        self.last_action_gesture = None
        self.last_action_time = 0
        
        # Tracks the last stable gesture seen to avoid re-triggering logic on the same gesture
        self.last_stable_gesture_seen = None

    def _process_frame(self):
        """Processes a single frame for gestures and returns data for rendering."""
        success, frame = self.cap.read()
        if not success:
            return None, None, []

        results, processed_frame = self.hand_tracker.process_frame(frame)
        hands_data = []

        if results.multi_hand_landmarks:
            # For simplicity, we'll only process gestures and combos for the *first* detected hand.
            # This avoids ambiguity when two hands are showing different things.
            first_hand_landmarks = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label
            stabilizer = self.stabilizers[0]

            raw_gesture, finger_states = self.gesture_recognizer.recognize(first_hand_landmarks, handedness)
            stable_gesture = stabilizer.update(raw_gesture)

            print(f"Hand 0 ({handedness}) | Raw: {raw_gesture} -> Stable: {stable_gesture}", end='\r')

            # --- Action & Combo Logic ---
            # We only act when a *new* stable gesture is confirmed.
            if stable_gesture and stable_gesture != self.last_stable_gesture_seen:
                self.last_stable_gesture_seen = stable_gesture
                
                combo_string = self.combo_manager.update(stable_gesture)
                print(f"\nNew stable gesture: {stable_gesture} | Current combo: {combo_string}")

                # 1. Check if the current sequence is a valid combo action
                if self.action_executor.get_action(combo_string):
                    self.action_executor.execute(combo_string)
                    self.combo_manager.reset() # Combo was successful, reset for the next one
                    # Reset cooldown timers as well
                    self.last_action_time = time.time()
                    self.last_action_gesture = combo_string
                
                # 2. If not a combo, check if it's a valid single action
                elif self.action_executor.get_action(stable_gesture):
                    current_time = time.time()
                    if stable_gesture != self.last_action_gesture or \
                       (current_time - self.last_action_time > ACTION_COOLDOWN):
                        
                        self.action_executor.execute(stable_gesture)
                        self.last_action_gesture = stable_gesture
                        self.last_action_time = current_time

            elif not stable_gesture:
                self.last_stable_gesture_seen = None

            # For rendering, process all hands
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                if i >= len(self.stabilizers): break
                h_handedness = results.multi_handedness[i].classification[0].label
                h_raw, h_states = self.gesture_recognizer.recognize(hand_landmarks, h_handedness)
                h_stable = self.stabilizers[i].update(h_raw)
                hands_data.append({
                    "handedness": h_handedness, "raw_gesture": h_raw,
                    "stable_gesture": h_stable, "states": h_states
                })
                
        return results, processed_frame, hands_data

    def run(self):
        """The main application loop."""
        if self.debug:
            print("Running in DEBUG mode. Press 'q' in the window to quit.")
        else:
            print("Running in HEADLESS mode. Press Ctrl+C to quit.")

        while True:
            try:
                results, frame, hands_data = self._process_frame()
                if frame is None:
                    break

                if self.debug:
                    display_frame = self.renderer.draw(frame, results, hands_data)
                    cv2.imshow("Gestura - Debug", display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    time.sleep(0.01)

            except KeyboardInterrupt:
                break
        
        self._cleanup()

    def _cleanup(self):
        print("\nClosing camera and windows...")
        self.cap.release()
        self.hand_tracker.close()
        if self.debug:
            cv2.destroyAllWindows()