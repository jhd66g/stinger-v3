import React, { useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useMovieStore } from '../lib/store'

const MovieDetails = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { getMovieById, getFilteredMovies } = useMovieStore()
  
  const movie = getMovieById(id)
  const filteredMovies = getFilteredMovies()

  // Scroll to top when component mounts or movie changes
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [id])
  
  if (!movie) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">🎬</div>
        <h2 className="empty-state__title">Movie Not Found</h2>
        <p className="empty-state__message">
          The movie you're looking for doesn't exist or has been removed.
        </p>
        <Link to="/" className="btn btn-primary">
          Back to Movies
        </Link>
      </div>
    )
  }

  const currentIndex = filteredMovies.findIndex(m => m.id === movie.id)
  const prevMovie = currentIndex > 0 ? filteredMovies[currentIndex - 1] : null
  const nextMovie = currentIndex < filteredMovies.length - 1 ? filteredMovies[currentIndex + 1] : null

  const formatCurrency = (amount) => {
    if (!amount || amount === 0) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatRuntime = (minutes) => {
    if (!minutes || minutes === 0) return 'N/A'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  return (
    <div className="movie-details">
      <div className="container">
        {/* Hero section */}
        <div className="movie-details__hero">
          <div className="movie-details__poster">
            <img
              src={movie.media.poster || '/placeholder-poster.jpg'}
              alt={`${movie.title} poster`}
              className="movie-details__poster-img"
            />
          </div>
          
          <div className="movie-details__info">
            <h1 className="movie-details__title">
              {movie.title} ({movie.release_year})
            </h1>
            
            <div className="movie-details__meta">
              <span className="movie-details__rating">{movie.mpa_rating}</span>
              <span className="movie-details__runtime">{formatRuntime(movie.runtime_min)}</span>
              <span className="movie-details__genres">{movie.genres.join(', ')}</span>
            </div>

            {movie.overview && (
              <p className="movie-details__overview">{movie.overview}</p>
            )}

            {/* Cast & Crew and Production in 2 columns */}
            <div className="movie-details__grid">
              {/* Cast & Crew and Ratings */}
              <div className="movie-details__section">
                {movie.director && (
                  <div className="movie-details__crew">
                    <strong>Director:</strong> {movie.director}
                  </div>
                )}
                {movie.cast.length > 0 && (
                  <div className="movie-details__cast">
                    <strong>Cast:</strong> {movie.cast.join(', ')}
                  </div>
                )}
                {/* Streaming services */}
                {movie.streaming.length > 0 && (
                  <div className="movie-details__streaming">
                    <strong>Available on:</strong> {movie.streaming.map((stream, index) => {
                      // Generate service-specific URLs
                      const getServiceUrl = (service, movieTitle, year) => {
                        const titleQuery = encodeURIComponent(movieTitle.replace(/\s+/g, '+'))
                        switch(service.toLowerCase()) {
                          case 'amazon prime':
                            return 'https://www.amazon.com/gp/video/storefront'
                          case 'netflix':
                            return `https://www.netflix.com/search?q=${encodeURIComponent(movieTitle)}`
                          case 'disney+':
                            return `https://www.disneyplus.com/en-gb/browse/search`
                          case 'hulu':
                            return `https://www.hulu.com/search`
                          case 'hbo max':
                          case 'max':
                            return `https://play.hbomax.com/search/result?q=${titleQuery}`
                          case 'paramount+':
                            return `https://www.paramountplus.com/search/`
                          case 'apple tv+':
                            return `https://tv.apple.com/us/search?term=${encodeURIComponent(movieTitle.toLowerCase())}`
                          case 'peacock':
                            return `https://www.peacocktv.com/watch/search`
                          default:
                            return `https://www.google.com/search?q=${encodeURIComponent(`${movieTitle} ${year}`)}+streaming`
                        }
                      }
                      
                      return (
                        <span key={index}>
                          <a
                            href={getServiceUrl(stream.service, movie.title, movie.release_year)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`streaming-service-link ${stream.service.toLowerCase().replace(/\s+/g, '').replace('+', '')}`}
                            style={{ textDecoration: 'none', color: 'inherit' }}
                          >
                            {stream.service}
                          </a>
                          {index < movie.streaming.length - 1 ? ', ' : ''}
                        </span>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Production and Streaming services */}
              <div className="movie-details__section">
                {movie.production_companies.length > 0 && (
                  <div className="movie-details__companies">
                    <strong>Production Companies:</strong> {movie.production_companies.join(', ')}
                  </div>
                )}
                <div className="movie-details__language">
                  <strong>Original Language:</strong> {movie.original_language}
                </div>
                <div className="movie-details__budget">
                  <strong>Budget:</strong> {formatCurrency(movie.budget_usd)}
                </div>
                <div className="movie-details__revenue">
                  <strong>Revenue:</strong> {formatCurrency(movie.revenue_usd)}
                </div>
                {/* Ratings */}
                <div className="movie-details__ratings">
                  {movie.ratings.rt_tomatometer > 0 && (
                    <div className="movie-details__rating-item">
                      <strong>Tomatometer</strong>
                      <span className="movie-details__rating-score">
                        {movie.ratings.rt_tomatometer}%
                      </span>
                    </div>
                  )}
                  
                  {movie.ratings.rt_audience > 0 && (
                    <div className="movie-details__rating-item">
                      <strong>Audience Score</strong>
                      <span className="movie-details__rating-score">
                        {movie.ratings.rt_audience}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Details section */}
        <div className="movie-details__content">
          {/* Trailer */}
          {movie.media.trailer_youtube && (
            <div className="movie-details__trailer">
              <div className="movie-details__video-container">
                <iframe
                  src={`${movie.media.trailer_youtube.replace('watch?v=', 'embed/')}?autoplay=0&showinfo=0&controls=1&modestbranding=1&rel=0&iv_load_policy=3`}
                  title={`${movie.title} trailer`}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="movie-details__navigation">
          {prevMovie && (
            <Link to={`/movie/${prevMovie.id}`} className="pagination-button">
              ← {prevMovie.title}
            </Link>
          )}
          
          {nextMovie && (
            <Link to={`/movie/${nextMovie.id}`} className="pagination-button">
              {nextMovie.title} →
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default MovieDetails
