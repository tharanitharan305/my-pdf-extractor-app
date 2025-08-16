from flask import Flask, request, jsonify
import camelot
import pandas as pd
import json
import re

app = Flask(__name__)

# (Helper functions like is_likely_quantity and post_process_table remain the same)
def is_likely_quantity(s):
    if s is None:
        return False
    return re.sub(r'[\.,]', '', str(s).strip()).isdigit()

def post_process_table(df):
    processed_rows = []
    temp_row = []
    num_columns = len(df.columns)
    data = df.values.tolist()
    i = 0
    while i < len(data):
        row = data[i]
        last_cell_content = next((cell for cell in reversed(row) if str(cell).strip()), None)
        if not temp_row:
            temp_row.extend(row)
        else:
            if not is_likely_quantity(last_cell_content):
                for j in range(num_columns):
                    temp_row[j] = f"{temp_row[j]} {row[j]}".strip()
            else:
                processed_rows.append(temp_row)
                temp_row = list(row)
        
        last_temp_cell = next((cell for cell in reversed(temp_row) if str(cell).strip()), None)
        if is_likely_quantity(last_temp_cell):
            processed_rows.append(temp_row)
            temp_row = []
        i += 1
    if temp_row:
        processed_rows.append(temp_row)
    return processed_rows

@app.route('/extract_table', methods=['POST'])
def extract_table():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    flavor = request.form.get('flavor', 'stream')
    # Get the column separators from the request, if provided
    columns_str = request.form.get('columns')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            filepath = "temp.pdf"
            file.save(filepath)

            # Prepare keyword arguments for Camelot
            camelot_kwargs = {'flavor': flavor, 'pages': '1-end'}

            # If column separators were provided, add them to the arguments
            if columns_str:
                try:
                    # Convert the comma-separated string to a list of integers
                    columns = [int(c.strip()) for c in columns_str.split(',')]
                    camelot_kwargs['column_separators'] = columns
                    print(f"Using custom column separators: {columns}")
                except ValueError:
                    return jsonify({"error": "Invalid format for columns. Must be comma-separated numbers."}), 400

            tables = camelot.read_pdf(filepath, **camelot_kwargs)

            if len(tables) > 0:
                all_tables_data = []
                for table in tables:
                    if flavor == 'stream':
                        processed_data = post_process_table(table.df)
                        all_tables_data.extend(processed_data)
                    else:
                        all_tables_data.extend(table.df.values.tolist())
                    all_tables_data.append([])

                return jsonify(all_tables_data), 200
            else:
                return jsonify([]), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
