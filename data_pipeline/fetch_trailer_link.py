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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

class TrailerLinkFetcher:
    def __init__(self, max_workers=10):
        self.rate_limit_delay = 0.05  # 20 requests per second (optimized)
        self.max_workers = max_workers
        self.last_request_time = 0
        self.min_request_interval = 0.05
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.current_ua_index = 0
    
    def _rate_limit(self):
        """Rate limiting for requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_headers(self):
        """Get headers with user agent rotation."""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return {
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    def search_trailer(self, title: str, year: int) -> Optional[str]:
        """Search for a movie trailer on YouTube using web scraping."""
        try:
            # Create search query
            search_query = f"{title} {year} official trailer"
            encoded_query = quote_plus(search_query)
            
            # YouTube search URL
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"  # Filter for videos
            
            # Use rate limiting and fresh headers
            self._rate_limit()
            headers = self._get_headers()
            
            # Get search results page
            response = self.session.get(search_url, headers=headers, timeout=(5, 10))
            response.raise_for_status()
            
            # Extract video IDs from the page
            video_ids = self._extract_video_ids(response.text)
            
            if video_ids:
                # Return the first (most relevant) video
                video_id = video_ids[0]
                return f"https://www.youtube.com/watch?v={video_id}"
            
            return None
            
        except requests.exceptions.RequestException as e:
            # Silent error handling for speed
            return None
        except Exception as e:
            # Silent error handling for speed
            return None
    
    def _extract_video_ids(self, html_content: str) -> List[str]:
        """Extract YouTube video IDs from HTML content, avoiding ads."""
        # Look for video renderer objects (actual videos, not ads)
        # Ads are typically in "adSlotRenderer" while videos are in "videoRenderer"
        video_renderer_pattern = r'"videoRenderer".*?"videoId":"([a-zA-Z0-9_-]{11})"'
        matches = re.findall(video_renderer_pattern, html_content)
        
        if matches:
            return matches[:5]  # Return top 5 video results
        
        # Fallback patterns if videoRenderer pattern doesn't work
        fallback_patterns = [
            r'watch\?v=([a-zA-Z0-9_-]{11})',
            r'/watch\?v=([a-zA-Z0-9_-]{11})',
            r'embed/([a-zA-Z0-9_-]{11})'
        ]
        
        video_ids = []
        for pattern in fallback_patterns:
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
        
        # Remove the separate sleep since we have rate limiting in _rate_limit()
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
