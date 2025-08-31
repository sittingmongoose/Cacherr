# Cached Tab Testing Plan

## Overview

This document outlines the comprehensive testing strategy for the new "Cached" tab implementation in Cacherr. The testing covers backend services, API endpoints, frontend components, and integration scenarios.

## Testing Scope

### **Backend Testing**
1. **CachedFilesService** - Core service functionality
2. **API Endpoints** - All 12 new REST endpoints
3. **Database Operations** - SQLite schema and operations
4. **WebSocket Events** - Real-time update system
5. **Integration Points** - File operations integration

### **Frontend Testing** 
1. **React Components** - UI component functionality
2. **TypeScript Types** - Type safety validation
3. **API Integration** - Frontend-backend communication
4. **Real-time Updates** - WebSocket integration
5. **User Interactions** - Complete user workflows

### **Integration Testing**
1. **Atomic Redirection** - Integration with file operations
2. **Active Watching** - Copy-only constraint validation
3. **Multi-user Attribution** - User tracking across operations
4. **Error Handling** - End-to-end error scenarios
5. **Performance** - Load and stress testing

## Test Environment Setup

### **Prerequisites**
- Cacherr development environment
- Test database with sample data
- Mock Plex server for testing
- WebSocket test client
- Frontend testing environment

### **Test Data**
```python
# Sample cached files for testing
TEST_CACHED_FILES = [
    {
        "file_path": "/media/movies/test_movie.mkv",
        "cache_method": "atomic_copy",
        "triggered_by_operation": "active_watching",
        "triggered_by_user": "test_user",
        "status": "active"
    },
    {
        "file_path": "/media/shows/test_show_s01e01.mkv", 
        "cache_method": "atomic_symlink",
        "triggered_by_operation": "watchlist",
        "triggered_by_user": "user2",
        "status": "active"
    }
]
```

## Backend Testing

### **1. CachedFilesService Tests**

#### **Unit Tests**
```python
# Test file addition with atomic operations
def test_add_cached_file_atomic_copy():
    service = CachedFilesService(":memory:")
    cached_file = service.add_cached_file(
        file_path="/test/file.mkv",
        original_path="/media/file.mkv",
        cached_path="/cache/file.mkv",
        cache_method="atomic_copy",
        operation_reason="active_watching"
    )
    assert cached_file.cache_method == "atomic_copy"
    assert cached_file.status == "active"

# Test automatic atomic upgrade
def test_automatic_atomic_upgrade():
    service = CachedFilesService(":memory:")
    cached_file = service.add_cached_file(
        file_path="/test/file.mkv",
        original_path="/media/file.mkv", 
        cached_path="/cache/file.mkv",
        cache_method="copy"  # Legacy method
    )
    assert cached_file.cache_method == "atomic_copy"  # Auto-upgraded

# Test active watching constraints
def test_active_watching_forces_copy():
    service = CachedFilesService(":memory:")
    cached_file = service.add_cached_file(
        file_path="/test/file.mkv",
        original_path="/media/file.mkv",
        cached_path="/cache/file.mkv", 
        cache_method="atomic_symlink",  # Would normally be symlink
        operation_reason="active_watching"
    )
    assert cached_file.cache_method == "atomic_copy"  # Forced for active watching

# Test filtering and pagination
def test_cached_files_filtering():
    service = CachedFilesService(":memory:")
    # Add test files...
    filter_params = CachedFilesFilter(
        triggered_by_operation="active_watching",
        limit=10
    )
    files, count = service.get_cached_files(filter_params)
    assert all(f.triggered_by_operation == "active_watching" for f in files)
    assert len(files) <= 10

# Test statistics calculation
def test_cache_statistics():
    service = CachedFilesService(":memory:")
    # Add test files...
    stats = service.get_cache_statistics()
    assert stats.total_files >= 0
    assert stats.active_files <= stats.total_files
```

#### **Integration Tests**
```python
# Test database schema and constraints
def test_database_schema():
    service = CachedFilesService(":memory:")
    # Verify tables exist
    with sqlite3.connect(":memory:") as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "cached_files" in table_names
        assert "cached_file_users" in table_names
        assert "cache_operations_log" in table_names

# Test user attribution
def test_multi_user_attribution():
    service = CachedFilesService(":memory:")
    # Test user attribution and junction table
```

### **2. API Endpoint Tests**

#### **GET /api/cached/files**
```python
def test_get_cached_files_success(client):
    response = client.get("/api/cached/files")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] == True
    assert "files" in data["data"]
    assert "pagination" in data["data"]

def test_get_cached_files_with_filters(client):
    response = client.get("/api/cached/files?status=active&user_id=test_user")
    assert response.status_code == 200
    # Verify filtering worked

def test_get_cached_files_pagination(client):
    response = client.get("/api/cached/files?limit=5&offset=10")
    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["pagination"]["limit"] == 5
    assert data["data"]["pagination"]["offset"] == 10
```

#### **DELETE /api/cached/files/{file_id}**
```python
def test_remove_cached_file_success(client):
    # Setup test file
    response = client.delete("/api/cached/files/test-file-id", 
                           json={"reason": "test_cleanup"})
    assert response.status_code == 200
    
def test_remove_cached_file_not_found(client):
    response = client.delete("/api/cached/files/nonexistent")
    assert response.status_code == 404
```

#### **GET /api/cached/statistics**
```python
def test_get_cache_statistics(client):
    response = client.get("/api/cached/statistics")
    assert response.status_code == 200
    data = response.get_json()
    assert "total_files" in data["data"]
    assert "active_files" in data["data"]
    assert "cache_hit_ratio" in data["data"]
```

### **3. WebSocket Event Tests**

```python
def test_websocket_cache_file_added():
    with SocketIOTestClient(app, socketio) as client:
        # Trigger cache file addition
        service.add_cached_file(...)
        
        # Verify WebSocket event sent
        received = client.get_received()
        assert len(received) > 0
        event = received[0]
        assert event["name"] == "cache_file_added"
        assert event["args"][0]["data"]["action"] == "added"

def test_websocket_cache_statistics_updated():
    with SocketIOTestClient(app, socketio) as client:
        # Trigger statistics update
        # Verify event received
```

## Frontend Testing

### **1. Component Unit Tests**

#### **CachedTab Component**
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { CachedTab } from '@/components/Cached'

describe('CachedTab', () => {
  test('renders cached files view by default', () => {
    render(<CachedTab />)
    expect(screen.getByText('Cached Files')).toBeInTheDocument()
  })

  test('switches to statistics view', async () => {
    render(<CachedTab />)
    const statsButton = screen.getByText('Statistics')
    fireEvent.click(statsButton)
    
    await waitFor(() => {
      expect(screen.getByText('Cache Statistics')).toBeInTheDocument()
    })
  })

  test('handles WebSocket updates', async () => {
    const { rerender } = render(<CachedTab />)
    
    // Mock WebSocket event
    act(() => {
      webSocketService.emit('cache_file_added', {
        data: { file_path: '/test/file.mkv', action: 'added' }
      })
    })

    // Verify UI updates
    await waitFor(() => {
      expect(screen.getByText('file.mkv')).toBeInTheDocument()
    })
  })
})
```

#### **CachedFilesView Component**
```typescript
describe('CachedFilesView', () => {
  test('renders file list with pagination', () => {
    const mockFiles = [/* test data */]
    render(<CachedFilesView files={mockFiles} />)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  test('filters files by status', async () => {
    render(<CachedFilesView />)
    const statusFilter = screen.getByLabelText('Status')
    fireEvent.change(statusFilter, { target: { value: 'active' } })
    
    // Verify API call with filter
    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'active' })
      )
    })
  })

  test('handles bulk operations', () => {
    // Test multi-select and bulk actions
  })
})
```

### **2. Hook Tests**

#### **API Hooks**
```typescript
import { renderHook } from '@testing-library/react-hooks'
import { useCachedFiles } from '@/hooks/useApi'

describe('useCachedFiles', () => {
  test('fetches cached files on mount', async () => {
    const { result, waitForNextUpdate } = renderHook(() =>
      useCachedFiles()
    )

    expect(result.current.isLoading).toBe(true)
    
    await waitForNextUpdate()
    
    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeDefined()
  })

  test('handles filtering updates', async () => {
    const { result, rerender } = renderHook(
      ({ filter }) => useCachedFiles(filter),
      { initialProps: { filter: { status: 'active' } } }
    )

    // Change filter
    rerender({ filter: { status: 'orphaned' } })
    
    // Verify new API call
    expect(mockApiCall).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'orphaned' })
    )
  })
})
```

### **3. Integration Tests**

#### **End-to-End Workflows**
```typescript
describe('Cached Tab E2E', () => {
  test('complete file management workflow', async () => {
    // Navigate to cached tab
    render(<App />)
    fireEvent.click(screen.getByText('Cached'))
    
    // Verify cached files load
    await waitFor(() => {
      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    // Test filtering
    const searchInput = screen.getByPlaceholderText('Search files...')
    fireEvent.change(searchInput, { target: { value: 'movie' } })
    
    // Verify filtered results
    await waitFor(() => {
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBeGreaterThan(1) // Header + data rows
    })

    // Test file removal
    const removeButton = screen.getByLabelText('Remove file')
    fireEvent.click(removeButton)
    
    // Confirm removal
    const confirmButton = screen.getByText('Confirm Remove')
    fireEvent.click(confirmButton)
    
    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/successfully removed/i)).toBeInTheDocument()
    })
  })

  test('real-time updates workflow', async () => {
    render(<App />)
    fireEvent.click(screen.getByText('Cached'))

    // Mock WebSocket connection
    act(() => {
      webSocketService.connect()
    })

    // Simulate cache file added event
    act(() => {
      webSocketService.emit('cache_file_added', {
        type: 'cache_file_added',
        data: {
          file_path: '/media/new_file.mkv',
          action: 'added',
          user_id: 'test_user',
          cache_method: 'atomic_copy'
        }
      })
    })

    // Verify UI updates in real-time
    await waitFor(() => {
      expect(screen.getByText('new_file.mkv')).toBeInTheDocument()
    })
  })
})
```

## Performance Testing

### **Load Testing**
```python
def test_api_performance():
    """Test API performance with large datasets"""
    # Create large dataset
    service = CachedFilesService(":memory:")
    for i in range(10000):
        service.add_cached_file(f"/test/file_{i}.mkv", ...)
    
    # Test pagination performance
    start_time = time.time()
    files, count = service.get_cached_files(CachedFilesFilter(limit=50))
    end_time = time.time()
    
    assert end_time - start_time < 0.1  # Should be under 100ms
    assert len(files) == 50

def test_websocket_event_performance():
    """Test WebSocket event handling under load"""
    # Simulate high-frequency cache events
    # Verify UI remains responsive
```

### **Memory Testing**
```typescript
describe('Memory Usage', () => {
  test('no memory leaks in cached files view', async () => {
    const { unmount } = render(<CachedFilesView />)
    
    // Monitor memory usage
    const initialMemory = performance.memory?.usedJSHeapSize || 0
    
    // Perform operations
    for (let i = 0; i < 100; i++) {
      // Trigger re-renders and API calls
    }
    
    unmount()
    
    // Force garbage collection and check memory
    if (global.gc) global.gc()
    const finalMemory = performance.memory?.usedJSHeapSize || 0
    
    // Memory should not grow significantly
    expect(finalMemory - initialMemory).toBeLessThan(1000000) // 1MB threshold
  })
})
```

## Security Testing

### **Input Validation**
```python
def test_sql_injection_prevention():
    """Test SQL injection attack prevention"""
    service = CachedFilesService(":memory:")
    
    # Attempt SQL injection in search parameter
    malicious_filter = CachedFilesFilter(
        search="'; DROP TABLE cached_files; --"
    )
    
    # Should not crash or execute SQL injection
    try:
        files, count = service.get_cached_files(malicious_filter)
        # Verify table still exists
        stats = service.get_cache_statistics()
        assert stats is not None
    except Exception as e:
        # Should be validation error, not SQL error
        assert "validation" in str(e).lower()

def test_path_traversal_prevention():
    """Test directory traversal attack prevention"""
    # Test with malicious file paths
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config",
        "/etc/shadow"
    ]
    
    for path in malicious_paths:
        try:
            service.add_cached_file(
                file_path=path,
                original_path="/media/safe",
                cached_path="/cache/safe"
            )
        except Exception as e:
            # Should be validation error
            assert "path" in str(e).lower() or "validation" in str(e).lower()
```

### **API Security**
```python
def test_api_input_validation(client):
    """Test API input validation"""
    # Test invalid JSON
    response = client.post("/api/cached/cleanup", 
                          data="invalid json")
    assert response.status_code == 400
    
    # Test invalid parameters
    response = client.get("/api/cached/files?limit=9999")
    data = response.get_json()
    # Should be limited to max 500
    assert data["data"]["pagination"]["limit"] <= 500

def test_api_error_handling(client):
    """Test API error responses don't leak sensitive info"""
    response = client.get("/api/cached/files/nonexistent")
    data = response.get_json()
    assert "error" in data
    # Should not contain stack traces or database details
    assert "Traceback" not in str(data)
    assert "sqlite" not in str(data).lower()
```

## Test Execution

### **Running Tests**

#### **Backend Tests**
```bash
# Unit tests
pytest src/tests/test_cached_files_service.py -v

# API tests
pytest src/tests/test_cached_api.py -v

# Integration tests
pytest src/tests/test_cached_integration.py -v

# All backend tests
pytest src/tests/ -k "cached" -v --coverage
```

#### **Frontend Tests**
```bash
# Unit tests
npm test -- components/Cached

# Integration tests
npm run test:integration -- cached

# E2E tests
npm run test:e2e -- cached

# All frontend tests with coverage
npm test -- --coverage --watchAll=false
```

### **Test Reporting**
- Generate HTML coverage reports
- Integration with CI/CD pipeline
- Performance metrics reporting
- Security scan results

## Success Criteria

### **Functional Requirements**
- ✅ All API endpoints return expected responses
- ✅ WebSocket events trigger UI updates
- ✅ Filtering and search work correctly
- ✅ Multi-user attribution functions properly
- ✅ Export functionality generates correct files
- ✅ Real-time updates display accurately

### **Performance Requirements**  
- ✅ API responses under 500ms for normal datasets
- ✅ UI remains responsive with 1000+ cached files
- ✅ WebSocket events processed within 100ms
- ✅ Memory usage stable under continuous operation

### **Security Requirements**
- ✅ No SQL injection vulnerabilities
- ✅ No path traversal vulnerabilities  
- ✅ Input validation prevents malicious input
- ✅ Error messages don't leak sensitive data
- ✅ WebSocket events don't expose unauthorized data

### **Quality Requirements**
- ✅ Code coverage >80% for critical paths
- ✅ All Pydantic v2.5 validations work correctly
- ✅ TypeScript types prevent runtime errors
- ✅ Accessibility guidelines met (WCAG 2.1)
- ✅ Cross-browser compatibility verified

This comprehensive testing plan ensures the Cached tab implementation meets all functional, performance, security, and quality requirements before deployment.