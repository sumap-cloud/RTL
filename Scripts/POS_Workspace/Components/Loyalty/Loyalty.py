# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: loyalty_base
# @Purpose: Provides basic loyalty functionality and popup handling
# @Dependencies: pywinauto.application.Application
# @Input_Params: None
# @Return_Values: Various based on functions (app connection, popup info)
# @Used_By_Tests: TC003_loyalty_basic_scenario_ai, TC005_loyalty_details_scenario
# @Known_Limitations: Basic implementation with minimal error handling
# ============================================

from pywinauto import Application 
import time

def connect_to_app():
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
    win = app.window(title_re=".*R10PosClient.*")
    #win.set_focus()
    return app, win



def popuphandle(win):
    # Get the top-most window
    popup = win.top_window()
    print("📝 Popup Window Title:", popup.window_text())

    # Print all text controls (messages, labels, etc.)
    texts = popup.descendants(control_type="Text")
    print("📝 Texts found in popup:")
    for txt in texts:
        print(f"- {txt.window_text()}")

    # Print and click the "Yes" button if found
    buttons = popup.descendants(control_type="Button")
    print("🔘 Buttons found in popup:")
    yes_clicked = False
    for btn in buttons:
        print(f"- {btn.window_text()}")
        if btn.window_text().strip().lower() == "cancel":
            btn.click_input()
            print("✅ Clicked 'Cancel' button.")
            yes_clicked = True
            break
    if not yes_clicked:
        print("❌ 'calcel' button not found.")
    return True

def main():
    app, win = connect_to_app()
    popuphandle(app)

if __name__ == "__main__":
   main()