#!/bin/bash

# STINGER V3 Data Pipeline Runner for Cron
# This script handles git operations and runs the data pipeline

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "STINGER V3 Automated Data Update"
echo "================================="
echo "Project directory: $PROJECT_DIR"
echo "Script directory: $SCRIPT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Git pull
echo "Step 1: Pulling latest changes..."
git pull origin main

# Step 2: Change to data pipeline directory
echo "Step 2: Entering data pipeline directory..."
cd data_pipeline

# Step 3: Activate virtual environment
echo "Step 3: Activating virtual environment..."
source venv/bin/activate

# Step 4: Run data pipeline
echo "Step 4: Running data pipeline..."
./data_pipeline.sh

# Step 5: Build project
echo "Step 5: Building project..."
cd "$PROJECT_DIR"
npm run build

# Step 6: Return to project root and add changes
echo "Step 6: Adding changes to git..."
git add .

# Step 7: Commit with timestamp
echo "Step 7: Committing changes..."
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "data update $timestamp"

# Step 8: Push changes
echo "Step 8: Pushing to remote..."
git push origin main

echo ""
echo "Automated data update completed successfully!"
echo "Timestamp: $timestamp"
