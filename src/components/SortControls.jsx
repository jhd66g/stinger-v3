import React from 'react'
import { useMovieStore } from '../lib/store'

const SortControls = () => {
  const { sortBy, sortOrder, setSorting } = useMovieStore()

  const sortOptions = [
    { value: 'title', label: 'Alphabetical' },
    { value: 'popularity', label: 'Popularity' },
    { value: 'rating', label: 'Rating' },
    { value: 'year', label: 'Year' }
  ]

  const handleSortChange = (newSortBy) => {
    setSorting(newSortBy, sortOrder)
  }

  const handleOrderChange = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    setSorting(sortBy, newOrder)
  }

  return (
    <div className="sort-controls">
      <select
        className="sort-select"
        value={sortBy}
        onChange={(e) => handleSortChange(e.target.value)}
      >
        {sortOptions.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      
      <button
        className={`sort-button ${sortOrder === 'asc' ? 'active' : ''}`}
        onClick={handleOrderChange}
        title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
      >
        {sortOrder === 'asc' ? '↑' : '↓'}
      </button>
    </div>
  )
}

export default SortControls
