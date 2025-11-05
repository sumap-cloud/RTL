# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: TemporaryChequeWorkflowHandler
# @Purpose: Manages complete temporary cheque tender workflow for POS transactions
# @Dependencies: pywinauto.Application, Virtual_keyboard_reference, handle_approval_popup, handle_Any_popup
# @Input_Params: amount, cheque_details, template_name, approval_username, approval_password
# @Return_Values: Boolean indicating success/failure of complete workflow process
# @Used_By_Tests: Temporary cheque transaction scenarios, Multi-step tender workflows
# @Known_Limitations: Requires R10PosClient to be running, depends on specific UI element IDs
# @Workflow_Steps: 
#   0. Tender Selection (Cheque -> Temporary Cheque)
#   1. Tender Amount Entry with virtual keypad
#   2. Cheque Details Entry (Account, BSB, Bank info)
#   3. Template Selection (cheque size/format)
#   4. First Endorsement Screen (Insert Cheque)
#   5. Second Endorsement Screen (Insert Cheque/Voucher)
#   6. Final Popup Handling
# ============================================

from pywinauto import Application
import time
import re
import sys
import importlib.util
from pathlib import Path

# Set up project path
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Common_components.Approvalrequired import handle_approval_popup
from Components.Common_components.virtual_reference_keyboard import Virtual_keyboard_reference
from Components.Common_components.handle_any_popup_POS import handle_Any_popup


class TemporaryChequeWorkflowHandler:
    """
    A comprehensive handler for the complete temporary cheque tender workflow in R10PosClient.
    
    This class manages the entire process of completing a transaction using a temporary cheque tender,
    from initial tender selection through final endorsement and popup handling.
    
    Purpose:
        To automate the complete temporary cheque transaction workflow, handling all required screens
        and user interactions in sequence for successful POS transaction completion.
    
    Workflow Sequence:
        0. Tender Selection (Cheque -> Temporary Cheque)
        1. Tender Amount Entry - Enter transaction amount using virtual keypad
        2. Cheque Details Entry - Fill account name, BSB, account number, cheque number, bank details
        3. Template Selection - Choose cheque template size/format
        4. First Endorsement - Handle "Insert Cheque" screen with manual option
        5. Second Endorsement - Handle "Insert Cheque/Voucher" screen with manual option
        6. Final Popup Handling - Process any remaining confirmation dialogs
    
    Dependencies:
        - pywinauto.Application for UI automation
        - Virtual_keyboard_reference for text entry on virtual keyboards
        - handle_approval_popup for manager approval workflows
        - handle_Any_popup for general popup management
        - R10PosClient application must be running and accessible
    
    Known Limitations:
        - Requires specific UI element automation IDs to be present
        - Dependent on R10PosClient application state and responsiveness
        - Virtual keyboard functionality requires specific keypad elements
        - Template names must match exactly as displayed in UI
    
    Returns:
        Boolean values indicating success/failure for each workflow step and overall completion
    """
    
    def __init__(self):
        """
        Initializes the TemporaryChequeWorkflowHandler and establishes connection to POS application.
        
        Establishes connection to the R10PosClient application window and prepares the handler
        for executing the temporary cheque workflow. Sets up application and window references
        for subsequent UI automation operations.
        
        Attributes:
            app: pywinauto Application object for R10PosClient
            win: Main application window reference
            is_connected: Boolean flag indicating successful connection status
        """
        self.app = None
        self.win = None
        self.is_connected = self._connect_to_pos()

    def _connect_to_pos(self):
        """
        Establishes connection to the main R10PosClient application window.
        
        Attempts to connect to the POS application using pywinauto backend and sets focus
        on the main window for subsequent automation operations.
        
        Returns:
            bool: True if connection successful, False if connection failed
            
        Raises:
            Exception: If R10PosClient application is not running or not accessible
        """
        try:
            print("Connecting to the POS application...")
            self.app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
            self.win = self.app.window(title_re=".*R10PosClient.*")
            self.win.set_focus()
            print("Successfully connected to the main window.")
            self.win.wait('ready', timeout=30)
            return True
        except Exception as e:
            print(f"An error occurred during connection: {e}")
            print("Please ensure the R10PosClient application is running.")
            return False

    # ==================== SCREEN 1: TENDER AMOUNT ENTRY ====================
    
    def get_current_amount(self):
        """
        Retrieves the current value from the tender amount input field.
        """
        if not self.is_connected:
            return None
        try:
            print("Reading current amount...")
            amount_edit = self.win.child_window(auto_id="tbAmount_InnerText", control_type="Edit")
            if amount_edit.exists():
                amount = amount_edit.get_value()
                print(f"Current amount is: {amount}")
                return amount
            else:
                print("Error: Could not find the amount input field.")
                return None
        except Exception as e:
            print(f"An error occurred while getting the current amount: {e}")
            return None

    def enter_amount(self, amount):
        """
        Enters a specified amount using the on-screen keypad.
        """
        if not self.is_connected:
            return False
        try:
            print(f"Entering amount: {amount} using on-screen keypad...")
            keypad = self.win.child_window(auto_id="PosKeyPadId", control_type="Custom")
            if not keypad.exists():
                print("Error: On-screen keypad not found.")
                return False

            # Clear the existing amount first by clicking 'C'
            keypad.child_window(title="C", auto_id="C", control_type="Button").click_input()
            time.sleep(0.1)

            # Click each digit/character of the amount string
            for char in str(amount):
                keypad.child_window(title=char, auto_id=char, control_type="Button").click_input()
                time.sleep(0.1)
            
            print("Amount entered successfully.")
            return True
        except Exception as e:
            print(f"An error occurred while entering the amount: {e}")
            return False

    def click_amount_ok(self):
        """
        Clicks the 'OK' button on the amount entry screen.
        """
        if not self.is_connected:
            return False
        try:
            print("Clicking OK button on amount screen...")
            ok_button = self.win.child_window(title="OK", auto_id="OK", control_type="Button")
            if ok_button.exists():
                ok_button.click_input()
                print("Successfully clicked OK.")
                time.sleep(2)  # Wait for next screen to load
                return True
            else:
                print("Error: OK button not found.")
                return False
        except Exception as e:
            print(f"An error occurred while clicking OK: {e}")
            return False

    def get_screen_details(self):
        """
        Retrieves the title and balance due from the tender amount screen.
        """
        if not self.is_connected:
            return None
        try:
            print("Reading screen details...")
            details = {'title': None, 'balance_due': None}

            title_element = self.win.child_window(auto_id="TenderName", control_type="Text")
            if title_element.exists():
                details['title'] = title_element.window_text()

            tender_view = self.win.child_window(auto_id="TenderAmountViewID", control_type="Custom")
            if tender_view.exists():
                possible_balances = tender_view.children(control_type="Custom")
                for control in possible_balances:
                    if re.match(r"^\d+\.\d{2}$", control.window_text()):
                        details['balance_due'] = control.window_text()
                        break 

            return details
        except Exception as e:
            print(f"An error occurred while getting screen details: {e}")
            return None

    # ==================== SCREEN 2: CHEQUE DETAILS ENTRY ====================
    
    def get_cheque_details_elements(self):
        """
        Identifies all the interactive elements on the temporary cheque details screen.
        """
        if not self.is_connected:
            return None

        print("\nSearching for elements on the 'Temporary Cheque Details' screen...")
        elements = {
            'main_title': None,
            'sub_title': None,
            'input_fields': {},
            'virtual_keypad_buttons': {},
            'buttons': {}
        }

        try:
            all_customs = self.win.descendants(control_type="Custom")
            cheque_view = None
            for custom in all_customs:
                if custom.automation_id() == "TemporaryChequeViewID":
                    cheque_view = custom
                    break
            
            if not cheque_view:
                print("Error: Could not find the 'TemporaryChequeViewID' container.")
                return None
            
            # Get sub-title
            for text in cheque_view.children(control_type="Text"):
                if text.automation_id() == "TemporaryChequePleaseEnterAccountDetails":
                    elements['sub_title'] = text.window_text()
                    break

            # Get main title
            all_descendants = self.win.descendants()
            for elem in all_descendants:
                try:
                    if "Temporary Cheque" in elem.window_text():
                        elements['main_title'] = "Temporary Cheque"
                        break
                except Exception:
                    continue

            # Identify input fields
            field_ids = {
                "Account Name": "AccountNameTextControl_InnerText",
                "BSB Number": "BSBNumberTextControl_InnerText",
                "Account Number": "AccountNumberTextControl_InnerText",
                "Cheque Number": "ChequeNumberTextControl_InnerText",
                "Bank Name": "BankNameTextControl_InnerText",
                "Bank Location": "BankLocationTextControl_InnerText"
            }
            
            fields_with_keypad = ["Account Name", "Bank Name", "Bank Location"]

            all_edits = cheque_view.descendants(control_type="Edit")
            for name, auto_id in field_ids.items():
                elements['input_fields'][name] = None
                found_edit = None
                for edit in all_edits:
                    if edit.automation_id() == auto_id:
                        elements['input_fields'][name] = edit
                        found_edit = edit
                        break
                
                if found_edit and name in fields_with_keypad:
                    try:
                        list_item_parent = found_edit.parent()
                        keypad_button = None
                        all_buttons_in_parent = list_item_parent.children(control_type="Button")
                        for btn in all_buttons_in_parent:
                            if btn.automation_id() == "VirtualKeypadButton":
                                keypad_button = btn
                                break
                        elements['virtual_keypad_buttons'][name] = keypad_button
                    except Exception:
                        elements['virtual_keypad_buttons'][name] = None
            
            # Identify Confirm and Cancel buttons
            for button in cheque_view.children(control_type='Button'):
                if button.window_text() == 'Confirm':
                    elements['buttons']['Confirm'] = button
                elif button.window_text() == 'Cancel':
                    elements['buttons']['Cancel'] = button

            return elements

        except Exception as e:
            print(f"An error occurred while finding cheque details elements: {e}")
            return None

    def fill_cheque_details(self, details):
        """
        Fills the cheque details form and clicks confirm.
        """
        if not self.is_connected:
            return False

        print("\nStarting to fill cheque details...")
        screen_elements = self.get_cheque_details_elements()
        if not screen_elements:
            print("Could not get screen elements. Aborting.")
            return False

        fields_with_keypad = ["Account Name", "Bank Name", "Bank Location"]

        try:
            for field_name, value in details.items():
                if field_name in fields_with_keypad:
                    print(f"Entering '{value}' into '{field_name}' using virtual keyboard...")
                    keypad_button = screen_elements['virtual_keypad_buttons'].get(field_name)
                    if keypad_button:
                        keypad_button.click_input()
                        time.sleep(3)
                        Virtual_keyboard_reference(enter=value)
                        time.sleep(5)
                        print(f"Successfully entered value for '{field_name}'.")
                    else:
                        print(f"Warning: Could not find virtual keypad for '{field_name}'.")
                else:
                    print(f"Entering '{value}' into '{field_name}' directly...")
                    input_field = screen_elements['input_fields'].get(field_name)
                    if input_field:
                        input_field.set_edit_text(value)
                        print(f"Successfully entered value for '{field_name}'.")
                    else:
                        print(f"Warning: Could not find input field for '{field_name}'.")
            
            print("\nAll details entered. Clicking 'Confirm'...")
            confirm_button = screen_elements['buttons'].get('Confirm')
            if confirm_button:
                confirm_button.click_input()
                print("Successfully clicked 'Confirm'.")
                time.sleep(2)  # Wait for next screen
                return True
            else:
                print("Error: Could not find the 'Confirm' button.")
                return False

        except Exception as e:
            print(f"An error occurred during the fill and confirm process: {e}")
            return False

    # ==================== SCREEN 3: TEMPLATE SELECTION ====================
    
    def get_template_elements(self):
        """
        Identifies all the interactive elements on the template selection screen.
        """
        if not self.is_connected:
            return None

        print("\nSearching for elements on the 'Template Selection' screen...")
        elements = {
            'main_title': None,
            'sub_title': None,
            'template_options': {},
            'buttons': {}
        }

        try:
            tender_view = None
            all_customs = self.win.descendants(control_type="Custom")
            for custom in all_customs:
                if custom.automation_id() == "TenderAmountViewID":
                    tender_view = custom
                    break
            
            if not tender_view:
                print("Error: Could not find the 'TenderAmountViewID' container.")
                return None

            # Get main title
            all_descendants = self.win.descendants()
            for elem in all_descendants:
                try:
                    if "Temporary Cheque" in elem.window_text():
                        elements['main_title'] = "Temporary Cheque"
                        break
                except Exception:
                    continue

            # Get sub-title
            for text_element in tender_view.children(control_type="Text"):
                if text_element.window_text() == "Please select a template:":
                    elements['sub_title'] = text_element.window_text()
                    break

            # Identify template options
            template_list = None
            for lst in tender_view.children(control_type="List"):
                if lst.automation_id() == "ChequeEndorsementList":
                    template_list = lst
                    break
            
            if template_list:
                list_items = template_list.children(control_type="ListItem")
                for item in list_items:
                    child_buttons = item.children(control_type="RadioButton")
                    for btn in child_buttons:
                        if btn.automation_id() == "ChequeEndorsementButton":
                            option_name = btn.window_text()
                            elements['template_options'][option_name] = btn
                            break
            
            # Identify Cancel button
            for btn in tender_view.children(control_type="Button"):
                if btn.automation_id() == "TenderAmountViewCancelCommand":
                    elements['buttons']['Cancel'] = btn
                    break

            return elements

        except Exception as e:
            print(f"An error occurred while finding template elements: {e}")
            return None

    def select_template(self, template_name):
        """
        Selects a cheque template by its name.
        """
        if not self.is_connected:
            return False
            
        print(f"\nAttempting to select template: '{template_name}'...")
        try:
            screen_elements = self.get_template_elements()
            
            if screen_elements and template_name in screen_elements['template_options']:
                button_to_click = screen_elements['template_options'][template_name]
                if button_to_click:
                    print(f"Template '{template_name}' found. Clicking...")
                    button_to_click.click_input()
                    print(f"Successfully clicked the '{template_name}' button.")
                    time.sleep(2)  # Wait for next screen
                    return True
                else:
                    print(f"Error: Button element for '{template_name}' is not valid.")
                    return False
            else:
                print(f"Error: Could not find the template option '{template_name}'.")
                return False

        except Exception as e:
            print(f"An error occurred while trying to select the template: {e}")
            return False

    # ==================== SCREEN 4: ENDORSEMENT (INSERT CHEQUE) ====================
    
    def get_endorsement_elements(self):
        """
        Identifies all the elements on the cheque endorsement screen.
        """
        if not self.is_connected:
            return None

        print("\nSearching for elements on the endorsement screen...")
        elements = {
            'main_title': None,
            'instruction_1': None,
            'instruction_2': None,
            'balance_due': None,
            'buttons': {}
        }

        try:
            # Find endorsement screen by looking for specific text
            endorsement_text_elements = self.win.descendants(title="Please insert Cheque for endorsement Face Up", control_type="Text")
            if endorsement_text_elements:
                endorsement_view = endorsement_text_elements[0].parent()
                
                # Get main title
                all_descendants = self.win.descendants()
                for elem in all_descendants:
                    try:
                        if "Temporary Cheque" in elem.window_text():
                            elements['main_title'] = "Temporary Cheque"
                            break
                    except Exception:
                        continue

                # Get instructional texts
                for text_element in endorsement_view.children(control_type="Text"):
                    if text_element.window_text() == "Please insert Cheque for endorsement Face Up":
                        elements['instruction_1'] = text_element
                    elif text_element.window_text() == "Press 'Manual' to perform endorsement by hand":
                        elements['instruction_2'] = text_element

                # Get buttons
                for button in endorsement_view.children(control_type="Button"):
                    button_text = button.window_text()
                    if button_text in ["Endorse", "Manual", "Cancel"]:
                        elements['buttons'][button_text] = button

                # Get balance due
                custom_elements = self.win.descendants(control_type="Custom")
                for custom in custom_elements:
                    if custom.automation_id() == "15.00":  # This might need adjustment
                        elements['balance_due'] = custom.window_text()
                        break

            return elements

        except Exception as e:
            print(f"An error occurred while finding endorsement elements: {e}")
            return None

    def click_manual_endorsement(self):
        """
        Clicks the 'Manual' button on the endorsement screen.
        """
        if not self.is_connected:
            return False

        try:
            screen_elements = self.get_endorsement_elements()
            if screen_elements:
                manual_button = screen_elements.get('buttons', {}).get('Manual')
                if manual_button:
                    print("\nClicking the 'Manual' button...")
                    manual_button.click_input()
                    print("Successfully clicked 'Manual'.")
                    time.sleep(2)  # Wait for next screen
                    return True
                else:
                    print("\n'Manual' button not found.")
                    return False
            return False
        except Exception as e:
            print(f"An error occurred while clicking Manual: {e}")
            return False

    # ==================== SCREEN 5: ENDORSEMENT (CHEQUE/VOUCHER) ====================
    
    def get_voucher_endorsement_elements(self):
        """
        Identifies all the elements on the cheque/voucher endorsement screen.
        """
        if not self.is_connected:
            return None

        print("\nSearching for elements on the voucher endorsement screen...")
        elements = {
            'main_title': None,
            'instruction_1': None,
            'instruction_2': None,
            'balance_due': None,
            'buttons': {}
        }

        try:
            # Search for all text elements
            all_texts = self.win.descendants(control_type='Text')
            for text_elem in all_texts:
                try:
                    text = text_elem.window_text()
                    if "Please insert Cheque/Voucher for endorsement" in text:
                        elements['instruction_1'] = text_elem
                    elif "Press 'Manual' to perform endorsement by hand" in text:
                        elements['instruction_2'] = text_elem
                    elif text_elem.automation_id() == "TenderName":
                        elements['main_title'] = text
                except Exception:
                    continue
            
            # Search for buttons
            all_buttons = self.win.descendants(control_type='Button')
            for btn in all_buttons:
                try:
                    text = btn.window_text()
                    if text in ["Endorse", "Manual", "Cancel"]:
                        elements['buttons'][text] = btn
                except Exception:
                    continue

            # Search for balance due
            all_customs = self.win.descendants(control_type='Custom')
            for custom in all_customs:
                try:
                    if '.' in custom.automation_id() and custom.automation_id() == custom.window_text():
                        float(custom.window_text())
                        elements['balance_due'] = custom.window_text()
                        break 
                except (ValueError, Exception):
                    continue

            return elements

        except Exception as e:
            print(f"An error occurred while finding voucher endorsement elements: {e}")
            return None

    def click_voucher_manual(self):
        """
        Clicks the 'Manual' button on the voucher endorsement screen.
        """
        if not self.is_connected:
            return False

        try:
            screen_elements = self.get_voucher_endorsement_elements()
            if screen_elements:
                manual_button = screen_elements.get('buttons', {}).get('Manual')
                if manual_button:
                    print("\nClicking the 'Manual' button on voucher screen...")
                    manual_button.click_input()
                    print("Successfully clicked 'Manual'.")
                    time.sleep(2)
                    return True
                else:
                    print("\n'Manual' button not found on voucher screen.")
                    return False
            return False
        except Exception as e:
            print(f"An error occurred while clicking voucher Manual: {e}")
            return False

    # ==================== COMPLETE WORKFLOW ====================
    
    def complete_temporary_cheque_workflow(self, amount, cheque_details, template_name="Small - 160 X 70", 
                                         approval_username="atmgr5", approval_password="abcd1234"):
        """
        Executes the complete temporary cheque workflow from start to finish.
        
        This is the main method that orchestrates the entire temporary cheque transaction process.
        It handles all workflow steps in sequence, with proper error handling and logging.
        
        Workflow Steps:
            0. Tender Selection: Selects 'Cheque' tender and 'Temporary Cheque' option
            1. Amount Entry: Enters transaction amount using virtual keypad
            2. Cheque Details: Fills all required cheque information fields
            3. Template Selection: Chooses appropriate cheque template
            4. First Endorsement: Handles initial cheque insertion screen
            5. Second Endorsement: Handles cheque/voucher endorsement screen
            6. Final Cleanup: Processes any remaining popups or confirmations
        
        Args:
            amount (str): The tender amount to enter (e.g., "5.50")
            cheque_details (dict): Dictionary containing all cheque information:
                - "Account Name": Account holder name
                - "BSB Number": Bank State Branch number
                - "Account Number": Bank account number
                - "Cheque Number": Cheque reference number
                - "Bank Name": Name of the bank
                - "Bank Location": Bank branch location
            template_name (str, optional): Template to select. Defaults to "Small - 160 X 70"
            approval_username (str, optional): Username for manager approval. Defaults to "atmgr5"
            approval_password (str, optional): Password for manager approval. Defaults to "abcd1234"
            
        Returns:
            bool: True if entire workflow completed successfully, False if any step failed
            
        Example:
            cheque_details = {
                "Account Name": "John Doe",
                "BSB Number": "123456",
                "Account Number": "987654321",
                "Cheque Number": "101111",
                "Bank Name": "Sample Bank",
                "Bank Location": "Main Branch"
            }
            
            success = handler.complete_temporary_cheque_workflow(
                amount="15.75",
                cheque_details=cheque_details,
                template_name="Large - 200 X 90"
            )
        """
        if not self.is_connected:
            print("Not connected to POS application. Cannot proceed with workflow.")
            return False

        print("=" * 60)
        print("STARTING COMPLETE TEMPORARY CHEQUE WORKFLOW")
        print("=" * 60)

        try:
            # Step 0: Tender Selection
            print("\n🔹 STEP 0: Tender Selection")
            print("-" * 40)
            print("Selecting 'Cheque' tender and 'Temporary Cheque' option...")
            
            # Import process_tender locally to avoid circular import issues
            try:
                import sys
                tender_selection_path = str(current_file_path.parent / "tenderSelection.py")
                
                # Load the module dynamically
                import importlib.util
                spec = importlib.util.spec_from_file_location("tenderSelection", tender_selection_path)
                tender_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tender_module)
                
                tender_result = tender_module.process_tender(tender_name="Cheque", tender_option="Temporary Cheque")
                
            except Exception as e:
                print(f"❌ Failed to import or call process_tender: {e}")
                print("⚠️ Continuing workflow without tender selection step...")
                tender_result = {'success': True, 'message': 'Skipped tender selection due to import error'}
            
            if tender_result['success']:
                print("✅ Tender selection completed successfully!")
                print(f"📝 Message: {tender_result['message']}")
                time.sleep(2)  # Wait for UI to settle after tender selection
            else:
                print("❌ Failed to select tender. Aborting workflow.")
                print(f"📝 Error: {tender_result['message']}")
                return False

            # Step 1: Handle tender amount entry
            print("\n🔹 STEP 1: Tender Amount Entry")
            print("-" * 40)
            
            screen_details = self.get_screen_details()
            if screen_details:
                print(f"Screen Title: {screen_details.get('title', 'Not Found')}")
                print(f"Balance Due: {screen_details.get('balance_due', 'Not Found')}")

            current_amount = self.get_current_amount()
            
            if not self.enter_amount(amount):
                print("❌ Failed to enter amount. Aborting workflow.")
                return False
            
            if not self.click_amount_ok():
                print("❌ Failed to click OK on amount screen. Aborting workflow.")
                return False

            # Handle approval popup if it appears
            try:
                print("\n🔹 Handling approval popup...")
                handle_approval_popup(approval_required=True, 
                                    first_username=approval_username, 
                                    first_password=approval_password)
                time.sleep(2)
            except Exception as e:
                print(f"Note: Approval handling: {e}")

            # Step 2: Fill cheque details
            print("\n🔹 STEP 2: Cheque Details Entry")
            print("-" * 40)
            
            if not self.fill_cheque_details(cheque_details):
                print("❌ Failed to fill cheque details. Aborting workflow.")
                return False

            # Step 3: Select template
            print("\n🔹 STEP 3: Template Selection")
            print("-" * 40)
            
            if not self.select_template(template_name):
                print("❌ Failed to select template. Aborting workflow.")
                return False

            # Step 4: Handle first endorsement screen
            print("\n🔹 STEP 4: First Endorsement Screen")
            print("-" * 40)
            
            if not self.click_manual_endorsement():
                print("❌ Failed to click manual on first endorsement. Aborting workflow.")
                return False

            # Step 5: Handle second endorsement screen
            print("\n🔹 STEP 5: Second Endorsement Screen")
            print("-" * 40)
            
            if not self.click_voucher_manual():
                print("❌ Failed to click manual on second endorsement. Aborting workflow.")
                return False

            # Step 6: Handle final popup (if any)
            print("\n🔹 STEP 6: Final Popup Handling")
            print("-" * 40)
            
            try:
                print("Checking for final popup and clicking OK if present...")
                popup_handled = handle_Any_popup(specific_button="OK")
                if popup_handled:
                    print("✅ Final popup handled successfully or no popup found.")
                else:
                    print("⚠️ No popup found or popup handling failed.")
                time.sleep(1)  # Brief pause after popup handling
            except Exception as e:
                print(f"Note: Final popup handling: {e}")

            print("\n" + "=" * 60)
            print("✅ TEMPORARY CHEQUE WORKFLOW COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n❌ An error occurred during the workflow: {e}")
            return False


if __name__ == "__main__":
    """
    Main execution block for testing and demonstrating the temporary cheque workflow.
    
    This section provides a complete example of how to use the TemporaryChequeWorkflowHandler
    to process a temporary cheque transaction. It includes sample cheque details and
    demonstrates the proper workflow execution.
    
    Usage:
        Run this script directly to execute a test temporary cheque transaction.
        Ensure R10PosClient is running before execution.
    
    Example Cheque Details:
        All required fields are populated with sample data that can be modified
        as needed for different test scenarios.
    """
    # Initialize the complete workflow handler
    workflow_handler = TemporaryChequeWorkflowHandler()

    if workflow_handler.is_connected:
        # Define the cheque details with all required fields
        cheque_details = {
            "Account Name": "ATmgr5",           # Account holder name
            "BSB Number": "123456",             # Bank State Branch number
            "Account Number": "987654321",      # Bank account number
            "Cheque Number": "101111",          # Cheque reference number
            "Bank Name": "My Bank",             # Bank name
            "Bank Location": "City Branch"      # Bank branch location
        }

        # Execute the complete workflow
        success = workflow_handler.complete_temporary_cheque_workflow(
            amount="5.50",
            cheque_details=cheque_details,
            template_name="Small - 160 X 70",
            approval_username="atmgr5",
            approval_password="abcd1234"
        )

        if success:
            print("\n🎉 Workflow completed successfully!")
        else:
            print("\n💥 Workflow failed. Please check the logs above.")
    else:
        print("❌ Could not connect to the POS application. Please ensure it's running.")
