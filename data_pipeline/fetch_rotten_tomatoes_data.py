#!/usr/bin/env python3
"""
Fetch Rotten Tomatoes ratings data using the rottentomatoes-python library.
This script adds Tomatometer and Audience scores to the movie dataset.
"""

import os
import json
import time
from typing import Dict, List, Any
from dotenv import load_dotenv
from tqdm import tqdm
import rottentomatoes as rt
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
load_dotenv()

class RottenTomatoesDataFetcher:
    def __init__(self, max_workers=10):
        self.rate_limit_delay = 0.2  # 5 requests per second
        self.max_workers = max_workers
        self.movies_lock = threading.Lock()
    
    def search_movie(self, title: str, year: int) -> Dict[str, Any]:
        """Search for a movie on Rotten Tomatoes using the library."""
        try:
            # Try to get movie data using the library
            movie_data = rt.Movie(title)
            
            # Check if the year matches (within 1 year tolerance)
            movie_year = int(movie_data.year) if hasattr(movie_data, 'year') and movie_data.year else 0
            
            if abs(movie_year - year) <= 1:
                return {
                    "tomatometer": movie_data.tomatometer if hasattr(movie_data, 'tomatometer') else 0,
                    "audience": movie_data.audience_score if hasattr(movie_data, 'audience_score') else 0,
                    "title": movie_data.name if hasattr(movie_data, 'name') else title,
                    "year": movie_year
                }
            
            return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
            
        except Exception as e:
            print(f"Error searching for {title}: {e}")
            return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
    
    def search_movie_parallel(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Search for ratings for a single movie (for parallel execution)."""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        
        if title and year:
            ratings = self.search_movie(title, year)
            
            movie['ratings']['rt_tomatometer'] = ratings.get('tomatometer', 0)
            movie['ratings']['rt_audience'] = ratings.get('audience', 0)
        
        time.sleep(self.rate_limit_delay)
        return movie
    
    def update_movie_ratings(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update movie data with Rotten Tomatoes ratings using parallel processing."""
        print("Fetching Rotten Tomatoes ratings (parallel)...")
        
        # Use parallel processing for better performance
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for movie in movies:
                future = executor.submit(self.search_movie_parallel, movie)
                futures.append(future)
            
            # Progress bar for ratings fetching
            updated_movies = []
            with tqdm(total=len(futures), desc="Updating ratings") as pbar:
                for future in as_completed(futures):
                    try:
                        updated_movie = future.result()
                        updated_movies.append(updated_movie)
                    except Exception as e:
                        print(f"Error in ratings search: {e}")
                    pbar.update(1)
        
        return updated_movies

def main():
    """Main function to update movie data with Rotten Tomatoes ratings."""
    try:
        # Load existing TMDB data
        input_file = "tmdb_movies.json"
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found. Run fetch_tmdb_data.py first.")
            return 1
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        movies = data.get('movies', [])
        if not movies:
            print("No movies found in data.")
            return 1
        
        # Update with RT ratings
        fetcher = RottenTomatoesDataFetcher(max_workers=15)  # Increased parallel workers
        updated_movies = fetcher.update_movie_ratings(movies)
        
        # Save updated data
        data['movies'] = updated_movies
        data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        output_file = "tmdb_movies_with_ratings.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nUpdated data saved to {output_file}")
        print(f"Total movies: {len(updated_movies)}")
        
        # Count movies with ratings
        movies_with_ratings = sum(1 for m in updated_movies if m.get('ratings', {}).get('rt_tomatometer', 0) > 0)
        print(f"Movies with Rotten Tomatoes ratings: {movies_with_ratings}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
