import React from 'react'
import { Link } from 'react-router-dom'

const About = () => {
  return (
    <div className="about">
      <div className="container">
        <div className="about__content">
          <h1>About STINGER Streaming</h1>
          
          <p>
            STINGER Streaming is a fast, static, privacy-friendly movie discovery web app that helps you find where to stream your favorite movies. 
            We aggregate streaming availability from multiple services and provide rich metadata including ratings, cast information, and trailers.
          </p>
          
          <h2>Features</h2>
          <ul>
            <li><strong>Streaming Service Filters:</strong> Filter by Netflix, Disney+, Hulu, Max, Paramount+, and Apple TV+</li>
            <li><strong>Advanced Search:</strong> Search by title, actor, director, or keywords</li>
            <li><strong>Genre & Year Filters:</strong> Find movies by genre and release year</li>
            <li><strong>Rating Filters:</strong> Filter by Rotten Tomatoes ratings</li>
            <li><strong>Rich Movie Details:</strong> View cast, crew, ratings, trailers, and streaming links</li>
            <li><strong>Responsive Design:</strong> Works perfectly on desktop, tablet, and mobile</li>
          </ul>
          
          <h2>Privacy & Performance</h2>
          <p>
            STINGER is built as a static website with no backend required. All movie data is pre-loaded and runs entirely in your browser, 
            ensuring fast performance and complete privacy. We don't track your searches or viewing habits.
          </p>
          
          <h2>Data Sources</h2>
          <p>
            Our movie data comes from The Movie Database (TMDB) API, with additional ratings from Rotten Tomatoes. 
            Streaming availability is updated regularly to provide accurate information about where you can watch each movie.
          </p>
          
          <h2>Technology</h2>
          <p>
            Built with React, Vite, and modern web technologies. The app is designed to be fast, accessible, and easy to use.
          </p>
          
          <div className="about__actions">
            <Link to="/" className="btn btn-primary">
              Start Discovering Movies
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default About
