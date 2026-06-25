import os
from datetime import datetime

def get_latest_log_for_today(log_directory):
    # 1. Get today's date in the format seen in your files (e.g., 2026-05-21)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 2. List all files in the directory
    try:
        files = os.listdir(log_directory)
    except FileNotFoundError:
        return "Directory not found."

    # 3. Filter files that start with EEAdapter and match today's date
    today_logs = [f for f in files if f.startswith(f"EEAdapter_{today_str}")]

    if not today_logs:
        return f"No logs found for today ({today_str})."

    # 4. Sort the filtered files
    # We sort them so the highest version number (e.g., .3 vs .0) is at the end
    today_logs.sort()

    # The last item in the sorted list is the latest version
    return today_logs[-1]

# Example Usage:
log_path = "C:\\Retalix\\EEAdapter\\Logs"
latest_file = get_latest_log_for_today(log_path)
print(f"✅ The latest log for today is: {latest_file}")