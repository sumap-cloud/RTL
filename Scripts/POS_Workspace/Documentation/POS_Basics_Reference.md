# POS Basics Documentation

## Overview
This document provides basic information about the Point of Sale (POS) system components, functionality, and usage patterns. It serves as a reference guide for test automation development and scenario creation.

## 1. Core POS Components

### Login and Authentication
```python
from Components.Common_components.pos_login import mainlogic

# Standard login with credentials
mainlogic("ATcash5", "abcd1234")
```

Different user types:
- **ATcash1-5**: Standard cashiers with varying permissions
- **ATsupervisor**: Supervisor with override capabilities
- **ATadmin**: Administrator with full system access

#### Invalid Login Testing and Error Validation
```python
from Components.Common_components.ocr_login_errormessage import attempt_login, find_visible_error, dismiss_screensaver_and_navigate_to_login

# OCR-based error detection for invalid credentials
possible_errors = [
    "Please enter user name",
    "Please Enter password", 
    "Invalid user or password, please follow company procedure to manage your user profile"
]

# Test invalid login with error detection
login_success = attempt_login(username="wronguser", password="abcd1234", error_list=possible_errors)

# Dismiss screensaver and prepare login form
dismiss_screensaver_and_navigate_to_login(window_object)

# Validate specific error messages using OCR
error_found = find_visible_error("R10PosClient", ["Invalid user or password, please follow company procedure to manage your user profile."])
```

**Login Security Protocols:**
- Invalid credentials trigger specific error messages
- OCR validation ensures compliance with security procedures
- Screensaver handling required for login form access
- System recovery validation after invalid attempts

### Navigation
```python
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate

# Navigate to specific menu path
toggle_menu_navigate(["Returns", "Transaction Based", "APPROVAL"])
```

### Window/App Connection
```python
from pywinauto import Application

# Connect to POS application window
app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=20)
win = app.window(title_re=".*R10PosClient.*")
win.set_focus()
```

## 2. Sale Mode Operations

### Item Addition Methods

#### Barcode/EAN Entry
```python
from Components.Salemode.Keyin_item import Kayin_EAN_POS

# Add items by barcode
Kayin_EAN_POS(eans_to_add=["8720400000210"])
```

#### GS1 Barcode Processing
```python
from Components.Salemode.gs1_manual_entry import automate_gs1_screen

# Handle GS1 barcode with embedded data
Kayin_EAN_POS(eans_to_add=["0109300675014830"])
automate_gs1_screen("25.00")  # Price override if needed
```

#### Item Search
```python
from Components.Salemode.item_search import perform_item_search

# Search for item by name
perform_item_search("item name", "exact item to select")
```

#### PLU Menu Navigation
```python
from Components.Salemode.PLUMenu import click_plu_path

# Navigate PLU categories
click_plu_path(["Category", "Subcategory", "Item"])
```

#### Department Sale
```python
from Components.Salemode.department_sale import department_sale
from Components.Salemode.department_amount import enter_item_price

# Department sale with amount
department_sale(department_name="BAKEHOUSE")
enter_item_price("20.00")
```

### Basket Management
```python
from Components.Salemode.basket_with_itemdetails import get_basket_info

# Verify basket contents
get_basket_info()
```

## 3. Payment Processing

### Tender Selection
```python
from Components.Tenders.Cash_tender_payment import process_tenders

# Process payment
process_tenders(app, tender_to_select="Cash")
```

Available tender types:
- Cash
- Card
- Gift Card
- Voucher
- Mixed Payment

### Cash Drawer Handling
```python
from Components.Common_components.cashDrawer import cashdrawer_move_and_close

# Close cash drawer
cashdrawer_move_and_close(status_to_set="close")
```

## 4. Transaction Management

### Save/Recall Transactions
```python
from Components.Recall.recall_transction import recall_transaction
from Components.Recall.transaction_selction_recall import select_recall_transaction

# Recall process
toggle_menu_navigate(["Recall Transaction"])
recall_transaction()
select_recall_transaction()
```

### Return Processing

#### Transaction Based Return
```python
from Components.Returns.refund_tbr import handle_refund_screen
from Components.Returns.tbr_load_transaction import handle_transaction_return_screen

# Search for transaction
handle_transaction_return_screen(action="click_search")
# Process refund
handle_refund_screen(expected_tender='Cash')
```

#### Department Return
```python
from Scripts.POS_Workspace.Components.Returns.departmentrefund_tbr import select_refund_department

# Department refund
select_refund_department(department_name="BAKEHOUSE")
```

#### Non-Receipted Return (NRR)
```python
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate
from Components.Returns.departmentrefund_nrr import return_item_by_department

# Navigate to NRR flow
toggle_menu_navigate(["Returns", "Non Receipted", "APPROVAL"])

# Process department return with threshold amount
return_item_by_department(department_name="BAKEHOUSE", 
                         reason_code="Damaged / Faulty", 
                         price="750.00")

# Handle approval based on threshold
from Components.Common_components.Approvalrequired import handle_approval_popup
handle_approval_popup(approval_required=True, first_username="atmgr5", first_password="abcd1234")
```

## 5. Regulatory Functions

### Age Restriction Handling
```python
from Components.legislation.ageRestriction_window import handle_age_restriction

# Handle age verification popup
handle_age_restriction()
```

### Price Override Controls
```python
# Price override with threshold control
from Components.Salemode.gs1_manual_entry import automate_gs1_screen

# Will trigger limit enforcement if exceeding threshold
automate_gs1_screen("25.00")  
```

### Approval Workflows
```python
from Components.Common_components.Approvalrequired import handle_approval_popup

# Handle supervisor approval prompt
handle_approval_popup()
```

## 6. Customer Management

### Loyalty Handling
```python
from Components.Loyalty.Loyalty_popup_validation import handle_customer_popup

# Handle loyalty popup (optionally enter customer number)
handle_customer_popup(app, customer_number=None)
```

## 7. Common Functions

### Popup Handling
```python
from Components.Common_components.handle_any_popup_POS import handle_Any_popup

# Handle general popups (receipt, notifications, etc.)
handle_Any_popup()
```

### Intervention Handling
```python
from Components.Recall.recall_intervention_List import solve_intervention

# Resolve transaction interventions
solve_intervention()
```

## 8. POS Screen Flow Patterns

### Standard Sale Flow
1. Item Addition → Basket Review
2. OK Button → Loyalty Screen
3. Cancel/Enter Customer → Tender Selection
4. Select Tender → Receipt Handling
5. Handle Receipt → Cash Drawer

### Return Flow
1. Return Navigation → Search Transaction
2. Select Item → Enter Return Reason
3. Confirm Return → Select Refund Method
4. Process Refund → Receipt Handling
5. Handle Receipt → Cash Drawer

## Best Practices for Test Automation

1. **Consistent Wait Times**
   - Use appropriate waits between critical operations
   - Typical wait: `time.sleep(2)` after navigation

2. **Error Handling**
   - Check return values from component functions
   - Handle unexpected popups with handle_Any_popup()

3. **Validation Points**
   - Verify basket after item additions with get_basket_info()
   - Confirm screen transitions with explicit checks

4. **Cash Drawer Management**
   - Always close drawer after transactions
   - Verify drawer state when appropriate

5. **Receipt Handling**
   - Use handle_Any_popup() for receipt prompts
   - Document receipt validation points

---

Note: This document covers basic functionality. See specific scenario documentation for detailed workflows.

### ABB Robot Integration
```python
from Components.BotActions.AbbAction import Trigger_Action

# Physical robot actions for cash drawer operations
robot_response = Trigger_Action(",Close_Drawer")

# Validate robot response
if "ERROR" in robot_response:
    print(f"❌ ABB robot action failed: {robot_response}")
    return False
else:
    print(f"✅ ABB robot drawer closure successful: {robot_response}")
```

**Robot Configuration:**
- **Robot IP**: 10.81.3.113
- **Port**: 5000
- **Available Actions**: 60+ predefined commands
- **Primary Actions**: `,Close_Drawer`, `,ups`, and others
- **Response Validation**: Robot returns confirmation or error message

**Physical vs. Software Simulation:**
```python
# Standard software simulation (existing tests)
from Components.Common_components.cashDrawer import cashdrawer_move_and_close
cashdrawer_move_and_close(status_to_set="close")

# ABB Robot physical integration (BOT tests)
from Components.BotActions.AbbAction import Trigger_Action
Trigger_Action(",Close_Drawer")
```

**Integration Points:**
- After cash payment completion
- Physical drawer operations
- Transaction finalization
- Hardware validation requirements

**Robot Test Requirements:**
- ABB robot connectivity verified
- Socket connection to 10.81.3.113:5000
- Command response validation
- Physical hardware operational status
