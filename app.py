from flask import Flask, render_template, abort
import csv
import os

app = Flask(__name__)

# Set the path to the folder containing CSV files
CSV_FOLDER = os.path.join(os.path.expanduser('~'), 'output')

@app.route('/<filename>')
def show_csv(filename):
    # Ensure the filename ends with '.csv' if not already specified
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    file_path = os.path.join(CSV_FOLDER, filename)
    
    # Check if the file exists in the output directory
    if not os.path.exists(file_path):
        return abort(404)  # Return a 404 if the file is not found

    # Read the CSV file
    with open(file_path, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        headers = rows[0] if rows else []  # First row as headers
        rows = rows[1:] if len(rows) > 1 else []  # Remaining rows as data

    # Render the HTML template and pass the CSV data
    return render_template('display_csv.html', headers=headers, rows=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
