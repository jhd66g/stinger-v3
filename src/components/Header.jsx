import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useMovieStore } from '../lib/store';

const Header = () => {
  const location = useLocation();
  const { searchQuery, setSearchQuery, sortBy, sortOrder, setSorting } = useMovieStore();
  const isHomePage = location.pathname === '/';

  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSorting(newSortBy, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSorting(newSortBy, 'desc');
    }
  };

  const handleSortOrderToggle = () => {
    setSorting(sortBy, sortOrder === 'asc' ? 'desc' : 'asc');
  };

  const getSortDisplayName = (sortValue) => {
    switch (sortValue) {
      case 'title': return 'Title';
      case 'year': return 'Year';
      case 'rating': return 'Rating';
      case 'popularity': return 'Popularity';
      default: return 'Title';
    }
  };

  return (
    <header className="header">
      <div className="header__content">
        <div className="header__left">
          <Link to="/" className="header__logo">
            <h1>STINGER</h1>
          </Link>
        </div>
        
        <div className="header__right">
          <Link to="/about" className="header__nav-link">
            About
          </Link>
          
          {isHomePage && (
            <>
              <div className="header__sort-controls">
                <select 
                  value={sortBy} 
                  onChange={(e) => handleSortChange(e.target.value)}
                  className="header__sort-select"
                >
                  <option value="title">Sort by Title</option>
                  <option value="year">Sort by Year</option>
                  <option value="rating">Sort by Rating</option>
                  <option value="popularity">Sort by Popularity</option>
                </select>
                <button 
                  onClick={handleSortOrderToggle}
                  className="header__sort-button"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
              
              <div className="header__search">
                <input
                  type="text"
                  placeholder="Search movies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="header__search-input"
                />
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
