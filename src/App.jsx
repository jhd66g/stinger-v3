import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { useMovieStore } from './lib/store'
import Header from './components/Header'
import MovieGrid from './components/MovieGrid'
import MovieDetails from './pages/MovieDetails'
import About from './pages/About'
import './styles/App.css'

function App() {
  const { movies, loading, error, loadMovies } = useMovieStore()

  React.useEffect(() => {
    if (movies.length === 0 && !loading) {
      loadMovies()
    }
  }, [movies.length, loading, loadMovies])

  if (error) {
    return (
      <div className="error-container">
        <h1>Error Loading Movies</h1>
        <p>{error}</p>
        <button onClick={loadMovies}>Retry</button>
      </div>
    )
  }

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<MovieGrid />} />
          <Route path="/movie/:id" element={<MovieDetails />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
