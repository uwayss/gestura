import math

# Using a class for constants to avoid magic numbers
class HandLandmark:
    WRIST = 0
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_PIP = 14
    RING_FINGER_TIP = 16
    PINKY_PIP = 18
    PINKY_TIP = 20

# Data-driven gesture definitions. Easy to add new gestures here.
GESTURE_DEFINITIONS = {
    "FINGER_GUN": {
        "thumb": "Extended", "index": "Extended", "middle": "Extended",
        "ring": "Curled", "pinky": "Curled"
    },
    "PEACE": {
        "thumb": "Curled", "index": "Extended", "middle": "Extended",
        "ring": "Curled", "pinky": "Curled"
    },
    "FIST": {
        "thumb": "Curled", "index": "Curled", "middle": "Curled",
        "ring": "Curled", "pinky": "Curled"
    },
    "FIVE": {
        "thumb": "Extended", "index": "Extended", "middle": "Extended",
        "ring": "Extended", "pinky": "Extended"
    },
}

class GestureRecognizer:
    def __init__(self):
        pass

    def _get_finger_states(self, hand_landmarks):
        landmarks = hand_landmarks.landmark

        def is_extended(tip_idx, pip_idx):
            return landmarks[tip_idx].y < landmarks[pip_idx].y

        # A more robust, distance-based check for the thumb
        thumb_tip_pt = landmarks[HandLandmark.THUMB_TIP]
        index_mcp_pt = landmarks[HandLandmark.INDEX_FINGER_MCP]
        thumb_to_index_dist = math.dist((thumb_tip_pt.x, thumb_tip_pt.y), (index_mcp_pt.x, index_mcp_pt.y))
        
        # Heuristic: Thumb is extended if its tip is far enough from the index knuckle
        thumb_state = "Extended" if thumb_to_index_dist > 0.15 else "Curled" # Threshold may need tuning

        return {
            "thumb": thumb_state,
            "index": "Extended" if is_extended(HandLandmark.INDEX_FINGER_TIP, HandLandmark.INDEX_FINGER_PIP) else "Curled",
            "middle": "Extended" if is_extended(HandLandmark.MIDDLE_FINGER_TIP, HandLandmark.MIDDLE_FINGER_PIP) else "Curled",
            "ring": "Extended" if is_extended(HandLandmark.RING_FINGER_TIP, HandLandmark.RING_FINGER_PIP) else "Curled",
            "pinky": "Extended" if is_extended(HandLandmark.PINKY_TIP, HandLandmark.PINKY_PIP) else "Curled",
        }

    def recognize(self, hand_landmarks):
        if not hand_landmarks:
            return None, {}

        finger_states = self._get_finger_states(hand_landmarks)
        
        for gesture_name, required_states in GESTURE_DEFINITIONS.items():
            if finger_states == required_states:
                return gesture_name, finger_states
        
        return None, finger_states