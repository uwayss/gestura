import cv2
import mediapipe as mp
import numpy as np

class Renderer:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_hands = mp.solutions.hands

    def _draw_debug_info(self, image, finger_states):
        y_pos = 50
        for finger, state in finger_states.items():
            color = (0, 255, 0) if state == "Extended" else (0, 0, 255)
            text = f"{finger.capitalize()}: {state}"
            cv2.putText(image, text, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_pos += 30

    def _draw_recognized_gesture(self, image, gesture_name):
        if gesture_name:
            cv2.putText(image, gesture_name, (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)

    def _draw_landmarks(self, image, hand_landmarks):
        self.mp_drawing.draw_landmarks(
            image=image,
            landmark_list=hand_landmarks,
            connections=self.mp_hands.HAND_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_hand_landmarks_style(),
            connection_drawing_spec=self.mp_drawing_styles.get_default_hand_connections_style()
        )

    def draw(self, frame, hand_results, recognized_gesture, finger_states):
        # Create a black background
        black_background = np.zeros_like(frame)

        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self._draw_landmarks(black_background, hand_landmarks)

        self._draw_debug_info(black_background, finger_states)
        self._draw_recognized_gesture(black_background, recognized_gesture)
        
        return black_background