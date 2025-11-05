from getdb_v1 import execute_query
def main_workflow():
    """
    Main workflow for your application.
    """
    
    # 2. Define your server and query
    my_server = r"10.80.79.2\SQLEXPRESS" # Use r"..." for strings with backslashes
    my_query = "Select TOP 3 PO.Code from Retail .. CAT_ProductRestriction PR WITH(NOLOCK) inner join Retail .. CAT_StoreRangeProduct CP WITH (NOLOCK)  on CP.Product_Id = PR.Product_Id inner join Retail..CAT_ProductIdentifier PO WITH (NOLOCK) on PO.Product_id = CP.Product_id Where  PR.RestrictionType ='2' and PR.IsRestricted ='1' and PO.Code like '9%';"

    print(f"Connecting to {my_server} to run query...")

    try:
        # 3. Call the function
        # Because of our last update, this will return a simple list
        # like: ['9328854011814', '9334892041409', '9344240000132']
        barcodes = execute_query(my_server, my_query)

        if barcodes:
            print(f"Successfully fetched {len(barcodes)} barcodes: {barcodes}")
            
            # 4. Call your function with the list
            print("\nSending list to Kayin_EAN_POS...")
          
            
        else:
            print("No barcodes found matching the query.")

    except Exception as e:
        print(f"An error occurred while running the query: {e}")

# This ensures the code runs when you execute this file directly
if __name__ == "__main__":
    main_workflow()
