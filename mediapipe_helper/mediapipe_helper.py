# mediapipe_helper.py
import sys
import json
import cv2
import mediapipe as mp
import base64
import argparse

def main(is_debug=False):
    """
    Initializes MediaPipe, captures video, and prints hand landmark data as JSON to stdout.
    If is_debug is True, it also base64 encodes the video frame and includes it in the output.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print_json_error("Cannot open webcam")
        sys.exit(1)

    hands = mp.solutions.hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=2
    )

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # Flip for selfie view, then convert for mediapipe
        flipped_image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(flipped_image, cv2.COLOR_BGR2RGB)
        
        rgb_image.flags.writeable = False
        results = hands.process(rgb_image)
        rgb_image.flags.writeable = True

        output_data = {'hands': []}

        # Add base64 encoded frame if in debug mode
        if is_debug:
            _, buffer = cv2.imencode('.jpg', flipped_image)
            output_data['frame'] = base64.b64encode(buffer).decode('utf-8')

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                landmarks_list = []
                for lm in hand_landmarks.landmark:
                    landmarks_list.append({'x': lm.x, 'y': lm.y, 'z': lm.z})

                hand_data = {
                    'handedness': handedness.classification[0].label,
                    'landmarks': landmarks_list
                }
                output_data['hands'].append(hand_data)
        
        print(json.dumps(output_data))
        sys.stdout.flush()

    hands.close()
    cap.release()

def print_json_error(message):
    print(json.dumps({'error': message}))
    sys.stdout.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Include base64 video frame in output.')
    args = parser.parse_args()

    try:
        main(is_debug=args.debug)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print_json_error(str(e))
        sys.exit(1)