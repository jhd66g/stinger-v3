#!/usr/bin/env python3
"""
Fast Rotten Tomatoes ratings scraper with anti-ban measures
"""

import os
import json
import time
import re
import random
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

class FastRTScraper:
    def __init__(self, max_workers=12):
        self.max_workers = max_workers
        self.base_url = "https://www.rottentomatoes.com/m/"
        self.success_count = 0
        self.processed_count = 0
        self.lock = threading.Lock()
        
        # Enhanced anti-ban measures
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        
        # Enhanced session configuration
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.max_retries_per_url = 3
        
        # Session pool for better performance
        self.sessions = []
        self._create_sessions()
    
    def _create_sessions(self):
        """Create multiple sessions with different configurations"""
        for i in range(min(10, self.max_workers)):
            session = requests.Session()
            
            # Retry strategy
            retry_strategy = Retry(
                total=2,
                backoff_factor=0.1,
                status_forcelist=[403, 429, 500, 502, 503, 504]
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=10
            )
            
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            session.timeout = (3, 8)
            
            self.sessions.append(session)
    
    def _get_session_and_headers(self) -> tuple:
        """Get random session and headers for enhanced anti-detection"""
        session = random.choice(self.sessions)
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        return session, headers
    
    def _preprocess_title(self, title: str) -> str:
        """Convert title to RT URL format: lowercase, alphanumeric only, single underscores, no leading/trailing underscores"""
        # Remove year in parentheses first
        title_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        # Keep only alphanumeric and spaces
        title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title_clean)
        # Convert to lowercase and replace spaces with underscores
        title_clean = title_clean.lower().replace(' ', '_')
        # Remove multiple underscores
        title_clean = re.sub(r'_+', '_', title_clean)
        # Remove leading/trailing underscores
        title_clean = title_clean.strip('_')
        return title_clean
    
    def _generate_url_variants(self, title: str, year: int) -> List[str]:
        """Generate URL variants in priority order and randomize order for stealth"""
        base_title = self._preprocess_title(title)
        urls = [
            f"{self.base_url}{base_title}",
            f"{self.base_url}{base_title}_{year}"
        ]
        no_article = re.sub(r'^(the_|an_|a_)', '', base_title)
        if no_article != base_title:
            urls.extend([
                f"{self.base_url}{no_article}",
                f"{self.base_url}{no_article}_{year}"
            ])
        random.shuffle(urls)
        return urls
    
    def _extract_ratings(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract ratings from RT page"""
        tomatometer = 0
        audience = 0
        
        # Method 1: rt-text elements
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
        
        # Method 2: score-board attributes
        if not tomatometer or not audience:
            score_board = soup.find('score-board')
            if score_board:
                if not tomatometer and score_board.get('criticsscore'):
                    tomatometer = int(score_board.get('criticsscore', 0))
                if not audience and score_board.get('popcornmeter'):
                    audience = int(score_board.get('popcornmeter', 0))
        
        return {'tomatometer': tomatometer, 'audience': audience}
    
    def fetch_movie_ratings(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch ratings for a single movie with enhanced robustness and speed"""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        if not title or not year:
            return movie
        url_variants = self._generate_url_variants(title, year)
        for url in url_variants:
            for retry_attempt in range(5):
                try:
                    session, headers = self._get_session_and_headers()
                    # Increased random delay for stealth
                    time.sleep(random.uniform(0.1, 0.3))
                    if retry_attempt > 0:
                        delay = self.retry_delays[min(retry_attempt - 1, len(self.retry_delays) - 1)]
                        time.sleep(delay + random.uniform(0, 1))
                    response = session.get(url, headers=headers, timeout=(5, 15))
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        ratings = self._extract_ratings(soup)
                        if ratings['tomatometer'] > 0 or ratings['audience'] > 0:
                            if 'ratings' not in movie:
                                movie['ratings'] = {}
                            movie['ratings']['rt_tomatometer'] = ratings['tomatometer']
                            movie['ratings']['rt_audience'] = ratings['audience']
                            with self.lock:
                                self.success_count += 1
                            return movie
                    elif response.status_code == 403:
                        time.sleep(random.uniform(10, 30) * (retry_attempt + 1))
                        continue
                    elif response.status_code == 429:
                        time.sleep(random.uniform(20, 40) * (retry_attempt + 1))
                        continue
                    elif response.status_code in [404, 301]:
                        break
                    else:
                        time.sleep(random.uniform(1, 3))
                        continue
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    time.sleep(random.uniform(2, 5))
                    continue
                except Exception:
                    continue
        with self.lock:
            self.processed_count += 1
        return movie
    
    def process_movies(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process movies with high parallelization and progress bar"""
        print(f"🍅 Starting RT ratings fetch for {len(movies)} movies with {self.max_workers} workers...")
        
        start_time = time.time()
        results = []
        
        # Create progress bar
        progress_bar = tqdm(
            total=len(movies), 
            desc="🍅 Fetching RT ratings", 
            unit="movies",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_movie = {
                executor.submit(self.fetch_movie_ratings, movie): movie 
                for movie in movies
            }
            
            for future in as_completed(future_to_movie):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress bar
                    progress_bar.update(1)
                    elapsed = time.time() - start_time
                    rate = len(results) / elapsed if elapsed > 0 else 0
                    progress_bar.set_description(f"🍅 RT ratings ({self.success_count} found, {rate:.1f}/sec)")
                
                except Exception:
                    # Add original movie on error
                    original_movie = future_to_movie[future]
                    results.append(original_movie)
                    progress_bar.update(1)
        
        progress_bar.close()
        
        elapsed_time = time.time() - start_time
        success_rate = (self.success_count / len(movies)) * 100 if movies else 0
        print(f"\n✅ RT fetch complete: {elapsed_time:.1f}s")
        print(f"   Success: {self.success_count}/{len(movies)} movies ({success_rate:.1f}%)")
        print(f"   Rate: {len(movies)/elapsed_time:.1f} movies/sec")
        
        return results

def main():
    """Main function"""
    try:
        # Load TMDB data
        with open('tmdb_movies.json', 'r') as f:
            data = json.load(f)
        
        movies = data.get('movies', [])
        if not movies:
            print("No movies found")
            return
        
        # Process with RT scraper
        scraper = FastRTScraper(max_workers=50)
        updated_movies = scraper.process_movies(movies)
        
        # Save results
        data['movies'] = updated_movies
        data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open('tmdb_movies_with_ratings.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(updated_movies)} movies with RT ratings")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
