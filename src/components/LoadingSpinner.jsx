import React from 'react'

const LoadingSpinner = () => {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="loading-spinner"></div>
        <p>Loading movies...</p>
      </div>
    </div>
  )
}

export default LoadingSpinner
