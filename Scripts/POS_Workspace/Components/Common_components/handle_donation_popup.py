from pywinauto import Application
import time

def connect_to_app():
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
    win = app.window(title_re=".*R10PosClient.*")
    return app, win


def handle_donation_popup(app):
    # Find the top-most popup window
    popup = app.top_window()
    print("📝 Donation Popup Window Title:", popup.window_text())
    # Print all text controls
    texts = popup.descendants(control_type="Text")
    print("📝 Texts found in donation popup:")
    for txt in texts:
        print(f"- {txt.window_text()}")
    # Print all buttons and click 'Skip' if found
    buttons = popup.descendants(control_type="Button")
    print("🔘 Buttons found in donation popup:")
    skip_clicked = False
    for btn in buttons:
        print(f"- {btn.window_text()}")
        if btn.window_text().strip().lower() == "skip":
            btn.click_input()
            print("✅ Clicked 'Skip' button.")
            skip_clicked = True
            break
    if not skip_clicked:
        print("❌ 'Skip' button not found in donation popup.")
    return True


def main():
    app, win = connect_to_app()
    handle_donation_popup(app)

if __name__ == "__main__":
    main()
