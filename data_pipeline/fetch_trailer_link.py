#!/usr/bin/env python3
"""
Fetch YouTube trailer links for movies using web scraping.
This script searches YouTube directly for official trailers and adds the links to movie data.
"""

import os
import json
import time
import requests
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

class TrailerLinkFetcher:
    def __init__(self, max_workers=10):
        self.rate_limit_delay = 0.2  # 5 requests per second
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_trailer(self, title: str, year: int) -> Optional[str]:
        """Search for a movie trailer on YouTube using web scraping."""
        try:
            # Create search query
            search_query = f"{title} {year} official trailer"
            encoded_query = quote_plus(search_query)
            
            # YouTube search URL
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"  # Filter for videos
            
            # Get search results page
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Extract video IDs from the page
            video_ids = self._extract_video_ids(response.text)
            
            if video_ids:
                # Return the first (most relevant) video
                video_id = video_ids[0]
                return f"https://www.youtube.com/watch?v={video_id}"
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching for trailer for {title}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for {title}: {e}")
            return None
    
    def _extract_video_ids(self, html_content: str) -> List[str]:
        """Extract YouTube video IDs from HTML content."""
        # Multiple patterns to try for extracting video IDs
        patterns = [
            r'"videoId":"([a-zA-Z0-9_-]{11})"',
            r'watch\?v=([a-zA-Z0-9_-]{11})',
            r'/watch\?v=([a-zA-Z0-9_-]{11})',
            r'embed/([a-zA-Z0-9_-]{11})',
            r'data-video-id="([a-zA-Z0-9_-]{11})"'
        ]
        
        video_ids = []
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            video_ids.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_video_ids = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                unique_video_ids.append(vid)
        
        return unique_video_ids[:5]  # Return top 5 results
    
    def search_trailer_parallel(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Search for trailer for a single movie (for parallel execution)."""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        
        if title and year:
            trailer_link = self.search_trailer(title, year)
            if trailer_link:
                movie['media']['trailer_youtube'] = trailer_link
        
        time.sleep(self.rate_limit_delay)
        return movie
    
    def update_movie_trailers(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update movie data with YouTube trailer links using parallel processing."""
        print("Fetching YouTube trailer links (parallel)...")
        
        # Use parallel processing for better performance
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for movie in movies:
                future = executor.submit(self.search_trailer_parallel, movie)
                futures.append(future)
            
            # Progress bar for trailer fetching
            updated_movies = []
            with tqdm(total=len(futures), desc="Adding trailers") as pbar:
                for future in as_completed(futures):
                    try:
                        updated_movie = future.result()
                        updated_movies.append(updated_movie)
                    except Exception as e:
                        print(f"Error in trailer search: {e}")
                    pbar.update(1)
        
        return updated_movies

def main():
    """Main function to update movie data with trailer links."""
    try:
        # Load existing movie data
        input_file = "tmdb_movies_with_ratings.json"
        if not os.path.exists(input_file):
            # Try the original TMDB file if ratings file doesn't exist
            input_file = "tmdb_movies.json"
            if not os.path.exists(input_file):
                print(f"Error: No movie data file found. Run fetch_tmdb_data.py first.")
                return 1
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        movies = data.get('movies', [])
        if not movies:
            print("No movies found in data.")
            return 1
        
        # Update with trailer links
        fetcher = TrailerLinkFetcher(max_workers=15)  # Increased parallel workers
        updated_movies = fetcher.update_movie_trailers(movies)
        
        # Save updated data
        data['movies'] = updated_movies
        data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        output_file = "movie_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nFinal data saved to {output_file}")
        print(f"Total movies: {len(updated_movies)}")
        
        # Count movies with trailers
        movies_with_trailers = sum(1 for m in updated_movies if m.get('media', {}).get('trailer_youtube'))
        print(f"Movies with trailers: {movies_with_trailers}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
