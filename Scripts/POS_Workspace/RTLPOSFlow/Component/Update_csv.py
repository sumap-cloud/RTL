# import csv
# import tempfile
# import shutil
# from pathlib import Path

# def update_csv_value(file_path, banner, tc_id, iteration, target_column, new_value):
#     """
#     Updates a specific cell in a CSV file where Banner, TC_ID, and Iteration match.
#     """
#     file_path = Path(file_path)
#     # Create a temporary file to write the updated data
#     fd, temp_path = tempfile.mkstemp(suffix=".csv", dir=file_path.parent)
    
#     updated = False
    
#     try:
#         # with open(file_path, mode='r', encoding='utf-8', newline='') as infile, \
#         #      open(temp_path, mode='w', encoding='utf-8', newline='') as outfile:
#         with open(file_path, mode='r', encoding='utf-8') as csvfile:
            
#             reader = csv.DictReader(csvfile)
#             writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
            
#             # Write the header to the new file
#             writer.writeheader()
            
#             for row in reader:
#                 # Check for the matching condition
#                 if (row['Banner'] == banner and 
#                     row['TC_ID'] == tc_id and 
#                     row['Iteration'] == str(iteration)):
                    
#                     if target_column in row:
#                         print(f"Updating {tc_id} ({target_column}): {row[target_column]} -> {new_value}")
#                         row[target_column] = new_value
#                         updated = True
#                     else:
#                         print(f"Warning: Column '{target_column}' not found in CSV.")
                
#                 # Write the row (modified or original) to the temp file
#                 writer.writerow(row)
        
#         # Replace the original file with the updated temp file
#         if updated:
#             shutil.move(temp_path, file_path)
#             print("Successfully updated the CSV.")
#         else:
#             print("No matching record found. No changes made.")
#             Path(temp_path).unlink() # Delete temp file if no changes

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         if Path(temp_path).exists():
#             Path(temp_path).unlink()

# # --- Example Usage ---
# # csv_file = 'test_results.csv'

# # # Condition to match
# # banner_val = "SM"
# # tc_id_val = "TC_001_RecentTransactionValidation"
# # iteration_val = 1

# # # Update the status and remarks
# # update_csv_value(csv_file, banner_val, tc_id_val, iteration_val, "status", "Passed")
# # update_csv_value(csv_file, banner_val, tc_id_val, iteration_val, "remarks", "Validated via API log extraction")




import csv
import tempfile
import shutil
import os
from pathlib import Path

def update_csv_value(file_path, banner, tc_id, iteration, target_column, new_value):
    """
    Updates a specific cell in a CSV file where Banner, TC_ID, and Iteration match.
    """
    file_path = Path(file_path)
    
    # mkstemp creates the file AND opens it at the OS level. It returns a file descriptor (fd)
    fd, temp_path = tempfile.mkstemp(suffix=".csv", dir=file_path.parent)
    
    updated = False
    
    try:
        # 1. Open the original file for READING (infile)
        # 2. Open the temporary file for WRITING (outfile)
        with open(file_path, mode='r', encoding='utf-8', newline='') as infile, \
             open(temp_path, mode='w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            
            # Write the header to the temp file
            writer.writeheader()
            
            for row in reader:
                # Check for the matching condition
                if (row.get('Banner') == banner and 
                    row.get('TC_ID') == tc_id and 
                    row.get('Iteration') == str(iteration)):
                    
                    if target_column in row:
                        print(f"Updating {tc_id} ({target_column}): {row[target_column]} -> {new_value}")
                        row[target_column] = new_value
                        updated = True
                    else:
                        print(f"Warning: Column '{target_column}' not found in CSV.")
                
                # Write the row (modified or original) to the temp file
                writer.writerow(row)
        
        # We must close the OS-level file descriptor before moving/deleting on Windows!
        os.close(fd)
        
        # Replace the original file with the updated temp file
        if updated:
            shutil.move(temp_path, file_path)
            print("Successfully updated the CSV.")
        else:
            print("No matching record found. No changes made.")
            Path(temp_path).unlink() # Delete temp file if no changes

    except Exception as e:
        # Close the fd even if it crashes, so we can delete the temp file
        os.close(fd) 
        print(f"An error occurred: {e}")
        if Path(temp_path).exists():
            Path(temp_path).unlink()