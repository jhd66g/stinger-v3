import React from 'react';
import { Link } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  const handleImageError = (e) => {
    e.target.src = '/placeholder-poster.jpg';
  };

  return (
    <Link to={`/movie/${movie.id}`} className="movie-card">
      <img
        src={movie.media?.poster || '/placeholder-poster.jpg'}
        alt={movie.title}
        className="movie-card__poster"
        loading="lazy"
        onError={handleImageError}
      />
      <div className="movie-card__content">
        <h3 className="movie-card__title">{movie.title}</h3>
        <div className="movie-card__year">{movie.release_year}</div>
      </div>
    </Link>
  );
};

export default MovieCard;
