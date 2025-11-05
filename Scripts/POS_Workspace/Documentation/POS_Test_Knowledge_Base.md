# POS Test Knowledge Base

## Overview
This document serves as a centralized knowledge base for all POS test scenarios, documenting key functionality, components, test parameters, and variations. It provides both documentation and a foundation for generating new test cases.

## How To Use This Knowledge Base

### 1. For Documentation Updates
Use this format to document new test cases:

```
POS-Doc-Update:
- TestCase: [filename.py]
- PrimaryFeatures: [main features being tested]
- Components: [key component files used]
- BusinessRules: [business rules validated]
- ValidationPoints: [key validation criteria]
- SpecialConsiderations: [user roles, permissions, special requirements]
```

### 2. For Test Generation
Use this format to generate new test cases:

```
POS-Test-Generate:
- FeatureToTest: [feature name]
- TestScenario: [brief description of what to test]
- RelatedExistingTests: [list any related existing tests to reference]
- Variations: [what variations from existing tests should be applied]
- ValidationRequirements: [what must be validated]
- UserRole: [which user role/permissions needed]
```

## Legislation Test Scenarios

### 1. Save Transaction and Training Mode Logoff (TC011_save_transaction_logoff_scenario.py)
- **Primary Features**: 
  * Save Transaction functionality in training mode
  * Session management with mode transitions (regular to training)
  * Training mode specific logoff procedures
  * Transaction persistence and basket validation with timing

- **Key Components**:
  * Components.Salemode.Keyin_item (Kayin_EAN_POS)
  * Components.Salemode.basket_with_itemdetails (get_basket_info)
  * Components.Common_components.toggle_menu_navigation (toggle_menu_navigate)
  * Components.Common_components.handle_any_popup_POS (handle_Any_popup)
  * Components.Common_components.Logoff (logoff_user with training mode support)
  * Components.Common_components.regular_to_traning_mode (enter_training_mode)

### 2. Invalid Login Error Validation (TC012_invalid_login_error_validation.py)
- **Primary Features**: 
  * Login Error Validation and Security Protocols
  * Session Management with OCR-based Error Detection
  * Error Message Verification and Compliance Validation
  * Screensaver Handling and Login Form Accessibility

- **Key Components**:
  * Components.Common_components.pos_login (mainlogic) - Regular mode login functionality
  * Components.Common_components.Logoff (logoff_user) - Session logoff functionality
  * Components.Common_components.ocr_login_errormessage:
    - attempt_login: Controlled login attempts with error detection
    - find_visible_error: OCR-based error message detection
    - dismiss_screensaver_and_navigate_to_login: UI preparation and navigation

- **Business Rules**:
  * Invalid credentials must display specific error messages
  * Screensaver dismissal required for login access
  * Error message compliance: "Invalid user or password, please follow company procedure to manage your user profile."
  * System must recover properly after invalid login attempts

- **Validation Points**:
  * Error message accuracy and OCR text detection
  * Invalid username/password handling protocols
  * System security validation and compliance
  * Login form accessibility after screensaver dismissal
  * Fallback validation with valid credentials for system recovery

- **User Roles & Test Data**:
  * Invalid test users: "wronguser" (for error validation)
  * Valid users: "ATcash1", "Atmgr5" (for initial setup and fallback validation)
  * Test passwords: "abcd1234" (standard test password format)

- **Special Configuration**:
  * OCR engine configuration (Tesseract-OCR)
  * Error message text validation protocols
  * Login security compliance requirements
  * Timing requirements: 1-second wait after login attempts, 2-second stabilization after logoff

- **Dependencies**:
  * ocr_login_errormessage.py: OCR error detection and login handling
  * Logoff.py: Session management and cleanup
  * Tesseract-OCR engine: Text extraction from error dialogs
  * pywinauto: UI automation and window management

- **Test Flow Summary**:
  1. Initial session preparation with valid login (ATcash1)
  2. Clean logoff and return to login screen
  3. Screensaver dismissal and login form preparation
  4. Invalid username testing with "wronguser" credentials
  5. Fallback validation with valid credentials (Atmgr5)
  6. Comprehensive validation and test results documentation

- **Test Configuration**:
  * Initial User Role: ATcash1 (Service Cashier - Regular Mode)
  * Training Mode User: atmgr5 (Manager for training mode and approval)
  * Test Items: EAN 9300675079686, EAN 9300675014779
  * Mode Transition: Regular to Training via complete logoff/login cycle
  * Expected Result: Transaction save in training mode, successful training mode logoff

- **Validation Points**:
  * Mode transition success (regular to training)
  * Item addition with basket reflection timing (3-second waits)
  * Real-time basket validation after each item addition
  * Transaction save confirmation in training mode environment
  * Training mode specific logoff popup handling ("Log Off" button)
  * Manager approval prompt processing with atmgr5 credentials

- **Business Rules Tested**:
  * Training mode requires manager credentials for access
  * Transaction save functionality must work in training mode
  * Training mode logoff requires "Log Off" button confirmation (vs "Yes" in regular mode)
  * Basket reflection requires processing time (3-second waits after additions)
  * Mode transitions require system stabilization time (2-second waits)
  * Manager approval required for training mode session termination

- **Timing Requirements**:
  * 3-second wait after each item addition for basket reflection
  * 2-second wait after mode transition for system stabilization
  * 2-second wait after save transaction for processing completion

- **Possible Variations**:
  * Testing save transaction in regular mode vs training mode
  * Different item combinations with varying processing times
  * Failed mode transition scenarios
  * Manager approval denial scenarios
  * Different training mode operations beyond save transaction

### 2. GS1 Barcode and Price Override (TC004_Gs1_scenario.py)
- **Primary Features**: 
  * GS1 barcode scanning with embedded data
  * Price override threshold enforcement
  * Regulatory compliance for price adjustments

- **Key Components**:
  * Components.Salemode.gs1_manual_entry
  * Components.Salemode.Keyin_item
  * Components.Tenders.Cash_tender_payment
  * Components.Common_components.handle_any_popup_POS

- **Test Configuration**:
  * User Role: ATcash5 (needs price override permissions)
  * GS1 Barcode: 0109300675014830
  * Override Price: 25.00 (exceeds 90% threshold)
  * Expected Result: Limit enforcement, fallback to compliant price

- **Validation Points**:
  * GS1 barcode data extraction accuracy
  * Price override threshold detection
  * Limit enforcement prompt display
  * Compliant price application
  * Receipt documentation of adjustment
  * Cash drawer handling with adjusted amount

- **Business Rules Tested**:
  * Price override changes exceeding 90% are blocked
  * Regulatory limit enforcement requires acknowledgment
  * Audit trail must be created for price adjustments
  * Receipt must document original and adjusted prices

- **Possible Variations**:
  * Testing with different GS1 format types (weight, date embedded)
  * Testing with different override percentages (just below threshold)
  * Testing with different user permission levels
  * Testing with multiple GS1 items in same transaction

### 2. Age Restriction Processing (TC002_agerestiction_Scenario.py)
- **Primary Features**: 
  * Age verification for restricted products
  * Save/Recall transaction with age restrictions
  * Multiple verification points

- **Key Components**:
  * Components.legislation.ageRestriction_window
  * Components.Salemode.item_search
  * Components.Recall.recall_transction
  * Components.Recall.recall_intervention_List

- **Test Configuration**:
  * User Role: ATcash5
  * Age-Restricted Item: "Henri Wintermans Cf Creme Cigars 10pk" (18+)
  * Regular Items: "8720400000210" and PLU menu items

- **Validation Points**:
  * Age restriction prompt appears for restricted items
  * Verification persists through transaction save/recall
  * Basket details accuracy with mixed items
  * Intervention handling during recall

- **Business Rules Tested**:
  * Items marked as 18+ require age verification
  * Age verification is required at initial sale and recall
  * Transaction with restricted items can be saved and recalled
  * Interventions must be resolved before proceeding

- **Possible Variations**:
  * Testing with 21+ restricted items
  * Failed verification scenarios
  * Manager override of restrictions
  * Mixed basket with multiple restricted items

### 3. Loyalty Basic Functionality (TC003_loyalty_basic_scenario_ai.py)
- **Primary Features**: 
  * Customer loyalty identification
  * Points calculation and association
  * Member benefits application

- **Key Components**:
  * Components.Loyalty.Loyalty_popup_validation
  * Components.Salemode.Keyin_item
  * Components.Tenders.Cash_tender_payment

- **Test Configuration**:
  * User Role: Standard cashier
  * Customer Number: Valid loyalty account
  * Test Items: Standard inventory items

- **Validation Points**:
  * Loyalty prompt appears after item addition
  * Customer identification works correctly
  * Member information displays properly
  * Points calculation accuracy
  * Transaction association with member account

- **Business Rules Tested**:
  * Loyalty prompt must appear at appropriate point in workflow
  * Valid customer numbers must be accepted
  * Invalid numbers must be rejected
  * Customer data must be displayed securely
  * Transaction must be properly associated with loyalty account

- **Possible Variations**:
  * Testing with invalid loyalty numbers
  * Testing loyalty tier benefits
  * Testing point promotions
  * Testing member-specific pricing

### 4. Customer Tax Details (TC003_customer_tax_details_scenario.py)
- **Primary Features**: 
  * Customer tax information collection
  * Tax document generation
  * Fiscal compliance for business customers

- **Key Components**:
  * Components specific to tax processing
  * Customer information entry
  * Receipt documentation

- **Test Configuration**:
  * User Role: Standard cashier
  * Customer Tax Info: Valid business tax details
  * Transaction: Standard sale items

- **Validation Points**:
  * Tax information entry fields
  * Data validation rules
  * Document generation with tax details
  * Proper storage of tax information

- **Business Rules Tested**:
  * Required tax fields must be validated
  * Tax information must appear on receipts
  * Data format rules must be enforced
  * Fiscal compliance requirements must be met

- **Possible Variations**:
  * Different tax jurisdictions
  * Various business customer types
  * Error handling for invalid tax data
  * Update of existing tax information

### 5. Loyalty Details Functionality (TC005_loyalty_details_scenario.py)
- **Primary Features**: 
  * Advanced loyalty member features
  * Detailed customer information
  * Special promotions and offers

- **Key Components**:
  * Extended loyalty components
  * Profile management
  * Promotion handling

- **Test Configuration**:
  * User Role: Standard cashier
  * Member Level: Various tier levels
  * Transaction: Items with loyalty benefits

- **Validation Points**:
  * Detailed member information display
  * Tier-specific benefits application
  * Promotion eligibility and application
  * Points calculation with multipliers

- **Business Rules Tested**:
  * Tier level must determine available benefits
  * Point calculations must follow defined rules
  * Special promotions must be correctly applied
  * Member preferences must be honored

- **Possible Variations**:
  * Testing various tier levels
  * Special promotion scenarios
  * Point redemption workflows
  * Member preference settings

### 6. Transaction Based Return with Force Quantity (TC006_TBR_forceQTY.py)
- **Primary Features**: 
  * Transaction-based return processing
  * Forced quantity return handling
  * Return authorization workflow

- **Key Components**:
  * Components.Returns.refund_tbr
  * Components.Returns.tbr_load_transaction
  * Return quantity management components

- **Test Configuration**:
  * User Role: Return-authorized cashier
  * Original Transaction: Completed sale with multiple items
  * Return Scenario: Force quantity beyond original

- **Validation Points**:
  * Transaction lookup functionality
  * Forced quantity validation
  * Authorization requirements
  * Receipt and documentation
  * Refund processing accuracy

- **Business Rules Tested**:
  * Returns must reference original transactions
  * Forced quantity requires appropriate authorization
  * Return documentation must be complete
  * Refund must be processed to correct tender

- **Possible Variations**:
  * Different authorization levels
  * Various refund methods
  * Partial returns
  * Returns without receipt reference

### 7. Department Return Processing (TC007_department_return.py)
- **Primary Features**: 
  * Department-based return workflow
  * Return without original transaction reference
  * Department code validation

- **Key Components**:
  * Department return specific components
  * Return reason handling
  * Refund processing

- **Test Configuration**:
  * User Role: Return-authorized cashier
  * Department: BAKEHOUSE
  * Return Amount: Partial of original sale

- **Validation Points**:
  * Department selection accuracy
  * Return reason application
  * Amount validation
  * Refund processing
  * Receipt documentation

- **Business Rules Tested**:
  * Department returns must require department selection
  * Return reason must be documented
  * Amount must be validated
  * Proper authorization must be enforced
  * Receipt must document return details

- **Possible Variations**:
  * Different departments
  * Various return reasons
  * Different refund methods
  * Authorization level variations

### 8. Non-Receipt Return Processing (TC008_nrr_scenario.py)
- **Primary Features**: 
  * Non-Receipted Return (NRR) functionality
  * Amount threshold validation
  * Department-based returns
  * Tiered approval workflows
  * Refund processing

- **Key Components**:
  * Components.Returns.departmentrefund_nrr (return_item_by_department)
  * Components.Common_components.Approvalrequired (handle_approval_popup)
  * Components.Common_components.handle_any_popup_POS (handle_Any_popup)
  * Components.Returns.refund_tbr (handle_refund_screen)
  * Components.Common_components.handle_chnage_screen (handle_chnagescreen_refunds)

- **Test Configuration**:
  * User Role: ATcash1 (initiates) and atmgr5 (approves)
  * Department: BAKEHOUSE for all returns
  * Amount Thresholds Tested:
    - $750.00 (First threshold: $500-$1000)
    - $5,000.00 (Second threshold: $1000.01-$9999.99)
    - $12,000.00 (Third threshold: ≥ $10,000)
  * Return Reason: "Damaged / Faulty"

- **Validation Points**:
  * Department selection and validation
  * Threshold amount validation
  * Return reason handling
  * Proper approval routing by threshold
  * Approval capture for each threshold level
  * Receipt generation with proper documentation
  * Transaction history recording
  * Cash drawer handling after refund

- **Business Rules Tested**:
  * Different amount thresholds trigger specific approval workflows:
    - $500-$1000: First level approval
    - $1000.01-$9999.99: Manager approval required
    - ≥$10,000: Highest level approval or restriction
  * Department must be selected for all NRR transactions
  * Return reason must be documented for audit compliance
  * Approval must be captured at appropriate level based on amount
  * Refund documentation must be complete and accurate
  * Cash drawer must be properly managed after refund

- **Possible Variations**:
  * Different departments for returns
  * Various return reasons
  * Amount at threshold boundaries
  * Different approval personnel
  * Different refund tender types
  * Failed approval scenarios

### 9. Basic Cash Flow with ABB Robot Integration (TC_Basic_Cash_Flow_ABBot.py)
- **Primary Features**: 
  * Service Cashier Login and Authentication
  * Item Addition via EAN/Keyin entry
  * Loyalty Skip functionality
  * Cash Payment Processing with ABB Robot Integration
  * Physical Cash Drawer Operations via Robot

- **Key Components**:
  * Components.Common_components.pos_login (mainlogic)
  * Components.Salemode.Keyin_item (Kayin_EAN_POS)
  * Components.Salemode.basket_with_itemdetails (get_basket_info)
  * Components.Loyalty.Loyalty_popup_validation (handle_customer_popup)
  * Components.Tenders.Cash_tender_payment (process_tenders)
  * Components.Common_components.handle_any_popup_POS (handle_Any_popup)
  * Components.BotActions.AbbAction (Trigger_Action) - **ABB Robot Integration**

- **Test Configuration**:
  * User Role: Service Cashier (ATcash5)
  * Test Item: Standard EAN code (9300675014779)
  * Payment Method: Cash tender
  * Robot Integration: ABB robot for physical drawer operations

- **Validation Points**:
  * Service cashier authentication successful
  * Item addition via EAN entry validated
  * Basket contents verification
  * Loyalty skip completion
  * Cash payment processing successful
  * ABB robot drawer closure executed physically
  * Transaction completion verified

- **Business Rules Tested**:
  * Service cashier access permissions
  * Item addition validation requirements
  * Loyalty mode optional processing
  * Cash payment completion with physical robot integration
  * Physical vs. software simulation drawer operations

- **Robot Integration**:
  * **Physical Action**: `,Close_Drawer` command to ABB robot
  * **Robot IP**: 10.81.3.113:5000
  * **Integration Point**: After cash payment completion
  * **Validation**: Robot response confirmation required
  * **Difference from Standard**: Uses physical robot instead of `cashdrawer_move_and_close()` software simulation

- **Special Configuration**:
  * ABB Robot must be connected and responsive
  * Service cashier permissions required
  * Physical cash drawer must be operational
  * Robot command validation required for completion

- **Related Tests**: TC003_loyalty_basic_scenario_ai, TC009_value_restriction_scenario

## Funds Management Test Scenarios

### 1. Paid Out Processing (TC001_paidout.py)
- **Primary Features**: 
  * Cash paid out from register
  * Denomination entry and tracking
  * Category selection and accounting
  * Authorization workflow

- **Key Components**:
  * Components.funds.change_screen_funds
  * Denomination entry components
  * Category selection components

- **Test Configuration**:
  * User Role: Cashier with paid out authorization
  * Paid Out Amount: Variable test amounts
  * Categories: Various accounting categories
  * Reference: Required reference numbers

- **Validation Points**:
  * Denomination entry accuracy
  * Category selection validation
  * Reference number requirements
  * Authorization workflow
  * Receipt documentation
  * Cash drawer handling

- **Business Rules Tested**:
  * Paid out requires proper authorization
  * Denominations must balance to total amount
  * Category selection is required
  * Reference information must be documented
  * Receipt must be generated with details
  * Cash drawer must be updated correctly

- **Possible Variations**:
  * Different paid out amounts
  * Various categories
  * Authorization level testing
  * Reference number formats
  * Cash drawer balancing

### 2. Paid Out with Screenshots (paidout_with_screenshots.py)
- **Primary Features**: 
  * Same as regular paid out
  * Additional screenshot capture
  * Extended validation points

- **Key Components**:
  * Same as regular paid out
  * Screenshot components

- **Test Configuration**:
  * Similar to regular paid out
  * Additional screenshot configuration

- **Validation Points**:
  * All regular paid out validations
  * Visual verification points
  * UI element validation

- **Business Rules Tested**:
  * Same as regular paid out
  * UI layout and presentation rules

- **Possible Variations**:
  * Different UI configurations
  * Accessibility testing
  * Various screen resolutions
  * Different languages/locales

## Common Test Patterns

### 1. Standard Transaction Flow
```
Login → Item Addition → Basket Validation → Loyalty → Payment → Receipt → Cash Drawer
```

### 2. Return Flow
```
Login → Return Navigation → Transaction Search → Item Selection → Return Reason → Refund Method → Receipt → Cash Drawer
```

### 3. Funds Management Flow
```
Login → Funds Menu → Operation Selection → Amount Entry → Category/Reason → Authorization → Documentation → Cash Drawer
```

### 4. Save/Recall Flow
```
Login → Item Addition → Save Transaction → Menu Navigation → Recall Transaction → Select Transaction → Handle Interventions → Complete Transaction
```

## Common Components by Functionality

### 1. Navigation
- toggle_menu_navigate - Menu navigation
- Application/Window handling - UI connection

### 2. Item Processing
- Kayin_EAN_POS - Barcode entry
- perform_item_search - Item search
- click_plu_path - PLU menu navigation
- department_sale - Department sales
- gs1_manual_entry - GS1 barcode processing

### 3. Transaction Management
- get_basket_info - Basket validation
- recall_transaction - Transaction recall
- handle_approval_popup - Approvals
- handle_Any_popup - General popup management

### 4. Compliance Features
- handle_age_restriction - Age verification
- automate_gs1_screen - Price override controls
- handle_customer_popup - Customer information

### 5. Payment Processing
- process_tenders - Tender selection and processing
- cashdrawer_move_and_close - Cash drawer management

### 6. Return Processing
- handle_refund_screen - Refund processing
- handle_transaction_return_screen - Transaction search
- select_refund_department - Department returns

## Test Generation Examples

### Example 1: Creating a Weight-Based GS1 Test
```
POS-Test-Generate:
- FeatureToTest: GS1 barcode with weight embedded data
- TestScenario: Validate correct weight extraction and price calculation
- RelatedExistingTests: TC004_Gs1_scenario.py
- Variations: Use AI(310n) for weight instead of price override, verify per-unit calculation
- ValidationRequirements: Weight extraction, price calculation, basket display
- UserRole: Standard cashier
```

### Example 2: Creating a Mixed Return Test
```
POS-Test-Generate:
- FeatureToTest: Mixed transaction with sale and return
- TestScenario: Process sale with new items and return of previous items
- RelatedExistingTests: TC007_department_return.py, TC004_Gs1_scenario.py
- Variations: Combine GS1 sale with department return in single transaction
- ValidationRequirements: Proper balance calculation, correct receipt documentation
- UserRole: Cashier with return authorization
```

---

*This knowledge base is designed to be updated with each new test case development. When creating a new test, use the POS-Doc-Update format to ensure consistent documentation.*
