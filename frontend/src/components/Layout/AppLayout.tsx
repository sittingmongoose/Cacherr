/**
 * AppLayout Component - Main Layout with Navigation
 * 
 * Provides consistent layout and navigation across Cacherr pages.
 * Features responsive design, theme support, and active route highlighting.
 */

import React from 'react'
import { useLocation, Link } from 'react-router-dom'
import { 
  Home, 
  Database, 
  Settings, 
  FileText, 
  Activity 
} from 'lucide-react'
import { classNames } from '../../utils/format'

interface AppLayoutProps {
  children: React.ReactNode
  className?: string
}

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home,
    description: 'System overview and controls'
  },
  {
    name: 'Cached',
    href: '/cached',
    icon: Database,
    description: 'Cached files and operations management'
  },
  {
    name: 'Logs',
    href: '/logs',
    icon: FileText,
    description: 'Application logs'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Configuration and preferences'
  }
]

export const AppLayout: React.FC<AppLayoutProps> = ({ children, className }) => {
  const location = useLocation()

  const isActiveRoute = (href: string): boolean => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  return (
    <div className={classNames('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Navigation Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo/Title */}
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <Database className="h-8 w-8 text-primary-600 dark:text-primary-400" />
                <h1 className="ml-3 text-xl font-bold text-gray-900 dark:text-gray-100">
                  Cacherr
                </h1>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-8" role="navigation" aria-label="Main navigation">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = isActiveRoute(item.href)
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={classNames(
                      isActive
                        ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200',
                      'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center transition-colors'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.description}
                  >
                    <Icon className="h-4 w-4 mr-1.5" aria-hidden="true" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

          </div>
        </div>

      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}

export default AppLayout