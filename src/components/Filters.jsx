import React, { useState } from 'react'
import { useMovieStore } from '../lib/store'
import RangeSlider from './RangeSlider'

const Filters = () => {
  const {
    filters,
    setFilters,
    getAvailableServices,
    getAvailableGenres
  } = useMovieStore()

  const [collapsedSections, setCollapsedSections] = useState({
    services: false,
    genres: false,
    year: false,
    rating: false
  })

  const availableServices = getAvailableServices()
  const availableGenres = getAvailableGenres()

  const handleServiceChange = (service) => {
    const newServices = filters.services.includes(service)
      ? filters.services.filter(s => s !== service)
      : [...filters.services, service]
    setFilters({ services: newServices })
  }

  const handleGenreChange = (genre) => {
    const newGenres = filters.genres.includes(genre)
      ? filters.genres.filter(g => g !== genre)
      : [...filters.genres, genre]
    setFilters({ genres: newGenres })
  }

  const handleYearRangeChange = (range) => {
    setFilters({ yearRange: range })
  }

  const handleRatingRangeChange = (range) => {
    setFilters({ ratingRange: range })
  }

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const clearServices = () => {
    setFilters({ services: [] })
  }

  const clearGenres = () => {
    setFilters({ genres: [] })
  }

  const resetFilters = () => {
    setFilters({
      services: [],
      genres: [],
      yearRange: [1900, new Date().getFullYear()],
      ratingRange: [0, 100]
    })
  }

  return (
    <div className="filters">
      {/* Streaming Services */}
      <div className="filter-group">
        <div 
          className="filter-group__header" 
          onClick={() => toggleSection('services')}
        >
          <label className="filter-group__label">Streaming Services</label>
          <span className={`filter-group__toggle ${collapsedSections.services ? 'collapsed' : ''}`}>▼</span>
        </div>
        {!collapsedSections.services && (
          <div className="filter-group__content">
            {availableServices.map(service => (
              <div key={service} className="filter-checkbox" data-service={service}>
                <input
                  type="checkbox"
                  id={`service-${service}`}
                  checked={filters.services.includes(service)}
                  onChange={() => handleServiceChange(service)}
                />
                <label htmlFor={`service-${service}`}>{service}</label>
              </div>
            ))}
            {filters.services.length > 0 && (
              <button onClick={clearServices} className="btn btn-ghost btn-sm filter-clear">
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* Genres */}
      <div className="filter-group">
        <div 
          className="filter-group__header" 
          onClick={() => toggleSection('genres')}
        >
          <label className="filter-group__label">Genres</label>
          <span className={`filter-group__toggle ${collapsedSections.genres ? 'collapsed' : ''}`}>▼</span>
        </div>
        {!collapsedSections.genres && (
          <div className="filter-group__content">
            {availableGenres.map(genre => (
              <div key={genre} className="filter-checkbox">
                <input
                  type="checkbox"
                  id={`genre-${genre}`}
                  checked={filters.genres.includes(genre)}
                  onChange={() => handleGenreChange(genre)}
                />
                <label htmlFor={`genre-${genre}`}>{genre}</label>
              </div>
            ))}
            {filters.genres.length > 0 && (
              <button onClick={clearGenres} className="btn btn-ghost btn-sm filter-clear">
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* Year Range */}
      <div className="filter-group">
        <div 
          className="filter-group__header" 
          onClick={() => toggleSection('year')}
        >
          <label className="filter-group__label">Release Year</label>
          <span className={`filter-group__toggle ${collapsedSections.year ? 'collapsed' : ''}`}>▼</span>
        </div>
        {!collapsedSections.year && (
          <div className="filter-group__content">
            <RangeSlider
              min={1900}
              max={2025}
              value={filters.yearRange}
              onChange={handleYearRangeChange}
              formatValue={(value) => value}
            />
          </div>
        )}
      </div>

      {/* Rating Range */}
      <div className="filter-group">
        <div 
          className="filter-group__header" 
          onClick={() => toggleSection('rating')}
        >
          <label className="filter-group__label">Rotten Tomatoes Rating</label>
          <span className={`filter-group__toggle ${collapsedSections.rating ? 'collapsed' : ''}`}>▼</span>
        </div>
        {!collapsedSections.rating && (
          <div className="filter-group__content">
            <RangeSlider
              min={0}
              max={100}
              value={filters.ratingRange}
              onChange={handleRatingRangeChange}
              formatValue={(value) => `${value}%`}
            />
          </div>
        )}
      </div>

      {/* Reset Button at Bottom */}
      <div className="filters__footer">
        <button onClick={resetFilters} className="btn btn-ghost btn-sm">
          Reset All
        </button>
      </div>
    </div>
  )
}

export default Filters
