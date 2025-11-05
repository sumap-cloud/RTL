# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: member_card_details
# @Purpose: Handles navigation and validation of member loyalty card details in POS
# @Dependencies: pywinauto.application.Application, pywinauto.mouse
# @Input_Params: None
# @Return_Values: Boolean indicating success/failure of operations
# @Used_By_Tests: TC005_loyalty_details_scenario, TC003_loyalty_basic_scenario_ai
# @Known_Limitations: Depends on consistent UI element locations
# ============================================

from pywinauto import Application, mouse
import time

def connect_to_app():
    """Connects to the POS application window."""
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
    win = app.window(title_re=".*R10PosClient.*")
    return app, win

def click_member_card_and_validate():
    """
    Finds the 'Member Card' element, clicks it, validates the details,
    and then clicks it again to close the details view.
    """
    try:
        app, win = connect_to_app()
        print("📝 Looking for member card element...")
        
        # Try to find the element directly for efficiency
        member_cards = win.descendants(title="Member Card", control_type="ListItem")
        if member_cards:
            member_card = member_cards[0]
            print(f"✅ Found target element using direct search")
        else:
            # If not found, use a more thorough fallback search
            member_card = None
            for element in win.descendants():
                try:
                    text = element.window_text().strip()
                    control_type = element.element_info.control_type
                    
                    if text == "Member Card" and control_type == "ListItem":
                        member_card = element
                        print(f"✅ Found target element using fallback search")
                        break
                except:
                    continue
        
        if member_card:
            print("\nAttempting to click member card...")
            try:
                # Get the element's position to calculate the center
                rect = member_card.rectangle()
                print(f"Element coordinates: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
                
                center_x = (rect.left + rect.right) // 2
                center_y = (rect.top + rect.bottom) // 2
                
                print(f"Clicking at center point ({center_x}, {center_y})...")
                member_card.set_focus()
                time.sleep(0.5)
                
                # Perform the first click using mouse coordinates
                mouse.click(coords=(center_x, center_y))
                time.sleep(1) # Wait for the UI to react
                print("✅ Clicked on member card")
                
                # --- VERIFICATION LOGIC ---
                print("\n📝 Checking for member card details...")
                
                all_elements = win.descendants()
                
                # First, gather all relevant text from the screen
                found_texts = []
                keywords_to_find = ["Loyalty Program", "Registered"]
                for element in all_elements:
                    try:
                        text = element.window_text().strip()
                        if any(keyword in text for keyword in keywords_to_find):
                            found_texts.append(text)
                    except:
                        continue
                
                # Now, process the collected texts to identify the label and status
                loyalty_program_label = None
                loyalty_status = None

                # Using set() removes any duplicate text elements found
                for text in set(found_texts):
                    if "Loyalty Program" in text:
                        loyalty_program_label = text
                    if "Registered" in text:
                        loyalty_status = text
                
                # Final validation and structured output
                if loyalty_program_label and loyalty_status:
                    print("\n✅ Member card details validation successful!")
                    print(f"  • Program Info: {loyalty_program_label}")
                    print(f"  • Status: {loyalty_status}")

                    # --- SECOND CLICK LOGIC ---
                    print("\n📝 Clicking the member card again...")
                    mouse.click(coords=(center_x, center_y))
                    time.sleep(1) # Wait for UI to update
                    print("✅ Second click on member card complete.")
                    
                    return True
                else:
                    print("\n❌ Failed to validate member card details after clicking.")
                    if not loyalty_program_label:
                        print("  - Could not find the 'Loyalty Program' label.")
                    if not loyalty_status:
                         print("  - Could not find the 'Registered' status.")
                    return False
                    
            except Exception as e:
                print(f"❌ Error during click or validation: {e}")
                return False
        else:
            print("\n❌ Could not find member card element")
            return False
            
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    print("🔍 Starting member card registration check...")
    click_member_card_and_validate()

if __name__ == "__main__":
    main()

