"""
Simple test to verify pytest-html with screenshots is working
"""
import pytest
import pytest_html
from PIL import ImageGrab
from pathlib import Path
from datetime import datetime

def capture_test_screenshot(step_name, extra):
    """Test screenshot capture"""
    try:
        screenshot_dir = Path(__file__).parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_{step_name.replace(' ', '_')}_{timestamp}.png"
        filepath = screenshot_dir / filename
        
        screenshot = ImageGrab.grab()
        screenshot.save(str(filepath))
        
        # Read image as binary and encode to base64 string
        # pytest-html expects base64 encoded STRING, not bytes
        with open(str(filepath), 'rb') as f:
            image_data = f.read()
        
        import base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        
        # Use the proper pytest_html.extras.png() method with base64 string
        extra.append(pytest_html.extras.png(base64_string, name=step_name))
        
        print(f"✅ Screenshot captured: {filename}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

@pytest.mark.smoke
def test_screenshot_functionality(extra):
    """Test to verify screenshot functionality works"""
    print("\n=== Testing Screenshot Functionality ===")
    
    print("\n📸 Capturing Test Screenshot 1...")
    capture_test_screenshot("Test Screenshot 1", extra)
    
    print("\n📸 Capturing Test Screenshot 2...")
    capture_test_screenshot("Test Screenshot 2", extra)
    
    print("\n✅ Test completed - Check the HTML report for screenshots!")
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--html=test_report.html", "--self-contained-html"])
