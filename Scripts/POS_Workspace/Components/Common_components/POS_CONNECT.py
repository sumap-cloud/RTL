from pywinauto import Application

app_title = ".*R10PosClient.*"  # Regex for the application title

def connect_to_pos_app(app_title):
    """
    Connects to the POS application using pywinauto.

    Args:
        app_title (str): The regex pattern for the application title.

    Returns:
        Application: The connected application object.
    """
    try:
        app = Application(backend="uia").connect(title_re=app_title, timeout=10)
        win = app.window(title_re=app_title)
        print(f"Connected to application: {app_title}")
        return win
    except Exception as e:
        print(f"Failed to connect to the application '{app_title}': {e}")
        return None