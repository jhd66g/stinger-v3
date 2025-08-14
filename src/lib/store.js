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
      itemsPerPage: 25,
      
      // Calculate optimal items per page based on window width
      calculateOptimalItemsPerPage: () => {
        const width = window.innerWidth;
        let columns;
        
        // Calculate columns based on CSS grid auto-fit with 160px minimum
        if (width < 768) {
          columns = Math.floor(width / 150); // Mobile breakpoint
        } else {
          columns = Math.floor((width - 320) / 160); // Account for sidebar width
        }
        
        // Ensure minimum 3 columns, maximum 8 columns
        columns = Math.max(3, Math.min(8, columns));
        
        // Fixed 5 rows, flexible columns
        const rows = 5;
        const itemsPerPage = rows * columns;
        
        return itemsPerPage;
      },
      
      // Update items per page based on window size
      updateItemsPerPage: () => {
        const { currentPage, itemsPerPage } = get();
        const optimal = get().calculateOptimalItemsPerPage();
        const filtered = get().getFilteredMovies();
        
        // Calculate the index of the first movie currently displayed
        const firstMovieIndex = (currentPage - 1) * itemsPerPage;
        
        // Calculate which page this movie should be on with the new items per page
        const newPage = Math.floor(firstMovieIndex / optimal) + 1;
        
        // If there's only one page worth of content, don't limit items per page
        if (filtered.length <= optimal) {
          set({ itemsPerPage: filtered.length || optimal, currentPage: 1 });
        } else {
          set({ itemsPerPage: optimal, currentPage: newPage });
        }
      },
      
      // Actions
      loadMovies: async (retryCount = 0) => {
        set({ loading: true, error: null })
        try {
          const response = await fetch('/movie_data.json', {
            cache: 'force-cache' // Use cached version if available
          })
          
          if (!response.ok) {
            if (response.status === 429 && retryCount < 3) {
              // Rate limited, wait and retry
              await new Promise(resolve => setTimeout(resolve, (retryCount + 1) * 2000))
              return get().loadMovies(retryCount + 1)
            }
            throw new Error(`Failed to load movie data (${response.status})`)
          }
          
          const data = await response.json()
          set({ 
            movies: data.movies || [],
            loading: false 
          })
        } catch (error) {
          if (retryCount < 2) {
            // Retry after a delay
            await new Promise(resolve => setTimeout(resolve, (retryCount + 1) * 1000))
            return get().loadMovies(retryCount + 1)
          }
          
          set({ 
            error: `${error.message}. Please refresh the page to try again.`,
            loading: false 
          })
        }
      },
      
      setFilters: (newFilters) => {
        set({ 
          filters: { ...get().filters, ...newFilters },
          currentPage: 1 
        })
        // Refresh grid layout when filters change
        get().updateItemsPerPage()
      },

      setSearchQuery: (query) => {
        set({ 
          searchQuery: query,
          currentPage: 1 
        })
        // Refresh grid layout when search changes
        get().updateItemsPerPage()
      },      setSorting: (sortBy, sortOrder) => {
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
      
      isLastPage: () => {
        const { currentPage } = get()
        return currentPage === get().getTotalPages()
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
