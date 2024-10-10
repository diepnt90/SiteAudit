#!/bin/bash

# Define the CSV output file
output_file="dll_info.csv"

# Create or overwrite the CSV file with headers
echo "module_name,modified_date,current_version,newest_version,tag,links,notes" > "$output_file"

# Traverse the /app directory and find all .dll files
find /app -name "*.dll" | while read -r dll_file; do
    # Get the filename
    module_name=$(basename "$dll_file")
    
    # Get the modified date using stat and format it to YYYY-MM-DD HH:MM
    modified_date=$(stat --format="%y" "$dll_file" | cut -d'.' -f1 | cut -d':' -f1,2)
    
    # Placeholder for other columns (current_version, newest_version, tag, links, notes)
    current_version=""
    newest_version=""
    tag=""
    links=""
    notes=""

    # Append the information to the CSV
    echo "$module_name,$modified_date,$current_version,$newest_version,$tag,$links,$notes" >> "$output_file"
done

echo "CSV file created: $output_file"

# Remove this script after execution
rm -- "$0"
