import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2):
        self.hands = mp.solutions.hands.Hands(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            max_num_hands=max_num_hands
        )

    def process_frame(self, image):
        # Flip, convert color, and process the frame
        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rgb_image.flags.writeable = False
        
        results = self.hands.process(rgb_image)
        
        rgb_image.flags.writeable = True
        return results, image

    def close(self):
        self.hands.close()