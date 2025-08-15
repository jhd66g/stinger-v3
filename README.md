# STINGER V3 (Something to Stream)
**https://somethingtostream.us/**

A fast, static, privacy‑friendly movie discovery web app that aggregates **where to stream** plus key metadata (ratings, cast, trailers) and lets users **filter, search, and sort** thousands of films. Built to run fully client‑side and deploy on GitHub Pages (no backend required).

## Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+ (for data pipeline)
- TMDB API Bearer Token

### 1. Setup Data Pipeline

```bash
# Navigate to data pipeline directory
cd data_pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  

# Install dependencies
pip install -r requirements.txt

# Create .env file with your TMDB API key
cp env.example .env

# Run the data pipeline
./data_pipeline.sh
```

### 2. Setup Web App

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### 3. Build for Production

```bash
npm run build
npm run preview
```

## Features

- **Streaming Service Filters**: Amazon Prime, Netflix, Disney+, Hulu, HBO Max, Paramount+, Apple TV+, Peacock
- **Advanced Search**: Search by title, actor, director, or keywords
- **Genre & Year Filters**: Find movies by genre and release year range
- **Rating Filters**: Filter by Rotten Tomatoes ratings (0-100%)
- **Rich Movie Details**: Cast, crew, ratings, trailers, and streaming links
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Fast Performance**: Static site with pre-loaded data
- **Privacy-First**: No tracking, runs entirely in your browser

## Architecture

### Data Pipeline
- **Highly Parallelized**: Uses ThreadPoolExecutor for concurrent API calls
- **TMDB Integration**: Fetches movies from multiple streaming services
- **Rotten Tomatoes**: Adds critic and audience ratings
- **YouTube Scraping**: Finds official trailers via web scraping (no API key needed)
- **Data Validation**: Ensures data integrity and handles errors gracefully

### Frontend
- **React 18**: Modern functional components with hooks
- **Vite**: Fast build tool and dev server
- **Zustand**: Lightweight state management with persistence
- **React Router**: Client-side routing
- **CSS Custom Properties**: Consistent design system
- **Responsive Grid**: Adaptive layout for all screen sizes

## 📊 Data Model

```json
{
  "id": 603,
  "title": "The Matrix",
  "release_year": 1999,
  "genres": ["Action", "Sci-Fi"],
  "mpa_rating": "R",
  "overview": "A computer hacker learns from mysterious rebels about the true nature of his reality...",
  "runtime_min": 136,
  "budget_usd": 63000000,
  "revenue_usd": 466364845,
  "cast": ["Keanu Reeves", "Carrie-Anne Moss"],
  "director": "The Wachowskis",
  "production_companies": ["Warner Bros."],
  "streaming": [
    { "service": "Netflix", "region": "US", "link": "https://..." }
  ],
  "ratings": {
    "tmdb_popularity": 82.1,
    "tmdb_vote": 8.2,
    "rt_tomatometer": 88,
    "rt_audience": 85
  },
  "media": {
    "poster": "https://image.tmdb.org/t/p/w500/...",
    "backdrop": "https://image.tmdb.org/t/p/original/...",
    "trailer_youtube": "https://youtu.be/..."
  },
  "keywords": ["simulation", "hacker"]
}
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the `data_pipeline` directory:

```env
# Required
TMDB_BEARER_TOKEN=your_tmdb_bearer_token_here

# Optional
RT_API_KEY=your_rotten_tomatoes_api_key_here
```

### API Keys
- **TMDB**: Get your bearer token from [The Movie Database](https://www.themoviedb.org/settings/api)
- **Rotten Tomatoes**: Optional, for enhanced ratings data
- **YouTube**: Not needed - uses web scraping for trailers

## Project Structure

```
stinger-v3/
├── data_pipeline/           # Data collection scripts
│   ├── fetch_tmdb_data.py   # Parallelized TMDB data fetching
│   ├── fetch_rotten_tomatoes_data.py
│   ├── fetch_trailer_link.py # YouTube web scraping
│   ├── data_pipeline.sh     # Orchestration script
│   └── requirements.txt
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/              # Page components
│   ├── lib/                # Utilities and store
│   └── styles/             # CSS files
├── public/
│   ├── movie_data.json     # Generated movie data
│   └── assets/             # Images and static files
└── package.json
```

## Deployment

### GitHub Pages
1. Build the project: `npm run build`
2. Push to `gh-pages` branch
3. Configure GitHub Pages to deploy from `gh-pages` branch

### Other Static Hosting
The built `dist` folder can be deployed to any static hosting service:
- Netlify
- Vercel
- AWS S3
- Cloudflare Pages

## Performance Optimizations

- **Parallel Data Fetching**: 15 concurrent workers for API calls
- **Lazy Loading**: Images load as needed
- **Code Splitting**: Separate bundles for different features
- **Compression**: Gzip/Brotli support
- **Caching**: Browser caching for static assets
- **Pagination**: Load movies in chunks

## Design System

- **Dark Theme**: Netflix-inspired dark interface
- **Responsive Grid**: 1-6 cards per row based on screen size
- **Smooth Animations**: CSS transitions for better UX
- **Accessibility**: Keyboard navigation and ARIA labels
- **Mobile-First**: Touch-friendly controls and layout


## License

MIT License - see LICENSE file for details

## Acknowledgments

- [The Movie Database](https://www.themoviedb.org/) for movie data
- [Rotten Tomatoes](https://www.rottentomatoes.com/) for ratings
- [YouTube](https://www.youtube.com/) for trailers
- React, Vite, and the open source community

---

**STINGER Streaming** - Discover where to watch your next favorite movie! 🎬

