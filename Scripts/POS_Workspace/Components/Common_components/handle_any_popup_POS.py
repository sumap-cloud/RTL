"""
Component: Generic Popup Handler
Location: Components/Common_components/handle_any_popup_POS.py

Purpose:
    Universal popup handler for POS application that detects and manages
    various types of popups that can appear during POS operations.

Flow Context:
    - Called after major actions that might trigger popups
    - Used before/after payment processing
    - Part of error recovery flows
    - Called during cleanup operations

UI Elements:
    1. Receipt Suppressor Popup:
       - Title: "Receipt Supresser"
       - OK Button (type: Button)
       - Cancel Button (type: Button, optional)

    2. Error Message Popups:
       - Various titles (error-specific)
       - OK Button (type: Button)
       - Details area (type: Text, optional)

    3. Confirmation Dialogs:
       - Yes/No buttons (type: Button)
       - Message text (type: Text)

    4. Warning Popups:
       - Warning icon
       - OK/Cancel buttons
       - Warning message

Popup Types Handled:
    1. Receipt Related:
       - Receipt suppression
       - Print failures
       - Receipt options

    2. Transaction Related:
       - Transaction completion
       - Sale confirmation
       - Void confirmations

    3. System Messages:
       - Network errors
       - Database warnings
       - System notifications

    4. User Prompts:
       - Confirmations
       - Warnings
       - Information messages

Functions:
    handle_Any_popup(specific_button=None) -> bool:
        Purpose: Detect and handle any popup window.
        Args:
            specific_button (str, optional): The text of a specific button to click.
                                             If provided, the function will only
                                             look for this button. If None, it
                                             searches a default list.
        Returns:
            - True: Popup handled successfully or no popup found.
            - False: Failed to handle popup.

Error Handling:
    - Timeout handling (waits up to 10 seconds)
    - Window not found scenarios
    - Multiple popup scenarios
    - Button click failures
    - Focus issues

Usage Example:
    ```python
    # Basic popup handling (searches for default buttons):
    if handle_Any_popup():
        print("Popup handled or no popup present")
    else:
        print("Failed to handle popup")

    # Handling a specific confirmation dialog:
    handle_Any_popup(specific_button="Yes")
    ```
"""

import time
from pywinauto import Application, findwindows

def handle_Any_popup(specific_button=None):
    """
    Waits for a specific popup window and clicks a button on it.

    This function can either click a specific button provided by the user
    or search for a default set of buttons.

    Args:
        specific_button (str, optional): The text of the button to click.
                                         If provided, only this button will be
                                         targeted. Defaults to None.

    Returns:
        bool: True if a popup was found and a button was clicked, or if a popup
              was found but no target button was present.
              False if no popup was found or a critical error occurred.
    """
    # --- Configuration ---
    window_title_pattern = r".*Retalix\.(Woolworths\.)?Client\.POS\.Presentation\.ViewModels.*"
    wait_timeout = 10 # How long to wait for the window to appear (in seconds).

    # --- Button Selection Logic ---
    if specific_button:
        # If a specific button name is passed, use only that one.
        buttons_to_click = [specific_button]
        print(f"🎯 Targeting specific button: '{specific_button}'")
    else:
        # Otherwise, use the default list of buttons to search for.
        # Reordered to prefer OK over Cancel for better UX
        buttons_to_click = [ "Close", "Skip", "No", "OK", "Cancel"]
        print(f"🔍 Searching for default buttons: {buttons_to_click}")

    # --- Main Script ---
    print(f"Waiting for a popup window matching: '{window_title_pattern}'...")

    try:
        # Wait for the window to appear and connect to it.
        app = Application(backend="uia").connect(title_re=window_title_pattern, timeout=wait_timeout)
        win = app.window(title_re=window_title_pattern)

        print(f"\n[SUCCESS] Popup window found!")
        print(f"          Title: '{win.window_text()}'")

        # Bring the window to the front.
        win.set_focus()
        
        # Get all text controls and buttons in organized format
        popup_content = extract_popup_content(win)

        # --- Read Popup Message ---
        try:
            # Find the static text control with the auto_id "Title"
            message_control = win.child_window(auto_id="Title", control_type="Text")
            if message_control.exists():
                popup_message = message_control.window_text()
                print(f"          Message: '{popup_message}'")
        except findwindows.ElementNotFoundError:
            print("          Could not find a specific message control with auto_id='Title'.")

        # --- Find and Click a Button ---
        print(f"\n🎯 BUTTON SEARCH & CLICK:")
        print("─" * 50)
        if specific_button:
            print(f"  Looking for SPECIFIC button: '{specific_button}'")
        else:
            print(f"  Searching for ANY of these buttons: {buttons_to_click}")
        
        button_found = False
        for button_text in buttons_to_click:
            try:
                # Look for a button with the text from our list.
                button_to_click = win[button_text]

                # Check if the button actually exists and is clickable.
                if button_to_click.exists() and button_to_click.is_enabled():
                    print(f"\n  ✅ FOUND: '{button_text}' - Clicking now...")
                    button_to_click.click()
                    print(f"  ✅ SUCCESS: Button '{button_text}' clicked successfully!")
                    button_found = True
                    time.sleep(1) # Give a moment for the action to complete.
                    return True # Success, return True and exit the function.

            except findwindows.ElementNotFoundError:
                # This is normal, it just means this button wasn't found.
                if specific_button:
                    print(f"  ❌ SPECIFIC BUTTON '{button_text}' NOT FOUND")
                else:
                    print(f"  ❌ '{button_text}' not available")
                pass
            except Exception as e:
                print(f"  ❌ ERROR: Failed to click '{button_text}' - {e}")
                return False # An unexpected error occurred during the click.

        # If the loop finishes, it means no button from our list was found.
        if specific_button:
            print(f"\n  ⚠️  SPECIFIC BUTTON '{specific_button}' NOT FOUND IN POPUP")
            print(f"  Check the available buttons listed above in the analysis.")
            return False  # Return False when specific button is not found
        else:
            print(f"\n  ⚠️  NO TARGET BUTTONS FOUND")
            print(f"  Available buttons were displayed above in the analysis.")
            return True # Popup was found and processed, but no button was clicked.

    except findwindows.ElementNotFoundError:
        print("\n[INFO] No pop up on screen.")
        return True # No popup is also a success condition (nothing to handle).
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return False # Return False for any other critical errors.

def extract_popup_content(window):
    """Extract and display all text controls and buttons from the popup window"""
    
    print("\n" + "="*70)
    print("                    POPUP WINDOW ANALYSIS")
    print("="*70)
    
    try:
        # Get all controls in the window
        all_controls = window.descendants()
        
        text_controls = []
        buttons = []
        other_controls = []
        
        # Categorize controls
        for control in all_controls:
            try:
                control_type = control.element_info.control_type
                control_text = control.window_text().strip()
                
                # Skip empty controls
                if not control_text:
                    continue
                
                if "Button" in control_type:
                    buttons.append({
                        'text': control_text,
                        'type': control_type,
                        'automation_id': getattr(control.element_info, 'automation_id', 'N/A'),
                        'control': control
                    })
                elif any(text_type in control_type for text_type in ["Text", "Static", "Label", "Edit"]):
                    text_controls.append({
                        'text': control_text,
                        'type': control_type,
                        'automation_id': getattr(control.element_info, 'automation_id', 'N/A'),
                        'control': control
                    })
                else:
                    other_controls.append({
                        'text': control_text,
                        'type': control_type,
                        'automation_id': getattr(control.element_info, 'automation_id', 'N/A'),
                        'control': control
                    })
                    
            except Exception as e:
                # Skip controls that can't be accessed
                continue
        
        # Display popup messages (text controls) organized
        print(f"\n📋 POPUP MESSAGES ({len(text_controls)} found):")
        print("─" * 50)
        if text_controls:
            for i, text_ctrl in enumerate(text_controls, 1):
                print(f"  {i}. '{text_ctrl['text']}'")
        else:
            print("  No messages found in popup.")
        
        # Display buttons section
        print(f"\n🔲 AVAILABLE BUTTONS ({len(buttons)} found):")
        print("─" * 50)
        if buttons:
            for i, button in enumerate(buttons, 1):
                print(f"  {i}. [{button['text']}]")
                if button['automation_id'] != 'N/A':
                    print(f"     AutoID: {button['automation_id']}")
        else:
            print("  No buttons available in this popup.")
        
        # Display other controls with values (like amounts, data)
        if other_controls:
            print(f"\n💰 VALUES & DATA ({len(other_controls)} found):")
            print("─" * 50)
            for i, other_ctrl in enumerate(other_controls, 1):
                if other_ctrl['text'] != 'DataPager':  # Skip system controls
                    print(f"  {i}. Value: '{other_ctrl['text']}'")
        
        # Clean summary
        print(f"\n{'='*70}")
        print(f"SUMMARY: {len(text_controls)} Messages | {len(buttons)} Buttons | {len(other_controls)} Values")
        print("="*70)
        
        return {
            'text_controls': text_controls,
            'buttons': buttons,
            'other_controls': other_controls
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to extract popup content - {str(e)}")
        return None

# --- Example of how to use the updated function ---
if __name__ == "__main__":
    print("🚀 POPUP HANDLER DEMO")
    print("="*50)
    
    # Only run one test at a time
    print("Choose test mode:")
    print("1. Default mode (any available button)")
    print("2. Specific button mode (specify button name)")
    print("3. Just analyze popup (no clicking)")
    
    # For demo purposes, let's just run default mode
    # print("\n--- Running: Default Mode ---")
    # was_handled_default = handle_Any_popup()

    # if was_handled_default:
    #     print("\n✅ Popup handler finished successfully.")
    # else:
    #     print("\n❌ Popup handler encountered a critical error.")
    
    # print("\n" + "="*50)
    # print("Demo completed!")
    
    #Uncomment below lines to test specific button mode:
    print("\n--- Testing: Specific Button Mode ---")
    # was_handled_specific = handle_Any_popup(specific_button="Close")
    # if was_handled_specific:
    #     print("\n✅ Specific popup handler finished successfully.")
    # else:
    #     print("\n❌ Specific popup handler encountered a critical error.")
    was_handled_specific = handle_Any_popup(specific_button="Save for Next Shop")
    if was_handled_specific:
        print("\n✅ Specific popup handler finished successfully.")
    else:
        print("\n❌ Specific popup handler encountered a critical error.")
