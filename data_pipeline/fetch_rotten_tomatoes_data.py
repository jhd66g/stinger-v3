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
    def __init__(self, max_workers=20):  # Reduced from 100 to 20 workers to avoid detection
        self.rate_limit_delay = 0.05  # Faster rate like streamlined fetcher
        self.max_workers = max_workers
        self.movies_lock = threading.Lock()
        self.processed_count = 0
        self.success_count = 0
        self.last_request_time = 0
        self.min_request_interval = 0.05  # Slower rate to avoid detection (was 0.01)
        self.timeout = (5, 10)  # Longer timeout to appear more human
        
        # Create session with retry strategy like streamlined fetcher
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Reduced from 3 to 2 retries
            backoff_factor=0.3,  # Faster backoff from 0.5
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # More realistic user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        self.current_ua_index = 0
    
    def _rate_limit(self):
        """Simple rate limiting like streamlined fetcher."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def process_movie_batch(self, movies_batch):
        """Process a batch of movies for RT ratings."""
        results = []
        for movie in movies_batch:
            try:
                title = movie.get('title', '')
                year = movie.get('release_year', 0)
                
                if title and year:
                    rt_data = self.search_movie(title, year)
                    if rt_data.get('tomatometer', 0) > 0 or rt_data.get('audience', 0) > 0:
                        movie['ratings']['rt_tomatometer'] = rt_data.get('tomatometer', 0)
                        movie['ratings']['rt_audience'] = rt_data.get('audience', 0)
                        
                        with self.movies_lock:
                            self.success_count += 1
                
                results.append(movie)
                
            except Exception as e:
                print(f"Error processing {movie.get('title', 'Unknown')}: {e}")
                results.append(movie)
        
        return results
    
    def _get_headers(self):
        """Rotate user agents and return fresh headers with better anti-detection."""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return {
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    def search_movie(self, title: str, year: int) -> Dict[str, Any]:
        """Search for a movie on Rotten Tomatoes using web scraping - streamlined for speed."""
        try:
            # Handle special character titles like #Alive
            if title.startswith('#'):
                # Try without the # symbol
                clean_title = title[1:].strip()
                url_title = clean_title.lower().replace(' ', '_')
                possible_urls = [
                    f"https://www.rottentomatoes.com/m/{url_title}_{year}",
                    f"https://www.rottentomatoes.com/m/{url_title}",
                    f"https://www.rottentomatoes.com/m/number_{url_title}_{year}",
                    f"https://www.rottentomatoes.com/m/hashtag_{url_title}_{year}"
                ]
            # Skip other problematic characters  
            elif any(char in title for char in ['@']):
                return {"tomatometer": 0, "audience": 0, "title": "", "year": 0}
            else:
                # Basic URL formatting
                clean_title = re.sub(r'[^\w\s-]', '', title).strip()
                url_title = re.sub(r'\s+', '_', clean_title.lower())
                url_title_no_articles = re.sub(r'^(the_|a_|an_)', '', url_title)
                
                # Streamlined URL patterns - prioritize most successful first
                possible_urls = [
                    # Top 3 patterns work for 80%+ of movies
                    f"https://www.rottentomatoes.com/m/{url_title_no_articles}_{year}",
                    f"https://www.rottentomatoes.com/m/{url_title}_{year}",
                    f"https://www.rottentomatoes.com/m/{re.sub(r'[^\w]', '', title.lower())}_{year}",
                    # Fallbacks without year
                    f"https://www.rottentomatoes.com/m/{url_title_no_articles}",
                    f"https://www.rottentomatoes.com/m/{url_title}",
                ]
                
                # If title has punctuation, try version with all punctuation removed (including hyphens)
                if re.search(r'[^\w\s]', title):
                    # Remove year first, then all punctuation including hyphens
                    title_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
                    no_punct_title = re.sub(r'[^\w\s]', '', title_no_year.lower()).replace(' ', '_')
                    possible_urls.extend([
                        f"https://www.rottentomatoes.com/m/{no_punct_title}_{year}",
                        f"https://www.rottentomatoes.com/m/{no_punct_title}"
                    ])
            
            # Remove None values and duplicates
            possible_urls = list(dict.fromkeys([url for url in possible_urls if url]))
            
            for url in possible_urls:
                try:
                    # Use rate limiting like TMDB fetcher
                    self._rate_limit()
                    
                    # Use fresh headers for each request
                    headers = self._get_headers()
                    response = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Optimized parsing - check most common patterns first
                        tomatometer = 0
                        audience = 0
                        
                        # Primary strategy: rt-text elements (fastest and most common)
                        critics_elem = soup.find('rt-text', {'slot': 'criticsScore'})
                        if critics_elem:
                            match = re.search(r'(\d+)', critics_elem.get_text())
                            if match:
                                tomatometer = int(match.group(1))
                        
                        audience_elem = soup.find('rt-text', {'slot': 'audienceScore'})
                        if audience_elem:
                            match = re.search(r'(\d+)', audience_elem.get_text())
                            if match:
                                audience = int(match.group(1))
                        
                        # Quick fallback: score-board attributes
                        if tomatometer == 0 or audience == 0:
                            score_board = soup.find('score-board')
                            if score_board:
                                if tomatometer == 0 and score_board.get('criticsscore'):
                                    tomatometer = int(score_board.get('criticsscore', 0))
                                if audience == 0 and score_board.get('popcornmeter'):
                                    audience = int(score_board.get('popcornmeter', 0))
                        
                        # Return immediately if we found scores
                        if tomatometer > 0 or audience > 0:
                            return {
                                "tomatometer": tomatometer,
                                "audience": audience,
                                "title": title,
                                "year": year
                            }
                    
                    elif response.status_code == 403:
                        # Access denied - longer backoff and rotate user agent
                        print(f"Access denied for {url}, backing off...")
                        time.sleep(5)
                        continue
                    elif response.status_code == 429:
                        # Rate limited - longer backoff
                        print(f"Rate limited, backing off...")
                        time.sleep(10)
                        continue
                    elif response.status_code == 404:
                        # Not found - try next URL pattern
                        continue
                
                except requests.RequestException as e:
                    # Network error backoff
                    time.sleep(1)
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
        """Update movie data with Rotten Tomatoes ratings using individual movie processing."""
        start_time = time.time()
        print(f"🍅 Starting Rotten Tomatoes ratings fetch for {len(movies)} movies...")
        print(f"   Using {self.max_workers} parallel workers")
        
        # Process movies individually for better progress tracking
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all movies as individual tasks
            future_to_movie = {
                executor.submit(self.search_movie_individual, movie): movie 
                for movie in movies
            }
            
            progress_bar = tqdm(total=len(movies), desc="🍅 Fetching RT ratings", unit="movies")
            
            for future in as_completed(future_to_movie):
                movie = future_to_movie[future]
                
                try:
                    updated_movie = future.result()
                    all_results.append(updated_movie)
                    
                    # Update progress immediately for each completed movie
                    progress_bar.update(1)
                    
                    elapsed_time = time.time() - start_time
                    rate = len(all_results) / elapsed_time if elapsed_time > 0 else 0
                    progress_bar.set_description(f"🍅 Fetching RT ratings ({rate:.1f} movies/sec)")
                    
                except Exception as e:
                    # Add the original movie on error
                    all_results.append(movie)
                    progress_bar.update(1)
            
            progress_bar.close()
        
        # Final stats
        elapsed_time = time.time() - start_time
        rate = len(all_results) / elapsed_time
        
        print(f"\n🍅 ROTTEN TOMATOES RATINGS FETCH COMPLETE")
        print(f"   Total time: {elapsed_time:.1f} seconds")
        print(f"   Rate: {rate:.1f} movies per second")
        print(f"   Total processed: {len(all_results)}")
        print(f"   Successfully found ratings: {self.success_count}")
        print(f"   Success rate: {self.success_count/len(all_results)*100:.1f}%")
        
        return all_results
    
    def search_movie_individual(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Search for ratings for a single movie (optimized for individual processing)."""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        
        if title and year:
            ratings = self.search_movie(title, year)
            
            if ratings.get('tomatometer', 0) > 0 or ratings.get('audience', 0) > 0:
                movie['ratings']['rt_tomatometer'] = ratings.get('tomatometer', 0)
                movie['ratings']['rt_audience'] = ratings.get('audience', 0)
                
                with self.movies_lock:
                    self.success_count += 1
        
        return movie

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
        
        print(f"Processing {len(movies)} movies...")
        
        # Update with Rotten Tomatoes ratings using streamlined approach
        fetcher = RottenTomatoesDataFetcher(max_workers=20)  # Reduced workers to avoid detection
        updated_movies = fetcher.update_movie_ratings(movies)
        
        # Save updated data
        data['movies'] = updated_movies
        data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        output_file = "tmdb_movies_with_ratings.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData with Rotten Tomatoes ratings saved to {output_file}")
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
