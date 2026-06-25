import csv
import time
import smbclient
from smbclient import register_session

# --- Data Source Configuration (Centralized) ---
from Components.Read_csv import get_data_source_path

# --- SMB Configuration ---
SMB_SERVER = "10.80.19.218"
SMB_USERNAME = r"10.80.19.218\backupuser"
SMB_PASSWORD = "ArC53rv3"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def _initialize_smb_session():
    """Initialize SMB session at module startup."""
    try:
        print(f"🔗 Registering SMB session with {SMB_SERVER}...")
        register_session(SMB_SERVER, SMB_USERNAME, SMB_PASSWORD)
        print(f"✅ SMB session registered successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to register SMB session: {e}")
        return False

_smb_initialized = _initialize_smb_session()

def update_csv_value(source_name, banner, tc_id, iteration, target_column, new_value):
    """
    Updates a specific value in a CSV file using centralized data source configuration.
    
    Args:
        source_name (str): Name of the data source (e.g., 'saledata', 'transactiondata')
        banner (str): Banner value to match
        tc_id (str): Test case ID to match
        iteration (int): Iteration number to match
        target_column (str): Column name to update
        new_value (str): New value to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not _smb_initialized:
        print("⚠️ WARNING: SMB session not initialized. Attempting to initialize now...")
        if not _initialize_smb_session():
            print(f"❌ Error: Unable to establish SMB connection to {SMB_SERVER}")
            return False
    
    # Get the file path based on source name (centralized)
    try:
        file_path = get_data_source_path(source_name)
        print(f"📂 Using data source: {source_name}")
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False
    
    # Retry logic for file access
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"📝 Updating CSV: {file_path} (Attempt {attempt}/{MAX_RETRIES})")
            
            import io
            # Read all rows via smbclient (open() fails on UNC paths with [Errno 22])
            with smbclient.open_file(file_path, mode='r', encoding='utf-8') as raw:
                content = raw.read()
            reader = csv.DictReader(io.StringIO(content))
            fieldnames = reader.fieldnames
            rows = []
            for row in reader:
                if (row.get('Banner') == banner and 
                    row.get('TC_ID') == tc_id and 
                    row.get('Iteration') == str(iteration)):
                    if target_column in row:
                        row[target_column] = new_value
                        print(f"✅ Updated {target_column} to: {new_value}")
                    else:
                        print(f"⚠️ Column '{target_column}' not found in CSV")
                        return False
                rows.append(row)
            
            # Write all rows back via smbclient
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            with smbclient.open_file(file_path, mode='w', encoding='utf-8') as wf:
                wf.write(output.getvalue())
            
            print(f"✅ CSV updated successfully")
            return True
        
        except FileNotFoundError as e:
            print(f"❌ File not found: {file_path}")
            return False
        except PermissionError as e:
            print(f"❌ Permission denied accessing file: {file_path}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return False
        except Exception as e:
            print(f"❌ Error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return False
    
    return False