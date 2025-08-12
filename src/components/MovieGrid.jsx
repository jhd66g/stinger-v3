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
    setPage,
    updateItemsPerPage
  } = useMovieStore();
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Update items per page on window resize
  React.useEffect(() => {
    updateItemsPerPage(); // Set initial value
    
    const handleResize = () => {
      updateItemsPerPage();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateItemsPerPage]);
  
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
    <div className={`layout ${!sidebarOpen ? 'sidebar-collapsed' : ''}`}>
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <Filters />
      </aside>
      
      <div 
        className={`mobile-overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}>
      </div>
      
      <main className="content">
        <div className="results-info">
          <button 
            className="mobile-menu-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle filters"
          >
            ☰
          </button>
          <div className="results-count">
            {filteredMovies.length.toLocaleString()} results found
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
