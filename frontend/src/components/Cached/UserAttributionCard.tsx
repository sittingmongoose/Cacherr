import React, { useState } from 'react'
import { 
  Users, 
  User, 
  Star, 
  Clock, 
  BarChart3, 
  ChevronDown,
  ChevronUp,
  Activity,
  Calendar,
  Eye
} from 'lucide-react'
import { UserCacheStatistics } from '@/types/api'
import { useUserCacheStatistics } from '@/hooks/useApi'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { classNames } from '@/utils/format'

/**
 * UserAttributionCard Component
 * 
 * Features:
 * - Multi-user attribution display
 * - Primary user highlighting
 * - Individual user statistics
 * - Expandable user details
 * - Recent activity per user
 * - Attribution context and reasons
 * - Responsive design
 * - Accessible interactions
 */

interface UserAttributionCardProps {
  users: string[]
  fileId?: string
  primaryUser?: string
  showStatistics?: boolean
  className?: string
}

interface UserCardProps {
  userId: string
  isPrimary?: boolean
  showStats?: boolean
  isExpanded?: boolean
  onToggleExpanded?: () => void
}

const UserCard: React.FC<UserCardProps> = ({
  userId,
  isPrimary = false,
  showStats = true,
  isExpanded = false,
  onToggleExpanded
}) => {
  const { 
    data: userStats, 
    isLoading: isLoadingStats 
  } = useUserCacheStatistics(userId, 30, { 
    immediate: showStats && isExpanded 
  })

  return (
    <div className={classNames(
      'border rounded-lg p-4 transition-all duration-200',
      isPrimary 
        ? 'border-primary-200 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20'
        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
    )}>
      {/* User Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={classNames(
            'p-2 rounded-full mr-3',
            isPrimary 
              ? 'bg-primary-100 dark:bg-primary-800 text-primary-600 dark:text-primary-300'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
          )}>
            <User className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center">
              <h4 className={classNames(
                'font-medium',
                isPrimary 
                  ? 'text-primary-900 dark:text-primary-100'
                  : 'text-gray-900 dark:text-gray-100'
              )}>
                {userId}
              </h4>
              {isPrimary && (
                <div className="ml-2 flex items-center">
                  <Star className="w-3 h-3 text-yellow-500 mr-1" />
                  <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                    Primary
                  </span>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {isPrimary ? 'Triggered this cache operation' : 'Associated with this file'}
            </p>
          </div>
        </div>

        {/* Expand/Collapse Button */}
        {showStats && onToggleExpanded && (
          <button
            onClick={onToggleExpanded}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Expanded Details */}
      {isExpanded && showStats && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          {isLoadingStats ? (
            <div className="flex items-center justify-center py-4">
              <LoadingSpinner size="sm" text="Loading user statistics..." />
            </div>
          ) : userStats ? (
            <div className="space-y-4">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {userStats.total_files}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Files
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {userStats.active_files}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Active
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {userStats.total_size_readable}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Size
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 dark:text-gray-100 capitalize">
                    {userStats.most_common_operation}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Top Op
                  </div>
                </div>
              </div>

              {/* Recent Files */}
              {userStats.recent_files && userStats.recent_files.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <Activity className="w-3 h-3 mr-1" />
                    Recent Files ({userStats.recent_files.length})
                  </h5>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {userStats.recent_files.map((file, index) => (
                      <div 
                        key={index}
                        className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-750 rounded p-2"
                      >
                        <div className="flex items-center min-w-0 flex-1">
                          <div className="w-2 h-2 rounded-full bg-gray-400 mr-2 flex-shrink-0" />
                          <span className="text-gray-700 dark:text-gray-300 truncate">
                            {file.filename}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 ml-2 flex-shrink-0">
                          <span className="text-gray-500 dark:text-gray-400">
                            {file.file_size_readable}
                          </span>
                          <span className="text-gray-400 dark:text-gray-500 capitalize">
                            {file.operation}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Time Period */}
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                <Calendar className="w-3 h-3 mr-1" />
                Statistics for last {userStats.period_days} days
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <User className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No statistics available for this user
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export const UserAttributionCard: React.FC<UserAttributionCardProps> = ({
  users,
  fileId,
  primaryUser,
  showStatistics = true,
  className
}) => {
  const [expandedUsers, setExpandedUsers] = useState<Set<string>>(new Set())

  const toggleUserExpanded = (userId: string) => {
    const newExpanded = new Set(expandedUsers)
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId)
    } else {
      newExpanded.add(userId)
    }
    setExpandedUsers(newExpanded)
  }

  // Sort users with primary user first
  const sortedUsers = [...users].sort((a, b) => {
    if (a === primaryUser) return -1
    if (b === primaryUser) return 1
    return a.localeCompare(b)
  })

  if (users.length === 0) {
    return (
      <div className={classNames(
        'bg-gray-50 dark:bg-gray-750 rounded-lg p-6 text-center',
        className
      )}>
        <Users className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No user attribution available
        </p>
      </div>
    )
  }

  return (
    <div className={classNames('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Users className="w-4 h-4 text-gray-400 mr-2" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
            User Attribution ({users.length})
          </h3>
        </div>
        
        {/* Summary Stats */}
        <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center">
            <Star className="w-3 h-3 mr-1" />
            <span>1 primary</span>
          </div>
          {users.length > 1 && (
            <div className="flex items-center">
              <User className="w-3 h-3 mr-1" />
              <span>{users.length - 1} associated</span>
            </div>
          )}
        </div>
      </div>

      {/* User Cards */}
      <div className="space-y-3">
        {sortedUsers.map((userId) => (
          <UserCard
            key={userId}
            userId={userId}
            isPrimary={userId === primaryUser}
            showStats={showStatistics}
            isExpanded={expandedUsers.has(userId)}
            onToggleExpanded={() => toggleUserExpanded(userId)}
          />
        ))}
      </div>

      {/* Additional Info */}
      {users.length > 1 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <div className="flex items-start">
            <Eye className="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Multi-User File
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                This file is associated with multiple users, which may indicate shared content or 
                overlapping watchlists. The primary user triggered the initial caching operation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <button 
          onClick={() => setExpandedUsers(new Set(users))}
          className="btn btn-ghost btn-sm text-xs"
        >
          <BarChart3 className="w-3 h-3 mr-1" />
          Expand All Stats
        </button>
        <button 
          onClick={() => setExpandedUsers(new Set())}
          className="btn btn-ghost btn-sm text-xs"
        >
          <ChevronUp className="w-3 h-3 mr-1" />
          Collapse All
        </button>
      </div>
    </div>
  )
}

export default UserAttributionCard