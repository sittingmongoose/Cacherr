/**
 * Test setup configuration for Cacherr frontend
 * 
 * Configures testing environment with jsdom, jest-dom matchers,
 * and global test utilities.
 */

import '@testing-library/jest-dom'
import { expect, afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Global test setup
beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks()
})

// Mock IntersectionObserver for components that might use it
global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  thresholds: [],
  root: null,
  rootMargin: '',
}))

// Mock ResizeObserver for components that might use it
global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock matchMedia for responsive design tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock WebSocket for real-time functionality tests
const MockWebSocket = vi.fn().mockImplementation((url) => ({
  url,
  readyState: 0,
  close: vi.fn(),
  send: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}))

// Add static properties to the mock constructor
;(MockWebSocket as any).CONNECTING = 0
;(MockWebSocket as any).OPEN = 1
;(MockWebSocket as any).CLOSING = 2
;(MockWebSocket as any).CLOSED = 3
MockWebSocket.prototype = WebSocket.prototype

global.WebSocket = MockWebSocket as any

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
})

// Mock fetch API
global.fetch = vi.fn()

// Mock navigator properties
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
})

Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: vi.fn().mockResolvedValue({}),
    ready: vi.fn().mockResolvedValue({}),
    controller: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  },
  writable: true,
})

// Mock console methods to reduce noise in tests
const originalError = console.error
beforeEach(() => {
  console.error = vi.fn((message, ...args) => {
    // Suppress React error messages in tests
    if (
      typeof message === 'string' &&
      (message.includes('Warning:') ||
       message.includes('Error:') ||
       message.includes('validateDOMNesting'))
    ) {
      return
    }
    originalError(message, ...args)
  })
})

afterEach(() => {
  console.error = originalError
})

// Extended matchers for better testing
expect.extend({
  toBeInTheDocument: (received) => {
    const pass = received && document.body.contains(received)
    return {
      pass,
      message: () => pass
        ? `Expected element NOT to be in the document`
        : `Expected element to be in the document`,
    }
  },
})

// Global test utilities
export const createMockApiResponse = <T>(data: T, success = true): any => ({
  success,
  data: success ? data : undefined,
  error: success ? undefined : 'Mock error',
  timestamp: new Date().toISOString(),
})

export const mockApiCall = <T>(response: T, delay = 0) => {
  return vi.fn().mockImplementation(() => 
    new Promise((resolve) => 
      setTimeout(() => resolve(createMockApiResponse(response)), delay)
    )
  )
}

export const mockApiError = (message = 'Mock API Error', delay = 0) => {
  return vi.fn().mockImplementation(() => 
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error(message)), delay)
    )
  )
}

// Mock system status for tests
export const mockSystemStatus = {
  status: 'idle' as const,
  pending_operations: {
    files_to_cache: 5,
    files_to_array: 2,
  },
  last_execution: {
    execution_time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    success: true,
    operation_type: 'cache' as const,
    duration_seconds: 45,
  },
  scheduler_running: false,
  cache_statistics: {
    total_files: 1247,
    total_size_bytes: 524288000000,
    total_size_readable: '524 GB',
    cache_hit_ratio: 0.85,
    last_updated: new Date().toISOString(),
  },
}

// Mock health status for tests
export const mockHealthStatus = {
  status: 'healthy' as const,
  timestamp: new Date().toISOString(),
  checks: [],
  services: {
    cache_service: 'healthy' as const,
    media_service: 'healthy' as const,
    file_service: 'healthy' as const,
  },
  uptime_seconds: 3600,
}

// Mock log entries for tests
export const mockLogEntries = [
  {
    level: 'info' as const,
    message: 'System started successfully',
    timestamp: new Date().toISOString(),
  },
  {
    level: 'warning' as const,
    message: 'Cache directory is getting full',
    timestamp: new Date(Date.now() - 30000).toISOString(),
  },
  {
    level: 'error' as const,
    message: 'Failed to connect to Plex server',
    timestamp: new Date(Date.now() - 60000).toISOString(),
  },
]