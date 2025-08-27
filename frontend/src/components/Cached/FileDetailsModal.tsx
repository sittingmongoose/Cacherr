import React, { useEffect, useState } from 'react'
import { 
  X, 
  FileText, 
  HardDrive, 
  Calendar, 
  Eye, 
  User,
  Users,
  MapPin,
  Settings,
  Trash2,
  Download,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Link,
  Info,
  Activity
} from 'lucide-react'
import { CachedFileInfo, RemoveCachedFileRequest } from '@/types/api'
import useAPI from '@/hooks/useApi'
import APIService from '@/services/api'
import { useCachedFilesOperations } from '@/hooks/useApi'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import StatusBadge from '@/components/common/StatusBadge'
import UserAttributionCard from './UserAttributionCard'
import { classNames } from '@/utils/format'

/**
 * FileDetailsModal Component
 * 
 * Features:
 * - Detailed file information display
 * - User attribution with context
 * - File operations (remove, download info)
 * - Metadata display
 * - Cache operation history
 * - Access statistics
 * - Responsive modal design
 * - Keyboard navigation support
 * - Real-time data updates
 */

interface FileDetailsModalProps {
  fileId: string
  isOpen: boolean
  onClose: () => void
  className?: string
}

export const FileDetailsModal: React.FC<FileDetailsModalProps> = ({
  fileId,
  isOpen,
  onClose,
  className
}) => {
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false)
  const [removeReason, setRemoveReason] = useState('')

  // API hooks
  const { 
    data: fileDetails, 
    isLoading, 
    error, 
    refetch 
  } = useAPI(
    () => APIService.getCachedFile(fileId),
    { 
      immediate: isOpen && !!fileId,
      onError: (error) => {
        console.error('Failed to fetch file details:', error)
      }
    }
  )

  const { 
    removeCachedFile, 
    isLoading: isRemoving 
  } = useCachedFilesOperations()

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Refresh data when modal opens
  useEffect(() => {
    if (isOpen && fileId) {
      refetch()
    }
  }, [isOpen, fileId, refetch])

  const handleRemoveFile = async () => {
    if (!fileDetails || !removeReason.trim()) return

    try {
      await removeCachedFile(fileDetails.id, {
        reason: removeReason.trim(),
        user_id: 'user' // This could be made dynamic
      })
      
      // Close modal after successful removal
      onClose()
    } catch (error) {
      // Error handled by hook
    } finally {
      setShowRemoveConfirm(false)
      setRemoveReason('')
    }
  }

  const getStatusIcon = (status: CachedFileInfo['status']) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'orphaned':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'pending_removal':
        return <Clock className="w-5 h-5 text-orange-500" />
      case 'removed':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />
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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add toast notification here
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className={classNames(
          'relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden',
          className
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <FileText className="w-6 h-6 text-gray-400 mr-3" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                File Details
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" text="Loading file details..." />
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Failed to load file details
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {error}
                </p>
                <button 
                  onClick={refetch}
                  className="btn btn-primary"
                >
                  Try Again
                </button>
              </div>
            ) : fileDetails ? (
              <div className="space-y-8">
                {/* File Overview */}
                <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start">
                      <FileText className="w-8 h-8 text-gray-400 mr-4 mt-1 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 break-all">
                          {fileDetails.filename}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 break-all">
                          {fileDetails.file_path}
                        </p>
                      </div>
                    </div>
                    <StatusBadge 
                      status={getStatusColor(fileDetails.status)}
                      icon={getStatusIcon(fileDetails.status)}
                    >
                      {fileDetails.status}
                    </StatusBadge>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <HardDrive className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {fileDetails.file_size_readable}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Size</p>
                    </div>
                    <div className="text-center">
                      <Eye className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {fileDetails.access_count}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Access Count</p>
                    </div>
                    <div className="text-center">
                      <Users className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {fileDetails.users.length}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Users</p>
                    </div>
                    <div className="text-center">
                      <Activity className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 capitalize">
                        {fileDetails.triggered_by_operation}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Operation</p>
                    </div>
                  </div>
                </div>

                {/* File Paths and Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                        <MapPin className="w-4 h-4 mr-2" />
                        File Locations
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Original Path
                          </label>
                          <div className="flex items-center mt-1">
                            <code className="flex-1 text-sm bg-gray-100 dark:bg-gray-700 rounded px-2 py-1 break-all">
                              {fileDetails.original_path}
                            </code>
                            <button
                              onClick={() => copyToClipboard(fileDetails.original_path)}
                              className="ml-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              title="Copy to clipboard"
                            >
                              <Link className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            Cached Path
                          </label>
                          <div className="flex items-center mt-1">
                            <code className="flex-1 text-sm bg-gray-100 dark:bg-gray-700 rounded px-2 py-1 break-all">
                              {fileDetails.cached_path}
                            </code>
                            <button
                              onClick={() => copyToClipboard(fileDetails.cached_path)}
                              className="ml-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              title="Copy to clipboard"
                            >
                              <Link className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                        <Settings className="w-4 h-4 mr-2" />
                        Cache Configuration
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Cache Method:</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {fileDetails.cache_method}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">File Size (bytes):</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {fileDetails.file_size_bytes.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                        <Calendar className="w-4 h-4 mr-2" />
                        Timeline
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Cached At:</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {formatDate(fileDetails.cached_at)}
                          </span>
                        </div>
                        {fileDetails.last_accessed && (
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Last Accessed:</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">
                              {formatDate(fileDetails.last_accessed)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                        <User className="w-4 h-4 mr-2" />
                        Attribution
                      </h4>
                      <div className="space-y-2 text-sm">
                        {fileDetails.triggered_by_user && (
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Triggered By:</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">
                              {fileDetails.triggered_by_user}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Operation:</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                            {fileDetails.triggered_by_operation.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* User Attribution */}
                {fileDetails.users.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                      <Users className="w-4 h-4 mr-2" />
                      User Attribution ({fileDetails.users.length})
                    </h4>
                    <UserAttributionCard 
                      users={fileDetails.users}
                      fileId={fileDetails.id}
                      primaryUser={fileDetails.triggered_by_user}
                    />
                  </div>
                )}

                {/* Metadata */}
                {fileDetails.metadata && Object.keys(fileDetails.metadata).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                      <Info className="w-4 h-4 mr-2" />
                      Metadata
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4">
                      <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                        {JSON.stringify(fileDetails.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <button
                      onClick={() => setShowRemoveConfirm(true)}
                      disabled={fileDetails.status === 'removed' || isRemoving}
                      className="btn btn-error flex-1 sm:flex-none"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Remove from Cache
                    </button>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(fileDetails, null, 2))}
                      className="btn btn-secondary flex-1 sm:flex-none"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export Details
                    </button>
                  </div>
                </div>

                {/* Remove Confirmation */}
                {showRemoveConfirm && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <div className="flex items-start">
                      <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h5 className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
                          Remove Cached File
                        </h5>
                        <p className="text-sm text-red-700 dark:text-red-300 mb-4">
                          This will remove the file from cache tracking. Please provide a reason:
                        </p>
                        <textarea
                          value={removeReason}
                          onChange={(e) => setRemoveReason(e.target.value)}
                          placeholder="Reason for removal..."
                          className="w-full px-3 py-2 text-sm border border-red-300 dark:border-red-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500"
                          rows={3}
                        />
                        <div className="flex gap-3 mt-4">
                          <button
                            onClick={handleRemoveFile}
                            disabled={!removeReason.trim() || isRemoving}
                            className="btn btn-error btn-sm"
                          >
                            {isRemoving ? (
                              <>
                                <LoadingSpinner size="sm" className="mr-2" />
                                Removing...
                              </>
                            ) : (
                              'Confirm Remove'
                            )}
                          </button>
                          <button
                            onClick={() => {
                              setShowRemoveConfirm(false)
                              setRemoveReason('')
                            }}
                            className="btn btn-ghost btn-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileDetailsModal