# ~/Code/gestura/action_executor.py
import json
import subprocess

class ActionExecutor:
    def __init__(self, config_path='actions.json'):
        self.actions = self._load_actions(config_path)

    def _load_actions(self, config_path):
        try:
            with open(config_path, 'r') as f:
                print(f"Loading actions from '{config_path}'...")
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Action config file not found at '{config_path}'.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{config_path}'.")
            return {}

    def execute(self, gesture_name):
        """Looks up a gesture and executes the corresponding command."""
        command = self.actions.get(gesture_name)
        if command:
            print(f"Executing action for '{gesture_name}': {command}")
            try:
                subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Error executing command '{command}': {e}")