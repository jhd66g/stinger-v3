import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useMovieStore = create(
  persist(
    (set, get) => ({
      // Movie data
      movies: [],
      loading: false,
      error: null,
      
      // Filters
      filters: {
        services: [],
        genres: [],
        yearRange: [1900, new Date().getFullYear() + 1],
        ratingRange: [0, 100]
      },
      
      // Search
      searchQuery: '',
      searchResults: [],
      
      // Sorting
      sortBy: 'title',
      sortOrder: 'asc',
      
      // Pagination
      currentPage: 1,
      itemsPerPage: 24,
      
      // Actions
      loadMovies: async () => {
        set({ loading: true, error: null })
        try {
          const response = await fetch('/movie_data.json')
          if (!response.ok) {
            throw new Error('Failed to load movie data')
          }
          const data = await response.json()
          set({ 
            movies: data.movies || [],
            loading: false 
          })
        } catch (error) {
          set({ 
            error: error.message,
            loading: false 
          })
        }
      },
      
      setFilters: (newFilters) => {
        set({ 
          filters: { ...get().filters, ...newFilters },
          currentPage: 1 
        })
      },
      
      setSearchQuery: (query) => {
        set({ 
          searchQuery: query,
          currentPage: 1 
        })
      },
      
      setSorting: (sortBy, sortOrder) => {
        set({ sortBy, sortOrder })
      },
      
      setPage: (page) => {
        set({ currentPage: page })
      },
      
      // Computed values
      getFilteredMovies: () => {
        const { movies, filters, searchQuery, sortBy, sortOrder } = get()
        
        let filtered = [...movies]
        
        // Apply search filter
        if (searchQuery.trim()) {
          const query = searchQuery.toLowerCase()
          filtered = filtered.filter(movie => 
            movie.title.toLowerCase().includes(query) ||
            movie.cast.some(actor => actor.toLowerCase().includes(query)) ||
            movie.director.toLowerCase().includes(query) ||
            movie.keywords.some(keyword => keyword.toLowerCase().includes(query))
          )
        }
        
        // Apply service filter
        if (filters.services.length > 0) {
          filtered = filtered.filter(movie =>
            movie.streaming.some(stream => 
              filters.services.includes(stream.service)
            )
          )
        }
        
        // Apply genre filter
        if (filters.genres.length > 0) {
          filtered = filtered.filter(movie =>
            movie.genres.some(genre => 
              filters.genres.includes(genre)
            )
          )
        }
        
        // Apply year filter
        filtered = filtered.filter(movie =>
          movie.release_year >= filters.yearRange[0] &&
          movie.release_year <= filters.yearRange[1]
        )
        
        // Apply rating filter
        filtered = filtered.filter(movie =>
          movie.ratings.rt_tomatometer >= filters.ratingRange[0] &&
          movie.ratings.rt_tomatometer <= filters.ratingRange[1]
        )
        
        // Apply sorting
        filtered.sort((a, b) => {
          let aVal, bVal
          
          switch (sortBy) {
            case 'title':
              aVal = a.title.toLowerCase()
              bVal = b.title.toLowerCase()
              break
            case 'popularity':
              aVal = a.ratings.tmdb_popularity
              bVal = b.ratings.tmdb_popularity
              break
            case 'rating':
              aVal = a.ratings.rt_tomatometer
              bVal = b.ratings.rt_tomatometer
              break
            case 'year':
              aVal = a.release_year
              bVal = b.release_year
              break
            default:
              aVal = a.title.toLowerCase()
              bVal = b.title.toLowerCase()
          }
          
          if (sortOrder === 'asc') {
            return aVal > bVal ? 1 : -1
          } else {
            return aVal < bVal ? 1 : -1
          }
        })
        
        return filtered
      },
      
      getPaginatedMovies: () => {
        const filtered = get().getFilteredMovies()
        const { currentPage, itemsPerPage } = get()
        const startIndex = (currentPage - 1) * itemsPerPage
        return filtered.slice(startIndex, startIndex + itemsPerPage)
      },
      
      getTotalPages: () => {
        const filtered = get().getFilteredMovies()
        return Math.ceil(filtered.length / get().itemsPerPage)
      },
      
      getAvailableServices: () => {
        const { movies } = get()
        const services = new Set()
        movies.forEach(movie => {
          movie.streaming.forEach(stream => {
            services.add(stream.service)
          })
        })
        return Array.from(services).sort()
      },
      
      getAvailableGenres: () => {
        const { movies } = get()
        const genres = new Set()
        movies.forEach(movie => {
          movie.genres.forEach(genre => {
            genres.add(genre)
          })
        })
        return Array.from(genres).sort()
      },
      
      getMovieById: (id) => {
        const { movies } = get()
        return movies.find(movie => movie.id === parseInt(id))
      }
    }),
    {
      name: 'stinger-store',
      partialize: (state) => ({
        filters: state.filters,
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder
      })
    }
  )
)

export { useMovieStore }
