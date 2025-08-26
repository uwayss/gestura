# ~/Code/gestura/feedback_manager.py
import os
from desktop_notifier import DesktopNotifier

class FeedbackManager:
    def __init__(self):
        self.notifier = None
        try:
            # This object handles platform-specific backends automatically.
            self.notifier = DesktopNotifier(
                app_name="Gestura",
                notification_limit=5 # Keep the screen clean
            )
            print("FeedbackManager initialized successfully (using desktop-notifier).")
        except Exception as e:
            print(f"Warning: Could not initialize notification service: {e}")
            print("Notifications will be disabled.")

    def show_notification(self, gesture, command):
        """Displays a desktop notification."""
        if not self.notifier:
            return

        title = f"Gestura: '{gesture}' triggered"
        # Get a cleaner command name, e.g., "gnome-screenshot" from "gnome-screenshot --interactive"
        message = f"Running: {os.path.basename(command.split()[0])}"
        
        try:
            # send_sync is a blocking call, but it's fast enough.
            self.notifier.send_sync(title=title, message=message)
        except Exception as e:
            # This can happen if the notification server is stopped mid-run.
            print(f"Error showing notification: {e}")