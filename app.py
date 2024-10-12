from flask import Flask, request, jsonify, render_template
import os
import subprocess
import threading
import csv

app = Flask(__name__)

# Define the upload folder and output folder
UPLOAD_FOLDER = os.path.expanduser('~/upload/')
OUTPUT_FOLDER = os.path.expanduser('~/outputcsv/')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Ensure the uploaded files have safe names
def save_file(file, filename):
    if file:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        return file_path
    return None

# Function to trigger the script in the background with file1 and file2
def run_script(file1_path, file2_path):
    subprocess.run(
        ['python', os.path.expanduser('~/script.py'), file1_path, file2_path]
    )

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Missing files. Please upload both file1 and file2.'}), 400

    file1 = request.files['file1']
    file2 = request.files['file2']

    # Save both files
    file1_path = save_file(file1, file1.filename)
    file2_path = save_file(file2, file2.filename)

    # Run the script in a separate thread with just the two files
    script_thread = threading.Thread(target=run_script, args=(file1_path, file2_path))
    script_thread.start()

    # Return 200 OK immediately after upload
    return jsonify({'message': 'Files successfully uploaded!'}), 200

@app.route('/<filename>', methods=['GET'])
def display_csv(filename):
    # Construct the full file path (with .csv extension)
    csv_file_path = os.path.join(OUTPUT_FOLDER, filename + '.csv')

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return jsonify({'error': 'File not found.'}), 404

    # Read the CSV file and pass the content to the template
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # The first row will be the header
        rows = [row for row in reader]

    # Render the display_csv.html template and pass headers and rows
    return render_template('display_csv.html', headers=headers, rows=rows)

# Route for the homepage to list all CSV files in the output folder
@app.route('/')
def home():
    # List all the CSV files in the output folder and their modification times
    csv_files = [
        (f.replace('.csv', ''), os.path.getmtime(os.path.join(OUTPUT_FOLDER, f)))
        for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.csv')
    ]
    
    # Sort files by modification time (newest first)
    csv_files.sort(key=lambda x: x[1], reverse=True)

    # Extract only the file names after sorting
    sorted_files = [file[0] for file in csv_files]

    # Render the homepage with the list of sorted CSV files (without the .csv extension)
    return render_template('homepage.html', files=sorted_files)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
