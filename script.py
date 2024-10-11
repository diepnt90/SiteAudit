import os
import pandas as pd
import json
import re
import sys
import requests
import time

# Function to get the current version from a .deps.json file
def find_current_version(module_name, deps_file):
    print(f"Searching for current version of module: {module_name} in {deps_file}")
    with open(deps_file, 'r') as f:
        data = json.load(f)
        targets = data.get('targets', {})
        for target_name, target_data in targets.items():
            for key, value in target_data.items():
                if 'runtime' in value and any(module_name in runtime_key for runtime_key in value['runtime']):
                    match = re.search(r'/([\d.]+)', key)
                    if match:
                        print(f"Found current version {match.group(1)} for module {module_name}")
                        return match.group(1)
                if 'compile' in value and any(module_name in compile_key for compile_key in value['compile']):
                    match = re.search(r'/([\d.]+)', key)
                    if match:
                        print(f"Found current version {match.group(1)} for module {module_name}")
                        return match.group(1)
    print(f"No current version found for module: {module_name}")
    return None

# Function to get the newest version from nuget.org API
def get_newest_version_nuget(link):
    print(f"Fetching newest version from NuGet API: {link}")
    try:
        response = requests.get(link)
        if response.status_code == 200:
            data = response.json()
            versions = data.get("versions", [])
            if versions:
                newest_version = versions[-1]
                print(f"Newest version from NuGet API: {newest_version}")
                return newest_version
    except Exception as e:
        print(f"Error fetching from nuget.org: {e}")
    return None

# Function to get the newest version from nuget.optimizely.com using regex
def get_newest_version_optimizely(link):
    print(f"Fetching newest version from Optimizely NuGet: {link}")
    try:
        response = requests.get(link)
        if response.status_code == 200:
            match = re.search(r"document\.title\s*=\s*'.*? (\d+\.\d+\.\d+)';", response.text)
            if match:
                newest_version = match.group(1)
                print(f"Newest version from Optimizely: {newest_version}")
                return newest_version
    except Exception as e:
        print(f"Error fetching from nuget.optimizely.com: {e}")
    return None

# Function to get the newest version from GitHub using regex
def get_newest_version_github(link):
    print(f"Fetching newest version from GitHub: {link}")
    try:
        response = requests.get(link)
        if response.status_code == 200:
            match = re.search(r'href=".*?/releases/tag/([\d.]+)"', response.text)
            if match:
                newest_version = match.group(1)
                print(f"Newest version from GitHub: {newest_version}")
                return newest_version
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
    return None

# Function to determine the source and fetch the newest version
def fetch_newest_version(link):
    if 'nuget.org' in link:
        return get_newest_version_nuget(link)
    elif 'optimizely' in link:
        return get_newest_version_optimizely(link)
    elif 'github.com' in link:
        return get_newest_version_github(link)
    else:
        print(f"Unknown link source: {link}")
        return None

# Function to update the current_version field in the CSV using the deps.json file
def update_current_version_in_csv(csv_path, deps_file):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_path)

    # Update the current_version for each module_name in the CSV
    for i, row in df.iterrows():
        module_name = row['module_name']
        current_version = find_current_version(module_name, deps_file)
        if current_version:
            df.at[i, 'current_version'] = current_version

    # Save the updated CSV back
    df.to_csv(csv_path, index=False)
    print(f"Updated current_version in CSV: {csv_path}")

# Function to update the newest_version field in the CSV using the link
def update_newest_version_in_csv(csv_path):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_path)

    # Update the newest_version for each link in the CSV
    for i, row in df.iterrows():
        link = row['links']
        
        # Ensure that the link is valid (i.e., not NaN and not empty)
        if pd.notna(link) and link.strip():
            newest_version = fetch_newest_version(link)
            if newest_version:
                df.at[i, 'newest_version'] = newest_version
        else:
            print(f"Skipping row {i} due to missing or empty link")

    # Save the updated CSV back
    df.to_csv(csv_path, index=False)
    print(f"Updated newest_version in CSV: {csv_path}")

# Function to download the CSV file from the provided GitHub URL with retry logic
def download_csv_from_github(github_url, output_filename, retries=3, timeout=10):
    print(f"Downloading CSV from {github_url}")
    attempts = 0
    while attempts < retries:
        try:
            response = requests.get(github_url, timeout=timeout)
            if response.status_code == 200:
                # Save the content to a file
                with open(output_filename, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded CSV file to {output_filename}")
                return
            else:
                print(f"Failed to download CSV (status code: {response.status_code}), retrying... ({attempts+1}/{retries})")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading CSV: {e}, retrying... ({attempts+1}/{retries})")
        attempts += 1
        time.sleep(2)  # Optional delay between retries

    print(f"Failed to download CSV after {retries} attempts.")
    sys.exit(1)

# Function to update the CSV file by comparing it with the downloaded CSV file
def update_csv(first_csv_path, second_csv_path, output_dir):
    # Load the CSV files into pandas DataFrames
    df1 = pd.read_csv(first_csv_path)
    df2 = pd.read_csv(second_csv_path)

    # Loop over the module_name in the first CSV
    for i, row in df1.iterrows():
        module_name = row['module_name']

        # Check if the module_name exists in the second CSV
        match = df2[df2['module_name'] == module_name]

        if not match.empty:
            # If exists, copy values of links, notes, tag from 2nd csv to 1st csv
            df1.at[i, 'links'] = match['links'].values[0]
            df1.at[i, 'notes'] = match['notes'].values[0]
            df1.at[i, 'tag'] = match['tag'].values[0]
        else:
            # If not exist, set its tag to 2
            df1.at[i, 'tag'] = 2

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Move the updated 1st CSV to ~/output
    output_path = os.path.join(output_dir, os.path.basename(first_csv_path))
    df1.to_csv(output_path, index=False)

    print(f"CSV file has been updated and moved to: {output_path}")
    return output_path

# Final function to process the CSV after all updates (remove tag=0, prioritize notes, and sort)
def finalize_csv(csv_path):
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # Remove rows where tag == 0
    df = df[df['tag'] != 0]

    # Ensure the 'notes' column is treated as strings, converting non-string values to an empty string if necessary
    df['notes'] = df['notes'].fillna('').astype(str)

    # Separate rows with non-empty 'notes'
    notes_non_empty = df[df['notes'].str.strip() != '']

    # Separate rows with empty 'notes' and sort by 'modified_date' in descending order
    notes_empty = df[df['notes'].str.strip() == '']
    notes_empty = notes_empty.sort_values(by='modified_date', ascending=False)

    # Concatenate the two DataFrames: first with non-empty notes, then sorted empty notes
    df_final = pd.concat([notes_non_empty, notes_empty])

    # Save the finalized CSV
    df_final.to_csv(csv_path, index=False)
    print(f"Finalized CSV has been saved at: {csv_path}")

# Move the final CSV to ~/outputcsv/
def move_to_outputcsv(csv_path):
    # Define the outputcsv directory
    outputcsv_dir = os.path.expanduser('~/outputcsv')

    # Ensure the directory exists
    if not os.path.exists(outputcsv_dir):
        os.makedirs(outputcsv_dir)

    # Define the destination path
    destination_path = os.path.join(outputcsv_dir, os.path.basename(csv_path))

    # Move the file
    os.rename(csv_path, destination_path)

    print(f"CSV file has been moved to: {destination_path}")

# Delete the deps.json file after processing
def delete_deps_json(deps_file_path):
    if os.path.exists(deps_file_path):
        os.remove(deps_file_path)
        print(f"Deleted deps.json file: {deps_file_path}")
    else:
        print(f"deps.json file not found: {deps_file_path}")

if __name__ == '__main__':
    # Check if enough arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_1st_csv> <path_to_deps.json>")
        sys.exit(1)

    # Get CSV path and deps.json path from command-line arguments
    first_csv_path = sys.argv[1]
    deps_file_path = sys.argv[2]

    # Download second CSV from GitHub with retry logic
    second_csv_path = "module.csv"
    github_url = "https://raw.githubusercontent.com/diepnt90/SiteAudit/main/module.csv"
    download_csv_from_github(github_url, second_csv_path)

    # Define the output directory (~/output)
    output_dir = os.path.expanduser('~/output')

    # Call the update_csv function
    updated_csv_path = update_csv(first_csv_path, second_csv_path, output_dir)

    # Now, update the current_version using the provided deps.json file
    update_current_version_in_csv(updated_csv_path, deps_file_path)

    # Update the newest_version using the links in the CSV
    update_newest_version_in_csv(updated_csv_path)

    # Finalize the CSV (remove tag=0, prioritize notes, sort by modified date)
    finalize_csv(updated_csv_path)

    # Move the final CSV to ~/outputcsv/
    move_to_outputcsv(updated_csv_path)

    # Delete the deps.json file after all processing is done
    delete_deps_json(deps_file_path)
