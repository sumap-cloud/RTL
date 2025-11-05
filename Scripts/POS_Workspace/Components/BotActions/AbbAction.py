import socket
import time
def Trigger_Action(command):
    """
    Sends action commands to ABB robot via socket connection.
    
    The ABB bot has 60+ predefined actions with unique keywords.
    Each action keyword triggers a specific physical action on the bot.
    
    Examples of action keywords:
    - ",Close_Drawer" - Closes cash drawer physically
    - ",ups" - Moves robot up
    
    - And 57+ more actions based on POS scenarios
    
    Args:
        command (str): Action keyword to send to ABB bot (e.g., ",Close_Drawer")
    
    Returns:
        str: Response from ABB bot if successful, "ERROR: No response" if failed
    """
    try:
        # Create socket connection to ABB bot
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Address = '10.81.3.113'  # ABB bot IP address
        Address = '10.80.1.199'
        port = 5000              # ABB bot communication port
        
        # Connect and send command
        s.connect((Address, port))
        s.send(command.encode())
        
        # Receive response from ABB bot
        response = s.recv(1024)
        response_text = response.decode().strip()
        
        # Check if response is empty (invalid command)
        if not response_text:
            print(f"ERROR: No response received for command '{command}' - Invalid action keyword")
            return "ERROR: No response"
        
        # Valid response received
        print(f"ABB Bot Response: {response_text}")
        s.close()
        return response_text
        
    except Exception as e:
        print(f"ERROR: Failed to communicate with ABB bot - {str(e)}")
        return f"ERROR: {str(e)}"

# Test with valid action to confirm it works
Trigger_Action(",ups")
Trigger_Action(",ups")
time.sleep(1)  # Small delay to ensure command is processed
Trigger_Action(",ups")

# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: AbbAction
# @Purpose: ABB robot communication for physical POS hardware operations
# @Dependencies: socket
# @Input_Params: command (str) - Robot action keyword
# @Return_Values: String response from ABB robot or error message
# @Used_By_Tests: TC_Basic_Cash_Flow_ABBot
# @Known_Limitations: Requires ABB robot connectivity on 10.81.3.113:5000
# ============================================
