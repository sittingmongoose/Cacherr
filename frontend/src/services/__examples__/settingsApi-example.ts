/**
 * Settings API Service Usage Examples
 * 
 * This file demonstrates how to use the Settings API service
 * in React components and other parts of the application.
 */

import SettingsAPIService from '../settingsApi'
import type { ConfigurationSettings, ValidationResult } from '@/types/api'
import type { SettingsUpdateRequest, PlexTestRequest } from '@/types/settings'

// Example 1: Get current configuration
export async function getCurrentSettings(): Promise<ConfigurationSettings> {
  try {
    const settings = await SettingsAPIService.getCurrentConfig()
    console.log('Current settings:', settings)
    return settings
  } catch (error) {
    console.error('Failed to get settings:', error)
    throw error
  }
}

// Example 2: Update Plex settings with validation
export async function updatePlexSettings(
  url: string,
  token: string,
  username?: string
): Promise<void> {
  try {
    // First, test the Plex connection
    const testRequest: PlexTestRequest = {
      url,
      token,
      timeout: 10000
    }
    
    const testResult = await SettingsAPIService.testPlexConnection(testRequest)
    
    if (testResult.status !== 'success') {
      throw new Error(`Plex connection test failed: ${testResult.error}`)
    }
    
    console.log('Plex connection test successful:', testResult)
    
    // If test passes, update the settings
    const updateRequest: SettingsUpdateRequest = {
      sections: {
        plex: { url, token, username }
      },
      validate_before_save: true,
      create_backup: true
    }
    
    const result = await SettingsAPIService.updateConfig(updateRequest)
    console.log('Plex settings updated:', result)
    
  } catch (error) {
    console.error('Failed to update Plex settings:', error)
    throw error
  }
}

// Example 3: Validate configuration before saving
export async function validateSettingsBeforeSave(
  settingsToValidate: Partial<ConfigurationSettings>
): Promise<ValidationResult> {
  try {
    const result = await SettingsAPIService.validateConfig({
      sections: settingsToValidate,
      full_validation: true
    })
    
    if (!result.valid) {
      console.warn('Validation errors found:', result.errors)
      console.warn('Validation warnings:', result.warnings)
    } else {
      console.log('Configuration validation successful')
    }
    
    return result
  } catch (error) {
    console.error('Failed to validate settings:', error)
    throw error
  }
}

// Example 4: Export and download configuration
export async function exportSettingsAsFile(): Promise<void> {
  try {
    const { blob, filename } = await SettingsAPIService.exportConfigAsDownload({
      include_secrets: false, // Don't include sensitive data
      format: 'json',
      minify: false
    })
    
    // Create download link
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    console.log(`Configuration exported as ${filename}`)
  } catch (error) {
    console.error('Failed to export settings:', error)
    throw error
  }
}

// Example 5: Import configuration from file
export async function importSettingsFromFile(file: File): Promise<void> {
  try {
    const fileContent = await file.text()
    const configuration = JSON.parse(fileContent) as Partial<ConfigurationSettings>
    
    const result = await SettingsAPIService.importConfig({
      configuration,
      validate_before_import: true,
      overwrite_existing: true
    })
    
    console.log('Configuration imported successfully:', result)
    
    if (result.skipped_sections.length > 0) {
      console.warn('Some sections were skipped:', result.skipped_sections)
    }
    
  } catch (error) {
    console.error('Failed to import settings:', error)
    throw error
  }
}

// Example 6: Reset configuration to defaults
export async function resetAllSettings(): Promise<void> {
  try {
    const result = await SettingsAPIService.resetConfig()
    console.log('All settings reset to defaults:', result)
  } catch (error) {
    console.error('Failed to reset settings:', error)
    throw error
  }
}

// Example 7: Reset specific sections only
export async function resetSpecificSections(sections: string[]): Promise<void> {
  try {
    const result = await SettingsAPIService.resetConfig(sections)
    console.log(`Settings sections ${sections.join(', ')} reset to defaults:`, result)
  } catch (error) {
    console.error('Failed to reset specific settings sections:', error)
    throw error
  }
}

// Example 8: Check persistence configuration
export async function checkPersistenceHealth(): Promise<boolean> {
  try {
    const result = await SettingsAPIService.validatePersistence()
    
    if (!result.persistence_working) {
      console.error('Persistence issues detected:', result.error_details)
      return false
    }
    
    console.log('Settings persistence is working correctly')
    return true
  } catch (error) {
    console.error('Failed to check persistence health:', error)
    return false
  }
}

// Example 9: Get configuration schema for dynamic forms
export async function getSettingsSchema() {
  try {
    const schema = await SettingsAPIService.getConfigSchema()
    
    console.log('Configuration schema:', schema)
    
    // Example: Build form fields from schema
    const formFields = Object.entries(schema.schema).map(([key, fieldSchema]) => ({
      name: key,
      title: fieldSchema.title,
      type: fieldSchema.type,
      required: fieldSchema.required,
      description: fieldSchema.description
    }))
    
    return { schema, formFields }
  } catch (error) {
    console.error('Failed to get settings schema:', error)
    throw error
  }
}

// Example 10: React hook for settings management
export function useSettingsOperations() {
  return {
    getCurrentSettings,
    updatePlexSettings,
    validateSettingsBeforeSave,
    exportSettingsAsFile,
    importSettingsFromFile,
    resetAllSettings,
    resetSpecificSections,
    checkPersistenceHealth,
    getSettingsSchema
  }
}