import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  const [imageLoaded, setImageLoaded] = useState(false);

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = (e) => {
    e.target.src = '/placeholder-poster.jpg';
    setImageLoaded(true);
  };

  return (
    <Link to={`/movie/${movie.id}`} className="movie-card">
      <div className="movie-card__poster-container">
        <img
          src={movie.media?.poster || '/placeholder-poster.jpg'}
          alt={movie.title}
          className={`movie-card__poster ${imageLoaded ? 'loaded' : ''}`}
          loading="lazy"
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      </div>
      <div className="movie-card__content">
        <h3 className="movie-card__title">{movie.title}</h3>
        <div className="movie-card__year">{movie.release_year}</div>
      </div>
    </Link>
  );
};

export default MovieCard;
