import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom
import html  # Import the html module for un-escaping
from datetime import datetime, timedelta

# --- Configuration Section ---
# You can change these parameters as needed.
ENV = "azwr10ast00004" #azwr10ast00004,#azwr10asa00029
STORE_NUMBER = "2078"
LANE_NUMBER = "001"
TRANSACTION_NUMBER = "7747"
# -----------------------------

def save_to_file(filename, content):
    """Saves content to a file and prints a confirmation message."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved data to '{filename}'")
    except IOError as e:
        print(f"Error saving file {filename}: {e}")

def format_xml_string(xml_string):
    """
    Parses an XML string and returns it in a pretty-printed format.
    If the string is not valid XML, it returns the original string.
    """
    try:
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")
    except Exception as e:
        print(f"Warning: Could not format the response as XML. Saving raw text. Error: {e}")
        return xml_string

def login_and_get_session(environment):
    """
    Sends a login request to get a session ID.
    Saves the request and response to files.
    Returns the session ID if successful, otherwise None.
    """
    print("--- Step 1: Attempting to log in... ---")
    url = f"http://{environment}:54473/StoreWebServices/IdmLogin.rti"
    login_payload = """<?xml version="1.0" encoding="utf-8"?>
<IDMRequest xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" MajorVersion="1" xmlns="http://www.nrf-arts.org/IXRetail/namespace/">
  <ARTSHeader>
    <MessageID>38</MessageID>
  </ARTSHeader>
  <Worker Version="1.0" MajorVersion="1" MinorVersion="0" FixVersion="1">
    <WorkerID>1</WorkerID>
    <SecurityIdentifier TypeCode="UserName">dms_user</SecurityIdentifier>
    <SecurityIdentifier TypeCode="Password">dmsuser</SecurityIdentifier>
  </Worker>
</IDMRequest>"""

    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    save_to_file("1_login_request.xml", format_xml_string(login_payload))

    try:
        response = requests.post(url, data=login_payload.encode('utf-8'), headers=headers, timeout=10)
        formatted_login_response = format_xml_string(response.text)
        save_to_file("1_login_response.xml", formatted_login_response)
        response.raise_for_status()
        print(f"Login successful for environment: {environment}")

        root = ET.fromstring(response.text)
        namespaces = {'ns': 'http://www.nrf-arts.org/IXRetail/namespace/'}
        session_id_element = root.find('.//ns:SessionId', namespaces)
        
        if session_id_element is not None:
            session_id = session_id_element.text
            print(f"Extracted Session ID: {session_id}")
            return session_id
        else:
            print("Could not find SessionId in the login response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during login: {e}")
        if 'response' in locals() and response:
            save_to_file("1_login_error_response.txt", response.text)
        return None
    except ET.ParseError as e:
        print(f"Failed to parse login response XML: {e}")
        return None

def lookup_transaction(session_id, environment, store, lane, trans_id):
    """
    Performs a transaction lookup, saves the full response, and also
    extracts the receipt image to a separate file.
    """
    print("\n--- Step 2: Looking up transaction log... ---")
    if not session_id:
        print("Cannot perform transaction lookup without a session ID.")
        return

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    from_date_str = yesterday.strftime('%Y-%m-%d')
    to_date_str = day_after_tomorrow.strftime('%Y-%m-%d')
    full_from_date = f"{from_date_str}T00:00:00"
    full_to_date = f"{to_date_str}T23:59:59"
    print(f"Using dynamic date range: From '{full_from_date}' To '{full_to_date}'")

    url = f"http://{environment}:54473/StoreWebServices/TransactionLogLookup.rti"
    transaction_payload = f"""<TransactionLogLookupRequest xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:r10Ex="http://www.Retalix.com/Extensions" MajorVersion="1" xmlns="http://retalix.com/R10/services">
  <RequestHeader><MessageId>70</MessageId></RequestHeader>
  <SearchCriteria><RetailTransactionCriteria><EndDateTimeRange><From>{full_from_date}</From><To>{full_to_date}</To></EndDateTimeRange><BusinessUnitIds><BusinessUnitId>{store}</BusinessUnitId></BusinessUnitIds><TouchPointIds><TouchPointId>{lane}</TouchPointId></TouchPointIds><TransactionIDRange><From>{trans_id}</From><To>{trans_id}</To></TransactionIDRange><IsTrainingMode>false</IsTrainingMode></RetailTransactionCriteria></SearchCriteria>
  <IncludeTips>false</IncludeTips>
</TransactionLogLookupRequest>"""

    headers = {'Content-Type': 'application/xml; charset=utf-8', 'token': session_id}
    save_to_file("2_transaction_lookup_request.xml", format_xml_string(transaction_payload))

    try:
        response = requests.post(url, data=transaction_payload.encode('utf-8'), headers=headers, timeout=15)
        response.raise_for_status()
        print("Successfully received a response for transaction lookup!")

        # --- NEW LOGIC: SAVE FULL TLOG AND EXTRACT RECEIPT ---

        # First, format and save the complete, original response. This will include the receipt.
        print("Saving full transaction response to '2_transaction_lookup_response.xml'...")
        formatted_full_response = format_xml_string(response.text)
        save_to_file("2_transaction_lookup_response.xml", formatted_full_response)
        
        # Now, parse the response to extract just the receipt for its own file.
        namespaces = {
            'srv': 'http://retalix.com/R10/services',
            'nrf': 'http://www.nrf-arts.org/IXRetail/namespace/'
        }

        # We parse the original text to find the receipt element
        root = ET.fromstring(response.text)
        receipt_image_element = root.find('.//nrf:ReceiptImage', namespaces)

        # If a receipt image is found, extract its content and save it separately.
        if receipt_image_element is not None:
            print("Found ReceiptImage. Extracting to '3_receipt.xml'...")
            receipt_line = receipt_image_element.find('nrf:ReceiptLine', namespaces)
            
            if receipt_line is not None and receipt_line.text:
                unescaped_receipt_xml = html.unescape(receipt_line.text)
                formatted_receipt = format_xml_string(unescaped_receipt_xml)
                save_to_file("3_receipt.xml", formatted_receipt)
        else:
            print("No ReceiptImage element found in the response to extract.")
        
        # --------------------------------------------------
        
        print(f"Status Code: {response.status_code}")
        print("Formatted Full Transaction Log Body (as saved to file):")
        print(formatted_full_response)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during transaction lookup: {e}")
        if 'response' in locals() and response:
            save_to_file("2_transaction_lookup_error_response.txt", response.text)
    except ET.ParseError as e:
        print(f"Failed to parse the transaction response XML: {e}")
        # Save the raw response if it can't be parsed
        save_to_file("2_transaction_lookup_unparseable.xml", response.text)


if __name__ == "__main__":
    session_token = login_and_get_session(ENV)
    
    if session_token:
        lookup_transaction(session_token, ENV, STORE_NUMBER, LANE_NUMBER, TRANSACTION_NUMBER)

