import cv2
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from renderer import Renderer

class App:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")
        
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.renderer = Renderer()

    def run(self):
        print("Starting Gestura. Press 'q' to quit.")
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                continue

            results, processed_frame = self.hand_tracker.process_frame(frame)

            recognized_gesture = None
            finger_states = {}

            if results.multi_hand_landmarks:
                # For simplicity, we'll only process the first hand detected
                hand_landmarks = results.multi_hand_landmarks[0]
                recognized_gesture, finger_states = self.gesture_recognizer.recognize(hand_landmarks)

            display_frame = self.renderer.draw(processed_frame, results, recognized_gesture, finger_states)
            cv2.imshow('Gestura', display_frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        self._cleanup()

    def _cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.hand_tracker.close()
        print("Gestura stopped.")