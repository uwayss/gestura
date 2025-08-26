# ~/Code/gestura/renderer.py
import cv2
import mediapipe as mp

class Renderer:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_hands = mp.solutions.hands

    def _draw_debug_info(self, image, hands_data):
        frame_width = image.shape[1]
        for i, hand_data in enumerate(hands_data):
            handedness = hand_data["handedness"]
            hand_state = hand_data["state"] # This now contains all the info
            raw_gesture = hand_data["raw_gesture"]
            stable_gesture = hand_data["stable_gesture"]
            
            x_pos = 50 if handedness.lower() == "left" else frame_width - 300
            y_pos = 50
            
            # Display Gestures
            cv2.putText(image, f"Raw: {raw_gesture}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
            y_pos += 30
            cv2.putText(image, f"Stable: {stable_gesture}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            y_pos += 40

            # Display Hand State
            state_info = [
                f'Hand: {hand_state.get("handedness", "N/A")}',
                f'Direction: {hand_state.get("direction", "N/A")}',
                f'Orientation: {hand_state.get("orientation", "N/A")}'
            ]
            for info in state_info:
                cv2.putText(image, info, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)
                y_pos += 30
            y_pos += 10

            # Display Finger States
            for finger, state in hand_state.get("fingers", {}).items():
                color = (0, 255, 0) if state == "extended" else (0, 0, 255)
                text = f"{finger.capitalize()}: {state}"
                cv2.putText(image, text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_pos += 25


    def draw(self, frame, hand_results, hands_data=[]):
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image=frame, landmark_list=hand_landmarks,
                    connections=self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    connection_drawing_spec=self.mp_drawing_styles.get_default_hand_connections_style()
                )
        
        if hands_data:
            self._draw_debug_info(frame, hands_data)

        return frame