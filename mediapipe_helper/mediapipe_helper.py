# mediapipe_helper/mediapipe_helper.py
import sys
import json
import cv2
import mediapipe as mp
import base64
import argparse
import struct

def print_json_error(message):
    """Sends errors as JSON, as Go might still be expecting it on failure."""
    print(json.dumps({'error': message}))
    sys.stdout.flush()

def main(is_debug=False):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print_json_error("Cannot open webcam")
        sys.exit(1)

    hands = mp.solutions.hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=2
    )

    # Use stdout's binary buffer for writing raw bytes
    stdout_buffer = sys.stdout.buffer

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        flipped_image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(flipped_image, cv2.COLOR_BGR2RGB)
        
        rgb_image.flags.writeable = False
        results = hands.process(rgb_image)
        rgb_image.flags.writeable = True

        num_hands = 0
        if results.multi_hand_landmarks:
            num_hands = len(results.multi_hand_landmarks)
        
        # --- BINARY PROTOCOL ---
        # 1. Pack and write the number of hands detected
        stdout_buffer.write(struct.pack('<B', num_hands))

        # 2. For each hand, pack and write its data
        if num_hands > 0:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Handedness: 'L' or 'R'
                hand_char = handedness.classification[0].label[0].encode('ascii')
                stdout_buffer.write(struct.pack('<c', hand_char))
                # Landmarks: 21 landmarks * 3 coordinates (x, y, z) = 63 floats
                for lm in hand_landmarks.landmark:
                    stdout_buffer.write(struct.pack('<fff', lm.x, lm.y, lm.z))

        # 3. In debug mode, send the frame separately after a magic number delimiter
        if is_debug:
            _, buffer = cv2.imencode('.jpg', flipped_image)
            frame_bytes = buffer.tobytes()
            # Write a magic number and the size of the upcoming frame
            stdout_buffer.write(b'FRAME')
            stdout_buffer.write(struct.pack('<I', len(frame_bytes)))
            stdout_buffer.write(frame_bytes)

        # Flush the buffer to ensure Go receives the data immediately
        stdout_buffer.flush()


    hands.close()
    cap.release()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Include binary video frame in output.')
    args = parser.parse_args()

    try:
        main(is_debug=args.debug)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print_json_error(str(e))
        sys.exit(1)