# ADR-004: Environment-Aware Configuration Management

## Status
Accepted

## Context

The original PlexCacheUltra configuration system had several critical problems:

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
            return Path.home() / ".plexcache" / "cache"
        elif self.environment == EnvironmentType.TEST:
            return Path(tempfile.gettempdir()) / "plexcache_test" / "cache"
        else:
            return self.base_directory / "cache"
```

### Configuration Validation
```python
class Config(BaseModel):
    """Main configuration model with validation"""
    
    # Plex settings
    plex_url: str = Field(..., regex=r'^https?://.+')
    plex_token: str = Field(..., min_length=20)
    
    # Directory paths
    cache_directory: Optional[Path] = None
    array_directory: Optional[Path] = None
    
    # Resource limits
    max_cache_size: int = Field(default=50_000_000_000, ge=1_000_000_000)  # 50GB default
    max_concurrent_operations: int = Field(default=4, ge=1, le=20)
    
    @validator('plex_url')
    def validate_plex_connectivity(cls, v):
        """Validate Plex server connectivity"""
        if not NetworkValidator.test_connectivity(v):
            raise ValueError(f"Cannot connect to Plex server: {v}")
        return v
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
cache_directory: ~/.plexcache/cache
array_directory: ~/.plexcache/array
plex_url: http://localhost:32400
log_level: DEBUG
enable_debugging: true
```

### Test Environment
```yaml
environment: test
cache_directory: /tmp/plexcache_test/cache
array_directory: /tmp/plexcache_test/array
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

## Future Considerations

1. **Configuration UI**: Web-based configuration interface
2. **Advanced Validation**: More sophisticated validation rules
3. **Dynamic Reconfiguration**: Runtime configuration updates
4. **Configuration Profiles**: Pre-defined configuration templates
5. **Cloud Configuration**: Remote configuration storage and sync

This ADR establishes a robust, flexible configuration system that adapts automatically to different environments while providing validation, migration, and user-friendly error handling.