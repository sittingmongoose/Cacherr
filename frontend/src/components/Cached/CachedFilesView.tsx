import React, { useState, useMemo } from 'react'
import { 
  ChevronLeft, 
  ChevronRight, 
  Clock, 
  User,
  Users,
  FileText,
  HardDrive,
  Eye,
  AlertCircle,
  CheckCircle,
  XCircle,
  Trash2,
  Filter,
  SortAsc,
  SortDesc,
  Calendar,
  Search
} from 'lucide-react'
import { CachedFileInfo, CachedFilesFilter } from '../../types/api'
import { LoadingSpinner, CardLoader, SkeletonLoader } from '../common/LoadingSpinner'
import StatusBadge from '../common/StatusBadge'
import { classNames } from '../../utils/format'
import { useCachedFilesOperations } from '../../hooks/useApi'

/**
 * CachedFilesView Component
 * 
 * Features:
 * - Filterable and searchable file list
 * - Pagination support
 * - Sortable columns
 * - Detailed file information cards
 * - User attribution display
 * - Status indicators
 * - Responsive design
 * - Bulk actions
 */

interface CachedFilesViewProps {
  files: CachedFileInfo[]
  pagination?: {
    limit: number
    offset: number
    total_count: number
    has_more: boolean
  }
  filter: CachedFilesFilter
  isLoading?: boolean
  showFilters?: boolean
  onFilterChange: (filter: Partial<CachedFilesFilter>) => void
  onPageChange: (page: number) => void
  onFileSelect: (fileId: string) => void
  className?: string
}

type SortField = 'filename' | 'file_size_bytes' | 'cached_at' | 'access_count' | 'status'
type SortOrder = 'asc' | 'desc'

export const CachedFilesView: React.FC<CachedFilesViewProps> = ({
  files,
  pagination,
  filter,
  isLoading = false,
  showFilters = false,
  onFilterChange,
  onPageChange,
  onFileSelect,
  className
}) => {
  // Local state for sorting and selection
  const [sortField, setSortField] = useState<SortField>('cached_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')

  // Operations hook for bulk actions
  const { removeCachedFile, isLoading: isOperationLoading } = useCachedFilesOperations()

  // Sort files based on current sort settings
  const sortedFiles = useMemo(() => {
    if (!files.length) return files

    return [...files].sort((a, b) => {
      let aVal: any = a[sortField]
      let bVal: any = b[sortField]

      // Handle different data types
      if (sortField === 'file_size_bytes' || sortField === 'access_count') {
        aVal = Number(aVal)
        bVal = Number(bVal)
      } else if (sortField === 'cached_at') {
        aVal = new Date(aVal).getTime()
        bVal = new Date(bVal).getTime()
      } else {
        aVal = String(aVal).toLowerCase()
        bVal = String(bVal).toLowerCase()
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
  }, [files, sortField, sortOrder])

  // Event handlers
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }

  const handleSelectFile = (fileId: string) => {
    const newSelection = new Set(selectedFiles)
    if (newSelection.has(fileId)) {
      newSelection.delete(fileId)
    } else {
      newSelection.add(fileId)
    }
    setSelectedFiles(newSelection)
  }

  const handleSelectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(files.map(f => f.id)))
    }
  }

  const handleBulkRemove = async () => {
    if (selectedFiles.size === 0) return

    const confirmed = confirm(`Are you sure you want to remove ${selectedFiles.size} cached files?`)
    if (!confirmed) return

    try {
      await Promise.all(
        Array.from(selectedFiles).map(fileId =>
          removeCachedFile(fileId, { reason: 'bulk_removal', user_id: 'user' })
        )
      )
      setSelectedFiles(new Set())
    } catch (error) {
      // Error handled by hook
    }
  }

  const getStatusIcon = (status: CachedFileInfo['status']) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'orphaned':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'pending_removal':
        return <Clock className="w-4 h-4 text-orange-500" />
      case 'removed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: CachedFileInfo['status']) => {
    switch (status) {
      case 'active': return 'success'
      case 'orphaned': return 'warning'
      case 'pending_removal': return 'warning'
      case 'removed': return 'error'
      default: return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const currentPage = Math.floor((pagination?.offset || 0) / (pagination?.limit || 50))
  const totalPages = Math.ceil((pagination?.total_count || 0) / (pagination?.limit || 50))

  if (isLoading && !files.length) {
    return (
      <div className={classNames('space-y-6', className)}>
        <CardLoader text="Loading cached files..." />
      </div>
    )
  }

  return (
    <div className={classNames('space-y-6', className)}>
      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Filters
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <select
                value={filter.status || ''}
                onChange={(e) => onFilterChange({ status: e.target.value as CachedFileInfo['status'] || undefined })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="orphaned">Orphaned</option>
                <option value="pending_removal">Pending Removal</option>
                <option value="removed">Removed</option>
              </select>
            </div>

            {/* Operation Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Operation Type
              </label>
              <select
                value={filter.triggered_by_operation || ''}
                onChange={(e) => onFilterChange({ 
                  triggered_by_operation: (e.target.value || undefined) as CachedFileInfo['triggered_by_operation'] | undefined 
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="">All Operations</option>
                <option value="watchlist">Watchlist</option>
                <option value="ondeck">On Deck</option>
                <option value="trakt">Trakt</option>
                <option value="manual">Manual</option>
                <option value="continue_watching">Continue Watching</option>
                <option value="real_time_watch">Real-time Watch</option>
              </select>
            </div>

            {/* User Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                User
              </label>
              <input
                type="text"
                placeholder="Filter by user..."
                value={filter.user_id || ''}
                onChange={(e) => onFilterChange({ user_id: e.target.value || undefined })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>

            {/* Date Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Cached Since
              </label>
              <input
                type="date"
                value={filter.cached_since?.split('T')[0] || ''}
                onChange={(e) => onFilterChange({ cached_since: e.target.value ? `${e.target.value}T00:00:00Z` : undefined })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          </div>

          {/* Clear Filters */}
          <div className="flex justify-end mt-4">
            <button
              onClick={() => onFilterChange({ 
                status: undefined, 
                triggered_by_operation: undefined, 
                user_id: undefined, 
                cached_since: undefined 
              })}
              className="btn btn-ghost text-sm"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* List Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Files ({pagination?.total_count || files.length})
              </h3>
              
              {/* Bulk Actions */}
              {selectedFiles.size > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedFiles.size} selected
                  </span>
                  <button
                    onClick={handleBulkRemove}
                    disabled={isOperationLoading}
                    className="btn btn-sm btn-error"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Remove
                  </button>
                </div>
              )}
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setViewMode('list')}
                className={classNames(
                  'p-2 rounded-md',
                  viewMode === 'list' 
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400'
                    : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                )}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 16a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={classNames(
                  'p-2 rounded-md',
                  viewMode === 'grid' 
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400'
                    : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                )}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Files List */}
        <div className="p-6">
          {files.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No cached files found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {filter.search || filter.status || filter.user_id || filter.triggered_by_operation
                  ? 'Try adjusting your filters to see more results.'
                  : 'Cache some files to see them here.'}
              </p>
            </div>
          ) : viewMode === 'list' ? (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4">
                      <input
                        type="checkbox"
                        checked={selectedFiles.size === files.length && files.length > 0}
                        onChange={handleSelectAll}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                    </th>
                    <th className="text-left py-3 px-4">
                      <button
                        onClick={() => handleSort('filename')}
                        className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        <span>File</span>
                        {sortField === 'filename' && (
                          sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="text-left py-3 px-4">
                      <button
                        onClick={() => handleSort('file_size_bytes')}
                        className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        <span>Size</span>
                        {sortField === 'file_size_bytes' && (
                          sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="text-left py-3 px-4">
                      <button
                        onClick={() => handleSort('status')}
                        className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        <span>Status</span>
                        {sortField === 'status' && (
                          sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="text-left py-3 px-4">
                      <button
                        onClick={() => handleSort('cached_at')}
                        className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        <span>Cached</span>
                        {sortField === 'cached_at' && (
                          sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="text-left py-3 px-4">
                      <button
                        onClick={() => handleSort('access_count')}
                        className="flex items-center space-x-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                      >
                        <span>Access</span>
                        {sortField === 'access_count' && (
                          sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="text-left py-3 px-4">Users</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFiles.map((file) => (
                    <tr 
                      key={file.id}
                      className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750"
                    >
                      <td className="py-4 px-4">
                        <input
                          type="checkbox"
                          checked={selectedFiles.has(file.id)}
                          onChange={() => handleSelectFile(file.id)}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center">
                          <FileText className="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                              {file.filename}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                              {file.triggered_by_operation}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-gray-900 dark:text-gray-100">
                          {file.file_size_readable}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <StatusBadge 
                          status={file.status}
                          icon={getStatusIcon(file.status)}
                        />
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(file.cached_at)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center">
                          <Eye className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-900 dark:text-gray-100">
                            {file.access_count}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center">
                          {file.users.length > 1 ? (
                            <Users className="w-4 h-4 text-gray-400 mr-1" />
                          ) : (
                            <User className="w-4 h-4 text-gray-400 mr-1" />
                          )}
                          <span className="text-sm text-gray-900 dark:text-gray-100">
                            {file.users.length}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <button
                          onClick={() => onFileSelect(file.id)}
                          className="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Grid View */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sortedFiles.map((file) => (
                <div
                  key={file.id}
                  className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center min-w-0 flex-1">
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(file.id)}
                        onChange={() => handleSelectFile(file.id)}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-3 flex-shrink-0"
                      />
                      <FileText className="w-5 h-5 text-gray-400 mr-2 flex-shrink-0" />
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {file.filename}
                      </h4>
                    </div>
                    <StatusBadge 
                      status={file.status}
                      icon={getStatusIcon(file.status)}
                      size="sm"
                    />
                  </div>
                  
                  <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
                    <div className="flex items-center justify-between">
                      <span>Size:</span>
                      <span className="font-medium">{file.file_size_readable}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Operation:</span>
                      <span className="font-medium">{file.triggered_by_operation}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Users:</span>
                      <span className="font-medium">{file.users.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Access:</span>
                      <span className="font-medium">{file.access_count}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Cached:</span>
                      <span className="font-medium">{formatDate(file.cached_at)}</span>
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <button
                      onClick={() => onFileSelect(file.id)}
                      className="w-full btn btn-sm btn-primary"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {pagination && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Showing {(pagination.offset + 1)} - {Math.min(pagination.offset + pagination.limit, pagination.total_count)} of {pagination.total_count} files
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage === 0}
                  className="btn btn-ghost btn-sm"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const page = currentPage <= 2 
                      ? i 
                      : currentPage >= totalPages - 2 
                        ? totalPages - 5 + i
                        : currentPage - 2 + i
                        
                    if (page < 0 || page >= totalPages) return null
                    
                    return (
                      <button
                        key={page}
                        onClick={() => onPageChange(page)}
                        className={classNames(
                          'px-3 py-1 text-sm rounded-md',
                          page === currentPage
                            ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                        )}
                      >
                        {page + 1}
                      </button>
                    )
                  })}
                </div>
                
                <button
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages - 1}
                  className="btn btn-ghost btn-sm"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading Overlay */}
      {isLoading && files.length > 0 && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 flex items-center justify-center">
          <LoadingSpinner size="lg" text="Updating files..." />
        </div>
      )}
    </div>
  )
}

export default CachedFilesView