/**
 * PWA Service for handling service worker registration,
 * app updates, and offline capabilities
 */

// Service worker registration and lifecycle management
export class PWAService {
  private registration: ServiceWorkerRegistration | null = null
  private updateAvailable = false
  private updateCallbacks: Set<() => void> = new Set()
  private installPromptEvent: any = null

  constructor() {
    this.setupEventListeners()
  }

  /**
   * Register service worker
   */
  async register(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      // Only log warning in production, not development
      if (import.meta.env.PROD) {
        console.warn('PWA: Service Worker not supported in this browser')
      }
      return false
    }

    try {
      console.log('PWA: Registering service worker...')
      
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      })

      console.log('PWA: Service worker registered successfully')

      // Handle service worker updates
      this.registration.addEventListener('updatefound', () => {
        const newWorker = this.registration!.installing
        
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker installed, update available
              console.log('PWA: Update available')
              this.updateAvailable = true
              this.notifyUpdateCallbacks()
            }
          })
        }
      })

      // Listen for controlling service worker changes
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('PWA: Controller changed, reloading page')
        window.location.reload()
      })

      return true

    } catch (error) {
      console.error('PWA: Service worker registration failed:', error)
      return false
    }
  }

  /**
   * Update service worker to latest version
   */
  async update(): Promise<void> {
    if (!this.registration) {
      throw new Error('No service worker registered')
    }

    const newWorker = this.registration.waiting || this.registration.installing

    if (newWorker) {
      // Tell the waiting service worker to skip waiting
      newWorker.postMessage({ type: 'SKIP_WAITING' })
    }
  }

  /**
   * Check if app can be installed
   */
  canInstall(): boolean {
    return this.installPromptEvent !== null
  }

  /**
   * Prompt user to install app
   */
  async install(): Promise<boolean> {
    if (!this.installPromptEvent) {
      throw new Error('Install prompt not available')
    }

    try {
      const result = await this.installPromptEvent.prompt()
      const { outcome } = await result.userChoice

      if (outcome === 'accepted') {
        console.log('PWA: Install accepted')
        this.installPromptEvent = null
        return true
      } else {
        console.log('PWA: Install declined')
        return false
      }

    } catch (error) {
      console.error('PWA: Install prompt failed:', error)
      return false
    }
  }

  /**
   * Check if update is available
   */
  isUpdateAvailable(): boolean {
    return this.updateAvailable
  }

  /**
   * Add callback for update notifications
   */
  onUpdateAvailable(callback: () => void): void {
    this.updateCallbacks.add(callback)
  }

  /**
   * Remove update callback
   */
  offUpdateAvailable(callback: () => void): void {
    this.updateCallbacks.delete(callback)
  }

  /**
   * Get installation status
   */
  getInstallationStatus(): 'installed' | 'not-installed' | 'unknown' {
    // Check if app is running in standalone mode (installed)
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return 'installed'
    }

    // Check for iOS PWA
    if ((window.navigator as any).standalone === true) {
      return 'installed'
    }

    // Check if install prompt is available
    if (this.installPromptEvent) {
      return 'not-installed'
    }

    return 'unknown'
  }

  /**
   * Cache specific URLs
   */
  async cacheUrls(urls: string[]): Promise<void> {
    if (!this.registration || !this.registration.active) {
      throw new Error('No active service worker')
    }

    this.registration.active.postMessage({
      type: 'CACHE_URLS',
      payload: { urls }
    })
  }

  /**
   * Clear cache
   */
  async clearCache(cacheName?: string): Promise<void> {
    if (!this.registration || !this.registration.active) {
      throw new Error('No active service worker')
    }

    this.registration.active.postMessage({
      type: 'CLEAR_CACHE',
      payload: { cacheName }
    })
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault()
      this.installPromptEvent = event
      console.log('PWA: Install prompt available')
    })

    // Listen for app installed
    window.addEventListener('appinstalled', () => {
      console.log('PWA: App installed successfully')
      this.installPromptEvent = null
    })

    // Listen for online/offline events
    window.addEventListener('online', () => {
      console.log('PWA: App back online')
      this.broadcastConnectivityChange(true)
    })

    window.addEventListener('offline', () => {
      console.log('PWA: App offline')
      this.broadcastConnectivityChange(false)
    })
  }

  /**
   * Notify update callbacks
   */
  private notifyUpdateCallbacks(): void {
    this.updateCallbacks.forEach(callback => {
      try {
        callback()
      } catch (error) {
        console.error('PWA: Update callback error:', error)
      }
    })
  }

  /**
   * Broadcast connectivity changes
   */
  private broadcastConnectivityChange(online: boolean): void {
    // Dispatch custom event for connectivity changes
    window.dispatchEvent(new CustomEvent('pwa-connectivity-change', {
      detail: { online }
    }))
  }
}

// Create singleton instance
const pwaService = new PWAService()

// Utility functions for React components
export const usePWA = () => {
  return {
    register: () => pwaService.register(),
    update: () => pwaService.update(),
    install: () => pwaService.install(),
    canInstall: () => pwaService.canInstall(),
    isUpdateAvailable: () => pwaService.isUpdateAvailable(),
    onUpdateAvailable: (callback: () => void) => pwaService.onUpdateAvailable(callback),
    offUpdateAvailable: (callback: () => void) => pwaService.offUpdateAvailable(callback),
    getInstallationStatus: () => pwaService.getInstallationStatus(),
    cacheUrls: (urls: string[]) => pwaService.cacheUrls(urls),
    clearCache: (cacheName?: string) => pwaService.clearCache(cacheName),
  }
}

// Auto-register service worker when module is imported
export const initializePWA = async (): Promise<void> => {
  // Only register in production or when explicitly enabled
  if (import.meta.env.PROD || import.meta.env.VITE_ENABLE_PWA === 'true') {
    await pwaService.register()
  } else {
    console.log('PWA: Service worker registration skipped in development')
  }
}

export default pwaService