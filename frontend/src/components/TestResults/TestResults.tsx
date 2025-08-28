import React, { useState, useMemo } from 'react'
import { 
  TestTube, 
  FileText, 
  HardDrive, 
  ChevronDown, 
  ChevronRight,
  Download,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react'
import { TestResults as TestResultsType, TestOperationResult, FileDetail } from '@/types/api'
import { LoadingSpinner, CardLoader } from '@/components/common/LoadingSpinner'
import { formatBytes, formatFilePath, formatOperationType, classNames } from '@/utils/format'

/**
 * TestResults component displays test mode analysis results
 * 
 * Features:
 * - Expandable operation sections
 * - File detail listings
 * - Size calculations and summaries
 * - Export functionality
 * - Search and filtering
 * - Responsive design
 * - Accessibility support
 */
interface TestResultsProps {
  testResults?: TestResultsType
  isLoading?: boolean
  error?: string
  onRefresh?: () => void
  className?: string
}

interface OperationSectionProps {
  operationType: string
  operationData: TestOperationResult
  isExpanded: boolean
  onToggleExpand: () => void
  searchTerm?: string
}

const OperationSection: React.FC<OperationSectionProps> = ({
  operationType,
  operationData,
  isExpanded,
  onToggleExpand,
  searchTerm = '',
}) => {
  const filteredFiles = useMemo(() => {
    if (!searchTerm.trim()) return operationData.file_details

    const term = searchTerm.toLowerCase()
    return operationData.file_details.filter(file =>
      file.filename.toLowerCase().includes(term) ||
      file.directory.toLowerCase().includes(term)
    )
  }, [operationData.file_details, searchTerm])

  const getOperationIcon = (type: string) => {
    if (type.includes('cache')) return <HardDrive className="w-5 h-5" />
    if (type.includes('array')) return <FileText className="w-5 h-5" />
    return <TestTube className="w-5 h-5" />
  }

  const getOperationColor = (type: string) => {
    if (type.includes('cache')) return 'text-blue-600'
    if (type.includes('array')) return 'text-green-600'
    return 'text-purple-600'
  }

  if (operationData.file_count === 0) {
    return null
  }

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Operation Header */}
      <button
        onClick={onToggleExpand}
        className="w-full px-6 py-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        aria-expanded={isExpanded}
        aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${formatOperationType(operationType)} section`}
      >
        <div className="flex items-center space-x-3">
          <div className={classNames('flex-shrink-0', getOperationColor(operationType))}>
            {getOperationIcon(operationType)}
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {formatOperationType(operationType)}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {operationData.file_count} files • {operationData.total_size_readable}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {searchTerm && filteredFiles.length !== operationData.file_details.length && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {filteredFiles.length} of {operationData.file_details.length}
            </span>
          )}
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Operation Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Summary */}
          <div className="px-6 py-4 bg-white dark:bg-gray-800">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                  {operationData.file_count}
                </div>
                <div className="text-gray-600 dark:text-gray-400">Files</div>
              </div>
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {formatBytes(operationData.total_size_bytes)}
                </div>
                <div className="text-gray-600 dark:text-gray-400">Total Size</div>
              </div>
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {Math.round(operationData.total_size_bytes / operationData.file_count / 1024 / 1024)}MB
                </div>
                <div className="text-gray-600 dark:text-gray-400">Avg Size</div>
              </div>
            </div>
          </div>

          {/* File List */}
          {filteredFiles.length > 0 ? (
            <div className="px-6 py-4 space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                File Details {searchTerm && `(filtered: ${filteredFiles.length})`}
              </h4>
              <div className="max-h-96 overflow-y-auto space-y-2">
                {filteredFiles.map((file, index) => (
                  <div
                    key={`${file.filename}-${index}`}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                        {file.filename}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                        {formatFilePath(file.directory)}
                      </div>
                      {file.last_modified && (
                        <div className="text-xs text-gray-500 dark:text-gray-500">
                          Modified: {new Date(file.last_modified).toLocaleString()}
                        </div>
                      )}
                    </div>
                    <div className="flex-shrink-0 ml-4 text-right">
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {file.size_readable}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-500 capitalize">
                        {file.operation_type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : searchTerm ? (
            <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
              No files match the search term "{searchTerm}"
            </div>
          ) : (
            <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
              No files found for this operation
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export const TestResults: React.FC<TestResultsProps> = ({
  testResults,
  isLoading = false,
  error,
  onRefresh,
  className
}) => {
  // State
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [showEmptyOperations, setShowEmptyOperations] = useState(false)

  // Calculate totals
  const totals = useMemo(() => {
    if (!testResults) return { files: 0, size: 0 }

    return Object.values(testResults).reduce(
      (acc, operation) => ({
        files: acc.files + operation.file_count,
        size: acc.size + operation.total_size_bytes,
      }),
      { files: 0, size: 0 }
    )
  }, [testResults])

  // Get operations with data
  const operationsWithData = useMemo(() => {
    if (!testResults) return []

    return Object.entries(testResults).filter(([_, data]) => 
      showEmptyOperations || data.file_count > 0
    )
  }, [testResults, showEmptyOperations])

  const handleToggleExpand = (operationType: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(operationType)) {
        newSet.delete(operationType)
      } else {
        newSet.add(operationType)
      }
      return newSet
    })
  }

  const handleExpandAll = () => {
    if (!testResults) return
    setExpandedSections(new Set(Object.keys(testResults)))
  }

  const handleCollapseAll = () => {
    setExpandedSections(new Set())
  }

  const handleExportResults = () => {
    if (!testResults) return

    let exportData = 'Cacherr Test Results\n'
    exportData += `Generated: ${new Date().toLocaleString()}\n\n`
    exportData += `Summary:\n`
    exportData += `- Total Files: ${totals.files}\n`
    exportData += `- Total Size: ${formatBytes(totals.size)}\n\n`

    Object.entries(testResults).forEach(([operationType, data]) => {
      if (data.file_count === 0) return

      exportData += `\n${formatOperationType(operationType)}:\n`
      exportData += `- Files: ${data.file_count}\n`
      exportData += `- Size: ${data.total_size_readable}\n`
      exportData += `Files:\n`
      
      data.file_details.forEach(file => {
        exportData += `  - ${file.filename} (${file.size_readable})\n`
        exportData += `    Path: ${file.directory}\n`
      })
    })

    const blob = new Blob([exportData], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test-results-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (error) {
    return (
      <div className={classNames('card bg-error-50 border-error-200 dark:bg-error-900/20 dark:border-error-800', className)}>
        <div className="text-center py-8">
          <TestTube className="w-12 h-12 text-error-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-error-900 dark:text-error-100 mb-2">
            Failed to Load Test Results
          </h3>
          <p className="text-error-700 dark:text-error-300 mb-4">
            {error}
          </p>
          {onRefresh && (
            <button onClick={onRefresh} className="btn btn-primary">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  if (isLoading || !testResults) {
    return (
      <div className={classNames('card', className)}>
        <CardLoader text="Loading test results..." />
      </div>
    )
  }

  if (Object.keys(testResults).length === 0 || totals.files === 0) {
    return (
      <div className={classNames('card', className)}>
        <div className="text-center py-12">
          <TestTube className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Test Results Available
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Run test mode to see what files would be processed by cache operations.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={classNames('card', className)}>
      {/* Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Test Mode Results
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Analysis of {totals.files} files ({formatBytes(totals.size)}) across {operationsWithData.length} operations
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {/* Export button */}
            <button
              onClick={handleExportResults}
              className="btn btn-ghost btn-sm"
              title="Export results"
            >
              <Download className="w-4 h-4" />
            </button>

            {/* Refresh button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="btn btn-ghost btn-sm"
                title="Refresh results"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={showEmptyOperations}
                onChange={(e) => setShowEmptyOperations(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-gray-600 dark:text-gray-400">Show empty operations</span>
            </label>

            <button
              onClick={handleExpandAll}
              className="btn btn-ghost btn-sm"
            >
              Expand All
            </button>
            
            <button
              onClick={handleCollapseAll}
              className="btn btn-ghost btn-sm"
            >
              Collapse All
            </button>
          </div>
        </div>
      </div>

      {/* Operations */}
      <div className="p-6 space-y-4">
        {operationsWithData.map(([operationType, operationData]) => (
          <OperationSection
            key={operationType}
            operationType={operationType}
            operationData={operationData}
            isExpanded={expandedSections.has(operationType)}
            onToggleExpand={() => handleToggleExpand(operationType)}
            searchTerm={searchTerm}
          />
        ))}

        {operationsWithData.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            {showEmptyOperations ? 'No operations found' : 'No operations with files found'}
          </div>
        )}
      </div>
    </div>
  )
}

export default TestResults