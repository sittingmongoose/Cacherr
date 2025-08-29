/**
 * Logs components barrel export
 * 
 * This module provides a centralized export for all Logs-related components,
 * following the established pattern used by Dashboard and Cached components.
 */

export { LogsPage as default } from './LogsPage'
export { LogsPage } from './LogsPage'
export { LogViewer } from '@/components/LogViewer'

// Export types that might be useful for other components
export type { LogViewerProps } from '@/components/LogViewer/LogViewer'