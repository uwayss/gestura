# ~/Code/gestura/gesture_recognizer.py
import math
import json
from utils import HandLandmark

class GestureRecognizer:
    def __init__(self, config_path='gestures.json'):
        self.custom_gestures = self._load_custom_gestures(config_path)
        # A thumb is considered "extended" if the distance from its tip to the pinky
        # knuckle is greater than 1.3 times the width of the palm. This is a
        # reliable, rotation-invariant heuristic.
        self.THUMB_EXTENSION_THRESHOLD = 1.3

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
        
        # --- Landmark Points ---
        p0, p4, p5 = landmarks[HandLandmark.WRIST], landmarks[HandLandmark.THUMB_TIP], landmarks[HandLandmark.INDEX_FINGER_MCP]
        p9, p17 = landmarks[HandLandmark.MIDDLE_FINGER_MCP], landmarks[HandLandmark.PINKY_MCP]

        # --- Palm Orientation ---
        is_palm_facing_camera = (p5.x < p17.x) if handedness == "Left" else (p5.x > p17.x)
        orientation = "front" if is_palm_facing_camera else "back"

        # --- Finger Extension States (Excluding Thumb) ---
        def get_dist(p1, p2): return math.dist((p1.x, p1.y), (p2.x, p2.y))
        finger_states = {
            "index": "extended" if get_dist(landmarks[HandLandmark.INDEX_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.INDEX_FINGER_PIP], p0) else "curled",
            "middle": "extended" if get_dist(landmarks[HandLandmark.MIDDLE_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.MIDDLE_FINGER_PIP], p0) else "curled",
            "ring": "extended" if get_dist(landmarks[HandLandmark.RING_FINGER_TIP], p0) > get_dist(landmarks[HandLandmark.RING_FINGER_PIP], p0) else "curled",
            "pinky": "extended" if get_dist(landmarks[HandLandmark.PINKY_TIP], p0) > get_dist(landmarks[HandLandmark.PINKY_PIP], p0) else "curled",
        }
        
        # --- FINAL, STABLE THUMB LOGIC (Distance-Based) ---
        # This logic is immune to rotation and orientation issues.
        palm_width = get_dist(p5, p17)
        thumb_distance = get_dist(p4, p17)
        
        is_extended = thumb_distance > (palm_width * self.THUMB_EXTENSION_THRESHOLD)
        finger_states["thumb"] = "extended" if is_extended else "curled"
        
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
        if not hand_landmarks: return None, {}
        live_hand_state = self._get_hand_state(hand_landmarks, handedness)
        for name, definition in self.custom_gestures.items():
            conditions, is_match = definition.get("conditions", {}), True
            for key, value in conditions.items():
                if key == "fingers":
                    for finger, required in value.items():
                        if live_hand_state["fingers"].get(finger) != required: is_match = False; break
                elif live_hand_state.get(key) != value: is_match = False; break
                if not is_match: break
            if is_match: return name.lower(), live_hand_state
        return None, live_hand_state