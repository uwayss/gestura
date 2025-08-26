# ~/Code/gestura/gesture_recognizer.py
import math
import json
from utils import HandLandmark

class GestureRecognizer:
    def __init__(self, config_path='gestures.json'):
        self.custom_gestures = self._load_custom_gestures(config_path)

    def _load_custom_gestures(self, config_path):
        try:
            with open(config_path, 'r') as f:
                print(f"Loading custom gestures from '{config_path}'...")
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Custom gesture file '{config_path}' not found. No gestures will be recognized.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{config_path}'.")
            return {}

    def _get_hand_state(self, hand_landmarks, handedness):
        """
        Analyzes a hand's landmarks to determine its complete state,
        including orientation, direction, and individual finger states.
        """
        landmarks = hand_landmarks.landmark
        
        # --- Common Landmark Points ---
        p0 = landmarks[HandLandmark.WRIST]
        p2 = landmarks[HandLandmark.THUMB_MCP]
        p4 = landmarks[HandLandmark.THUMB_TIP]
        p5 = landmarks[HandLandmark.INDEX_FINGER_MCP]
        p9 = landmarks[HandLandmark.MIDDLE_FINGER_MCP]
        p17 = landmarks[HandLandmark.PINKY_MCP]

        # --- Palm Orientation (Corrected) ---
        is_palm_facing_camera = False
        if handedness == "Left": # Your real Right Hand
            is_palm_facing_camera = p5.x > p17.x
        else: # Your real Left Hand
            is_palm_facing_camera = p5.x < p17.x
        orientation = "front" if is_palm_facing_camera else "back"

        # --- Finger Extension States ---
        def get_dist(p1, p2): return math.dist((p1.x, p1.y), (p2.x, p2.y))
        finger_states = {
            "index": "extended" if get_dist(landmarks[HandLandmark.INDEX_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.INDEX_FINGER_PIP], p0) else "curled",
            "middle": "extended" if get_dist(landmarks[HandLandmark.MIDDLE_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.MIDDLE_FINGER_PIP], p0) else "curled",
            "ring": "extended" if get_dist(landmarks[HandLandmark.RING_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.RING_FINGER_PIP], p0) else "curled",
            "pinky": "extended" if get_dist(landmarks[HandLandmark.PINKY_TIP], p0) > get_dist(landmarks[HandLandmark.PINKY_PIP], p0) else "curled",
        }
        
        # --- NEW & FINAL: Truly Rotation-Invariant Thumb Logic (Dot Product) ---
        # We define the "width" of the palm and check if the thumb points along it.
        # This is immune to rotation issues.
        thumb_vec = (p4.x - p2.x, p4.y - p2.y)
        
        # Palm width vector points from pinky side to index side.
        if handedness == "Left": # Real Right Hand
             palm_width_vec = (p5.x - p17.x, p5.y - p17.y)
        else: # Real Left Hand
             palm_width_vec = (p17.x - p5.x, p17.y - p5.y)
        
        # Dot product tells us if the vectors are pointing in the same direction.
        # If dot > 0, thumb is extended outwards. If dot < 0, it's curled inwards.
        dot_product = thumb_vec[0] * palm_width_vec[0] + thumb_vec[1] * palm_width_vec[1]
        finger_states["thumb"] = "extended" if dot_product > 0 else "curled"
        
        # --- Hand Direction ---
        hand_vec = (p9.x - p0.x, p9.y - p0.y)
        angle = math.degrees(math.atan2(-hand_vec[1], hand_vec[0]))
        direction = ""
        if -45 <= angle < 45: direction = "right"
        elif 45 <= angle < 135: direction = "up"
        elif -135 <= angle < -45: direction = "down"
        else: direction = "left"

        return {
            "handedness": handedness.lower(),
            "orientation": orientation,
            "direction": direction,
            "fingers": finger_states
        }

    def recognize(self, hand_landmarks, handedness):
        if not hand_landmarks:
            return None, {}

        live_hand_state = self._get_hand_state(hand_landmarks, handedness)

        for name, definition in self.custom_gestures.items():
            conditions = definition.get("conditions", {})
            is_match = True

            for key, value in conditions.items():
                if key == "fingers":
                    for finger, required_state in value.items():
                        if live_hand_state["fingers"].get(finger) != required_state:
                            is_match = False; break
                elif live_hand_state.get(key) != value:
                    is_match = False; break
                if not is_match: break
            
            if is_match:
                return name.lower(), live_hand_state

        return None, live_hand_state