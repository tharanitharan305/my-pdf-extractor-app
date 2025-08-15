from flask import Flask, request, jsonify
import camelot
import pandas as pd
import json

app = Flask(__name__)

@app.route('/extract_table', methods=['POST'])
def extract_table():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    # Get the flavor from the request, default to 'stream' if not provided
    flavor = request.form.get('flavor', 'stream')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            filepath = "temp.pdf"
            file.save(filepath)

            # Use the 'flavor' provided by the Flutter app
            print(f"Processing with flavor: {flavor}") # For debugging
            tables = camelot.read_pdf(filepath, flavor=flavor, pages='1-end')

            if len(tables) > 0:
                all_tables_data = []
                for table in tables:
                    table_data = table.df.values.tolist()
                    all_tables_data.extend(table_data)
                    all_tables_data.append([]) # Add a blank row for spacing

                return jsonify(all_tables_data), 200
            else:
                return jsonify([]), 200 # Return empty list if no tables found

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)