import csv
import time
from smbclient import register_session
import smbclient

# --- SMB Configuration ---
SMB_SERVER = "10.80.19.218"
SMB_USERNAME = r"10.80.19.218\backupuser"
SMB_PASSWORD = "ArC53rv3"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Data Source Configuration ---
# Central configuration for all data files
DATA_SOURCES = {
    "saledata": {
        "filename": "SaleData.csv",
        "description": "Sales transaction data",
        "path": r"\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv"
    },
    "transactiondata": {
        "filename": "TransactionData.csv",
        "description": "Transaction details and logs",
        "path": r"\\10.80.19.218\d$\RTL_Pywinauto\TransactionData.csv"
    }
}

# --- Register SMB Session Once at Module Load ---
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

# Try to initialize SMB session when module loads
_smb_initialized = _initialize_smb_session()

def get_data_source_path(source_name):
    """
    Get the file path for a specific data source.
    
    Args:
        source_name (str): Name of the data source (e.g., 'saledata', 'transactiondata')
    
    Returns:
        str: Full file path to the data source
    
    Raises:
        ValueError: If source name is not found in configuration
    """
    source_name = source_name.lower().strip()
    
    if source_name not in DATA_SOURCES:
        available = ", ".join(DATA_SOURCES.keys())
        raise ValueError(f"Unknown data source '{source_name}'. Available sources: {available}")
    
    return DATA_SOURCES[source_name]["path"]

def get_data_source_info(source_name):
    """
    Get information about a data source.
    
    Args:
        source_name (str): Name of the data source
    
    Returns:
        dict: Information about the data source
    """
    source_name = source_name.lower().strip()
    
    if source_name not in DATA_SOURCES:
        return None
    
    return DATA_SOURCES[source_name]

def get_csv_value(source_name, banner, tc_id, iteration, target_column):
    """
    Finds a specific value in a CSV file by matching Banner, TC_ID, and Iteration.
    Now uses centralized data source configuration.
    
    Args:
        source_name (str): Name of the data source (e.g., 'saledata', 'transactiondata')
        banner (str): Banner value to match
        tc_id (str): Test case ID to match
        iteration (int): Iteration number to match
        target_column (str): Column name to retrieve
    
    Returns:
        str: Value from the requested column or error message
    """
    if not _smb_initialized:
        print("⚠️ WARNING: SMB session not initialized. Attempting to initialize now...")
        if not _initialize_smb_session():
            return f"Error: Unable to establish SMB connection to {SMB_SERVER}"
    
    # Get the file path based on source name
    try:
        file_path = get_data_source_path(source_name)
        source_info = get_data_source_info(source_name)
        print(f"📂 Using data source: {source_info['description']}")
    except ValueError as e:
        return f"Error: {e}"
    
    # Retry logic for file access
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"📂 Reading CSV from: {file_path} (Attempt {attempt}/{MAX_RETRIES})")
            # Use smbclient.open_file() for UNC paths — Python's built-in open()
            # raises [Errno 22] on \\server\share paths on Windows.
            import io
            with smbclient.open_file(file_path, mode='r', encoding='utf-8') as raw:
                content = raw.read()
            csvfile = io.StringIO(content)
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # Perform the multi-criteria match
                # Iteration is often read as a string from CSV, so we check accordingly
                if (row.get('Banner') == banner and 
                    row.get('TC_ID') == tc_id and 
                    row.get('Iteration') == str(iteration)):
                    
                    # Return the value from the requested column
                    value = row.get(target_column, f"Column '{target_column}' not found")
                    print(f"✅ Found value: {value}")
                    return value
            
            print(f"⚠️ No matching record found for Banner={banner}, TC_ID={tc_id}, Iteration={iteration}")
            return "No matching record found."

        except FileNotFoundError as e:
            print(f"❌ File not found: {file_path}")
            return f"Error: File not found - {file_path}"
        except PermissionError as e:
            print(f"❌ Permission denied accessing file: {file_path}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return f"Error: Permission denied - {file_path}"
        except Exception as e:
            print(f"❌ Error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return f"An error occurred: {e}"
    
    return "Error: Failed to read CSV after all retries."

def test_smb_connection():
    """
    Diagnostic function to test SMB connection.
    Run this to verify the connection is working.
    """
    print("\n" + "="*60)
    print("🧪 Testing SMB Connection")
    print("="*60)
    print(f"Server: {SMB_SERVER}")
    print(f"Username: {SMB_USERNAME}")
    print(f"Password: {'*' * len(SMB_PASSWORD)}")
    
    try:
        print("\n🔗 Attempting to register SMB session...")
        register_session(SMB_SERVER, SMB_USERNAME, SMB_PASSWORD)
        print("✅ SMB session registered successfully!")
        
        # Try to list shares
        print("\n📂 Attempting to list available shares...")
        shares = smbclient.listdir(f"//{SMB_SERVER}")
        print(f"✅ Available shares: {shares}")
        
        # Test available data sources
        print("\n📋 Available Data Sources:")
        print("="*60)
        for source_name, source_info in DATA_SOURCES.items():
            print(f"  • {source_name.upper()}")
            print(f"    Description: {source_info['description']}")
            print(f"    File: {source_info['filename']}")
            print(f"    Path: {source_info['path']}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("   1. Verify SMB_SERVER IP address is correct")
        print("   2. Verify SMB_USERNAME format (domain\\username)")
        print("   3. Verify SMB_PASSWORD is correct")
        print("   4. Check firewall allows SMB (port 445)")
        print("   5. Verify the user account has file share access")
        return False


# Using the NEW centralized data source configuration approach

# Example 1: Get data from SaleData.csv
# result = get_csv_value("saledata", "SM", "TC_001", 1, "price")

# Example 2: Get data from TransactionData.csv
# result = get_csv_value("transactiondata", "SM", "TC_001", 1, "transaction_id")

# Example 3: Get any column from configured CSV files
# result = get_csv_value("saledata", "SM", "TC_003", 1, "remarks")

# Example 4: Get information about available data sources
# info = get_data_source_info("saledata")
# print(f"Data Source: {info['description']}")
# print(f"File Path: {info['path']}")

# Example 5: Test SMB connection and available data sources
# test_smb_connection()

# print(f"Value found: {result}")