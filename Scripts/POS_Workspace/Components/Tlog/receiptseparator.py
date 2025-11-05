import xml.etree.ElementTree as ET
import re
import json
import argparse
from datetime import datetime

def parse_receipt_xml_to_structured_elements(xml_content):
    """
    Parses the OPOSPrint XML and reconstructs a list of structured elements
    (like text lines and images) in the order they appear.

    Args:
        xml_content (str): The string content of the receipt XML file.

    Returns:
        list: A list of dictionaries, each representing an element on the receipt.
    """
    elements = []
    try:
        root = ET.fromstring(xml_content)
        # Find all direct children of Document, which can be TextObject, ImageObject, etc.
        for element in root.findall('.//Document/*'):
            # Handle Text Sections
            if element.tag == 'PrintSection':
                for sub_element in element:
                    if sub_element.tag == 'TextObject':
                        text_line = sub_element.find('.//TextLine')
                        if text_line is not None:
                            line_fragments = []
                            for text in text_line.findall('./Text'):
                                if text.get('Text') is not None:
                                    line_fragments.append(text.get('Text'))
                            elements.append({
                                "type": "text",
                                "content": "".join(line_fragments).strip()
                            })
                    # Handle Image Objects
                    elif sub_element.tag == 'ImageObject':
                        elements.append({
                            "type": "image",
                            "attributes": sub_element.attrib
                        })

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    return elements

def extract_data_from_elements(elements):
    """
    Uses regular expressions and state tracking to extract structured data
    from a list of receipt elements (text and images).

    Args:
        elements (list): A list of element dicts from the receipt.

    Returns:
        dict: A dictionary containing the structured receipt data.
    """
    receipt_data = {
        "storeInfo": {},
        "totals": {},
        "lineItems": [],
        "tenders": [],
        "barcode": None,
        "promotionalContent": [],
        "footerContent": []
    }

    # --- Regex Patterns ---
    store_info_pattern = re.compile(
        r"STORE\s+(\d+)\s+POS\s+(\d+)\s+TRANS\s+(\d+)\s+([\d:]+)\s+([\d/]+)", re.IGNORECASE)
    store_name_phone_pattern = re.compile(r"^(.*?)\s+PH:\s+(.*)$", re.IGNORECASE)
    abn_pattern = re.compile(r"ABN\s+([\d\s]+)", re.IGNORECASE)
    item_pattern = re.compile(r"^[#\s]?(\S+)\s+(.*?)\s{2,}([\d.]+)$")
    subtotal_pattern = re.compile(r"^\s*(?:(\d+)\s+)?SUBTOTAL\s+\$?([\d.]+)", re.IGNORECASE)
    total_pattern = re.compile(r"^\s*TOTAL\s+\$?([\d.]+)", re.IGNORECASE)
    gst_pattern = re.compile(r"TOTAL includes GST\s+\$?([\d.]+)", re.IGNORECASE)
    tender_pattern = re.compile(r"^\s*(Cash|Card)\s+\$?([\d.]+)", re.IGNORECASE)
    change_pattern = re.compile(r"Change\s+\$?([\d.]+)", re.IGNORECASE)
    barcode_pattern = re.compile(r"^(\d{20,})$")
    delimiter_pattern = re.compile(r"^-{10,}$") # A line of 10 or more dashes

    # --- State Tracking ---
    current_section = None # Can be 'promo', 'footer', or None

    element_iterator = iter(elements)
    for element in element_iterator:
        # We only process text content in this main loop
        if element['type'] != 'text':
            # If we are in a section, add the non-text element to it
            if current_section == 'promo':
                receipt_data['promotionalContent'].append(element)
            elif current_section == 'footer':
                receipt_data['footerContent'].append(element)
            continue

        line = element['content']
        if not line: # Skip empty lines
            continue

        # --- State Change Logic ---
        # A delimiter line always ends the current section
        if delimiter_pattern.match(line):
            current_section = None
            continue
        # Keywords that start a new section
        if "Everyday Rewards" in line:
            current_section = 'promo'
        elif "Thank you for shopping" in line:
            current_section = 'footer'

        # --- Data Extraction Logic ---
        # Try to match specific data; if it's found, 'continue' to the next line.
        # Otherwise, if we are in a section, append the line to that section's content.
        
        store_name_match = store_name_phone_pattern.search(line)
        if store_name_match:
            receipt_data["storeInfo"]["name"] = store_name_match.group(1).strip()
            receipt_data["storeInfo"]["phone"] = store_name_match.group(2).strip()
            # The next element is likely the address
            try:
                receipt_data["storeInfo"]["address"] = next(element_iterator)['content']
            except (StopIteration, KeyError): pass
            continue

        abn_match = abn_pattern.search(line)
        if abn_match:
            receipt_data["storeInfo"]["abn"] = abn_match.group(1).replace(" ", "")
            continue

        store_match = store_info_pattern.search(line)
        if store_match:
            date_str, time_str = store_match.group(5), store_match.group(4)
            try:
                dt_obj = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                receipt_data["storeInfo"]["timestamp"] = dt_obj.isoformat()
            except ValueError:
                print(f"Warning: Could not parse date/time: {date_str} {time_str}")
            receipt_data["storeInfo"]["storeNumber"] = store_match.group(1)
            receipt_data["storeInfo"]["posNumber"] = store_match.group(2)
            receipt_data["storeInfo"]["transactionNumber"] = store_match.group(3)
            continue

        item_match = item_pattern.search(line)
        if item_match:
            item_id = item_match.group(1).strip()
            description = item_match.group(2).strip()
            price = float(item_match.group(3))

            # --- VALIDATION ADDED HERE ---
            # Check if the item ID contains special characters (^ for caret or # for hash)
            # and print a warning message to the console if it does.
            if '^' in item_id or '#' in item_id:
                print(f"Validation Warning: Item '{description}' has an ID ('{item_id}') with a special character.")

            receipt_data["lineItems"].append({
                "id": item_id,
                "description": description,
                "price": price,
                "quantity": 1
            })
            continue

        subtotal_match = subtotal_pattern.search(line)
        if subtotal_match:
            quantity, amount = subtotal_match.group(1), subtotal_match.group(2)
            receipt_data["totals"]["subtotal"] = float(amount)
            if quantity and receipt_data["lineItems"]:
                receipt_data["lineItems"][-1]["quantity"] = int(quantity)
            continue
        
        total_match = total_pattern.search(line)
        if total_match:
            receipt_data["totals"]["total"] = float(total_match.group(1))
            continue

        gst_match = gst_pattern.search(line)
        if gst_match:
            receipt_data["totals"]["gst"] = float(gst_match.group(1))
            continue
            
        tender_match = tender_pattern.search(line)
        if tender_match:
            receipt_data["tenders"].append({
                "type": tender_match.group(1).strip(), "amount": float(tender_match.group(2))
            })
            continue

        change_match = change_pattern.search(line)
        if change_match:
            receipt_data["totals"]["change"] = float(change_match.group(1))
            continue
            
        barcode_match = barcode_pattern.search(line)
        if barcode_match:
            receipt_data["barcode"] = barcode_match.group(1)
            continue
        
        # --- Section Content Appending ---
        # If no specific pattern was matched, and we are inside a section,
        # add this line's content to that section.
        if current_section == 'promo':
            receipt_data['promotionalContent'].append(element)
        elif current_section == 'footer':
            receipt_data['footerContent'].append(element)
            
    return receipt_data


def Fastentry_Tlogvalidation():
    """Main function to run the parser from the command line."""
    parser = argparse.ArgumentParser(description="Parse a receipt XML file and convert it to JSON.")
    parser.add_argument(
        "-i", "--input", default="3_receipt.xml",
        help="Path to the input receipt XML file (default: 3_receipt.xml).")
    parser.add_argument(
        "-o", "--output", default="4_receipt_data.json",
        help="Path for the output JSON file (default: 4_receipt_data.json).")
    args = parser.parse_args()

    print(f"--- Starting Receipt Parser ---")
    print(f"Reading from: '{args.input}'")

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input}'")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    xml_content = re.sub(r"&(?![a-zA-Z]+;|#[0-9]+;)", "&amp;", xml_content)

    # Step 1: Convert XML into a list of structured elements (text, images).
    receipt_elements = parse_receipt_xml_to_structured_elements(xml_content)

    # Step 2: Extract data from the elements into a final dictionary.
    structured_data = extract_data_from_elements(receipt_elements)

    # Step 3: Save the data as a formatted JSON file.
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully parsed receipt and saved data to '{args.output}'")
        print("\n--- Parsed JSON Data ---")
        print(json.dumps(structured_data, indent=2))
        print("------------------------")
    except Exception as e:
        print(f"Error writing JSON file: {e}")


if __name__ == "__main__":
    Fastentry_Tlogvalidation()

