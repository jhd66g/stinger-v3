#!/usr/bin/env python3
"""
Fetch YouTube trailer links for movies by manually scraping YouTube search results.
This script searches YouTube for movie trailers using web scraping with parallelization.
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from tqdm import tqdm
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

# Load environment variables
load_dotenv()

class TrailerLinkFetcher:
    def __init__(self, max_workers=20):
        self.max_workers = max_workers
        self.rate_limit_delay = 0.05  # 20 requests per second
        self.last_request_time = 0
        self.min_request_interval = 0.05
        self.success_count = 0
        self.movies_lock = threading.Lock()
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # User agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.current_ua_index = 0
    
    def _rate_limit(self):
        """Simple rate limiting."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_next_user_agent(self):
        """Rotate user agents."""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return ua
    
    def _is_short_video(self, duration_text: str) -> bool:
        """Check if video duration is less than 30 seconds based on accessibility label."""
        try:
            # Duration format examples: "1 minute, 30 seconds", "45 seconds", "2 minutes"
            duration_lower = duration_text.lower()
            
            # If it contains minutes, it's definitely longer than 30 seconds
            if 'minute' in duration_lower:
                return False
            
            # Extract seconds
            import re
            seconds_match = re.search(r'(\d+)\s*second', duration_lower)
            if seconds_match:
                seconds = int(seconds_match.group(1))
                return seconds < 30
            
            # If we can't parse it, assume it's not short
            return False
        except:
            return False
        
    def search_trailer(self, movie_title: str, year: int) -> Optional[str]:
        """Search for movie trailer on YouTube by scraping search results."""
        try:
            self._rate_limit()
            
            # Create search query: "movie title year official trailer"
            query = f"{movie_title} {year} official trailer"
            search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            
            headers = {
                'User-Agent': self._get_next_user_agent(),
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for video links in the page
            video_links = []
            video_titles = []
            
            # Method 1: Find script tags with video data
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'var ytInitialData' in script.string:
                    # Extract video IDs and titles from the script content
                    video_id_matches = re.findall(r'"videoId":"([^"]+)"', script.string)
                    title_matches = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"', script.string)
                    duration_matches = re.findall(r'"lengthText":{"accessibility":{"accessibilityData":{"label":"([^"]+)"', script.string)
                    
                    for i, video_id in enumerate(video_id_matches[:10]):  # Check first 10
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        title = title_matches[i] if i < len(title_matches) else ""
                        duration = duration_matches[i] if i < len(duration_matches) else ""
                        video_links.append(video_url)
                        video_titles.append(title.lower())
                        # Store duration info for filtering
                        if not hasattr(self, 'video_durations'):
                            self.video_durations = {}
                        self.video_durations[video_url] = duration
                    break
            
            # Method 2: Look for anchor tags with /watch? URLs
            if not video_links:
                links = soup.find_all('a', href=re.compile(r'/watch\?v='))
                for link in links[:10]:
                    href = link.get('href')
                    if href:
                        full_url = urljoin('https://www.youtube.com', href)
                        # Try to get title from aria-label or title attribute
                        title = link.get('aria-label', '') or link.get('title', '')
                        video_links.append(full_url)
                        video_titles.append(title.lower())
            
            # Filter for actual trailers (prioritize official trailers)
            if video_links:
                movie_title_lower = movie_title.lower()
                trailer_keywords = ['trailer', 'official', 'teaser', 'preview']
                official_keywords = ['official', 'studio', movie_title_lower]
                bad_keywords = [
                    'ad', 'advertisement', 'commercial', 'review', 'reaction', 
                    'breakdown', 'explained', 'interview', 'behind the scenes',
                    'making of', 'bloopers', 'deleted scene', 'clip', 'scene',
                    'tv spot', 'promo', 'featurette', 'comparison', 'vs',
                    'easter egg', 'theory', 'analysis', 'ending explained'
                ]
                
                # Score each video based on relevance
                scored_videos = []
                for i, (url, title) in enumerate(zip(video_links, video_titles)):
                    score = 0
                    title_words = title.split()
                    
                    # Strong bonus for containing exact movie title
                    if movie_title_lower in title:
                        score += 15
                    
                    # Bonus for official keywords (highest priority)
                    for keyword in official_keywords:
                        if keyword in title:
                            score += 10
                    
                    # Bonus for trailer keywords
                    for keyword in trailer_keywords:
                        if keyword in title:
                            score += 8
                    
                    # Strong penalty for bad keywords
                    for keyword in bad_keywords:
                        if keyword in title:
                            score -= 25
                    
                    # Penalty for very long titles (often fan-made content)
                    if len(title_words) > 8:
                        score -= 5
                    
                    # Bonus for position (earlier = more relevant)
                    score += (15 - i)
                    
                    # Bonus for "official trailer" exact phrase
                    if 'official trailer' in title:
                        score += 20
                    
                    # Penalty for numbers in parentheses (often fan cuts)
                    if re.search(r'\(\d+\)', title):
                        score -= 10
                    
                    # Strong penalty for short videos (likely ads)
                    duration = getattr(self, 'video_durations', {}).get(url, '')
                    if duration:
                        # Parse duration to check if it's less than 30 seconds
                        if self._is_short_video(duration):
                            score -= 30  # Heavy penalty for short videos
                    
                    scored_videos.append((score, url, title))
                
                # Sort by score and return the best one above threshold
                scored_videos.sort(key=lambda x: x[0], reverse=True)
                if scored_videos and scored_videos[0][0] > 5:  # Higher threshold
                    return scored_videos[0][1]
            
            return None
            
        except Exception as e:
            print(f"Error searching for {movie_title} ({year}): {e}")
            return None
    
    def process_movie_batch(self, movies_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of movies for trailer links."""
        results = []
        for movie in movies_batch:
            try:
                title = movie.get('title', '')
                year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                
                if title and year:
                    trailer_url = self.search_trailer(title, int(year))
                    if trailer_url:
                        if 'media' not in movie:
                            movie['media'] = {}
                        movie['media']['trailer_youtube'] = trailer_url
                        
                        with self.movies_lock:
                            self.success_count += 1
                
                results.append(movie)
                
            except Exception as e:
                print(f"Error processing {movie.get('title', 'Unknown')}: {e}")
                results.append(movie)
        
        return results
    
    def update_movie_trailers(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update movie data with YouTube trailer links using parallel processing."""
        start_time = time.time()
        print(f"🎬 Starting trailer search for {len(movies)} movies...")
        print(f"   Using {self.max_workers} parallel workers")
        
        # Split into batches
        batch_size = max(1, len(movies) // self.max_workers)
        batches = [movies[i:i + batch_size] for i in range(0, len(movies), batch_size)]
        
        print(f"   Processing {len(batches)} batches (avg {batch_size} movies per batch)")
        
        # Process batches in parallel
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self.process_movie_batch, batch): batch
                for batch in batches
            }
            
            progress_bar = tqdm(total=len(movies), desc="🎬 Fetching trailers", unit="movies")
            
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    progress_bar.update(len(batch_results))
                    
                    elapsed_time = time.time() - start_time
                    rate = len(all_results) / elapsed_time if elapsed_time > 0 else 0
                    progress_bar.set_description(f"🎬 Fetching trailers ({rate:.1f} movies/sec)")
                    
                except Exception as e:
                    print(f"Batch processing error: {e}")
                    # Add error placeholders for the entire batch
                    all_results.extend(batch)
                    progress_bar.update(len(batch))
            
            progress_bar.close()
        
        # Final stats
        elapsed_time = time.time() - start_time
        rate = len(all_results) / elapsed_time
        
        print(f"\n🎬 TRAILER SEARCH COMPLETE")
        print(f"   Total time: {elapsed_time:.1f} seconds")
        print(f"   Rate: {rate:.1f} movies per second")
        print(f"   Total processed: {len(all_results)}")
        print(f"   Successfully found trailers: {self.success_count}")
        print(f"   Success rate: {self.success_count/len(all_results)*100:.1f}%")
        
        return all_results

def main():
    """Main function to update movie data with trailer links."""
    try:
        # Load existing movie data
        input_file = "tmdb_movies_with_ratings.json"
        if not os.path.exists(input_file):
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
        
        print(f"Processing {len(movies)} movies...")
        
        # Update with trailer links using parallelization
        fetcher = TrailerLinkFetcher(max_workers=20)
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
