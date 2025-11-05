# -*- coding: utf-8 -*-
"""
POS Database Data Retriever (Refactored)

This script connects to a SQL Server database using adodbapi,
executes a query, and returns the data.

It is designed to be both executable for testing and easily
importable into other Python scripts.

Usage:
1. Import and use (Recommended):
   from Get_DB_Data import execute_query
   
   # Get results as a simple string (default)
   results_str = execute_query("10.80.79.2\\SQLEXPRESS", "SELECT Code FROM table")
   print(results_str)
   
   # Get results as a list of tuples
   results_list = execute_query("server", "query", return_as_string=False)
   
   # Override default credentials
   results_str = execute_query(
       "server", "query", 
       database_name="OtherDB", 
       username="new_user", 
       password="new_password"
   )

2. Command Line (for testing):
   python Get_DB_Data.py "server_name" "SELECT * FROM table"
"""

import adodbapi
import sys

def get_sql_data(server_name, database_name, username, password, query, verbose=False):
    """
    Connects to a SQL Server, executes a query, and fetches data. (Core function)

    Args:
        server_name (str): The name or IP address of the SQL Server.
        database_name (str): The name of the database to connect to.
        username (str): The username for SQL Server authentication.
        password (str): The password for the user.
        query (str): The SQL query to be executed.
        verbose (bool): If True, prints connection and status messages.

    Returns:
        list: A list of tuples, where each tuple represents a row from the result set.
              Returns an empty list if an error occurs or no data is found.
    """
    data = []
    conn_string = (
        f"Provider=SQLOLEDB;"
        f"Data Source={server_name};"
        f"Initial Catalog={database_name};"
        f"User ID={username};"
        f"Password={password};"
    )
    conn = None # Initialize conn to None
    try:
        # Establish the database connection
        if verbose: print(f"Connecting to '{server_name}'...")
        conn = adodbapi.connect(conn_string)
        if verbose: print("Connection successful.")

        # Create a cursor object
        with conn.cursor() as cursor:
            # Execute the query
            if verbose: print(f"Executing query: {query}")
            cursor.execute(query)

            # Fetch all the rows
            if verbose: print("Fetching data...")
            data = cursor.fetchall()
            if verbose: print(f"Successfully fetched {len(data)} rows.")

    except adodbapi.DatabaseError as e:
        print(f"Database Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            if verbose: print("Connection closed.")

    return data

def execute_query(
    server_name, 
    sql_query, 
    database_name="Retail", 
    username="SA", 
    password="7XH2LKkkctEp", 
    return_as_string=False, # CHANGED: Default is now False
    delimiter=";",
    verbose=False
):
    """
    Simplified function to execute a SQL query. 
    This is the recommended function to import.

    Args:
        server_name (str): The SQL Server name (e.g., '10.80.79.2\\SQLEXPRESS')
        sql_query (str): The SQL query to execute
        database_name (str): Database name (default: "Retail")
        username (str): Database username (default: "SA")
        password (str): Database password (default: "7XH2LKkkctEp")
        return_as_string (bool): If False (default), returns a simple list of values (e.g., ['val1', 'val2']).
                               If True, returns a simple delimiter-separated string.
                               NOTE: The list/string format assumes single-column queries.
        delimiter (str): Delimiter to use if return_as_string=True (default: ";")
        verbose (bool): If True, prints connection and status messages (default: False)

    Returns:
        list or str: Query results as a simple list (default) or formatted string.
                     Returns an empty list or empty string if no data.
    """
    # get_sql_data returns a list of tuples, e.g., [('9328854011814',), ('9334892041409',)]
    results_tuples = get_sql_data(server_name, database_name, username, password, sql_query, verbose)
    
    if not results_tuples:
        return [] if not return_as_string else "" # Return empty list or string

    # NEW: Flatten the list of tuples into a simple list of the first item from each tuple.
    # This assumes your queries return a single column, as in your examples.
    try:
        # We also convert items to string here for consistency
        simple_list = [str(row[0]) if row[0] is not None else "" for row in results_tuples]
    except (IndexError, TypeError):
        # Fallback for multi-column queries or unexpected data
        if verbose: print("Warning: Query may have multiple columns or unexpected data. Returning list of tuples.")
        return results_tuples # Return the raw tuples if flattening fails

    if return_as_string:
        # Join the simple list with the delimiter
        return delimiter.join(simple_list)
    
    # If return_as_string is False, return the new simple list
    return simple_list


def main():
    """
    Main function to run when the script is executed directly.
    Used primarily for testing.
    """
    # Check if command line arguments are provided
    if len(sys.argv) >= 3:
        # Use command line arguments
        server = sys.argv[1]
        query = sys.argv[2]
        print(f"Using command line arguments:")
        print(f"Server: {server}")
        print(f"Query: {query}")
    else:
        # Use default values for testing
        print("No command line arguments provided. Using default values for testing...")
        
        # Use raw string (r'...') to avoid SyntaxWarning with backslashes
        server = r'10.80.79.2\SQLEXPRESS'
        query = "Select TOP 3 PO.Code from Retail .. CAT_ProductRestriction PR WITH(NOLOCK) inner join Retail .. CAT_StoreRangeProduct CP WITH (NOLOCK)  on CP.Product_Id = PR.Product_Id inner join Retail..CAT_ProductIdentifier PO WITH (NOLOCK) on PO.Product_id = CP.Product_id Where  PR.RestrictionType ='2' and PR.IsRestricted ='1' and PO.Code like '9%';"
        print(f"Default Server: {server}")
        print(f"Default Query: {query}")

    # Execute the query, get string output, and be verbose
    # We explicitly ask for the string output here for testing the main() function.
    # When imported, the default will be a list.
    results_string = execute_query(server, query, return_as_string=True, verbose=True)

    # Display results
    if results_string:
        print(f"\n--- Query Results ---")
        print(results_string)
        print("---------------------\n")
    else:
        print("\nNo data was returned.\n")
        
    #example
        # barcodes = execute_query(my_server, my_query)

        # if barcodes:
        #     print(f"Successfully fetched {len(barcodes)} barcodes: {barcodes}")
            
        #     # 4. Call your function with the list
        #     print("\nSending list to Kayin_EAN_POS...")
          
            
        # else:
        #     print("No barcodes found matching the query.")


# --- This block runs only when the script is executed directly ---
if __name__ == "__main__":
    main()

