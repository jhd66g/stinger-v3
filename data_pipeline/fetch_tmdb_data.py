#!/usr/bin/env python3
"""
Fetch movie data from TMDB API for multiple streaming services.
This script collects movies available on Netflix, Disney+, Hulu, Max, Paramount+, Apple TV+, and Amazon Prime.
Highly parallelized for better performance.
"""

import os
import json
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

class TMDBDataFetcher:
    def __init__(self, max_workers=10):
        self.bearer_token = os.getenv('TMDB_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TMDB_BEARER_TOKEN not found in environment variables")
        
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # Streaming service provider IDs from TMDB
        self.providers = {
            "Netflix": 8,
            "Disney+": 337,
            "Hulu": 15,
            "HBO Max": 1899,
            "Paramount+": 531,
            "Apple TV+": 350,
            "Peacock": 386,
            "Amazon Prime": 9
        }
        
        self.movies = {}
        self.movies_lock = threading.Lock()
        self.max_workers = max_workers
        # Highly optimized for performance like streamlined fetcher
        self.timeout = (5, 10)
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 20 requests per second
        
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
        
        # Set headers for session
        self.session.headers.update(self.headers)
    
    def _rate_limit(self):
        """Simple rate limiting like streamlined fetcher."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def process_provider_batch(self, providers_batch):
        """Process a batch of providers in parallel."""
        results = []
        for provider_name, provider_id in providers_batch:
            try:
                provider_movies = self.get_movies_by_provider(provider_id, provider_name)
                results.extend(provider_movies)
            except Exception as e:
                print(f"Error processing provider {provider_name}: {e}")
        return results

    def get_movies_by_provider(self, provider_id: int, provider_name: str) -> List[Dict]:
        """Fetch movies available on a specific streaming service."""
        movies = []
        page = 1
        
        while True:
            try:
                url = f"{self.base_url}/discover/movie"
                params = {
                    "with_watch_providers": provider_id,
                    "watch_region": "US",
                    "page": page,
                    "sort_by": "popularity.desc",
                    "include_adult": False,
                    "include_video": False
                }
                
                # Use rate limiting and session
                self._rate_limit()
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                for movie in results:
                    movie_id = movie['id']
                    with self.movies_lock:
                        if movie_id not in self.movies:
                            self.movies[movie_id] = {
                                "id": movie_id,
                                "title": movie.get('title', ''),
                                "original_title": movie.get('original_title', ''),
                                "original_language": movie.get('original_language', ''),
                                "release_date": movie.get('release_date', ''),
                                "release_year": self._extract_year(movie.get('release_date', '')),
                                "genres": [],
                                "mpa_rating": movie.get('adult', False) and 'R' or 'PG-13',
                                "overview": movie.get('overview', ''),
                                "runtime_min": 0,
                                "budget_usd": movie.get('budget', 0),
                                "revenue_usd": movie.get('revenue', 0),
                                "cast": [],
                                "director": "",
                                "production_companies": [],
                                "streaming": [],
                                "ratings": {
                                    "tmdb_popularity": movie.get('popularity', 0),
                                    "tmdb_vote": movie.get('vote_average', 0),
                                    "rt_tomatometer": 0,
                                    "rt_audience": 0
                                },
                                "media": {
                                    "poster": f"/assets/posters/{movie_id}.jpg",
                                    "backdrop": f"/assets/backdrops/{movie_id}.jpg",
                                    "trailer_youtube": ""
                                },
                                "keywords": []
                            }
                        
                        # Add streaming service to existing movie
                        streaming_entry = {
                            "service": provider_name,
                            "region": "US",
                            "link": f"https://www.themoviedb.org/movie/{movie_id}"
                        }
                        
                        if streaming_entry not in self.movies[movie_id]["streaming"]:
                            self.movies[movie_id]["streaming"].append(streaming_entry)
                
                page += 1
                # Remove the separate sleep since we have rate limiting in _rate_limit()
                
            except requests.exceptions.RequestException as e:
                # Silent error handling for speed
                break
        
        return movies

    def enrich_movie_details(self, movie_id: int) -> None:
        """Fetch detailed information for a specific movie."""
        try:
            # Get movie details
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                "append_to_response": "credits,keywords,images"
            }
            
            # Use rate limiting and session
            self._rate_limit()
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Update movie data
            with self.movies_lock:
                if movie_id in self.movies:
                    movie = self.movies[movie_id]
                    
                    # Update basic info
                    movie["runtime_min"] = data.get('runtime', 0)
                    movie["mpa_rating"] = data.get('adult', False) and 'R' or 'PG-13'
                    movie["budget_usd"] = data.get('budget', 0)
                    movie["revenue_usd"] = data.get('revenue', 0)
                    
                    # Get genres
                    genres = data.get('genres', [])
                    movie["genres"] = [genre['name'] for genre in genres]
                    
                    # Get cast (top 10)
                    credits = data.get('credits', {})
                    cast = credits.get('cast', [])
                    movie["cast"] = [person['name'] for person in cast[:10]]
                    
                    # Get director
                    crew = credits.get('crew', [])
                    directors = [person['name'] for person in crew if person['job'] == 'Director']
                    movie["director"] = directors[0] if directors else ""
                    
                    # Get production companies
                    companies = data.get('production_companies', [])
                    movie["production_companies"] = [company['name'] for company in companies]
                    
                    # Get keywords
                    keywords_data = data.get('keywords', {}).get('keywords', [])
                    movie["keywords"] = [kw['name'] for kw in keywords_data[:20]]
                    
                    # Update poster/backdrop paths with language preference
                    images = data.get('images', {})
                    posters = images.get('posters', [])
                    backdrops = images.get('backdrops', [])
                    
                    if posters:
                        # Prioritize English posters first, then original language, then any poster
                        original_lang = movie.get("original_language", "")
                        english_poster = next((p for p in posters if p.get('iso_639_1') == 'en'), None)
                        original_lang_poster = next((p for p in posters if p.get('iso_639_1') == original_lang), None)
                        any_poster = posters[0] if posters else None
                        
                        selected_poster = english_poster or original_lang_poster or any_poster
                        if selected_poster:
                            poster_path = selected_poster.get('file_path', '')
                            if poster_path:
                                movie["media"]["poster"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    
                    if backdrops:
                        backdrop_path = backdrops[0].get('file_path', '')
                        if backdrop_path:
                            movie["media"]["backdrop"] = f"https://image.tmdb.org/t/p/original{backdrop_path}"
                
                # Remove separate sleep since we have rate limiting in _rate_limit()
                
        except requests.exceptions.RequestException as e:
            # Silent error handling for speed
            pass

    def fetch_provider_data_parallel(self, provider_name: str, provider_id: int):
        """Fetch data for a single provider (for parallel execution)."""
        print(f"Fetching movies from {provider_name}...")
        return self.get_movies_by_provider(provider_id, provider_name)

    def enrich_movie_parallel(self, movie_id: int):
        """Enrich a single movie (for parallel execution)."""
        return self.enrich_movie_details(movie_id)

    def _extract_year(self, date_string: str) -> int:
        """Extract year from date string."""
        if not date_string:
            return 0
        try:
            return int(date_string.split('-')[0])
        except (ValueError, IndexError):
            return 0

    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all movie data from all streaming services using parallel processing."""
        print("Fetching movies from streaming services (parallel)...")
        
        # Parallel fetch from all providers
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = []
            for provider_name, provider_id in self.providers.items():
                future = executor.submit(self.fetch_provider_data_parallel, provider_name, provider_id)
                futures.append(future)
            
            # Wait for all providers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in provider fetch: {e}")
        
        print(f"\nFound {len(self.movies)} unique movies across all services.")
        
        # Parallel enrichment of movie details
        print("\nEnriching movie details (parallel)...")
        movie_ids = list(self.movies.keys())
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for movie_id in movie_ids:
                future = executor.submit(self.enrich_movie_parallel, movie_id)
                futures.append(future)
            
            # Progress bar for enrichment
            with tqdm(total=len(futures), desc="Enriching movies") as pbar:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error in movie enrichment: {e}")
                    pbar.update(1)
        
        # Convert to list and sort
        movies_list = list(self.movies.values())
        movies_list.sort(key=lambda x: (x['title'], x['release_year']))
        
        return {
            "movies": movies_list,
            "total_count": len(movies_list),
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def main():
    """Main function to run the TMDB data fetcher."""
    try:
        fetcher = TMDBDataFetcher(max_workers=15)  # Increased parallel workers
        data = fetcher.fetch_all_data()
        
        # Save to JSON file
        output_file = "tmdb_movies.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {output_file}")
        print(f"Total movies: {data['total_count']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
