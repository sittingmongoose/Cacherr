import React from 'react'
import { LogViewer } from '../LogViewer'

/**
 * LogsPage component - Main page for viewing application logs
 * 
 * Features:
 * - Real-time log streaming
 * - Advanced filtering and search
 * - Log export functionality
 * - WebSocket integration for live updates
 * - Responsive design with dark mode support
 */
export const LogsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <LogViewer />
      </div>
    </div>
  )
}