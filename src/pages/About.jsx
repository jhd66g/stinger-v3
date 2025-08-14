import React from 'react'
import { Link } from 'react-router-dom'

const About = () => {
  return (
    <div className="about">
      <div className="container">
        <div className="about__content">
          <p>
            <strong><em>SOMETHING TO STREAM</em></strong> is a fast, easy-to-use website that helps you find where to stream your favorite movies. 
            It aggregates the libraries of streaming services like{' '}
            <a href="https://tv.apple.com" className="streaming-link apple-tv" target="_blank" rel="noopener noreferrer">Apple TV+</a>,{' '}
            <a href="https://www.disneyplus.com" className="streaming-link disney-plus" target="_blank" rel="noopener noreferrer">Disney+</a>,{' '}
            <a href="https://www.max.com" className="streaming-link hbo-max" target="_blank" rel="noopener noreferrer">HBO Max</a>,{' '}
            <a href="https://www.hulu.com" className="streaming-link hulu" target="_blank" rel="noopener noreferrer">Hulu</a>,{' '}
            <a href="https://www.netflix.com" className="streaming-link netflix" target="_blank" rel="noopener noreferrer">Netflix</a>,{' '}
            <a href="https://www.paramountplus.com" className="streaming-link paramount-plus" target="_blank" rel="noopener noreferrer">Paramount+</a>, and{' '}
            <a href="https://www.peacocktv.com" className="streaming-link peacock" target="_blank" rel="noopener noreferrer">Peacock</a>, 
            and displays them in a simple grid, letting users filter as they wish.
          </p>
          
          <p>
            The website maintains an up-to-date database fetching movie data from{' '}
            <a href="https://www.themoviedb.org" className="external-link" target="_blank" rel="noopener noreferrer">The Movie Database (TMDB)</a>, 
            ratings from{' '}
            <a href="https://www.rottentomatoes.com" className="external-link" target="_blank" rel="noopener noreferrer">Rotten Tomatoes</a>, 
            and trailers from{' '}
            <a href="https://www.youtube.com" className="external-link" target="_blank" rel="noopener noreferrer">YouTube</a>.
          </p>
          
          <p>
            More features coming soon …
          </p>
          
          <p>
            Enjoy!
          </p>
          
          <p>
            - Jack D
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
