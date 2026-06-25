import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError
import subprocess
import os


sco_path = r"BAUSCOAutomation\\SCOApplicationLaunch\\Start.bat"
MultiSimulator_Path = r"BAUSCOAutomation\\EFT Simulator\\multi\\MultiSimulator.exe"

#Launch application initially and wait for 60 seconds for SCO to launch
def launch_sco(sco_path):
    subprocess.Popen(sco_path, shell=True)
    print("SCO application launched...")
    print("Waiting for SCO UI to launch... (60 seconds)")
    time.sleep(60)

#Insitailize SCO window with below method to use this everytime we need to use SCO window
def Initialize_Window(title):
    app = Application(backend="uia").connect(title=title)
    window = app.window(title=title)
    return window

#Launch multisimulator
def MultiSimulator(path):
    subprocess.Popen(path, shell=True)
    time.sleep(20)

#Handling Username & Password Screen in single method
def UserName_Screen(window, Mode):
    window.set_focus()
    try:

        if not Mode == "Assist Mode":
            login = window.child_window(auto_id="StoreLogin")
        else:
            login = window.child_window(auto_id="StoreLoginButton", control_type="Button")
        assert login.exists(), "Store Login button not found"
        assert login.is_enabled(), "Store Login button not enabled"
        login.click()
        print("Clicked Store Login button")

        input_box = window.child_window(auto_id="InputTextBox", control_type="Edit")
        assert input_box.exists(timeout=5), "Username input box not found"
        input_box.set_focus()
        input_box.type_keys("scoatt5")
        print("Entered username")

        enter_button = window.child_window(auto_id="EnterButton", control_type="Button")
        assert enter_button.exists(), "Enter button not found"
        enter_button.click()
        print("Clicked Enter after username")

        input_box = window.child_window(auto_id="InputTextBox", control_type="Edit")
        assert input_box.exists(timeout=5), "Password input box not found"
        input_box.set_focus()
        input_box.type_keys("abcd1234")
        print("Entered password")
        
        enter_button = window.child_window(auto_id="EnterButton", control_type="Button")
        assert enter_button.exists(), "Enter button not found"
        enter_button.click()
        print("Clicked Enter after password")

        return "Successfully logged in"
    
    except Exception as e:
        return str(e)

#To Resolve any assitance needed prompts
def Assistance_Needed(window):

    assist_btn = window.child_window(auto_id="AssistanceButton", control_type="Button")
    assert assist_btn.exists(), "Assistance button not found"
    assist_btn.click()

    UserName_Screen(window, "Assist Mode")

    #This can be commented if we are not using any function in assist mode
    return_btn = window.child_window(auto_id="StoreButton8", control_type="Button")
    assert return_btn.exists(), "Return to Shopping Mode button not found"
    return_btn.click()

# Do you wish to continue prompt
def Do_You_Wish_To_Continue(window):

    window.set_focus()
    continue_prompt_text = window.child_window(title="Would you like to continue with your purchase?", auto_id="Instructions", control_type="Text")
    if continue_prompt_text.exists(timeout=1):
        print("Detected 'Would you like to continue?' prompt by its unique text.")
        continue_prompt_yes_button = window.child_window(auto_id="Yes_Button", control_type="Button")
        continue_prompt_yes_button.wait('ready', timeout=3)
        continue_prompt_yes_button.click_input()
        continue_prompt_yes_button.wait_not('visible', timeout=5)
        print("Successfully clicked Yes and prompt disappeared.")

#Click start scanning button
def Start_Scanning(window):

    window.set_focus()
    start_scan = window.child_window(auto_id="StartScanButton", control_type="Button")
    assert start_scan.exists(), "Start Scanning button not found"
    start_scan.click_input()

#Adding an article using scanner simulator
def Scan_Article(window, EAN):

    window.set_focus()
    symbology_combo = window.child_window(title="Symbology:", auto_id="1003", control_type="ComboBox")
    symbology_combo.select("Code 128")
    
    tag_data = window.child_window(title="Tag Data:", auto_id="1001", control_type="Edit")
    tag_data.set_text(EAN)  # Assuming this is an age-restricted item
    print("Entered barcode data.")
    
    scan_button = window.child_window(title="Scan", auto_id="1001", control_type="Button")
    scan_button.click()
    print("Clicked Scan button in emulator.")

#Aknowledge age restriction prompt
def Age_Restriction_Aknowledge(window):

    window.set_focus()
    ok_button = window.child_window(auto_id="OK_Button", control_type="Button")
    if ok_button.exists(timeout=1):
        print("Detected a generic 'OK' prompt.")
        try:
            ok_button.wait('ready', timeout=3)
            ok_button.click_input()
            ok_button.wait_not('visible', timeout=5)
            print("Clicked 'OK' button.")
        except Exception as e:
            print(f"Error clicking generic 'OK' button: {e}")

#Proceed to payment screen
def Payment_Screen(window):

    window.set_focus()
    pay_button = window.child_window(auto_id="PayButton", control_type="Button")
    assert pay_button.exists(timeout=5), "'Pay Now' button not found"
    pay_button.click_input()

#Enter DOB and click on enter on age restriction entry
def Age_Entry(window, DOB):

    window.set_focus()
    dob_input = window.child_window(auto_id="InputTextBox", control_type="Edit")
    dob_input.wait('ready', timeout=5)
    dob_input.type_keys(DOB, with_spaces=False)
    enter_button = window.child_window(auto_id="StoreButton1", control_type="Button")
    enter_button.wait('ready', timeout=5)
    enter_button.click_input()

#Test Case execution starts from here

#1. Launch the SCO as the first step
#launch_sco(sco_path)

#2. Initialize SCO & Scanner window to do actions
SCO_Window = Initialize_Window("NCR NEXTGENUI")
Scanner_Window = Initialize_Window("Scanner\\Emulator_Scanner")

#10. Launch multisimulator
#MultiSimulator(MultiSimulator_Path)

#3. Login with valid credentials
UserName_Screen(SCO_Window, "Login Mode")
time.sleep(20)

#4. Login to Assistance and return back
#Assistance_Needed(SCO_Window)
time.sleep(20)

#5. Add an age restriction article on no sale mode after clicking Start Scanning
Start_Scanning(SCO_Window)
Scan_Article(Scanner_Window, "9310797286794")

#6. Click on ok button after adding age restriction article
Age_Restriction_Aknowledge(SCO_Window)

#7.  Click on Pay Now button
Payment_Screen(SCO_Window)

#8. Resolve age restriction intervention
UserName_Screen(SCO_Window, "Intervention Mode")

#9. Handle happy scenario for age restriction
Age_Entry(SCO_Window, "01012000")