import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from '@/store'
import { AppLayout } from '@/components/Layout'
import { FullPageLoader } from '@/components/common/LoadingSpinner'
import { ToastContainer } from '@/components/common/Toast'

/**
 * Main App component
 * 
 * Features:
 * - React Router setup
 * - Global state provider
 * - Error boundary
 * - Theme provider
 * - Route configuration
 */

// Error Boundary Component
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    })
    
    // Enhanced error logging with more context
    const errorContext = {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    }
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 React Error Boundary')
      console.error('Error:', error)
      console.error('Component Stack:', errorInfo.componentStack)
      console.error('Full Context:', errorContext)
      console.groupEnd()
    }
    
    // In production, you could send this to an error reporting service
    // Example: sendErrorToService(errorContext)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="text-center">
              <div className="text-6xl mb-4">😵</div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                The application encountered an unexpected error. Please refresh the page to try again.
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => window.location.reload()}
                  className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Refresh Page
                </button>
                
                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details className="text-left">
                    <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                      Show Error Details
                    </summary>
                    <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-900 rounded text-xs overflow-auto max-h-48">
                      {this.state.error.toString()}
                      {this.state.errorInfo?.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Loading component for lazy-loaded routes
const PageLoader: React.FC = () => (
  <FullPageLoader text="Loading..." />
)

// Lazy load components for better performance and code splitting
const Dashboard = React.lazy(() => import('@/components/Dashboard'))
const CachedTab = React.lazy(() => import('@/components/Cached'))
const LogsPage = React.lazy(() => import('@/components/Logs'))
const Settings = React.lazy(() => import('@/components/Settings/SettingsPage'))

// Route components wrapper with Suspense for lazy loading
const DashboardPage: React.FC = () => (
  <React.Suspense fallback={<PageLoader />}>
    <Dashboard />
  </React.Suspense>
)

const CachedPage: React.FC = () => (
  <React.Suspense fallback={<PageLoader />}>
    <CachedTab />
  </React.Suspense>
)

const LogsPageWrapper: React.FC = () => (
  <React.Suspense fallback={<PageLoader />}>
    <LogsPage />
  </React.Suspense>
)

const SettingsPageWrapper: React.FC = () => (
  <React.Suspense fallback={<PageLoader />}>
    <Settings />
  </React.Suspense>
)


// NotFound component
const NotFound: React.FC = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div className="text-center">
      <div className="text-6xl mb-4">🔍</div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        Page Not Found
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        The page you're looking for doesn't exist.
      </p>
      <button
        onClick={() => window.location.href = '/'}
        className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
      >
        Go to Dashboard
      </button>
    </div>
  </div>
)

// Main App component
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AppProvider>
        <Router basename="/">
          <div className="App">
            <AppLayout>
              <Routes>
                {/* Main dashboard route */}
                <Route path="/" element={<DashboardPage />} />
                
                {/* Dashboard explicit route */}
                <Route path="/dashboard" element={<Navigate to="/" replace />} />
                
                {/* Cached files tab */}
                <Route path="/cached" element={<CachedPage />} />
                
                {/* Legacy results route - redirect to cached */}
                <Route path="/results" element={<Navigate to="/cached" replace />} />
                
                {/* Settings route */}
                <Route path="/settings" element={<SettingsPageWrapper />} />
                
                {/* Logs route */}
                <Route path="/logs" element={<LogsPageWrapper />} />
                
                {/* Catch-all route for 404 */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </AppLayout>
            
            {/* Global components */}
            <ToastContainer />
          </div>
        </Router>
      </AppProvider>
    </ErrorBoundary>
  )
}

export default App