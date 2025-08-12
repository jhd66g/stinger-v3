#!/usr/bin/env python3
"""
Fetch Rotten Tomatoes ratings data using web scraping.
This script adds Tomatometer and Audience scores to the movie dataset.
"""

import os
import json
import time
import re
import urllib.parse
from typing import Dict, List, Any
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

class RottenTomatoesDataFetcher:
    def __init__(self, max_workers=10):  # Reduced workers to avoid overwhelming RT
        self.rate_limit_delay = 0.1  # Minimal delay for speed
        self.max_workers = max_workers
        self.movies_lock = threading.Lock()
        self.processed_count = 0
        self.success_count = 0
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 20 requests per second max
        
        # Create session with retry strategy like TMDB fetcher
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
        """Simple rate limiting like TMDB fetcher."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_headers(self):
        """Rotate user agents and return fresh headers."""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return {
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
    
    def search_movie(self, title: str, year: int) -> Dict[str, Any]:
        """Search for a movie on Rotten Tomatoes using web scraping."""
        try:
            # Skip movies with only the most problematic characters
            if any(char in title for char in ['#', '@']):
                return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
            
            # Clean and format title for URL - more comprehensive patterns
            clean_title = re.sub(r'[^\w\s-]', '', title).strip()
            url_title = re.sub(r'\s+', '_', clean_title.lower())
            
            # Try comprehensive URL patterns for Rotten Tomatoes
            possible_urls = [
                f"https://www.rottentomatoes.com/m/{url_title}",
                f"https://www.rottentomatoes.com/m/{url_title}_{year}",
                f"https://www.rottentomatoes.com/m/{url_title.replace('_', '')}",
                f"https://www.rottentomatoes.com/m/{url_title.replace('_', '-')}",
                f"https://www.rottentomatoes.com/m/{url_title.replace('_the_', '_')}",
                f"https://www.rottentomatoes.com/m/{url_title.replace('_a_', '_')}",
                f"https://www.rottentomatoes.com/m/{re.sub(r'_the_|_a_|_an_', '_', url_title)}",
                f"https://www.rottentomatoes.com/m/{url_title.replace('_', '')}_{year}",
                f"https://www.rottentomatoes.com/m/{title.lower().replace(' ', '_').replace(':', '').replace("'", '')}",
                f"https://www.rottentomatoes.com/m/{title.lower().replace(' ', '').replace(':', '').replace("'", '')}"
            ]
            
            for url in possible_urls:
                try:
                    # Use rate limiting like TMDB fetcher
                    self._rate_limit()
                    
                    # Use fresh headers for each request
                    headers = self._get_headers()
                    response = self.session.get(url, headers=headers, timeout=(5, 10), allow_redirects=True)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Multiple strategies to extract scores
                        tomatometer = 0
                        audience = 0
                        
                        # Strategy 1: Look for rt-text elements with specific slot attributes (current RT design)
                        critics_elem = soup.find('rt-text', {'slot': 'criticsScore'})
                        if critics_elem:
                            text = critics_elem.get_text().strip()
                            match = re.search(r'(\d+)', text)
                            if match:
                                tomatometer = int(match.group(1))
                        
                        audience_elem = soup.find('rt-text', {'slot': 'audienceScore'})
                        if audience_elem:
                            text = audience_elem.get_text().strip()
                            match = re.search(r'(\d+)', text)
                            if match:
                                audience = int(match.group(1))
                        
                        # Strategy 2: Look for score-board element (fallback)
                        if tomatometer == 0 or audience == 0:
                            score_board = soup.find('score-board')
                            if score_board:
                                if tomatometer == 0:
                                    critics_score = score_board.get('criticsscore')
                                    if critics_score and critics_score.isdigit():
                                        tomatometer = int(critics_score)
                                if audience == 0:
                                    popcorn_score = score_board.get('popcornmeter')
                                    if popcorn_score and popcorn_score.isdigit():
                                        audience = int(popcorn_score)
                        
                        # Strategy 2: Look for percentage in text content
                        if tomatometer == 0 or audience == 0:
                            # Look for tomatometer percentage
                            tomato_elements = soup.find_all(string=re.compile(r'\d+%'))
                            for elem in tomato_elements:
                                if 'tomatometer' in elem.parent.get_text().lower() or 'critics' in elem.parent.get_text().lower():
                                    match = re.search(r'(\d+)%', elem)
                                    if match and tomatometer == 0:
                                        tomatometer = int(match.group(1))
                                elif 'audience' in elem.parent.get_text().lower() or 'popcorn' in elem.parent.get_text().lower():
                                    match = re.search(r'(\d+)%', elem)
                                    if match and audience == 0:
                                        audience = int(match.group(1))
                        
                        # Strategy 3: Look for specific CSS classes or data attributes
                        if tomatometer == 0:
                            tomato_elem = soup.find(attrs={'data-qa': 'tomatometer'}) or soup.find(class_=re.compile(r'.*tomato.*', re.I))
                            if tomato_elem:
                                text = tomato_elem.get_text()
                                match = re.search(r'(\d+)', text)
                                if match:
                                    tomatometer = int(match.group(1))
                        
                        if audience == 0:
                            audience_elem = soup.find(attrs={'data-qa': 'audience-score'}) or soup.find(class_=re.compile(r'.*audience.*', re.I))
                            if audience_elem:
                                text = audience_elem.get_text()
                                match = re.search(r'(\d+)', text)
                                if match:
                                    audience = int(match.group(1))
                        
                        # If we found any scores, return them
                        if tomatometer > 0 or audience > 0:
                            return {
                                "tomatometer": tomatometer,
                                "audience": audience,
                                "title": title,
                                "year": year
                            }
                    
                    elif response.status_code == 403:
                        # Access denied - back off longer and try with different user agent
                        time.sleep(2)
                        continue  # Try next URL instead of breaking
                    elif response.status_code == 404:
                        # Not found - try next URL pattern
                        continue
                
                except requests.RequestException as e:
                    # For network errors, retry with backoff
                    time.sleep(0.5)
                    continue
            
            return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
            
        except Exception as e:
            # Silent error handling for speed
            return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
    
    def search_movie_parallel(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Search for ratings for a single movie (for parallel execution)."""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        
        if title and year:
            ratings = self.search_movie(title, year)
            
            movie['ratings']['rt_tomatometer'] = ratings.get('tomatometer', 0)
            movie['ratings']['rt_audience'] = ratings.get('audience', 0)
            
            with self.movies_lock:
                self.processed_count += 1
                if ratings.get('tomatometer', 0) > 0:
                    self.success_count += 1
                
                # Print progress every 100 movies
                if self.processed_count % 100 == 0:
                    print(f"Processed {self.processed_count} movies, {self.success_count} with ratings")
        
        # Remove the extra delay in parallel processing for speed
        return movie
    
    def update_movie_ratings(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update movie data with Rotten Tomatoes ratings using parallel processing."""
        print("Fetching Rotten Tomatoes ratings (web scraping)...")
        
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
        fetcher = RottenTomatoesDataFetcher(max_workers=10)  # Optimized worker count
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
