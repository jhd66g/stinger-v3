import React, { useState } from 'react';
import { useMovieStore } from '../lib/store';
import MovieCard from './MovieCard';
import Filters from './Filters';
import Pagination from './Pagination';
import LoadingSpinner from './LoadingSpinner';

const MovieGrid = () => {
  const { 
    movies, 
    loading, 
    error, 
    getFilteredMovies, 
    getPaginatedMovies, 
    getTotalPages,
    currentPage,
    setPage
  } = useMovieStore();
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const filteredMovies = getFilteredMovies();
  const paginatedMovies = getPaginatedMovies();
  const totalPages = getTotalPages();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h1>Error Loading Movies</h1>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <Filters />
      </aside>
      
      <div 
        className={`mobile-overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}>
      </div>
      
      <main className="content">
        <div className="results-info">
          <div className="results-count">
            {filteredMovies.length} results found
          </div>
        </div>
        
        {filteredMovies.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">🎬</div>
            <h2 className="empty-state__title">No movies found</h2>
            <p className="empty-state__message">
              Try adjusting your filters or search terms.
            </p>
          </div>
        ) : (
          <>
            <div className="movie-grid">
              {paginatedMovies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
            
            {totalPages > 1 && (
              <Pagination 
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default MovieGrid;
