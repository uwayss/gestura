# ~/Code/gestura/main.py
import argparse
from app import App

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gestura - Hand Gesture Recognition")
    parser.add_argument(
        '--debug', action='store_true',
        help='Enable debug mode to show the camera feed with landmarks.'
    )
    args = parser.parse_args()

    app = None
    try:
        app = App(debug=args.debug)
        app.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if app:
            app._cleanup()