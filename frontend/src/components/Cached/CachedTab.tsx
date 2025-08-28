import React, { useState, useEffect } from 'react'
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Download,
  Trash2,
  Users,
  BarChart3,
  FileText,
  Clock,
  HardDrive
} from 'lucide-react'
import { CachedFilesFilter } from '@/types/api'
import { useCachedFilesRealTime, useCachedFilesOperations } from '@/hooks/useApi'
import { useAppContext } from '@/store/AppContext'
import { LoadingSpinner, FullPageLoader } from '@/components/common/LoadingSpinner'
import { classNames } from '@/utils/format'
import webSocketService from '@/services/websocket'

// Import child components (will be created)
import CachedFilesView from './CachedFilesView'
import CacheStatistics from './CacheStatistics'
import CacheActionsPanel from './CacheActionsPanel'
import FileDetailsModal from './FileDetailsModal'

/**
 * Main Cached Tab Component
 * 
 * Features:
 * - Real-time cached files monitoring
 * - Advanced filtering and search capabilities
 * - Cache statistics dashboard
 * - File management operations
 * - Multi-user attribution tracking
 * - Export functionality
 * - Responsive design with mobile support
 * - WebSocket integration for live updates
 */

interface CachedTabProps {
  className?: string
}

export const CachedTab: React.FC<CachedTabProps> = ({ className }) => {
  // State management
  const { state } = useAppContext()
  const [filter, setFilter] = useState<CachedFilesFilter>({ limit: 50, offset: 0 })
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [activeView, setActiveView] = useState<'files' | 'stats'>('files')

  // API hooks
  const { 
    cachedFiles, 
    cacheStatistics, 
    refreshAll, 
    isLoading 
  } = useCachedFilesRealTime(filter)
  
  const {
    isLoading: isOperationLoading,
    cleanupCache,
    exportCachedFiles,
    searchCachedFiles
  } = useCachedFilesOperations()

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    webSocketService.connect()
    
    // Listen for cache-related WebSocket events
    const handleCacheUpdate = () => {
      refreshAll()
    }

    // Add event listeners for cache updates
    webSocketService.addEventListener('cache_file_added', handleCacheUpdate)
    webSocketService.addEventListener('cache_file_removed', handleCacheUpdate)
    webSocketService.addEventListener('cache_statistics_updated', handleCacheUpdate)
    
    return () => {
      webSocketService.removeEventListener('cache_file_added', handleCacheUpdate)
      webSocketService.removeEventListener('cache_file_removed', handleCacheUpdate)
      webSocketService.removeEventListener('cache_statistics_updated', handleCacheUpdate)
    }
  }, [refreshAll])

  // Event handlers
  const handleSearch = async (term: string) => {
    setSearchTerm(term)
    if (term.trim()) {
      try {
        const results = await searchCachedFiles(term, 'all', 50)
        setFilter(prev => ({ ...prev, search: term, offset: 0 }))
      } catch (error) {
        // Error handled by hook
      }
    } else {
      setFilter(prev => ({ ...prev, search: undefined, offset: 0 }))
    }
  }

  const handleFilterChange = (newFilter: Partial<CachedFilesFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter, offset: 0 }))
  }

  const handlePageChange = (page: number) => {
    const offset = page * (filter.limit || 50)
    setFilter(prev => ({ ...prev, offset }))
  }

  const handleExport = async (format: 'csv' | 'json' | 'txt') => {
    try {
      await exportCachedFiles(format, filter, true)
    } catch (error) {
      // Error handled by hook
    }
  }

  const handleCleanup = async (removeOrphaned: boolean = false) => {
    try {
      await cleanupCache({ 
        remove_orphaned: removeOrphaned,
        user_id: 'system' // Could be made dynamic based on current user
      })
      // Refresh data after cleanup
      refreshAll()
    } catch (error) {
      // Error handled by hook
    }
  }

  const handleFileSelect = (fileId: string) => {
    setSelectedFileId(fileId)
  }

  const handleCloseModal = () => {
    setSelectedFileId(null)
  }

  // Get current data
  const files = cachedFiles.data?.files || []
  const pagination = cachedFiles.data?.pagination
  const statistics = cacheStatistics.data
  const error = cachedFiles.error || cacheStatistics.error

  // Show loading state on initial load
  if (isLoading && !files.length && !statistics) {
    return <FullPageLoader text="Loading cached files data..." />
  }

  return (
    <div className={classNames('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Title and Navigation */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <HardDrive className="w-6 h-6 text-primary-600 mr-2" />
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  Cached Files
                </h1>
              </div>

              {/* View Toggle */}
              <div className="hidden sm:flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setActiveView('files')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'files'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <FileText className="w-4 h-4 mr-1 inline" />
                  Files
                </button>
                <button
                  onClick={() => setActiveView('stats')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'stats'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <BarChart3 className="w-4 h-4 mr-1 inline" />
                  Statistics
                </button>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3">
              {/* Quick Stats */}
              {statistics && (
                <div className="hidden lg:flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center">
                    <FileText className="w-4 h-4 mr-1" />
                    <span>{statistics.total_files} files</span>
                  </div>
                  <div className="flex items-center">
                    <HardDrive className="w-4 h-4 mr-1" />
                    <span>{statistics.total_size_readable}</span>
                  </div>
                  <div className="flex items-center">
                    <Users className="w-4 h-4 mr-1" />
                    <span>{statistics.users_count} users</span>
                  </div>
                </div>
              )}

              {/* Refresh */}
              <button
                onClick={refreshAll}
                disabled={isLoading}
                className="btn btn-ghost p-2"
                aria-label="Refresh cached files data"
              >
                <RefreshCw className={classNames(
                  'w-4 h-4',
                  isLoading && 'animate-spin'
                )} />
              </button>

              {/* Export */}
              <div className="relative">
                <button
                  className="btn btn-ghost p-2"
                  aria-label="Export cached files"
                  onClick={() => handleExport('csv')}
                  disabled={isOperationLoading}
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Filters Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={classNames(
                  'btn btn-ghost p-2',
                  showFilters && 'bg-gray-100 dark:bg-gray-700'
                )}
                aria-label="Toggle filters"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="pb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search cached files..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              {searchTerm && (
                <button
                  onClick={() => handleSearch('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Error Message */}
          {error && (
            <div className="bg-error-50 border border-error-200 rounded-lg p-4 dark:bg-error-900/20 dark:border-error-800">
              <p className="text-error-700 dark:text-error-300">
                {error}
              </p>
            </div>
          )}

          {/* Status Info */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {activeView === 'files' ? 'Cached Files' : 'Cache Statistics'}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Last updated: {cachedFiles.lastFetched?.toLocaleTimeString() || 'Never'}
                {state.ui.autoRefresh && (
                  <span className="ml-2 text-xs">
                    (refreshes every {state.ui.refreshInterval / 1000}s)
                  </span>
                )}
              </p>
            </div>
            
            {isLoading && (
              <LoadingSpinner size="sm" text="Updating..." />
            )}
          </div>

          {/* Cache Actions Panel */}
          <CacheActionsPanel
            statistics={statistics}
            onCleanup={handleCleanup}
            onExport={handleExport}
            isLoading={isOperationLoading}
            className={showFilters ? 'block' : 'hidden lg:block'}
          />

          {/* Main Content Area */}
          {activeView === 'files' ? (
            <CachedFilesView
              files={files}
              pagination={pagination}
              filter={filter}
              isLoading={isLoading}
              showFilters={showFilters}
              onFilterChange={handleFilterChange}
              onPageChange={handlePageChange}
              onFileSelect={handleFileSelect}
            />
          ) : (
            <CacheStatistics
              statistics={statistics}
              isLoading={cacheStatistics.isLoading}
            />
          )}
        </div>
      </main>

      {/* File Details Modal */}
      {selectedFileId && (
        <FileDetailsModal
          fileId={selectedFileId}
          isOpen={!!selectedFileId}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}

export default CachedTab