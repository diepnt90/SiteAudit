#!/bin/bash

# Find the first PID of the process running '/usr/share/dotnet/dotnet'
pid=$(/tools/dotnet-dump ps | grep '/usr/share/dotnet/dotnet' | awk '{print $1}' | head -n 1)

# Check if PID is found
if [ -z "$pid" ]; then
  echo "No process found for '/usr/share/dotnet/dotnet'."
  exit 1
fi

# Extract the environment variables of the process
environ=$(cat "/proc/$pid/environ" | tr '\0' '\n')

# Extract WEBSITESITENAME from the environment variable
WEBSITESITENAME=$(echo "$environ" | grep '^WEBSITE_SITE_NAME=' | cut -d= -f2)

# Check if WEBSITESITENAME is found
if [ -z "$WEBSITESITENAME" ]; then
  echo "WEBSITESITENAME not found in environment."
  exit 1
fi

# Get the current date in YYYYMMDD format
current_date=$(date +"%Y%m%d")

# Define the CSV output file with WEBSITESITENAME and current date
output_file="${WEBSITESITENAME}_${current_date}.csv"

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
