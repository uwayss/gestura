# ~/Code/gestura/main.py
from app import App

if __name__ == '__main__':
    app = None
    try:
        app = App()
        app.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if app:
            app._cleanup()