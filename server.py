# python_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS # Import the CORS library
import tabula
import pandas as pd
import re

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

def clean_cell(cell_data):
    """Removes currency symbols and commas from a string."""
    if isinstance(cell_data, str):
        cleaned = re.sub(r'[\$\€\£\₹\,]', '', cell_data).strip()
        return cleaned
    return cell_data

def process_merged_tax_cell(cell_data):
    """
    Detects and processes merged tax cells for both rates and amounts.
    - Handles "9%9%" -> "18%"
    - Handles "8%9%" -> "17%"
    - Handles "5712.715712.71" -> "11425.42"
    """
    if isinstance(cell_data, str):
        # Case 1: Handle merged percentages like "9%9%" or "8.5%9.5%"
        rates = re.findall(r'(\d+\.?\d*)%', cell_data)
        if len(rates) > 1:
            try:
                total_rate = sum(float(r) for r in rates)
                return f"{int(total_rate) if total_rate.is_integer() else total_rate}%"
            except (ValueError, TypeError):
                pass

        # Case 2: Handle merged amounts like "5712.715712.71"
        if '%' not in cell_data and re.match(r'^[0-9\.]+$', cell_data) and cell_data.count('.') > 1:
            midpoint = len(cell_data) // 2
            part1 = cell_data[:midpoint]
            part2 = cell_data[midpoint:]
            try:
                if '.' in part1 and '.' in part2:
                    total_amount = float(part1) + float(part2)
                    return str(round(total_amount, 2))
            except (ValueError, TypeError):
                pass

    return cell_data

@app.route('/extract_raw_table', methods=['POST'])
def extract_raw_table():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            # tabula.read_pdf can handle a file-like object directly,
            # which is what request.files['file'] provides.
            tables = tabula.read_pdf(file, pages='all', lattice=True, multiple_tables=True)

            if not tables:
                return jsonify({"table_data": [], "currency_symbol": None}), 200

            all_tables_data = []
            for table in tables:
                table.fillna('', inplace=True)
                cleaned_table = table.applymap(clean_cell)

                # --- LOGIC TO PROCESS MERGED CELLS ---
                tax_rate_col_index = 5
                tax_amount_col_index = 7

                if cleaned_table.shape[1] > tax_rate_col_index:
                    cleaned_table.iloc[:, tax_rate_col_index] = cleaned_table.iloc[:, tax_rate_col_index].apply(process_merged_tax_cell)
                
                if cleaned_table.shape[1] > tax_amount_col_index:
                    cleaned_table.iloc[:, tax_amount_col_index] = cleaned_table.iloc[:, tax_amount_col_index].apply(process_merged_tax_cell)
                # --- END OF LOGIC ---

                cleaned_table.dropna(how='all', inplace=True)
                all_tables_data.extend(cleaned_table.values.tolist())
            
            return jsonify({
                "table_data": all_tables_data,
                "currency_symbol": None 
            }), 200

        except Exception as e:
            # Added more descriptive error handling
            return jsonify({"error": f"An error occurred during PDF processing: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    # Add debug=True for development
    # host='0.0.0.0' allows it to be accessible from other devices on the network.
    app.run(host='0.0.0.0', port=5000, debug=True)
