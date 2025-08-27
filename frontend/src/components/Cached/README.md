# Cached Tab Components

A comprehensive React implementation for managing and monitoring cached files in PlexCacheUltra. This tab provides real-time visibility into cached files, user attribution, performance statistics, and management operations.

## Component Overview

### Core Components

#### `CachedTab.tsx`
**Main container component that orchestrates the entire cached files experience.**

**Features:**
- Real-time WebSocket integration for live updates
- View switching between Files and Statistics
- Global search functionality
- Filter management
- Export operations
- Cache cleanup operations
- Responsive header with quick stats
- Error handling and loading states

**Key Props:**
```typescript
interface CachedTabProps {
  className?: string
}
```

#### `CachedFilesView.tsx`
**Advanced file list view with comprehensive filtering and management capabilities.**

**Features:**
- List and grid view modes
- Advanced filtering by status, user, operation type, date
- Multi-column sorting with visual indicators
- Bulk selection and operations
- Pagination with navigation
- File search and filtering
- Responsive design for mobile/desktop
- Accessibility compliance

**Key Props:**
```typescript
interface CachedFilesViewProps {
  files: CachedFileInfo[]
  pagination?: PaginationInfo
  filter: CachedFilesFilter
  isLoading?: boolean
  showFilters?: boolean
  onFilterChange: (filter: Partial<CachedFilesFilter>) => void
  onPageChange: (page: number) => void
  onFileSelect: (fileId: string) => void
}
```

#### `CacheStatistics.tsx`
**Comprehensive dashboard displaying cache performance and analytics.**

**Features:**
- Visual statistics cards with trend indicators
- File status breakdown with progress bars
- Cache health assessment
- Performance recommendations
- Quick action buttons
- Mobile-responsive layout
- Loading states and empty states

**Key Props:**
```typescript
interface CacheStatisticsProps {
  statistics: CacheStatistics | null
  isLoading?: boolean
  className?: string
}
```

#### `FileDetailsModal.tsx`
**Detailed file information modal with management capabilities.**

**Features:**
- Complete file metadata display
- File path information with copy-to-clipboard
- User attribution details
- Access statistics
- Cache configuration details
- File removal functionality with confirmation
- Metadata JSON viewer
- Keyboard navigation support

**Key Props:**
```typescript
interface FileDetailsModalProps {
  fileId: string
  isOpen: boolean
  onClose: () => void
}
```

#### `UserAttributionCard.tsx`
**Multi-user attribution display with expandable user statistics.**

**Features:**
- Primary user highlighting
- Individual user statistics on expansion
- Recent activity per user
- User contribution metrics
- Multi-user file indicators
- Expandable/collapsible interface

**Key Props:**
```typescript
interface UserAttributionCardProps {
  users: string[]
  fileId?: string
  primaryUser?: string
  showStatistics?: boolean
}
```

#### `CacheActionsPanel.tsx`
**Management operations panel with safety confirmations.**

**Features:**
- Cache cleanup operations with preview
- Export functionality with format selection
- Cache health monitoring
- Quick statistics display
- Action confirmations and safety checks
- Progress indicators
- Batch operation support

**Key Props:**
```typescript
interface CacheActionsPanelProps {
  statistics: CacheStatistics | null
  onCleanup: (removeOrphaned?: boolean) => Promise<void>
  onExport: (format: 'csv' | 'json' | 'txt') => Promise<void>
  isLoading?: boolean
}
```

## API Integration

### Custom Hooks

#### `useCachedFiles(filter, options)`
Fetches cached files with filtering and pagination support.

#### `useCacheStatistics(options)`
Retrieves comprehensive cache statistics.

#### `useUserCacheStatistics(userId, days, options)`
Gets user-specific cache statistics and activity.

#### `useCachedFilesOperations()`
Provides operations like remove, cleanup, search, and export.

#### `useCachedFilesRealTime(filter)`
Combines cached files and statistics with auto-refresh capability.

### API Service Methods

#### File Operations
- `getCachedFiles(filter)` - Retrieve filtered cached files
- `getCachedFile(fileId)` - Get specific file details
- `removeCachedFile(fileId, request)` - Remove file from cache
- `searchCachedFiles(query, type, limit, includeRemoved)` - Advanced search

#### Statistics Operations
- `getCacheStatistics()` - Get overall cache statistics
- `getUserCacheStatistics(userId, days)` - Get user-specific stats

#### Management Operations
- `cleanupCache(request)` - Clean up orphaned cache entries
- `exportCachedFiles(format, filter, includeMetadata)` - Export cache data

## Real-time Updates

### WebSocket Integration

The components integrate with WebSocket events for real-time updates:

#### Supported Events
- `cache_file_added` - When a new file is cached
- `cache_file_removed` - When a file is removed from cache
- `cache_statistics_updated` - When cache statistics change

#### WebSocket Event Handlers
```typescript
// In CachedTab component
useEffect(() => {
  webSocketService.connect()
  
  const handleCacheUpdate = () => {
    refreshAll()
  }

  webSocketService.addEventListener('cache_file_added', handleCacheUpdate)
  webSocketService.addEventListener('cache_file_removed', handleCacheUpdate)
  webSocketService.addEventListener('cache_statistics_updated', handleCacheUpdate)
  
  return () => {
    webSocketService.removeEventListener('cache_file_added', handleCacheUpdate)
    webSocketService.removeEventListener('cache_file_removed', handleCacheUpdate)
    webSocketService.removeEventListener('cache_statistics_updated', handleCacheUpdate)
  }
}, [refreshAll])
```

## Data Models

### Core Interfaces

#### `CachedFileInfo`
```typescript
interface CachedFileInfo {
  id: string
  file_path: string
  filename: string
  original_path: string
  cached_path: string
  cache_method: string
  file_size_bytes: number
  file_size_readable: string
  cached_at: string
  last_accessed?: string
  access_count: number
  triggered_by_user?: string
  triggered_by_operation: string
  status: 'active' | 'orphaned' | 'pending_removal' | 'removed'
  users: string[]
  metadata?: Record<string, unknown>
}
```

#### `CacheStatistics`
```typescript
interface CacheStatistics {
  total_files: number
  total_size_bytes: number
  total_size_readable: string
  active_files: number
  orphaned_files: number
  users_count: number
  oldest_cached_at?: string
  most_accessed_file?: string
  cache_hit_ratio: number
}
```

#### `CachedFilesFilter`
```typescript
interface CachedFilesFilter {
  search?: string
  user_id?: string
  status?: CachedFileInfo['status']
  triggered_by_operation?: string
  size_min?: number
  size_max?: number
  cached_since?: string
  limit?: number
  offset?: number
}
```

## Features by Component

### Search and Filtering
- **Global Search**: Search across filenames, paths, and metadata
- **Advanced Filters**: Filter by status, user, operation type, size, date
- **Real-time Search**: Immediate results as you type
- **Filter Persistence**: Maintains filter state during navigation

### File Management
- **Bulk Operations**: Select multiple files for batch operations
- **File Details**: Complete metadata and attribution information
- **Remove Operations**: Safe file removal with confirmation and reason
- **Export Functionality**: Export file data in multiple formats

### User Attribution
- **Multi-user Tracking**: Track which users are associated with each file
- **Primary User Highlighting**: Distinguish who triggered the cache operation
- **User Statistics**: Individual user activity and contribution metrics
- **Attribution Context**: Understand why files were cached for each user

### Performance Monitoring
- **Cache Statistics**: Comprehensive performance metrics
- **Health Assessment**: Automatic cache health evaluation
- **Optimization Recommendations**: Actionable suggestions for improvement
- **Trend Analysis**: Visual indicators for performance trends

### Real-time Features
- **Live Updates**: Automatic refresh when cache changes occur
- **WebSocket Integration**: Real-time notifications of cache operations
- **Status Indicators**: Live connection status and update timestamps
- **Auto-refresh Options**: Configurable automatic data refresh

## Responsive Design

### Mobile Support
- **Responsive Grid**: Adaptive layouts for different screen sizes
- **Touch-friendly**: Large touch targets and swipe gestures
- **Mobile Navigation**: Optimized navigation for mobile devices
- **Condensed Views**: Simplified interfaces for smaller screens

### Desktop Features
- **Multi-column Layouts**: Efficient use of screen real estate
- **Keyboard Navigation**: Full keyboard accessibility
- **Advanced Interactions**: Hover states and detailed tooltips
- **Multi-panel Views**: Side-by-side information display

## Accessibility

### WCAG Compliance
- **Screen Reader Support**: Comprehensive ARIA labels and descriptions
- **Keyboard Navigation**: Full functionality via keyboard
- **Color Contrast**: High contrast ratios for readability
- **Focus Management**: Clear focus indicators and logical tab order

### Inclusive Design
- **Alternative Text**: Descriptive text for visual elements
- **Loading States**: Clear indication of loading and progress
- **Error States**: Accessible error messages and recovery options
- **Status Announcements**: Screen reader announcements for state changes

## Performance Considerations

### Optimization Techniques
- **Virtual Scrolling**: Efficient rendering of large file lists
- **Pagination**: Chunked data loading to reduce memory usage
- **Memoization**: React.memo and useMemo for expensive operations
- **Debounced Search**: Optimized search input handling

### Data Management
- **Caching Strategy**: Intelligent caching of frequently accessed data
- **Background Refresh**: Non-blocking data updates
- **Error Recovery**: Automatic retry mechanisms for failed requests
- **Memory Management**: Proper cleanup of subscriptions and timers

## Usage Examples

### Basic Integration
```typescript
import { CachedTab } from '@/components/Cached'

function App() {
  return (
    <div className="app">
      <CachedTab />
    </div>
  )
}
```

### Custom Filter Implementation
```typescript
import { CachedFilesView } from '@/components/Cached'
import { useCachedFiles } from '@/hooks/useApi'

function CustomCachedFiles() {
  const [filter, setFilter] = useState<CachedFilesFilter>({
    status: 'active',
    limit: 20
  })
  
  const { data, isLoading } = useCachedFiles(filter)
  
  return (
    <CachedFilesView
      files={data?.files || []}
      pagination={data?.pagination}
      filter={filter}
      isLoading={isLoading}
      onFilterChange={(newFilter) => setFilter(prev => ({ ...prev, ...newFilter }))}
      onPageChange={(page) => setFilter(prev => ({ ...prev, offset: page * (prev.limit || 50) }))}
      onFileSelect={(fileId) => console.log('Selected file:', fileId)}
    />
  )
}
```

### WebSocket Event Handling
```typescript
import webSocketService from '@/services/websocket'

function useRealTimeCacheUpdates() {
  useEffect(() => {
    const handleFileAdded = (data) => {
      console.log('File added to cache:', data)
      // Refresh data or update local state
    }
    
    const handleFileRemoved = (data) => {
      console.log('File removed from cache:', data)
      // Update UI accordingly
    }
    
    webSocketService.addEventListener('cache_file_added', handleFileAdded)
    webSocketService.addEventListener('cache_file_removed', handleFileRemoved)
    
    return () => {
      webSocketService.removeEventListener('cache_file_added', handleFileAdded)
      webSocketService.removeEventListener('cache_file_removed', handleFileRemoved)
    }
  }, [])
}
```

## Styling and Theming

### Tailwind CSS Classes
The components use a consistent set of Tailwind CSS classes that support dark mode:

#### Common Patterns
- Background: `bg-white dark:bg-gray-800`
- Borders: `border-gray-200 dark:border-gray-700`
- Text: `text-gray-900 dark:text-gray-100`
- Secondary text: `text-gray-600 dark:text-gray-400`

#### Status Colors
- Success: `text-green-600 dark:text-green-400`
- Warning: `text-yellow-600 dark:text-yellow-400`
- Error: `text-red-600 dark:text-red-400`
- Info: `text-blue-600 dark:text-blue-400`

### Custom Styling
Components accept `className` props for custom styling while maintaining internal consistency.

## Testing Considerations

### Unit Testing
- Component rendering with different props
- User interaction handling
- API integration mocking
- Error state handling
- Loading state management

### Integration Testing
- WebSocket event handling
- Real-time update behavior
- Cross-component communication
- Filter and search functionality
- Pagination and navigation

### Accessibility Testing
- Screen reader compatibility
- Keyboard navigation
- Focus management
- ARIA compliance
- Color contrast validation

This implementation provides a comprehensive, production-ready solution for cached file management in PlexCacheUltra with modern React patterns, excellent user experience, and robust real-time capabilities.