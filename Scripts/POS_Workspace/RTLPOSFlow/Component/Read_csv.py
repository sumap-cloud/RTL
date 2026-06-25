import csv

def get_csv_value(file_path, banner, tc_id, iteration, target_column):
    """
    Finds a specific value in a CSV file by matching Banner, TC_ID, and Iteration.
    """
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            # Use DictReader to access columns by their header names
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # Perform the multi-criteria match
                # Iteration is often read as a string from CSV, so we check accordingly
                if (row['Banner'] == banner and 
                    row['TC_ID'] == tc_id and 
                    row['Iteration'] == str(iteration)):
                    
                    # Return the value from the requested column
                    return row.get(target_column, f"Column '{target_column}' not found")
            
            return "No matching record found."

    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"An error occurred: {e}"

# # --- Example Usage ---
# csv_file = 'your_data.csv'  # Replace with your actual file path

# # Define your search criteria
# target_banner = "SM"
# target_tc_id = "TC_001_RecentTransactionValidation"
# target_iteration = 1
# column_to_find = "remarks"

# result = get_csv_value(csv_file, target_banner, target_tc_id, target_iteration, column_to_find)

# print(f"Value found: {result}")