import subprocess
import os
import time
import ctypes
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

# --- Configuration ---
# The full path to your batch file for the EFT Simulator.
BAT_FILE_PATH = r"C:\python\python\Scripts\POS_Workspace\Components\Common_components\launch_eft.bat"
# The regex pattern to identify the EFT Simulator window.
EFT_WINDOW_TITLE_REGEX = ".*EFT MultiSimulator.*"


class ServiceController:
    """
    A class to control a Windows service.
    Requires administrator privileges for start/stop/restart actions.
    """

    def __init__(self, service_name):
        """Initializes the ServiceController."""
        self.service_name = service_name
        self.service_exists = self._check_service_exists()

    def _is_admin(self):
        """Checks if the script is running with administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _check_service_exists(self):
        """Checks if the service exists using the 'sc' command."""
        try:
            subprocess.run(
                ['sc', 'query', self.service_name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"Successfully found service: '{self.service_name}'")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Error: Service '{self.service_name}' not found.")
            return False

    def get_status(self):
        """Gets the current status of the service."""
        if not self.service_exists:
            return None
        try:
            result = subprocess.check_output(['sc', 'query', self.service_name], text=True, stderr=subprocess.DEVNULL)
            for line in result.splitlines():
                if 'STATE' in line:
                    status = line.split(':')[1].strip().split(' ')[-1]
                    return status.upper()
            return "UNKNOWN"
        except subprocess.CalledProcessError:
            return "NOT_FOUND"
        except Exception as e:
            print(f"Error getting status for '{self.service_name}': {e}")
            return None

    def status(self):
        """Prints the current status of the service."""
        current_status = self.get_status()
        if current_status:
            print(f"Status for '{self.service_name}': {current_status}")
        return current_status

    def start(self):
        """Starts the service."""
        if not self.service_exists:
            return
        try:
            if self.get_status() == 'RUNNING':
                print(f"'{self.service_name}' is already running.")
                return
            print(f"Starting '{self.service_name}'...")
            subprocess.run(['net', 'start', self.service_name], check=True, capture_output=True)
            print(f"'{self.service_name}' started successfully.")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8', errors='ignore').strip()
            print(f"Error starting '{self.service_name}': {error_message}")
        except Exception as e:
            print(f"An unexpected error occurred while starting: {e}")

    def stop(self):
        """Stops the service."""
        if not self.service_exists:
            return
        try:
            if self.get_status() == 'STOPPED':
                print(f"'{self.service_name}' is already stopped.")
                return
            print(f"Stopping '{self.service_name}'...")
            subprocess.run(['net', 'stop', self.service_name], check=True, capture_output=True)
            print(f"'{self.service_name}' stopped successfully.")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8', errors='ignore').strip()
            print(f"Error stopping '{self.service_name}': {error_message}")
        except Exception as e:
            print(f"An unexpected error occurred while stopping: {e}")

    def restart(self):
        """Restarts the service."""
        if not self.service_exists:
            return
        print(f"Restarting '{self.service_name}'...")
        self.stop()
        time.sleep(2)
        self.start()
        print(f"'{self.service_name}' restart command issued.")


def manage_windows_service(service_name, action):
    """
    Manages a Windows service based on the provided action.
    """
    controller = ServiceController(service_name)

    if not controller._is_admin() and action in ['start', 'stop', 'restart']:
        print("\nWARNING: Administrator privileges are required to manage services.")
        print("Please re-run this script from an elevated Command Prompt or PowerShell.\n")
        # We can still attempt the action, as some systems might not require it.

    if not controller.service_exists:
        return

    action = action.lower()
    if action == 'start':
        controller.start()
    elif action == 'stop':
        controller.stop()
    elif action == 'restart':
        controller.restart()
    elif action == 'status':
        controller.status()
    else:
        print(f"Invalid action for service: '{action}'. Use 'start', 'stop', 'restart', or 'status'.")


def manage_eft_simulator(action: str):
    """
    Manages the EFT MultiSimulator application by launching or closing it.
    """
    action = action.lower()

    if action == 'start':
        print(f"--- Action: START EFT SIMULATOR ---")
        if not os.path.exists(BAT_FILE_PATH):
            print(f"Error: Cannot find batch file: {BAT_FILE_PATH}")
            return
        try:
            file_directory = os.path.dirname(BAT_FILE_PATH)
            window_title = "EFT MultiSimulator Launcher"
            print(f"Launching batch file in a new window...")
            subprocess.Popen(f'start "{window_title}" "{BAT_FILE_PATH}"', shell=True, cwd=file_directory)
            print("Batch file launched successfully.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif action == 'stop':
        print(f"--- Action: STOP EFT SIMULATOR ---")
        try:
            print(f"Attempting to find and close window matching: '{EFT_WINDOW_TITLE_REGEX}'")
            app = Application(backend="uia").connect(title_re=EFT_WINDOW_TITLE_REGEX, timeout=10)
            win = app.window(title_re=EFT_WINDOW_TITLE_REGEX)
            print("Window found. Attempting to close...")
            win.set_focus()
            win.close()
            print("Close command sent successfully.")
        except ElementNotFoundError:
            print("Error: Could not find the EFT Simulator window.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print(f"Invalid action for EFT simulator: '{action}'. Please use 'start' or 'stop'.")


def EFT_controller(task_type: str, task_name: str, action: str):
    """
    Main controller to delegate tasks for services or applications.

    Args:
        task_type (str): The type of task. Accepts 'service' or 'eft'.
        task_name (str): The name of the service or app (can be empty for EFT).
        action (str): The action to perform (e.g., 'start', 'stop').
    """
    task_type = task_type.lower()
    print(f"\n>>> Executing Task: Manage '{task_name}' ({task_type}) with action '{action}' <<<")
    
    if task_type == 'service':
        manage_windows_service(service_name=task_name, action=action)
    elif task_type == 'eft':
        manage_eft_simulator(action=action)
    else:
        print(f"Error: Invalid task_type '{task_type}'. Please use 'service' or 'eft'.")
    
    print("--- Operation finished ---")

# --- Example Usage ---
if __name__ == "__main__":
    
    # --- Example 1: Manage a Windows Service ---
    # Change these values as needed
    service_to_manage = "RemedyEFTPOSServer"
    action_for_service = "stop"  # <-- Change to 'start', 'stop', 'restart', or 'status'
    
    EFT_controller(task_type="service", task_name=service_to_manage, action=action_for_service)

    # # --- Example 2: Start the EFT Simulator ---
    # print("\n--- Starting EFT Simulator in 5 seconds... ---")
    # time.sleep(5)
    #EFT_controller(task_type="eft", task_name="EFT MultiSimulator", action="start")

    # # --- Example 3: Stop the EFT Simulator after a delay ---
    # print("\n--- Stopping EFT Simulator in 15 seconds... ---")
    # time.sleep(15)
    #EFT_controller(task_type="eft", task_name="EFT MultiSimulator", action="stop")