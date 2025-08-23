/**
 * Dashboard component tests
 * 
 * Tests the main dashboard component functionality including:
 * - Rendering with proper structure
 * - API integration and data display
 * - User interactions (buttons, theme switching)
 * - Responsive behavior
 * - Accessibility compliance
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from './Dashboard'
import { AppProvider } from '@/store'
import { mockSystemStatus, mockHealthStatus, mockApiCall, mockApiError } from '@/test-setup'
import APIService from '@/services/api'

// Mock the API service
vi.mock('@/services/api')
vi.mock('@/services/websocket', () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addConnectionListener: vi.fn(),
    removeConnectionListener: vi.fn(),
    getStatus: vi.fn(() => ({
      connected: false,
      reconnecting: false,
      lastConnectedAt: null,
    })),
  }
}))

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AppProvider>
      {children}
    </AppProvider>
  </BrowserRouter>
)

describe('Dashboard Component', () => {
  const user = userEvent.setup()
  
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()
    
    // Mock successful API calls by default
    vi.mocked(APIService.getSystemStatus).mockImplementation(
      mockApiCall(mockSystemStatus, 100)
    )
    vi.mocked(APIService.getHealthStatus).mockImplementation(
      mockApiCall(mockHealthStatus, 100)
    )
    vi.mocked(APIService.getLogs).mockImplementation(
      mockApiCall({ logs: [], total_entries: 0 }, 100)
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders the dashboard with main sections', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Check for main sections
      expect(screen.getByRole('banner')).toBeInTheDocument() // header
      expect(screen.getByRole('main')).toBeInTheDocument() // main content
      expect(screen.getByRole('contentinfo')).toBeInTheDocument() // footer

      // Check for title
      expect(screen.getByText('PlexCacheUltra')).toBeInTheDocument()

      // Wait for initial data loading
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })
    })

    it('displays loading state initially', () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      expect(screen.getByText('Loading PlexCacheUltra Dashboard...')).toBeInTheDocument()
    })

    it('displays error message when API fails', async () => {
      // Mock API failure
      vi.mocked(APIService.getSystemStatus).mockImplementation(
        mockApiError('Network error')
      )

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument()
      })
    })
  })

  describe('Theme Switching', () => {
    it('cycles through theme options when theme button is clicked', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      const themeButton = screen.getByLabelText(/Switch theme/)
      
      // Initial theme should be auto
      expect(screen.getByText('Theme: auto')).toBeInTheDocument()

      // Click to change to light
      await user.click(themeButton)
      await waitFor(() => {
        expect(screen.getByText('Theme: light')).toBeInTheDocument()
      })

      // Click to change to dark
      await user.click(themeButton)
      await waitFor(() => {
        expect(screen.getByText('Theme: dark')).toBeInTheDocument()
      })

      // Click to change back to auto
      await user.click(themeButton)
      await waitFor(() => {
        expect(screen.getByText('Theme: auto')).toBeInTheDocument()
      })
    })
  })

  describe('Auto-refresh Functionality', () => {
    it('toggles auto-refresh when checkbox is clicked', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      const autoRefreshCheckbox = screen.getByLabelText(/Auto-refresh/)
      
      // Should be checked by default
      expect(autoRefreshCheckbox).toBeChecked()

      // Uncheck auto-refresh
      await user.click(autoRefreshCheckbox)
      expect(autoRefreshCheckbox).not.toBeChecked()

      // Check auto-refresh again
      await user.click(autoRefreshCheckbox)
      expect(autoRefreshCheckbox).toBeChecked()
    })

    it('shows refresh interval information when auto-refresh is enabled', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/refreshes every \d+s/)).toBeInTheDocument()
      })
    })
  })

  describe('Manual Refresh', () => {
    it('calls refresh function when refresh button is clicked', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      const refreshButton = screen.getByLabelText('Refresh data')
      await user.click(refreshButton)

      // API should be called again
      expect(APIService.getSystemStatus).toHaveBeenCalledTimes(2) // Initial + manual refresh
    })

    it('shows loading state during refresh', async () => {
      // Mock slower API response
      vi.mocked(APIService.getSystemStatus).mockImplementation(
        mockApiCall(mockSystemStatus, 1000)
      )

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      const refreshButton = screen.getByLabelText('Refresh data')
      await user.click(refreshButton)

      // Should show loading indicator
      const refreshIcon = refreshButton.querySelector('svg')
      expect(refreshIcon).toHaveClass('animate-spin')
    })
  })

  describe('WebSocket Status', () => {
    it('displays offline status when WebSocket is disconnected', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Offline')).toBeInTheDocument()
      })
    })

    it('shows live updates indicator when WebSocket is connected', async () => {
      // Mock connected WebSocket
      const { default: mockWebSocket } = await vi.importMock('@/services/websocket')
      vi.mocked(mockWebSocket.getStatus).mockReturnValue({
        connected: true,
        reconnecting: false,
        lastConnectedAt: new Date(),
      })

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Live')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels on interactive elements', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Check for ARIA labels
      expect(screen.getByLabelText('Refresh data')).toBeInTheDocument()
      expect(screen.getByLabelText(/Switch theme/)).toBeInTheDocument()
      expect(screen.getByLabelText('Settings')).toBeInTheDocument()
    })

    it('has proper heading hierarchy', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument() // PlexCacheUltra title
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument() // Dashboard title
      })
    })

    it('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Tab to first interactive element
      await user.tab()
      expect(document.activeElement).toHaveAttribute('type', 'checkbox') // Auto-refresh checkbox

      // Tab to refresh button
      await user.tab()
      expect(document.activeElement).toHaveAttribute('aria-label', 'Refresh data')

      // Tab to theme button
      await user.tab()
      expect(document.activeElement).toHaveAttribute('aria-label', expect.stringMatching(/Switch theme/))
    })
  })

  describe('Responsive Behavior', () => {
    it('adapts layout for mobile screens', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          matches: query.includes('max-width: 768px'),
          media: query,
          onchange: null,
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Check that mobile-specific classes are applied
      const container = screen.getByRole('main')
      expect(container).toHaveClass('px-4', 'sm:px-6', 'lg:px-8')
    })
  })

  describe('Data Display', () => {
    it('displays system status information correctly', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should display system status data
        expect(screen.getByText('5')).toBeInTheDocument() // files to cache
        expect(screen.getByText('2')).toBeInTheDocument() // files to array
      })
    })

    it('updates display when system status changes', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Mock updated status
      const updatedStatus = {
        ...mockSystemStatus,
        pending_operations: {
          files_to_cache: 10,
          files_to_array: 5,
        },
      }

      vi.mocked(APIService.getSystemStatus).mockImplementation(
        mockApiCall(updatedStatus, 100)
      )

      // Trigger refresh
      const refreshButton = screen.getByLabelText('Refresh data')
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('10')).toBeInTheDocument() // updated files to cache
        expect(screen.getByText('5')).toBeInTheDocument() // updated files to array
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message and provides dismissal option', async () => {
      // Mock API error after initial success
      vi.mocked(APIService.getSystemStatus)
        .mockImplementationOnce(mockApiCall(mockSystemStatus, 100))
        .mockImplementationOnce(mockApiError('Connection failed'))

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Trigger a refresh that fails
      const refreshButton = screen.getByLabelText('Refresh data')
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText(/Connection failed/)).toBeInTheDocument()
      })

      // Should have dismiss button
      const dismissButton = screen.getByText('Dismiss')
      expect(dismissButton).toBeInTheDocument()

      // Click dismiss
      await user.click(dismissButton)
      
      await waitFor(() => {
        expect(screen.queryByText(/Connection failed/)).not.toBeInTheDocument()
      })
    })
  })
})