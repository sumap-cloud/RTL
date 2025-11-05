import subprocess
import ctypes
import time
import sys

class ServiceController:
    """
    A class to control a Windows service.
    Requires administrator privileges to run.
    """

    def __init__(self, service_name):
        """
        Initializes the ServiceController.

        Args:
            service_name (str): The name of the service to control.
        """
        self.service_name = service_name
        self.service_exists = self._check_service_exists()

    def _is_admin(self):
        """Checks if the script is running with administrative privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _check_service_exists(self):
        """
        Checks if the service exists using the 'sc' command.

        Returns:
            bool: True if the service exists, False otherwise.
        """
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
        """
        Gets the current status of the service by parsing the output of 'sc query'.

        Returns:
            str or None: The service status (e.g., 'RUNNING', 'STOPPED') or None on error.
        """
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
        """
        Starts the service.
        """
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
        """
        Stops the service.
        """
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


def manage_service(service_name, action):
    """
    A reusable function to manage a windows service.

    Args:
        service_name (str): The name of the service to manage.
        action (str): The action to perform. Can be 'start', 'stop', 'restart', or 'status'.
    """
    controller = ServiceController(service_name)

    if not controller._is_admin():
        print("\nWARNING: Administrator privileges are required to start, stop, or restart services.")
        print("Please re-run this script from an elevated Command Prompt or PowerShell.\n")

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
        print(f"Invalid action: '{action}'. Please use 'start', 'stop', 'restart', or 'status'.")


if __name__ == "__main__":
    # --- Example of how to use the reusable function ---

    # 1. Define the service name and the action you want to perform
    service_to_manage = "RemedyEFTPOSServer"
    action_to_perform = "start"  # <-- Change this to 'start', 'stop', 'restart', or 'status'

    # 2. Call the function
    print(f"--- Attempting to '{action_to_perform}' the '{service_to_manage}' service ---")
    manage_service(service_to_manage, action_to_perform)
    print("--- Operation finished ---")
