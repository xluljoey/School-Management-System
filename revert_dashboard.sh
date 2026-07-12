#!/bin/bash

# Dashboard Revert Script
# This script allows you to revert the dashboard changes if needed

echo "Dashboard Revert Script"
echo "======================"
echo ""
echo "Current status:"
git status sis/templates/sis/dashboard.html
echo ""

read -p "Do you want to revert to the backup version? (y/n) " choice
case "$choice" in
  y|Y )
    echo "Reverting to backup..."
    cp sis/templates/sis/dashboard.html.backup sis/templates/sis/dashboard.html
    echo "Dashboard reverted successfully!"
    echo ""
    echo "You can restore the new design later with:"
    echo "git checkout sis/templates/sis/dashboard.html"
    ;;
  n|N )
    echo "No changes made. Keeping current dashboard design."
    ;;
  * )
    echo "Invalid choice. No changes made."
    ;;
esac