import sys
from pathlib import Path

# Add the parent directory to Python path
current_file = Path(__file__).resolve()
pos_workspace_dir = current_file.parent.parent
if str(pos_workspace_dir) not in sys.path:
    sys.path.insert(0, str(pos_workspace_dir))

from Components.Tenders.Temporary_Cheque_Complete_Workflow import TemporaryChequeWorkflowHandler

def process_cheque_payment(amount, account_name, bsb, account_number, cheque_number, bank_name, bank_location):
    """
    Process a cheque payment using the temporary cheque workflow.
    
    Args:
        amount (str): Amount to process (e.g., "15.50")
        account_name (str): Name on the account
        bsb (str): BSB number
        account_number (str): Account number
        cheque_number (str): Cheque number
        bank_name (str): Name of the bank
        bank_location (str): Bank branch location
        
    Returns:
        bool: True if payment was successful, False otherwise
    """
    # Create an instance of the workflow handler
    handler = TemporaryChequeWorkflowHandler()
    
    if not handler.is_connected:
        print("Could not connect to POS application")
        return False
    
    # Prepare the cheque details
    cheque_details = {
        "Account Name": account_name,
        "BSB Number": bsb,
        "Account Number": account_number,
        "Cheque Number": cheque_number,
        "Bank Name": bank_name,
        "Bank Location": bank_location
    }
    
    # Execute the workflow
    success = handler.complete_temporary_cheque_workflow(
        amount=amount,
        cheque_details=cheque_details,
        template_name="Small - 160 X 70"  # You can change this if needed
    )
    
    return success

# Example usage
if __name__ == "__main__":
    # Example of processing a $25.50 cheque payment
    success = process_cheque_payment(
        amount="25.50",
        account_name="John Smith",
        bsb="123456",
        account_number="987654321",
        cheque_number="000123",
        bank_name="Example Bank",
        bank_location="Main Branch"
    )
    
    if success:
        print("✅ Cheque payment processed successfully!")
    else:
        print("❌ Failed to process cheque payment. Check the logs for details.")
