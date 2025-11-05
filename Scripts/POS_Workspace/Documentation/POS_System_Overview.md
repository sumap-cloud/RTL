# POS System Technical Documentation

## System Overview
The R10PosClient is a comprehensive Point of Sale system with integrated loyalty, funds management, and compliance features.

### Core Architecture
- **Application Name:** R10PosClient
- **UI Framework:** Windows-based (using pywinauto for automation)
- **Testing Framework:** Python-based automated testing
- **Data Storage:** CSV for test scenarios, system databases for transactions

## Key Modules and Features

### 1. Sale Mode
```plaintext
Login -> Item Entry -> Loyalty -> Payment -> Receipt
```
- Multiple item entry methods:
  - EAN scanning (standard barcodes)
  - GS1 barcode processing (embedded data)
  - PLU menu navigation
  - Item search
  - Department sale
- Basket management
- Price management:
  - Base price lookup
  - Price override controls
  - Threshold enforcement (>90% change prevention)
  - Authorization requirements
- Quantity modifications

### 2. Loyalty System
- Member identification
- Points calculation
- Discount application
- Member benefits
- Card validation
- Customer profiles

### 3. Payment Processing
- Multiple tender types
- Cash drawer management
- Balance calculation
- Receipt generation
- Change calculation
- Transaction persistence

### 4. Session Management and Mode Operations
- **Mode Support:**
  - Regular mode (standard operations)
  - Training mode (practice/testing operations)
  
- **Login and Authentication:**
  - User credential validation
  - Session establishment and management
  - Invalid login error handling with OCR validation
  - Security compliance with specific error messaging
  - Screensaver integration and dismissal protocols
  
- **Error Validation Framework:**
  - OCR-based error message detection (Tesseract-OCR)
  - Compliance validation for security error messages
  - Expected error: "Invalid user or password, please follow company procedure to manage your user profile."
  - Login form accessibility after screensaver dismissal
  - System recovery validation after failed login attempts

- **Session Termination:**
  - Logoff procedures for different modes
  - Clean session termination and state management
  - Return to login screen validation
  - System stabilization timing (2-second wait after logoff)
  - Training mode (safe practice environment)
  - Mode transition capabilities
- **Session Control:**
  - User authentication and role management
  - Session state preservation
  - Transaction save/recall functionality
  - Training mode specific operations
- **Logoff Procedures:**
  - Mode-aware confirmation buttons
  - Manager approval requirements
  - Session cleanup and validation

### 5. Training Mode Features
- **Safe Environment:** Practice without affecting live data
- **Full Functionality:** All POS operations available
- **Mode Transition:** Complete logoff/login cycle required
- **Access Control:** Manager credentials required (atmgr5)
- **Specific Handling:** 
  - Training mode logoff uses "Log Off" button
  - Regular mode logoff uses "Yes" button
  - Manager approval for session termination

### 6. Transaction Management
- **Save Transaction:** Preserve transaction state for later completion
- **Transaction Recall:** Restore previously saved transactions  
- **State Persistence:** Maintain transaction data across sessions
- **Mode Context:** Available in both regular and training modes
- **Processing Times:** 2-second wait for save completion

### 7. Compliance Features
- Age restriction management
  - 18+ verification
  - 21+ verification
- Price manipulation controls
  - Override threshold enforcement (>90% prevention)
  - Authorization level requirements
  - Audit trail for price adjustments
  - Documentation on receipts
- GS1 barcode compliance
  - Application Identifier (AI) processing
  - Data extraction and validation
  - Embedded price/weight/date handling
  - Format verification
- Transaction approvals
- Return authorizations
- Audit trail maintenance

### 8. Funds Management
- Cash drawer controls
- Paid out processing
- Denomination tracking
- Balance reconciliation
- Cash summary reporting

### 9. Robot Integration System
- **ABB Robot Integration:**
  - Physical cash drawer operations
  - Socket-based communication (10.81.3.113:5000)
  - 60+ predefined robot actions
  - Command validation and response handling
  - Hardware-software integration testing

- **Robot Commands:**
  - `,Close_Drawer` - Physical drawer closure
  - `,ups` - Robot movement actions
  - Additional commands for various POS scenarios

- **Integration Architecture:**
  ```plaintext
  POS Application -> Socket Communication -> ABB Robot -> Physical Action
  ```

- **Test Types:**
  - **Standard Tests:** Software simulation via `cashdrawer_move_and_close()`
  - **BOT Tests:** Physical robot integration via `Trigger_Action()`
  - **Hybrid Tests:** Combined software and hardware validation

## Test Architecture

### Data-Driven Framework
```python
test_scenarios.csv:
- scenario_id      # Unique test identifier
- scenario_name    # Test description
- username         # Login credentials
- password         # Authentication
- ean_codes        # Test items
- loyalty_card    # Member number
- payment_method  # Tender type
- status          # Execution status
- execution_time  # Performance metrics
- remarks         # Test notes
```

### Common Components
1. **Authentication:**
   - Login management
   - Role-based access
   - Session handling

2. **UI Interaction:**
   - Window navigation
   - Control identification
   - State management
   - Popup handling

3. **Transaction Flow:**
   - Item addition
   - Basket validation
   - Payment processing
   - Receipt generation

4. **Error Handling:**
   - Exception management
   - Cleanup procedures
   - State recovery
   - Logging

## Test Scenarios

### 1. Basic Sales Flow
- Standard item sale
- GS1 barcode processing
- Price override management
- Loyalty integration
- Payment processing
- Receipt validation

### 2. Age Restricted Sales
- Age verification
- Item restrictions
- Compliance checks
- Documentation

### 3. Returns and Refunds
- Transaction lookup
- Item verification
- Approval workflow
- Refund processing
- Non-Receipted Returns
  - Amount threshold validation ($500-$1000, $1000.01-$9999.99, ≥$10,000)
  - Department-based return processing
  - Tiered approval requirements
  - Documentation and compliance controls

### 4. Loyalty Features
- Member identification
- Points calculation
- Benefit application
- Profile management

### 5. Funds Management
- Cash handling
- Denomination tracking
- Drawer management
- Financial controls

### 6. GS1 and Price Control Workflows
- GS1-128 barcode scanning
- Embedded data extraction
- Price override threshold testing
- Regulatory limit enforcement
- Documentation compliance

## Common Functions

### UI Navigation
```python
def validate_step(condition: bool, message: str, screenshot: bool = False) -> bool:
    """Standard step validation with logging"""

def handle_Any_popup():
    """Generic popup management"""

def perform_login():
    """Authentication and window initialization"""
```

### Transaction Management
```python
def add_items_to_basket():
    """Item addition and verification"""

def process_loyalty_card():
    """Member processing and validation"""

def complete_payment():
    """Payment workflow and finalization"""
```

## Error Prevention

### Key Validation Points
1. **Data Integrity:**
   - Input validation
   - State verification
   - Data consistency

2. **UI State:**
   - Window presence
   - Control accessibility
   - Response validation

3. **Timing Requirements:**
   - Item addition: 3-second wait for basket reflection
   - Mode transitions: 2-second stabilization wait
   - Save operations: 2-second processing wait
   - System response validation

4. **Mode-Specific Operations:**
   - Training mode confirmation handling ("Log Off" button)
   - Regular mode confirmation handling ("Yes" button)  
   - Manager approval prompt processing
   - Session state validation

5. **Business Rules:**
   - Age restrictions
   - Price override thresholds
   - GS1 barcode format validation
   - Authorization levels
   - Transaction limits
   - Non-receipted return thresholds
   - Approval routing by amount
   - Training mode access requirements

### Recovery Procedures
```python
def cleanup_on_failure():
    """System state restoration"""
    - Close popups
    - Secure cash drawer
    - Reset transaction state
```

## Best Practices

### Test Implementation
1. Use data-driven approach for test scenarios
2. Implement proper cleanup procedures
3. Validate each step with clear messaging
4. Maintain test independence
5. Handle all possible UI states

### Error Handling
1. Implement comprehensive exception handling
2. Provide clear error messages
3. Ensure proper cleanup on failures
4. Maintain system state consistency
5. Log all significant events

### Documentation
1. Maintain clear scenario descriptions
2. Document all test configurations
3. Keep execution logs
4. Track test results
5. Document known issues and workarounds

## Future Enhancements
1. Implement screenshot capability for failures
2. Add more detailed logging
3. Enhance error recovery procedures
4. Expand test coverage
5. Implement performance metrics
