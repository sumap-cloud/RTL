# -*- coding: utf-8 -*-
"""
POS Database Data Retriever

This script connects to a SQL Server database using adodbapi (part of pywin32),
executes a given query, and returns the data as a list of tuples.

Usage:
1. Command Line:
   python Get_DB_Data.py "server_name" "SELECT * FROM table"
   
2. Import and use:
   from Get_DB_Data import execute_query
   results = execute_query("10.80.79.2\\SQLEXPRESS", "SELECT * FROM table")
   
3. Direct function call:
   from Get_DB_Data import get_sql_data
   results = get_sql_data("server", "database", "user", "pass", "query")

Examples:
- python Get_DB_Data.py "10.80.79.2\\SQLEXPRESS" "SELECT TOP 5 * FROM Retail..CAT_Product"
- python Get_DB_Data.py "localhost\\SQLEXPRESS" "SELECT COUNT(*) FROM Retail..CAT_Store"
"""

import adodbapi
import sys

def get_sql_data(server_name, database_name, username, password, query):
    """
    Connects to a SQL Server, executes a query, and fetches data.

    Args:
        server_name (str): The name or IP address of the SQL Server.
        database_name (str): The name of the database to connect to.
        username (str): The username for SQL Server authentication.
        password (str): The password for the user.
        query (str): The SQL query to be executed.

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
        print(f"Connecting to '{server_name}'...")
        conn = adodbapi.connect(conn_string)
        print("Connection successful.")

        # Create a cursor object
        with conn.cursor() as cursor:
            # Execute the query
            print(f"Executing query: {query}")
            cursor.execute(query)

            # Fetch all the rows
            print("Fetching data...")
            data = cursor.fetchall()
            print(f"Successfully fetched {len(data)} rows.")

    except adodbapi.DatabaseError as e:
        print(f"Database Error: {e}")
        # Typically, you might want to handle different exceptions differently
        # For example, login failed, server not found, etc.
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # The 'with' statement ensures the cursor is closed,
        # but we must explicitly close the connection.
        if conn:
            conn.close()
            print("Connection closed.")

    return data

def execute_query(server_name, sql_query, database_name="Retail", username="SA", password="7XH2LKkkctEp", return_as_string=False, delimiter=";"):
    """
    Simplified function to execute a SQL query with server and query as main parameters.
    
    Args:
        server_name (str): The SQL Server name (e.g., '10.80.79.2\\SQLEXPRESS')
        sql_query (str): The SQL query to execute
        database_name (str): Database name (default: "Retail")
        username (str): Database username (default: "SA")
        password (str): Database password (default: "7XH2LKkkctEp")
        return_as_string (bool): If True, returns formatted string instead of list (default: False)
        delimiter (str): Delimiter to separate rows when return_as_string=True (default: ";")
    
    Returns:
        list or str: Query results as list of tuples, or formatted string if return_as_string=True
    """
    results = get_sql_data(server_name, database_name, username, password, sql_query)
    
    if return_as_string and results:
        # Convert results to single line string with delimiter
        result_data = []
        for row in results:
            # Convert each row tuple to string and join multiple columns with comma
            row_str = ",".join(str(item) if item is not None else "" for item in row)
            result_data.append(row_str)
        
        # Join all rows with the delimiter
        return delimiter.join(result_data)
    
    return results


def main():
    """
    Main function that can be called with parameters or use defaults for testing.
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
        
        server = r'10.80.79.2\SQLEXPRESS'
        query = "Select TOP 3 PO.Code from Retail .. CAT_ProductRestriction PR WITH(NOLOCK) inner join Retail .. CAT_StoreRangeProduct CP WITH (NOLOCK)  on CP.Product_Id = PR.Product_Id inner join Retail..CAT_ProductIdentifier PO WITH (NOLOCK) on PO.Product_id = CP.Product_id Where  PR.RestrictionType ='2' and PR.IsRestricted ='1' and PO.Code like '9%';"
        print(f"Default Server: {server}")
        print(f"Default Query: {query}")

    # Execute the query
    results = execute_query(server, query)

    # Display results
    if results:
        print(f"\n--- Query Results ({len(results)} rows) ---")
        # Convert all row data to a single line with delimiter
        delimiter = ";"  # You can change this delimiter as needed
        result_data = []
        for row in results:
            # Convert each row tuple to string and join multiple columns with comma
            row_str = ",".join(str(item) if item is not None else "" for item in row)
            result_data.append(row_str)
        
        # Join all rows with the delimiter
        single_line_output = delimiter.join(result_data)
        print(f"{single_line_output}")
        print("---------------------\n")
        return results
    else:
        print("\nNo data was returned. Please check your query and credentials.\n")
        return []


# --- Example Usage ---
if __name__ == "__main__":
    main()

