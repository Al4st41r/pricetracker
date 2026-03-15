#!/bin/bash

# Create a backup of the application files
zip -r /home/pi/WebApps/pricetracker/backup/$(date +%F).zip /home/pi/WebApps/pricetracker -x /home/pi/WebApps/pricetracker/backup/\*
zip -r /home/pi/WebApps/pricetracker/backup/$(date +%F).zip /var/www/html/pricetracker

# Get the current version
CURRENT_VERSION=$(grep -o 'Version: [0-9.]*' /home/pi/WebApps/pricetracker/gemini.md | awk '{print $2}')

echo "Current version: $CURRENT_VERSION"

# Get the new version from the first argument
NEW_VERSION=$1

# If no version is provided, ask for it
if [ -z "$NEW_VERSION" ]; then
    read -p "Enter the new version number: " NEW_VERSION
fi

# Update the version in gemini.md
sed -i "s/Version: $CURRENT_VERSION/Version: $NEW_VERSION/g" /home/pi/WebApps/pricetracker/gemini.md
sed -i "s/Version: $CURRENT_VERSION/Version: $NEW_VERSION/g" /home/pi/WebApps/pricetracker/templates/index.html
