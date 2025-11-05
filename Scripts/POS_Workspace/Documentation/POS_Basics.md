# POS System Documentation

## Basic POS Modes and Flows

### 1. Sale Mode
The primary mode for processing sales transactions. There are four main ways to add items:

#### Item Addition Methods
1. **Key-in EAN**
   - Manual entry of item EAN/barcode
   - Used when barcode can't be scanned
   - Requires exact EAN number

2. **PLU Menu**
   - Pre-configured menu for frequently sold items
   - Items organized in categories
   - Quick selection without needing codes/barcodes

3. **Department Sale**
   - For items sold by department (e.g., BAKEHOUSE)
   - Usually requires amount entry
   - May require approval based on amount
   - Common in fresh goods/bulk items

4. **Scan** (Hardware dependent)
   - Physical barcode scanning
   - Currently not in automation scope
   - Most common in retail operations

### 2. Basket Validation
- **Mandatory Step** after adding any items
- Checks required for ALL sale types:
  - Article details verification
  - Balance due confirmation
  - Item quantities and prices
  - Total amount validation

### 3. Loyalty Mode
Handles customer loyalty processing:

#### Two Paths:
1. **With Customer Card**
   - Enter customer card number
   - Validate card details
   - Apply any eligible promotions
   
2. **Without Customer Card**
   - Click Cancel to skip
   - Proceed to tender mode directly

#### Special Handling:
- Multiple promotion popups possible
- All popups must be handled
- Validation of loyalty card addition

### 4. Tender Mode
Final stage of transaction processing:

#### Features:
- Multiple tender types available
- Default: Cash tender
- Special tender handling based on scenario
- Loyalty validation if card was added

#### Common Validations:
- Promotion popup handling
- Balance verification
- Receipt generation
- Cash drawer operations

## Return Flows

### Transaction Based Return (TBR)
1. **Prerequisites**
   - Original transaction reference
   - Approval requirements
   - Valid return reason

2. **Special Considerations**
   - Department returns must match original sale
   - Amount validation
   - Manager approval for amounts > $500

## Funds Management

### Available Operations
1. **Cash Operations**
   - Paid In
   - Paid Out
   - Pick Up at POS
   
2. **Tender Management**
   - Tender Correction
   - Tender Loan
   - POS Declaration

## Mode Management

### Training Mode vs Regular Mode
Training mode provides a safe environment for practice and testing without affecting live data.

#### Mode Transition Process
1. **Regular to Training Mode**
   - Requires complete logoff from regular mode
   - Re-login with manager credentials (atmgr5)
   - System stabilization time required (2-second wait)
   - Training mode session establishment

2. **Training Mode Features**
   - Transaction save functionality available
   - All regular POS operations supported
   - Safe environment for testing scenarios
   - Manager approval required for session termination

#### Training Mode Logoff Specifics
- **Confirmation Button**: "Log Off" (vs "Yes" in regular mode)
- **Approval Required**: Manager credentials for session termination
- **System Processing**: Allow time for proper cleanup

## Transaction Management

### Save Transaction Functionality
Available in both regular and training modes:

#### Process Flow
1. **Navigate to Save Transaction** via toggle menu
2. **Confirm Save Operation** - system processes request
3. **Transaction Persistence** - state preserved for later recall
4. **System Processing Time** - allow 2-second wait for completion

#### Timing Considerations
- **Item Addition**: 3-second wait for basket reflection
- **Save Processing**: 2-second wait for completion confirmation
- **Mode Changes**: 2-second stabilization after transitions

## Common Error Prevention
1. **Navigation Validation**
   - Confirm each menu change
   - Proper screen transitions
   - Handle unexpected popups
   - Allow sufficient processing time

2. **Transaction Validation**
   - Basket details with timing waits
   - Item reflection validation (3-second waits)
   - Loyalty processing
   - Tender completion
   - Receipt handling

3. **Mode Management**
   - Proper mode transition procedures
   - Training mode specific confirmations
   - Manager approval handling
   - Session cleanup verification

4. **Hardware Management**
   - Cash drawer status
   - Receipt printer status
   - Scanner functionality (when applicable)

## Test Case Structure
For each test scenario, follow this pattern:
1. **Initial Setup**
   - Login verification
   - System state validation

2. **Transaction Flow**
   - Clear step documentation
   - Expected outcomes
   - Error handling

3. **Validation Points**
   - Critical checkpoints
   - Expected popups
   - Required approvals

4. **Cleanup**
   - Cash drawer management
   - Receipt handling
   - System state restoration

---
Note: This documentation will be updated as new scenarios are developed and tested.
