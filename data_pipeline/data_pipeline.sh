#!/bin/bash

# STINGER V3 Data Pipeline Orchestrator
# This script runs all data collection steps in order to build the final movie_data.json
# Now with highly parallelized processing for better performance

set -e  # Exit on any error

echo "STINGER V3 Data Pipeline (Parallelized)"
echo "=========================================="


# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your TMDB API key."
    echo "   Copy env.example to .env and add your TMDB_BEARER_TOKEN"
    echo "   Note: Rotten Tomatoes and YouTube use web scraping (no API keys needed)"
fi

# Step 1: Fetch TMDB data (parallelized)
echo ""
echo "Step 1: Fetching TMDB movie data (parallelized)..."
python fetch_tmdb_data.py

if [ ! -f "tmdb_movies.json" ]; then
    echo "❌ Error: tmdb_movies.json was not created"
    exit 1
fi

# Step 2: Add Rotten Tomatoes ratings (using rottentomatoes-python library)
echo ""
echo "Step 2: Adding Rotten Tomatoes ratings (web scraping)..."
python fetch_rotten_tomatoes_data.py
if [ -f "tmdb_movies_with_ratings.json" ]; then
    echo "✅ Rotten Tomatoes ratings added via web scraping"
else
    echo "⚠️  Rotten Tomatoes data not available, continuing with TMDB data only"
    cp tmdb_movies.json tmdb_movies_with_ratings.json
fi

# Step 3: Add YouTube trailer links (web scraping, no API key needed)
echo ""
echo "Step 3: Adding YouTube trailer links (web scraping)..."
python fetch_trailer_link.py
if [ -f "movie_data.json" ]; then
    echo "✅ YouTube trailer links added via web scraping"
else
    echo "⚠️  YouTube data not available, continuing without trailers"
    # Create final movie_data.json from TMDB data
    if [ -f "tmdb_movies_with_ratings.json" ]; then
        cp tmdb_movies_with_ratings.json movie_data.json
    else
        cp tmdb_movies.json movie_data.json
    fi
fi

# Step 4: Validate and finalize
echo ""
echo "Step 4: Validating final dataset..."

if [ -f "movie_data.json" ]; then
    # Count movies
    movie_count=$(python -c "import json; data=json.load(open('movie_data.json')); print(len(data.get('movies', [])))")
    echo "✅ Final dataset created: $movie_count movies"
    
    # Count movies with ratings
    movies_with_ratings=$(python -c "import json; data=json.load(open('movie_data.json')); print(sum(1 for m in data.get('movies', []) if m.get('ratings', {}).get('rt_tomatometer', 0) > 0))")
    echo "Movies with Rotten Tomatoes ratings: $movies_with_ratings"
    
    # Count movies with trailers
    movies_with_trailers=$(python -c "import json; data=json.load(open('movie_data.json')); print(sum(1 for m in data.get('movies', []) if m.get('media', {}).get('trailer_youtube')))")
    echo "Movies with trailers: $movies_with_trailers"
    
    # Copy to public directory for web app
    echo "Copying to public directory..."
    cp movie_data.json ../public/movie_data.json
    
    echo ""
    echo "Data pipeline completed successfully!"
    echo "Dataset: $movie_count movies"
    echo "Ratings: $movies_with_ratings movies"
    echo "Trailers: $movies_with_trailers movies"
    echo "Output: public/movie_data.json"
    
else
    echo "❌ Error: movie_data.json was not created"
    exit 1
fi

# Deactivate virtual environment
deactivate

echo ""
echo "Pipeline complete!"
