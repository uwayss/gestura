# ~/Code/gestura/gesture_recognizer.py
import math
import json
from utils import HandLandmark

class GestureRecognizer:
    def __init__(self, config_path='gestures.json'):
        self.finger_count_map = {
            0: "FIST", 1: "ONE", 2: "TWO",
            3: "THREE", 4: "FOUR", 5: "FIVE",
        }
        self.custom_gestures = self._load_custom_gestures(config_path)

    def _load_custom_gestures(self, config_path):
        try:
            with open(config_path, 'r') as f:
                print(f"Loading custom gestures from '{config_path}'...")
                definitions = json.load(f)
                # Validate gesture names to prevent conflicts with combo delimiter
                for name in definitions.keys():
                    if '-' in name:
                        print(f"Warning: Gesture name '{name}' contains a hyphen '-'. "
                              "This is discouraged as it's used as the combo delimiter.")
                return definitions
        except FileNotFoundError:
            print(f"Info: Custom gesture file not found at '{config_path}'. Using defaults.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{config_path}'.")
            return {}

    def _get_finger_states(self, hand_landmarks, handedness):
        """
        Calculates finger states using a hybrid, definitive approach that
        accounts for both handedness and palm orientation.
        """
        landmarks = hand_landmarks.landmark
        wrist = landmarks[HandLandmark.WRIST]

        def get_distance(point1, point2):
            return math.dist((point1.x, point1.y), (point2.x, point2.y))

        is_index_extended = get_distance(landmarks[HandLandmark.INDEX_FINGER_TIP], wrist) > get_distance(landmarks[HandLandmark.INDEX_FINGER_PIP], wrist)
        is_middle_extended = get_distance(landmarks[HandLandmark.MIDDLE_FINGER_TIP], wrist) > get_distance(landmarks[HandLandmark.MIDDLE_FINGER_PIP], wrist)
        is_ring_extended = get_distance(landmarks[HandLandmark.RING_FINGER_TIP], wrist) > get_distance(landmarks[HandLandmark.RING_FINGER_PIP], wrist)
        is_pinky_extended = get_distance(landmarks[HandLandmark.PINKY_TIP], wrist) > get_distance(landmarks[HandLandmark.PINKY_PIP], wrist)

        thumb_tip = landmarks[HandLandmark.THUMB_TIP]
        thumb_mcp = landmarks[HandLandmark.THUMB_MCP]
        index_mcp = landmarks[HandLandmark.INDEX_FINGER_MCP]
        pinky_mcp = landmarks[HandLandmark.PINKY_MCP]

        is_palm_facing_camera = False
        if handedness == "Right":
            is_palm_facing_camera = index_mcp.x < pinky_mcp.x
        else: # Left
            is_palm_facing_camera = index_mcp.x > pinky_mcp.x

        is_thumb_extended = False
        if is_palm_facing_camera:
            if handedness == "Right":
                is_thumb_extended = thumb_tip.x < thumb_mcp.x
            else: # Left
                is_thumb_extended = thumb_tip.x > thumb_mcp.x
        else: # Palm facing away
            if handedness == "Right":
                is_thumb_extended = thumb_tip.x > thumb_mcp.x
            else: # Left
                is_thumb_extended = thumb_tip.x < thumb_mcp.x
                
        states = {
            "thumb": "Extended" if is_thumb_extended else "Curled",
            "index": "Extended" if is_index_extended else "Curled",
            "middle": "Extended" if is_middle_extended else "Curled",
            "ring": "Extended" if is_ring_extended else "Curled",
            "pinky": "Extended" if is_pinky_extended else "Curled",
        }
        return states

    def _match_custom_gesture(self, finger_states):
        """Check if finger states match any custom gesture definition."""
        for name, definition in self.custom_gestures.items():
            if all(finger_states.get(finger) == state for finger, state in definition.items()):
                return name
        return None

    def recognize(self, hand_landmarks, handedness):
        if not hand_landmarks:
            return None, {}
        
        finger_states = self._get_finger_states(hand_landmarks, handedness)
        
        # Prioritize custom gestures over default count-based gestures
        custom_gesture_name = self._match_custom_gesture(finger_states)
        if custom_gesture_name:
            return custom_gesture_name, finger_states

        # Fallback to finger counting
        extended_fingers_count = list(finger_states.values()).count("Extended")
        gesture_name = self.finger_count_map.get(extended_fingers_count)
        
        return gesture_name, finger_states