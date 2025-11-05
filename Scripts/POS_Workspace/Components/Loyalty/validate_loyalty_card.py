# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: validate_loyalty_card
# @Purpose: Validates loyalty card data display on operator and customer screens
# @Dependencies: pywinauto.Application, re
# @Input_Params: None
# @Return_Values: Boolean success/failure of loyalty card validation
# @Used_By_Tests: TC005_loyalty_details_scenario
# @Known_Limitations: Relies on specific UI text patterns
# ============================================

from pywinauto import Application
import time
import re # Import the regular expression module

def connect_to_app():
    """Connects to the running POS application."""
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
    return app

def validate_loyalty_card():
    """
    Validates the presence of loyalty card indicators on both operator and customer displays.
    It also captures and validates the savings amount and points collected.
    """
    try:
        app = connect_to_app()
        
        # --- 1. Check Operator Display ---
        operator_window = app.window(title_re=".*R10PosClient.*")
        print("📝 Checking operator display for loyalty card...")
        
        loyalty_elements = operator_window.descendants()
        loyalty_found = False
        loyalty_keywords = ["everyday", "rewards", "loyalty", "member card", "woolworths"]
        
        for element in loyalty_elements:
            try:
                text = element.window_text().lower().strip()
                if any(keyword in text for keyword in loyalty_keywords):
                    control_type = element.element_info.control_type
                    print(f"✅ Loyalty card found in operator display - Element: '{text}' (Type: {control_type})")
                    loyalty_found = True
                    break # Found it, no need to keep scanning
            except Exception:
                # Some elements might not have text or other properties, so we continue
                continue
                
        # --- 2. Check Customer Display ---
        customer_window = app.window(auto_id="GraphicCustomerDisplayID")
        print("\n📝 Checking customer display for member card, savings, and points...")
        
        # Scan ALL descendant elements, not just Text controls, for better reliability.
        customer_elements = customer_window.descendants()
        
        savings_found = False
        points_found = False
        customer_card_found = False
        
        savings_value = None
        points_value = None

        # Flags to indicate that the next text element contains the value we want
        next_element_is_savings = False
        next_element_is_points = False

        print("📝 Scanning customer display elements:")
        for element in customer_elements:
            try:
                text = element.window_text().strip()
                if not text:
                    continue # Skip elements with no text

                # If a flag was set in the previous iteration, this element is our value.
                if next_element_is_savings:
                    # Use regex to find the floating point number in a string like "$3.00"
                    match = re.search(r'[\d.]+', text)
                    if match:
                        savings_value = float(match.group(0))
                        print(f"💰 Savings amount captured: ${savings_value:.2f}")
                        savings_found = True
                    next_element_is_savings = False # Reset the flag
                    continue # Value found, move to the next element

                if next_element_is_points:
                    if text.isdigit():
                        points_value = int(text)
                        print(f"📊 Points collected captured: {points_value}")
                        points_found = True
                    next_element_is_points = False # Reset the flag
                    continue # Value found, move to the next element

                # --- Check for labels and other static text ---

                # Check for member card related text
                if any(keyword in text.lower() for keyword in ["member card", "everyday rewards"]):
                    print(f"✅ Member card indicator found in customer display - Element: '{text}'")
                    customer_card_found = True

                # If we find a label, set a flag to process the *next* text element as its value
                if "your savings" in text.lower():
                    print(f"✅ Found savings label: '{text}'")
                    next_element_is_savings = True
                
                if "points collected" in text.lower():
                    print(f"✅ Found points label: '{text}'")
                    next_element_is_points = True
            
            except Exception:
                continue

        # --- 3. Final Validation ---
        if loyalty_found and customer_card_found and savings_found and points_found:
            print("\n✅ Loyalty card validation successful!")
            print(f"✓ Operator display: Member card indicator found")
            print(f"✓ Customer display: Member card indicator found")
            print(f"✓ Customer display: Savings information found (${savings_value:.2f})")
            print(f"✓ Customer display: Points collected ({points_value})")
            return True
        else:
            print("\n❌ Validation Failed. Results:")
            print(f"- Operator Display Check: {'Passed' if loyalty_found else 'Failed'}")
            print(f"- Customer Display Card Check: {'Passed' if customer_card_found else 'Failed'}")
            print(f"- Customer Display Savings Check: {'Passed' if savings_found else 'Failed'} (Value: {savings_value})")
            print(f"- Customer Display Points Check: {'Passed' if points_found else 'Failed'} (Value: {points_value})")
            return False

    except Exception as e:
        print(f"❌ An error occurred during validation: {str(e)}")
        return False

def main():
    """Main function to run the validation."""
    print("🔍 Starting loyalty card validation...")
    time.sleep(2) # Give a moment to switch to the target application
    validate_loyalty_card()

if __name__ == "__main__":
    main()

