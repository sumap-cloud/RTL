from pywinauto.application import Application

# Define the path to your application's executable
# The 'r' before the string is important for Windows paths
app_path = r"C:\Retalix\StoreServices\POSClient\Retalix.Client.POS.Shell.exe"

# Connect to the application using its stable path
# This will work every time, regardless of the process ID
app = Application(backend="uia").connect(path=app_path)

# The rest of your code works perfectly with this change
main_window = app.window(auto_id="GraphicCustomerDisplayID")
main_window.set_focus()
main_window.print_control_identifiers()