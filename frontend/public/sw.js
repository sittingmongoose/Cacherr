/**
 * Service Worker for PlexCacheUltra Dashboard PWA
 * 
 * Features:
 * - Offline support with cache-first strategy
 * - Background sync for API requests
 * - Push notifications (future)
 * - Asset caching and updates
 */

const CACHE_NAME = 'cacherr-v1'
const API_CACHE_NAME = 'cacherr-api-v1'
const OFFLINE_URL = '/offline.html'

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
]

// API endpoints that can be cached
const CACHEABLE_API_ROUTES = [
  '/api/status',
  '/health',
  '/health/detailed',
]

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Install event')
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets')
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        console.log('Service Worker: Static assets cached successfully')
        return self.skipWaiting()
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets:', error)
      })
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activate event')
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        console.log('Service Worker: Old caches cleaned up')
        return self.clients.claim()
      })
  )
})

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)
  
  // Skip cross-origin requests (correct comparison)
  if (url.origin !== location.origin) {
    return
  }
  
  // Handle navigation requests (HTML pages)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => {
          // If offline, serve the offline page
          return caches.match(OFFLINE_URL)
        })
    )
    return
  }
  
  // Handle API requests
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/health')) {
    event.respondWith(handleApiRequest(request))
    return
  }
  
  // Handle static assets with cache-first strategy
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Serve from cache, but also fetch to update cache in background
          fetch(request)
            .then((networkResponse) => {
              if (networkResponse.status === 200) {
                const responseClone = networkResponse.clone()
                caches.open(CACHE_NAME)
                  .then((cache) => {
                    cache.put(request, responseClone)
                  })
              }
            })
            .catch(() => {
              // Network failed, but we have cached version
            })
          
          return cachedResponse
        }
        
        // Not in cache, fetch from network
        return fetch(request)
          .then((networkResponse) => {
            // Cache successful responses
            if (networkResponse.status === 200) {
              const responseClone = networkResponse.clone()
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(request, responseClone)
                })
            }
            return networkResponse
          })
      })
  )
})

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url)
  const isCacheableRoute = CACHEABLE_API_ROUTES.some(route => 
    url.pathname.startsWith(route)
  )
  
  try {
    // Always try network first for API requests
    const networkResponse = await fetch(request)
    
    // Cache successful GET requests for cacheable routes
    if (networkResponse.status === 200 && 
        request.method === 'GET' && 
        isCacheableRoute) {
      const responseClone = networkResponse.clone()
      const cache = await caches.open(API_CACHE_NAME)
      await cache.put(request, responseClone)
    }
    
    return networkResponse
    
  } catch (error) {
    // Network failed, try to serve from cache
    if (request.method === 'GET' && isCacheableRoute) {
      const cachedResponse = await caches.match(request)
      if (cachedResponse) {
        console.log('Service Worker: Serving API request from cache (offline)')
        return cachedResponse
      }
    }
    
    // Return a meaningful offline response
    return new Response(
      JSON.stringify({
        success: false,
        error: 'Network unavailable. Please check your connection.',
        offline: true,
        timestamp: new Date().toISOString()
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  }
}

// Background sync for failed API requests (future implementation)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-api') {
    event.waitUntil(handleBackgroundSync())
  }
})

async function handleBackgroundSync() {
  // This would handle retrying failed API requests when connection is restored
  console.log('Service Worker: Background sync triggered')
  
  // Implementation would:
  // 1. Get stored failed requests from IndexedDB
  // 2. Retry them
  // 3. Clean up successful requests
  // 4. Notify the main app of results
}

// Message handling for communication with the main app
self.addEventListener('message', (event) => {
  const { type, payload } = event.data
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting()
      break
      
    case 'CACHE_URLS':
      // Cache specific URLs on demand
      event.waitUntil(
        caches.open(CACHE_NAME)
          .then((cache) => cache.addAll(payload.urls))
      )
      break
      
    case 'CLEAR_CACHE':
      // Clear specific cache or all caches
      event.waitUntil(
        payload.cacheName 
          ? caches.delete(payload.cacheName)
          : caches.keys().then((names) => 
              Promise.all(names.map((name) => caches.delete(name)))
            )
      )
      break
      
    default:
      console.log('Service Worker: Unknown message type:', type)
  }
})

// Error handling
self.addEventListener('error', (event) => {
  console.error('Service Worker: Global error:', event.error)
})

self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker: Unhandled promise rejection:', event.reason)
  event.preventDefault()
})

console.log('Service Worker: Loaded successfully')