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

class FastRTScraper:
    def __init__(self, max_workers=50):
        self.max_workers = max_workers
        self.base_url = "https://www.rottentomatoes.com/m/"
        self.success_count = 0
        self.processed_count = 0
        self.lock = threading.Lock()
        
        # Anti-ban measures
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ]
        
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
        """Get random session and headers for anti-detection"""
        session = random.choice(self.sessions)
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        return session, headers
    
    def _preprocess_title(self, title: str) -> str:
        """Convert title to RT URL format: lowercase, alphanumeric only, spaces to underscores"""
        # Remove year in parentheses first
        title_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        # Replace colons and other punctuation with spaces first, then clean
        title_clean = re.sub(r'[^\w\s]', ' ', title_clean)
        # Normalize multiple spaces to single spaces
        title_clean = re.sub(r'\s+', ' ', title_clean).strip()
        # Convert to lowercase and replace spaces with underscores
        return title_clean.lower().replace(' ', '_')
    
    def _generate_url_variants(self, title: str, year: int) -> List[str]:
        """Generate URL variants in priority order"""
        base_title = self._preprocess_title(title)
        urls = []
        
        # 1. Base title without year
        urls.append(f"{self.base_url}{base_title}")
        
        # 2. Base title with year
        urls.append(f"{self.base_url}{base_title}_{year}")
        
        # 3. Remove leading articles and test
        no_article = re.sub(r'^(the_|an_|a_)', '', base_title)
        if no_article != base_title:
            urls.append(f"{self.base_url}{no_article}")
            urls.append(f"{self.base_url}{no_article}_{year}")
        
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
        """Fetch ratings for a single movie"""
        title = movie.get('title', '')
        year = movie.get('release_year', 0)
        
        if not title or not year:
            return movie
        
        # Generate URL variants
        url_variants = self._generate_url_variants(title, year)
        
        for url in url_variants:
            try:
                session, headers = self._get_session_and_headers()
                
                # Random delay for anti-detection
                time.sleep(random.uniform(0.01, 0.05))
                
                response = session.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    ratings = self._extract_ratings(soup)
                    
                    if ratings['tomatometer'] > 0 or ratings['audience'] > 0:
                        # Add ratings to movie
                        if 'ratings' not in movie:
                            movie['ratings'] = {}
                        movie['ratings']['rt_tomatometer'] = ratings['tomatometer']
                        movie['ratings']['rt_audience'] = ratings['audience']
                        
                        with self.lock:
                            self.success_count += 1
                        
                        # Found ratings, no need to try other URLs
                        break
                
                elif response.status_code == 403:
                    # Rate limited - longer delay
                    time.sleep(random.uniform(2, 5))
                    continue
                elif response.status_code in [404, 301]:
                    # Not found or redirect - try next URL
                    continue
                
            except Exception:
                # Silent error handling for speed
                continue
        
        with self.lock:
            self.processed_count += 1
        
        return movie
    
    def process_movies(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process movies with high parallelization"""
        print(f"🍅 Starting RT ratings fetch for {len(movies)} movies with {self.max_workers} workers...")
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_movie = {
                executor.submit(self.fetch_movie_ratings, movie): movie 
                for movie in movies
            }
            
            for future in as_completed(future_to_movie):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Progress update
                    if len(results) % 50 == 0:
                        elapsed = time.time() - start_time
                        rate = len(results) / elapsed
                        print(f"   Processed {len(results)}/{len(movies)} movies ({rate:.1f}/sec, {self.success_count} found)")
                
                except Exception:
                    # Add original movie on error
                    original_movie = future_to_movie[future]
                    results.append(original_movie)
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ RT fetch complete: {elapsed_time:.1f}s, {self.success_count}/{len(movies)} movies found ratings")
        
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
