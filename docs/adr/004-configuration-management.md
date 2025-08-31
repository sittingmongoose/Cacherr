# ADR-004: Environment-Aware Configuration Management

## Status
Accepted

## Context

The original Cacherr configuration system had several critical problems:

1. **Hard-coded Docker paths**: Paths were hardcoded to `/cache` and `/array`, making non-Docker deployments problematic
2. **Environment coupling**: Configuration was tightly coupled to Docker environment assumptions
3. **No validation**: Configuration values were not validated, leading to runtime errors
4. **Poor defaults**: No intelligent defaults based on deployment environment
5. **Manual path management**: Users had to manually configure paths for different environments
6. **No migration support**: Configuration changes broke existing deployments
7. **Limited override capabilities**: Difficult to override specific settings without changing entire configuration
8. **No environment detection**: System couldn't automatically adapt to different deployment scenarios

These issues made the system difficult to deploy outside Docker containers and prone to configuration errors.

## Decision

We decided to implement a comprehensive, environment-aware configuration management system:

### Environment Detection
- **Automatic detection**: Automatically detect Docker, development, test, and production environments
- **Override capabilities**: Allow manual environment specification via environment variables
- **Intelligent defaults**: Provide appropriate defaults for each environment type
- **Path resolution**: Dynamic path resolution based on detected environment

### Configuration Architecture
- **Factory pattern**: Environment-specific configuration factories
- **Provider pattern**: Pluggable configuration providers for different sources
- **Validation system**: Comprehensive validation using Pydantic models
- **Migration support**: Automatic configuration migration between versions

### Key Features
- **Multi-source support**: Environment variables, files, command line arguments
- **Schema validation**: Strong typing and validation for all configuration values
- **Network validation**: Connectivity testing for external services (Plex, webhooks)
- **Resource management**: Automatic resource limit calculation based on system capabilities
- **Backup and recovery**: Configuration backup and rollback capabilities

## Consequences

### Positive Consequences

1. **Environment Flexibility**
   - Works seamlessly across Docker, bare metal, development, and test environments
   - No more hard-coded paths breaking non-Docker deployments
   - Intelligent defaults reduce configuration burden

2. **Improved Reliability**
   - Validation catches configuration errors at startup
   - Network connectivity testing prevents runtime failures
   - Resource limit calculation prevents system overload

3. **Better User Experience**
   - Automatic environment detection reduces setup complexity
   - Clear error messages for configuration issues
   - Migration support prevents breaking changes

4. **Enhanced Security**
   - Validation prevents injection attacks through configuration
   - Sensitive data handling with proper masking
   - Secure default configurations

5. **Development Benefits**
   - Easy switching between environments for testing
   - Configuration mocking for unit tests
   - Clear separation of environment-specific concerns

### Negative Consequences

1. **Increased Complexity**
   - More sophisticated configuration system to understand
   - Additional abstraction layers
   - More components to maintain and test

2. **Startup Overhead**
   - Configuration validation takes time during startup
   - Network connectivity testing adds delay
   - Environment detection processing

3. **Migration Challenges**
   - Existing configurations need migration
   - Potential breaking changes during upgrade
   - Backup and recovery complexity

4. **Testing Complexity**
   - Need to test multiple environment scenarios
   - Configuration validation testing required
   - Mock implementations for testing

## Alternatives Considered

### 1. Simple Configuration Updates (Status Quo+)
- **Pros**: Minimal changes, easy to implement
- **Cons**: Doesn't solve fundamental environment coupling issues
- **Why rejected**: Doesn't address the root cause of deployment problems

### 2. External Configuration Management (Consul, etcd)
- **Pros**: Centralized configuration, advanced features
- **Cons**: Additional infrastructure, complexity, deployment dependencies
- **Why rejected**: Adds unnecessary complexity for single-instance deployments

### 3. Configuration File Templates
- **Pros**: Simple approach, familiar pattern
- **Cons**: Manual template management, still requires environment-specific setup
- **Why rejected**: Doesn't provide automatic adaptation capabilities

### 4. Environment Variable Only
- **Pros**: Simple, Docker-native, no file management
- **Cons**: Complex configurations become unwieldy, no structured validation
- **Why rejected**: Poor user experience for complex configurations

### 5. Configuration Database
- **Pros**: Centralized, queryable, audit trail
- **Cons**: Additional dependency, complexity for simple deployments
- **Why rejected**: Overkill for current requirements

## Implementation Details

### Environment Detection
```python
class EnvironmentDetector:
    def detect_environment(self) -> EnvironmentType:
        """Automatically detect the current environment"""
        if self._is_docker_environment():
            return EnvironmentType.DOCKER
        elif self._is_test_environment():
            return EnvironmentType.TEST
        elif self._is_development_environment():
            return EnvironmentType.DEVELOPMENT
        else:
            return EnvironmentType.PRODUCTION
    
    def _is_docker_environment(self) -> bool:
        """Detect if running in Docker container"""
        return (Path('/.dockerenv').exists() or 
                os.getenv('DOCKER_CONTAINER') == 'true')
```

### Configuration Factory
```python
class ConfigurationFactory:
    def create_config(self, env: EnvironmentType = None) -> Config:
        """Create environment-specific configuration"""
        if env is None:
            env = EnvironmentDetector().detect_environment()
        
        if env == EnvironmentType.DOCKER:
            return self._create_docker_config()
        elif env == EnvironmentType.DEVELOPMENT:
            return self._create_development_config()
        elif env == EnvironmentType.TEST:
            return self._create_test_config()
        else:
            return self._create_production_config()
```

### Path Resolution
```python
class PathConfiguration(BaseModel):
    """Environment-aware path configuration"""
    
    def get_cache_directory(self) -> Path:
        """Get cache directory based on environment"""
        if self.environment == EnvironmentType.DOCKER:
            return Path("/cache")
        elif self.environment == EnvironmentType.DEVELOPMENT:
            return Path.home() / ".cacherr" / "cache"
        elif self.environment == EnvironmentType.TEST:
            return Path(tempfile.gettempdir()) / "cacherr_test" / "cache"
        else:
            return self.base_directory / "cache"
```

### Configuration Validation (Pydantic v2)
```python
from pydantic import BaseModel, Field, ConfigDict, HttpUrl, field_validator
from pydantic_settings import BaseSettings

class PlexConfig(BaseModel):
    """Plex server configuration with Pydantic v2 validation"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra='forbid'
    )
    
    url: HttpUrl = Field(..., description="Plex server URL")
    token: str = Field(..., min_length=20, description="Plex authentication token")
    username: Optional[str] = Field(None, description="Plex username (optional)")
    password: Optional[str] = Field(None, description="Plex password (optional)")
    
    @field_validator('token')
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Validate Plex token format"""
        if not v.startswith(('plex_', 'X-Plex-Token-')):
            # Allow any alphanumeric token for flexibility
            pass
        return v

class MediaConfig(BaseModel):
    """Media processing configuration with enhanced validation"""
    model_config = ConfigDict(
        validate_default=True,
        extra='forbid'
    )
    
    copy_to_cache: bool = Field(True, description="Copy files to cache (vs move)")
    delete_from_cache_when_done: bool = Field(True, description="Delete from cache when done")
    watched_move: bool = Field(True, description="Move watched content")
    users_toggle: bool = Field(True, description="Enable multi-user support")
    exit_if_active_session: bool = Field(False, description="Exit if Plex session active")
    
    # Numeric constraints with Pydantic v2
    days_to_monitor: PositiveInt = Field(99, description="Days to monitor media")
    number_episodes: PositiveInt = Field(5, description="Number of episodes to cache")
    watchlist_episodes: PositiveInt = Field(1, description="Watchlist episodes to cache")
    
    @computed_field
    @property
    def cache_mode_description(self) -> str:
        """Human-readable cache mode description"""
        return "Copy to cache (preserves originals)" if self.copy_to_cache else "Move to cache (frees source space)"

class CacherrSettings(BaseSettings):
    """Main application settings using Pydantic v2 BaseSettings"""
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.prod'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Core settings
    debug: bool = Field(False, description="Enable debug mode")
    config_dir: str = Field("/config", description="Configuration directory")
    
    # Nested configuration models
    plex: PlexConfig
    media: MediaConfig = Field(default_factory=MediaConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
```

### Migration System
```python
class ConfigurationMigration:
    def migrate_config(self, old_config: Dict, target_version: str) -> Dict:
        """Migrate configuration to target version"""
        current_version = old_config.get('version', '1.0')
        
        for migration in self._get_migrations(current_version, target_version):
            old_config = migration.apply(old_config)
            
        return old_config
```

## Environment-Specific Configurations

### Docker Environment
```yaml
environment: docker
cache_directory: /cache
array_directory: /array
plex_url: ${PLEX_URL}
plex_token: ${PLEX_TOKEN}
max_cache_size: 50000000000
log_level: INFO
```

### Development Environment
```yaml
environment: development
cache_directory: ~/.cacherr/cache
array_directory: ~/.cacherr/array
plex_url: http://localhost:32400
log_level: DEBUG
enable_debugging: true
```

### Test Environment
```yaml
environment: test
cache_directory: /tmp/cacherr_test/cache
array_directory: /tmp/cacherr_test/array
plex_url: http://mock-plex:32400
dry_run: true
log_level: DEBUG
```

## Validation Features

### Network Validation
```python
class NetworkValidator:
    @staticmethod
    def test_plex_connectivity(url: str, token: str) -> bool:
        """Test connectivity to Plex server"""
        try:
            response = requests.get(f"{url}/status/sessions", 
                                  params={'X-Plex-Token': token}, 
                                  timeout=5)
            return response.status_code == 200
        except RequestException:
            return False
```

### Path Validation
```python
class PathValidator:
    @staticmethod
    def validate_directory_access(path: Path) -> ValidationResult:
        """Validate directory access permissions"""
        if not path.exists():
            return ValidationResult(False, f"Directory does not exist: {path}")
        
        if not os.access(path, os.R_OK | os.W_OK):
            return ValidationResult(False, f"Insufficient permissions: {path}")
        
        return ValidationResult(True, "Directory access validated")
```

## Configuration Sources Priority

The system loads configuration from multiple sources in priority order:

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Environment-specific defaults**
5. **System defaults** (lowest priority)

## Usage Examples

### Automatic Environment Detection
```python
# Configuration automatically adapts to environment
config = ConfigurationFactory().create_config()
print(f"Running in {config.environment} environment")
print(f"Cache directory: {config.get_cache_directory()}")
```

### Manual Environment Override
```python
# Force specific environment
config = ConfigurationFactory().create_config(EnvironmentType.DEVELOPMENT)
```

### Configuration Validation
```python
try:
    config = Config(**config_dict)
    print("Configuration is valid")
except ValidationError as e:
    print(f"Configuration error: {e}")
```

## Migration Process

### Automatic Migration
The system automatically detects and migrates old configuration formats:

1. **Detection**: Identify configuration version
2. **Backup**: Create backup of existing configuration
3. **Migration**: Apply necessary transformations
4. **Validation**: Validate migrated configuration
5. **Commit**: Save new configuration format

### Manual Migration
For complex migrations, manual intervention may be required:

1. **Analysis**: System reports migration requirements
2. **User Input**: Request user confirmation or input
3. **Guided Process**: Step-by-step migration assistance
4. **Verification**: User verification of migrated settings

## Implementation Update: Pydantic v2 Migration (2024)

### Status: COMPLETED
The configuration system has been fully migrated to Pydantic v2 with enhanced type safety, performance, and validation capabilities.

### Key Improvements
1. **Modern Pydantic v2**: Full migration from dataclasses to Pydantic BaseModel
2. **BaseSettings Integration**: Automatic environment variable loading via pydantic-settings
3. **Enhanced Validation**: Comprehensive field validation with helpful error messages
4. **Performance Optimizations**: Model caching and production-ready optimizations
5. **Type Safety**: Complete type hints with IDE support and static analysis
6. **Real-time Validation**: API endpoints validate configuration updates in real-time

### New Configuration Architecture
```python
# Modern configuration structure
config = get_config()

# Type-safe access with IDE completion
print(config.media.copy_to_cache)  # bool
print(config.media.cache_mode_description)  # computed field
print(config.plex.url)  # HttpUrl (validated)
print(config.performance.max_concurrent_moves_cache)  # PositiveInt

# Validation and persistence
config.save_updates({
    'media': {'copy_to_cache': True},
    'performance': {'max_concurrent_moves_cache': 3}
})

# Comprehensive validation
validation_results = config.validate_all()
if not validation_results['valid']:
    print(f"Errors: {validation_results['errors']}")
```

### Configuration Flow
```
Environment Variables → CacherrSettings (BaseSettings) → Config Class → Pydantic Models
                    ↓
            Automatic Type Conversion & Validation
                    ↓
            Application Services (Type-Safe Access)
```

### Benefits Achieved
- **🛡️ Type Safety**: All configuration access is type-safe
- **⚡ Performance**: Model caching and optimized validation  
- **🔧 Maintainability**: Self-documenting Pydantic models
- **🐛 Reliability**: Comprehensive validation prevents invalid configs
- **🔄 Backward Compatibility**: Existing Docker setups work unchanged
- **📝 Self-Documenting**: Pydantic models serve as living documentation

## Future Considerations

1. **Configuration UI**: Enhanced web-based configuration interface with real-time validation
2. **Advanced Validation**: Cross-field validation and business rule enforcement
3. **Dynamic Reconfiguration**: Hot-reload capabilities for configuration updates
4. **Configuration Profiles**: Environment-specific configuration templates
5. **Cloud Configuration**: Remote configuration storage and synchronization
6. **Schema Evolution**: Automated schema migration for configuration updates

This ADR establishes a robust, modern configuration system using Pydantic v2 that provides excellent type safety, validation, and developer experience while maintaining backward compatibility.