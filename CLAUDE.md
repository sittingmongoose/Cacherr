# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Commands

### Backend (Python)
```bash
# Start development server
python main.py

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Type checking (use Pydantic v2.5 syntax)
python -m mypy src/

# Lint Python code
python -m flake8 src/
```

### Frontend (React + TypeScript)
```bash
cd frontend/

# Development server
npm run dev

# Build production bundle
npm run build

# Type checking
npm run type-check

# Lint and fix
npm run lint:fix

# Run tests
npm run test
```

### Docker Development
```bash
# Build for Unraid (amdx64 compatible)
docker build -t sittingmongoose/cacherr:dev .

# Run with development config
docker run -d --name cacherr -p 5445:5445 \
  -e PLEX_URL="http://localhost:32400" \
  -e PLEX_TOKEN="test-token" \
  -v /tmp/cacherr:/config \
  sittingmongoose/cacherr:dev

# View logs
docker logs cacherr --tail 50

# Rebuild and restart quickly
docker stop cacherr && docker rm cacherr && docker build -t sittingmongoose/cacherr:dev . && docker run -d --name cacherr -p 5445:5445 -e PLEX_URL="http://localhost:32400" -e PLEX_TOKEN="test-token" -v /tmp/cacherr:/config sittingmongoose/cacherr:dev
```

## High-Level Architecture

### Core System Design
PlexCacheUltra is a **dependency-injection based** Python application with a **React frontend**. The system uses a **custom DI container** for service management and follows **SOLID principles** throughout.

**Key Architectural Patterns:**
- **Dependency Injection Container** (`src/core/container.py`) - Central service registry with lifecycle management
- **Application Context** (`src/application.py`) - Main bootstrap that wires all services together
- **Repository Pattern** (`src/repositories/`) - Data access layer with file-based storage
- **Command Pattern** (`src/core/commands/`) - Encapsulated operations with undo/redo capability
- **Service Layer** (`src/core/`) - Business logic services (cache engine, Plex integration, etc.)

### Backend Architecture (Python Flask + Pydantic v2)

**Configuration System** (`src/config/`):
- **Pydantic v2.5 models** with comprehensive validation (`pydantic_models.py`)
- **Settings hierarchy**: Web GUI overrides → Environment variables → .env file → defaults
- **Type-safe configuration** with computed fields and field validators
- **Persistent configuration** saved to `/config/cacherr_config.json`

**Core Services** (`src/core/`):
- **CacherrEngine** - Main media caching orchestrator
- **PlexCacheEngine** - Plex API integration and media discovery
- **CachedFilesService** - SQLite-based file tracking with fallback database paths
- **TaskScheduler** - APScheduler-based job management
- **WebSocket Service** - Real-time communication with frontend

**Web Layer** (`src/web/`):
- **Flask app** with CORS support for React frontend
- **API routes** (`routes/api.py`) - RESTful endpoints following APIResponse pattern
- **Health endpoints** (`routes/health.py`) - Docker health checks and monitoring
- **Static serving** - Serves React production build from `/frontend/dist/`

**Error Handling Strategy**:
- **Graceful degradation** - Services fail independently without crashing the app
- **Database fallback paths** - Multiple locations tried for SQLite database
- **Service initialization** - Non-critical services (CachedFilesService) allow startup to continue on failure

### Frontend Architecture (React + TypeScript)

**State Management** (`src/store/AppContext.tsx`):
- **React Context + useReducer** for global state
- **Type-safe actions** and reducers with comprehensive error handling
- **Real-time WebSocket integration** for live updates
- **Persistent UI settings** saved to localStorage

**Component Architecture**:
- **Lazy-loaded routes** - Code splitting for better performance  
- **Error boundaries** - Comprehensive error handling prevents app crashes
- **Custom hooks** (`src/hooks/useApi.ts`) - API integration with loading/error states
- **Compound components** - Reusable UI patterns (StatusCard, StatsGrid, etc.)

**API Integration** (`src/services/api.ts`):
- **APIService class** with retry logic and comprehensive error handling
- **TypeScript interfaces** for all API responses
- **WebSocket service** for real-time updates with automatic reconnection

**Styling & UI**:
- **Tailwind CSS** with custom design system
- **Responsive design** with mobile-first approach
- **Dark/light theme** with auto-detection
- **Accessibility** features built-in

## Critical Development Notes

### Always Use Pydantic v2.5 Syntax
```python
# Correct Pydantic v2 syntax
from pydantic import BaseModel, Field, ConfigDict, field_validator

class MyModel(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Name field")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.upper()
```

### Docker Build Requirements
- **Always build for amdx64** Unraid compatibility
- **Multi-stage builds** - Frontend built in Node stage, copied to Python stage
- **Security considerations** - Non-root user execution with proper permission handling

### Mount Problem Troubleshooting
When encountering mount-related issues, reference `test_mount.sh` to see previous attempts. Document any new solutions in `mountproblem.md` to track progress.

### Database Initialization Pattern
The `CachedFilesService` uses a **fallback database path strategy**:
1. `/config/data/cached_files.db` (preferred)
2. `/config/cached_files.db` (secondary)  
3. `/tmp/cached_files.db` (fallback)

This allows the application to start even with permission issues.

### React Error Boundary Best Practices
- **Always wrap components** in error boundaries to prevent app crashes
- **Add proper error handling** to WebSocket connections and API calls
- **Use try-catch blocks** in useEffect hooks to prevent unhandled errors
- **Provide fallback UI** for degraded functionality

### Service Registration Pattern
Services are registered in `src/application.py` using the DI container:
```python
# Singleton services
container.register_singleton(ServiceInterface, ServiceImplementation)

# Factory services with dependencies
container.register_factory(
    ServiceInterface,
    lambda provider: ServiceImplementation(
        provider.resolve(DependencyInterface)
    )
)
```

### API Response Pattern
All API endpoints follow a consistent response format:
```python
{
    "success": bool,
    "data": any,  # null on error
    "error": str,  # null on success
    "message": str,  # optional
    "timestamp": str
}
```

### Context7 Usage
Always check if Context7 can help with library documentation and examples, especially for:
- Pydantic model patterns
- React component best practices
- Flask API development
- Docker configuration