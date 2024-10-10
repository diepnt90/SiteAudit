import os
import pandas as pd
import json
import re
import sys
import requests

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

# Function to find any .deps.json file in the given directory
def find_deps_json(upload_dir):
    for file in os.listdir(upload_dir):
        if file.endswith('.deps.json'):
            return os.path.join(upload_dir, file)
    print("No .deps.json file found in the directory")
    sys.exit(1)

# Function to update the CSV file by comparing it with another CSV file
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

if __name__ == '__main__':
    # Check if enough arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_1st_csv> <path_to_2nd_csv>")
        sys.exit(1)

    # Get CSV paths from command-line arguments
    first_csv_path = sys.argv[1]
    second_csv_path = sys.argv[2]

    # Define the output directory (~/output)
    output_dir = os.path.expanduser('~/output')

    # Call the update_csv function
    updated_csv_path = update_csv(first_csv_path, second_csv_path, output_dir)

    # Find the correct .deps.json file in the ~/upload directory
    upload_dir = os.path.expanduser('~/upload')
    deps_file_path = find_deps_json(upload_dir)

    # Now, update the current_version using the found deps.json file
    update_current_version_in_csv(updated_csv_path, deps_file_path)

    # Finally, update the newest_version using the links in the CSV
    update_newest_version_in_csv(updated_csv_path)
