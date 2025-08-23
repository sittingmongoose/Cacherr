# PlexCacheUltra Architecture Overview

This document provides a high-level overview of the PlexCacheUltra architecture after the comprehensive refactoring completed in phases 1-6 of the architectural improvement project.

## Table of Contents
- [System Overview](#system-overview)
- [Core Architectural Principles](#core-architectural-principles)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Key Design Patterns](#key-design-patterns)
- [Technology Stack](#technology-stack)

## System Overview

PlexCacheUltra is a sophisticated media file caching system designed to optimize Plex Media Server performance by intelligently managing file placement between high-speed cache storage and slower array storage. The system has been completely restructured using modern architectural patterns to ensure maintainability, testability, and scalability.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PlexCacheUltra System                    │
├─────────────────────────────────────────────────────────────┤
│                    Web Interface Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Dashboard   │ │ REST API    │ │ Health Endpoints    │   │
│  │ Routes      │ │ Endpoints   │ │                     │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Application Context & Bootstrap               │ │
│  │         (Dependency Injection Orchestration)           │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Command     │ │ Cache       │ │ Media & File        │   │
│  │ Service     │ │ Service     │ │ Services            │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Data Access Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Cache       │ │ Config      │ │ Metrics             │   │
│  │ Repository  │ │ Repository  │ │ Repository          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Task        │ │ File System │ │ Configuration       │   │
│  │ Scheduler   │ │ Interface   │ │ Management          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Architectural Principles

The new architecture follows these key principles:

### 1. **Separation of Concerns**
- **Web Layer**: Handles HTTP requests, routing, and presentation
- **Service Layer**: Contains business logic and domain operations
- **Data Access Layer**: Manages data persistence and retrieval
- **Infrastructure Layer**: Provides system-level services

### 2. **Dependency Injection**
- All dependencies are managed through a centralized DI container
- Promotes loose coupling and high testability
- Enables easy mocking and testing of components

### 3. **Command Pattern Implementation**
- All operations are encapsulated as commands
- Provides undo/redo capabilities
- Enables operation queuing and scheduling
- Comprehensive audit trails

### 4. **Repository Pattern**
- Clean abstraction over data access
- File-based persistence with atomic operations
- Comprehensive error handling and data validation

### 5. **Configuration Management**
- Environment-aware configuration system
- Automatic path resolution for different deployment environments
- Validation and migration support

## System Components

### Web Application Module (`src/web/`)
Handles all HTTP interactions and user interface:

- **Flask Application Factory**: Environment-specific app configuration
- **Route Handlers**: RESTful API endpoints and dashboard routes
- **Middleware**: Authentication, security, and request processing
- **Health Checks**: Docker and orchestration-ready endpoints

### Application Bootstrap (`src/application.py`)
Central bootstrap and lifecycle management:

- **ApplicationContext**: Main application lifecycle coordinator
- **Service Registration**: DI container setup and service wiring
- **Startup/Shutdown**: Graceful application lifecycle management
- **Configuration Integration**: Environment-specific configuration loading

### Core Services (`src/core/`)
Business logic and domain services:

- **Dependency Injection Container**: Complete IoC implementation
- **Command System**: Command pattern with queuing and monitoring
- **Cache Engine**: Core caching logic and Plex integration
- **Service Interfaces**: Clean contracts between components

### Repository Layer (`src/repositories/`)
Data access and persistence:

- **File-Based Repositories**: JSON persistence with atomic operations
- **Cache Repository**: Manages cached file metadata and statistics
- **Configuration Repository**: Handles configuration persistence
- **Metrics Repository**: Stores operational metrics and analytics

### Task Scheduler (`src/scheduler/`)
Background task processing:

- **Recurring Tasks**: Scheduled cache operations and maintenance
- **Cron Integration**: Flexible scheduling with cron expressions
- **Task Management**: Queue management and error recovery

### Configuration System (`src/config/`)
Comprehensive configuration management:

- **Environment Detection**: Automatic Docker/development/production detection
- **Path Resolution**: Dynamic path configuration based on environment
- **Validation**: Pydantic-based configuration validation
- **Migration**: Version-aware configuration migration support

## Data Flow

### 1. **Request Processing Flow**
```
HTTP Request → Flask Router → Route Handler → Service Layer → 
Repository Layer → Data Storage → Response
```

### 2. **Command Execution Flow**
```
Command Creation → Command Queue → Command Executor → 
Service Resolution (DI) → Operation Execution → 
Result Logging → History Storage
```

### 3. **Scheduled Task Flow**
```
Scheduler Trigger → Task Factory → Command Creation → 
Command Service → Execution → Status Update → 
Metrics Collection
```

### 4. **Configuration Loading Flow**
```
Environment Detection → Configuration Factory → 
Provider Selection → Validation → Migration (if needed) → 
Service Registration
```

## Key Design Patterns

### 1. **Dependency Injection Container**
- **Purpose**: Manage service dependencies and lifetimes
- **Implementation**: Complete IoC container with factory patterns
- **Benefits**: Loose coupling, easy testing, flexible service management

### 2. **Command Pattern**
- **Purpose**: Encapsulate operations as objects
- **Implementation**: Commands with undo/redo and queuing capabilities
- **Benefits**: Operation history, scheduled execution, error recovery

### 3. **Repository Pattern**
- **Purpose**: Abstract data access operations
- **Implementation**: File-based repositories with thread-safe operations
- **Benefits**: Clean separation, easy testing, data consistency

### 4. **Application Factory Pattern**
- **Purpose**: Create configured application instances
- **Implementation**: Environment-specific factory methods
- **Benefits**: Flexible deployment, consistent setup, easy testing

### 5. **Service Locator Pattern**
- **Purpose**: Central service resolution
- **Implementation**: Integrated with DI container
- **Benefits**: Dynamic service resolution, runtime flexibility

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Flask**: Web framework for HTTP interface
- **Pydantic**: Data validation and serialization
- **APScheduler**: Task scheduling and background jobs

### Development & Testing
- **pytest**: Testing framework
- **unittest.mock**: Mocking and test doubles
- **Type Hints**: Static type checking support

### Deployment & Infrastructure
- **Docker**: Containerization and deployment
- **Docker Compose**: Multi-container orchestration
- **JSON**: Configuration and data persistence

### External Integrations
- **Plex Media Server**: Primary media server integration
- **Webhook Notifications**: External notification services
- **File Systems**: Direct file system operations

## Key Architectural Benefits

### 1. **Maintainability**
- Clear separation of concerns
- Modular component structure
- Comprehensive error handling
- Extensive logging and monitoring

### 2. **Testability**
- Dependency injection enables easy mocking
- Comprehensive test suite with unit and integration tests
- Mock implementations for external dependencies
- Test fixtures and utilities

### 3. **Scalability**
- Modular architecture supports independent scaling
- Command queuing handles high load scenarios
- Repository pattern supports different storage backends
- Service-oriented design enables microservice migration

### 4. **Reliability**
- Robust error handling and recovery
- Atomic file operations prevent data corruption
- Command history enables operation rollback
- Health monitoring and diagnostics

### 5. **Flexibility**
- Environment-aware configuration
- Pluggable service implementations
- Command pattern enables easy feature extension
- Repository pattern supports multiple backends

## Next Steps

This architecture provides a solid foundation for future enhancements:

1. **Microservice Migration**: Services can be easily extracted to separate processes
2. **Database Backend**: Repository pattern enables database integration
3. **Advanced Monitoring**: Enhanced metrics and monitoring capabilities
4. **API Extensions**: RESTful API can be extended for mobile/web clients
5. **Performance Optimization**: Component-level performance tuning

For detailed implementation information, see the specific architectural component documentation in this directory.