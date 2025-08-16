from flask import Flask, request, jsonify
import camelot
import pandas as pd
import json
import re # Import the regular expressions library

app = Flask(__name__)

def is_likely_quantity(s):
    """
    Helper function to check if a string is likely a quantity (a number).
    This helps us identify the last column of a valid row.
    """
    if s is None:
        return False
    # Remove commas, periods, etc., then check if the string is all digits.
    return re.sub(r'[\.,]', '', str(s).strip()).isdigit()

def post_process_table(df):
    """
    This is the core logic to fix broken rows caused by text wrapping.
    """
    processed_rows = []
    temp_row = []
    num_columns = len(df.columns)

    # Convert the DataFrame to a list of lists for easier processing
    data = df.values.tolist()

    i = 0
    while i < len(data):
        row = data[i]
        
        # A "complete" row is one that has content and likely ends with a quantity.
        # We check the last non-empty cell.
        last_cell_content = next((cell for cell in reversed(row) if str(cell).strip()), None)

        # If the temporary row is empty, we start a new one.
        if not temp_row:
            temp_row.extend(row)
        else:
            # If the current row is incomplete, merge it with the temporary row.
            # An "incomplete" row is one that doesn't seem to end with a quantity.
            if not is_likely_quantity(last_cell_content):
                # Merge by combining elements column by column
                for j in range(num_columns):
                    temp_row[j] = f"{temp_row[j]} {row[j]}".strip()
            else:
                # The temporary row was complete, so we save it and start a new one.
                processed_rows.append(temp_row)
                temp_row = list(row)
        
        # Check if the temporary row is now "complete"
        last_temp_cell = next((cell for cell in reversed(temp_row) if str(cell).strip()), None)
        if is_likely_quantity(last_temp_cell):
            processed_rows.append(temp_row)
            temp_row = []

        i += 1
    
    # Add the last temporary row if it exists
    if temp_row:
        processed_rows.append(temp_row)

    return processed_rows


@app.route('/extract_table', methods=['POST'])
def extract_table():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    flavor = request.form.get('flavor', 'stream')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            filepath = "temp.pdf"
            file.save(filepath)

            print(f"Processing with flavor: {flavor}")
            tables = camelot.read_pdf(filepath, flavor=flavor, pages='1-end')

            if len(tables) > 0:
                all_tables_data = []
                for table in tables:
                    # If using stream, apply our advanced post-processing logic
                    if flavor == 'stream':
                        print("Applying post-processing for stream flavor...")
                        processed_data = post_process_table(table.df)
                        all_tables_data.extend(processed_data)
                    else:
                        # For 'lattice', the structure is usually correct, so we just add it
                        all_tables_data.extend(table.df.values.tolist())
                    
                    all_tables_data.append([]) # Add a blank row for spacing

                return jsonify(all_tables_data), 200
            else:
                return jsonify([]), 200

        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
