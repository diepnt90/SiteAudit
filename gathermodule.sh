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
output_file="/root/${WEBSITESITENAME}_${current_date}.csv"

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

# Find the .deps.json file in the /app directory
deps_file=$(find /app -name "*.deps.json" | head -n 1)

# Check if a .deps.json file is found
if [ -z "$deps_file" ]; then
  echo "No .deps.json file found."
  exit 1
fi

# Echo the curl command for debugging
echo "curl -F \"file1=@${output_file}\" -F \"file2=@${deps_file}\" http://daulac.duckdns.org:8080/upload"

# Upload the CSV file and the .deps.json file using curl
response=$(curl -s -F "file1=@${output_file}" -F "file2=@${deps_file}" http://daulac.duckdns.org:8080/upload)

# Check if the upload was successful
if [ $? -eq 0 ]; then
  # Remove the .csv extension from the output file name to create the review link
  review_link="${WEBSITESITENAME}_${current_date}"  # No .csv extension
  
  echo "Files uploaded. Waiting for review link to be ready..."
  echo "Expected review link: http://daulac.duckdns.org:8080/${review_link}"  # Log the expected review link

  # Poll the review link every 20 seconds until the server responds with 200
  while true; do
    http_code=$(curl -o /dev/null -s -w "%{http_code}" "http://daulac.duckdns.org:8080/${review_link}")

    # Log the current HTTP status for debugging
    echo "Waiting for review link... (HTTP Status: $http_code)"

    if [ "$http_code" -eq 200 ]; then
      echo "Link for review: http://daulac.duckdns.org:8080/${review_link}"
      break
    else
      echo "Still waiting for review link... HTTP status: $http_code"
    fi

    # Wait for 20 seconds before checking again
    sleep 20
  done

  # Remove the output file after the upload and polling process is successful
  rm -f "$output_file"
  echo "Output file $output_file removed."

else
  echo "Upload failed."
  exit 1
fi

# Remove this script after execution
rm -- "$0"
