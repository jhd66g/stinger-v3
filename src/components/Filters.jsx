import React from 'react'
import { useMovieStore } from '../lib/store'
import RangeSlider from './RangeSlider'

const Filters = () => {
  const {
    filters,
    setFilters,
    getAvailableServices,
    getAvailableGenres
  } = useMovieStore()

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

  const resetFilters = () => {
    setFilters({
      services: [],
      genres: [],
      yearRange: [1900, new Date().getFullYear() + 1],
      ratingRange: [0, 100]
    })
  }

  return (
    <div className="filters">
      <div className="filters__header">
        <h2 className="filters-section__title">Filters</h2>
        <button onClick={resetFilters} className="btn btn-ghost btn-sm">
          Reset
        </button>
      </div>

      {/* Streaming Services */}
      <div className="filter-group">
        <label className="filter-group__label">Streaming Services</label>
        {availableServices.map(service => (
          <div key={service} className="filter-checkbox">
            <input
              type="checkbox"
              id={`service-${service}`}
              checked={filters.services.includes(service)}
              onChange={() => handleServiceChange(service)}
            />
            <label htmlFor={`service-${service}`}>{service}</label>
          </div>
        ))}
      </div>

      {/* Genres */}
      <div className="filter-group">
        <label className="filter-group__label">Genres</label>
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
      </div>

      {/* Year Range */}
      <div className="filter-group">
        <label className="filter-group__label">Release Year</label>
        <RangeSlider
          min={1900}
          max={new Date().getFullYear() + 1}
          value={filters.yearRange}
          onChange={handleYearRangeChange}
          formatValue={(value) => value}
        />
      </div>

      {/* Rating Range */}
      <div className="filter-group">
        <label className="filter-group__label">Rotten Tomatoes Rating</label>
        <RangeSlider
          min={0}
          max={100}
          value={filters.ratingRange}
          onChange={handleRatingRangeChange}
          formatValue={(value) => `${value}%`}
        />
      </div>
    </div>
  )
}

export default Filters
