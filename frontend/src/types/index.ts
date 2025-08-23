/**
 * Index file for all TypeScript type definitions.
 * Provides convenient access to all types used throughout the application.
 */

// Re-export all API types
export * from './api'

// Component-specific types
export interface ComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  color?: string
  text?: string
}

export interface ErrorProps {
  error: Error | string
  onRetry?: () => void
  showDetails?: boolean
}

// Form types
export interface FormFieldProps {
  label: string
  name: string
  type?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  error?: string
  help?: string
}

export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
  description?: string
}

// Navigation types
export interface NavItem {
  id: string
  label: string
  path: string
  icon?: React.ComponentType<{ className?: string }>
  badge?: string | number
  disabled?: boolean
  external?: boolean
}

export interface BreadcrumbItem {
  label: string
  path?: string
  current?: boolean
}

// Modal and Dialog types
export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  preventClose?: boolean
}

export interface ConfirmDialogProps extends ModalProps {
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'info' | 'warning' | 'error' | 'success'
  onConfirm: () => void
}

// Toast/Notification types
export interface ToastOptions {
  id?: string
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
  persistent?: boolean
  actions?: ToastAction[]
}

export interface ToastAction {
  label: string
  action: () => void
  style?: 'primary' | 'secondary'
}

// Theme types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto'
  primaryColor: string
  accentColor?: string
  fontFamily?: string
  borderRadius?: 'none' | 'sm' | 'md' | 'lg' | 'full'
  animations?: boolean
}

// Utility types
export type ValueOf<T> = T[keyof T]
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

// Function types
export type EventHandler<T = Event> = (event: T) => void
export type AsyncEventHandler<T = Event> = (event: T) => Promise<void>
export type Callback<T = void> = () => T
export type AsyncCallback<T = void> = () => Promise<T>

// Generic component types
export type As<T = React.ElementType> = T
export type PropsOf<T extends As> = React.ComponentPropsWithoutRef<T>

// Polymorphic component types
export interface AsProp<T extends As = As> {
  as?: T
}

export type PolymorphicProps<T extends As, P = {}> = P & 
  AsProp<T> & 
  Omit<PropsOf<T>, keyof AsProp<T> | keyof P>

// Hook types
export interface UseApiOptions<T> {
  initialData?: T
  enabled?: boolean
  refetchInterval?: number
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
  retry?: boolean | number
  staleTime?: number
}

export interface UseApiResult<T> {
  data: T | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => Promise<void>
  mutate: (newData: T) => void
}

// Storage types
export interface StorageAdapter {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
  clear(): void
}

// Validation types
export interface ValidationRule<T = any> {
  required?: boolean | string
  min?: number | string
  max?: number | string
  pattern?: RegExp | string
  custom?: (value: T) => boolean | string
}

export interface ValidationSchema<T = Record<string, any>> {
  [K in keyof T]?: ValidationRule<T[K]>
}

export interface ValidationResult<T = Record<string, any>> {
  isValid: boolean
  errors: Partial<Record<keyof T, string>>
  values: T
}

// Date and time types
export interface DateRange {
  start: Date | null
  end: Date | null
}

export interface TimeRange {
  start: string // HH:mm format
  end: string   // HH:mm format
}

// File handling types
export interface FileUpload {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  id: string
}

export interface FilePreview {
  name: string
  size: number
  type: string
  url: string
  thumbnail?: string
}

// Search and filter types
export interface SearchOptions {
  query: string
  filters: Record<string, any>
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface FilterOption {
  key: string
  label: string
  type: 'text' | 'select' | 'date' | 'number' | 'boolean'
  options?: SelectOption[]
  placeholder?: string
}

// Export commonly used React types
export type {
  FC,
  ReactNode,
  CSSProperties,
  MouseEvent,
  KeyboardEvent,
  ChangeEvent,
  FocusEvent,
  FormEvent,
  RefObject,
  MutableRefObject,
} from 'react'