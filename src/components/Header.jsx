import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useMovieStore } from '../lib/store';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { searchQuery, setSearchQuery, sortBy, sortOrder, setSorting } = useMovieStore();
  const isHomePage = location.pathname === '/';
  const isDetailsOrAboutPage = location.pathname.startsWith('/movie/') || location.pathname === '/about';

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

  const sortOptions = [
    { value: 'title', label: 'Sort by Title' },
    { value: 'year', label: 'Sort by Year' },
    { value: 'rating', label: 'Sort by Rating' },
    { value: 'popularity', label: 'Sort by Popularity' }
  ];

  return (
    <header className="header">
      <div className="header__content">
        <div className="header__top">
          <div className="header__left">
            <Link to="/" className="header__logo">
              <h1>SOMETHING TO STREAM</h1>
            </Link>
          </div>
          
          <div className="header__right">
            {isDetailsOrAboutPage ? (
              <button 
                onClick={() => navigate(-1)} 
                className="header__nav-link"
              >
                ← Back
              </button>
            ) : (
              <Link to="/about" className="header__nav-link">
                About
              </Link>
            )}
          </div>
        </div>

        {isHomePage && (
          <div className="header__bottom">
            <div className="header__sort-controls">
              <div className="header__sort-dropdown">
                <button 
                  className="header__sort-select"
                >
                  {sortOptions.find(option => option.value === sortBy)?.label}
                </button>
                <div className="header__sort-dropdown-menu">
                  {sortOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handleSortChange(option.value)}
                      className={`header__sort-dropdown-item ${sortBy === option.value ? 'active' : ''}`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
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
                placeholder="Search movies, actors, directors, studios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="header__search-input"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="header__search-clear"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
