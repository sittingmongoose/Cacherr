#!/usr/bin/env python3
"""
Migration script to convert old PlexCache settings to PlexCacheUltra environment variables
"""

import json
import os
import sys
from pathlib import Path

def load_old_settings(settings_file):
    """Load settings from old PlexCache settings file"""
    try:
        with open(settings_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading old settings: {e}")
        return None

def convert_to_env_vars(settings):
    """Convert old settings to environment variables"""
    env_vars = {}
    
    # Plex configuration
    env_vars['PLEX_URL'] = settings.get('PLEX_URL', '')
    env_vars['PLEX_TOKEN'] = settings.get('PLEX_TOKEN', '')
    
    # Path configuration
    env_vars['CACHE_DIR'] = settings.get('cache_dir', '/mnt/cache')
    env_vars['REAL_SOURCE'] = settings.get('real_source', '/mnt/user')
    env_vars['PLEX_SOURCE'] = settings.get('plex_source', '/media')
    
    # New: Flexible destination configuration (optional)
    # env_vars['CACHE_DESTINATION'] = ''  # Uncomment and set if you want custom destination
    
    # New: Multiple source support (optional)
    # env_vars['ADDITIONAL_SOURCES'] = ''  # Uncomment and set if you have additional sources
    
    # Media configuration
    env_vars['NUMBER_EPISODES'] = str(settings.get('number_episodes', 5))
    env_vars['DAYS_TO_MONITOR'] = str(settings.get('days_to_monitor', 99))
    env_vars['WATCHLIST_TOGGLE'] = str(settings.get('watchlist_toggle', True)).lower()
    env_vars['WATCHLIST_EPISODES'] = str(settings.get('watchlist_episodes', 1))
    env_vars['WATCHLIST_CACHE_EXPIRY'] = str(settings.get('watchlist_cache_expiry', 6))
    env_vars['WATCHED_MOVE'] = str(settings.get('watched_move', True)).lower()
    env_vars['WATCHED_CACHE_EXPIRY'] = str(settings.get('watched_cache_expiry', 48))
    env_vars['USERS_TOGGLE'] = str(settings.get('users_toggle', True)).lower()
    env_vars['EXIT_IF_ACTIVE_SESSION'] = str(settings.get('exit_if_active_session', False)).lower()
    
    # Performance configuration
    env_vars['MAX_CONCURRENT_MOVES_CACHE'] = str(settings.get('max_concurrent_moves_cache', 5))
    env_vars['MAX_CONCURRENT_MOVES_ARRAY'] = str(settings.get('max_concurrent_moves_array', 2))
    
    # Debug configuration
    env_vars['DEBUG'] = str(settings.get('debug', False)).lower()
    
    # Notification configuration
    notification_type = settings.get('notification', 'system')
    if notification_type == 'unraid':
        env_vars['NOTIFICATION_TYPE'] = 'unraid'
    else:
        env_vars['NOTIFICATION_TYPE'] = 'webhook'
    
    # Webhook URL (if available)
    webhook_url = settings.get('webhook_url', '')
    if webhook_url:
        env_vars['WEBHOOK_URL'] = webhook_url
    
    # Logging configuration
    log_level = settings.get('log_level', '')
    if log_level:
        env_vars['LOG_LEVEL'] = log_level.upper()
    
    # New: Test mode configuration (optional)
    env_vars['TEST_MODE'] = 'false'  # Default to false for production use
    env_vars['TEST_SHOW_FILE_SIZES'] = 'true'
    env_vars['TEST_SHOW_TOTAL_SIZE'] = 'true'
    env_vars['TEST_DRY_RUN'] = 'true'
    
    return env_vars

def write_env_file(env_vars, output_file):
    """Write environment variables to .env file"""
    try:
        with open(output_file, 'w') as f:
            f.write("# PlexCacheUltra Environment Variables\n")
            f.write("# Generated from old PlexCache settings\n\n")
            
            # Write required configuration
            f.write("# Plex Configuration\n")
            f.write(f"PLEX_URL={env_vars.get('PLEX_URL', '')}\n")
            f.write(f"PLEX_TOKEN={env_vars.get('PLEX_TOKEN', '')}\n\n")
            
            f.write("# Path Configuration\n")
            f.write(f"CACHE_DIR={env_vars.get('CACHE_DIR', '/mnt/cache')}\n")
            f.write(f"REAL_SOURCE={env_vars.get('REAL_SOURCE', '/mnt/user')}\n")
            f.write(f"PLEX_SOURCE={env_vars.get('PLEX_SOURCE', '/media')}\n\n")
            
            # Write new optional configuration with comments
            f.write("# New: Flexible Destination Configuration (Optional)\n")
            f.write("# CACHE_DESTINATION=/mnt/cache/media  # Uncomment to specify custom destination\n\n")
            
            f.write("# New: Multiple Source Support (Optional)\n")
            f.write("# ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media  # Uncomment to add sources\n\n")
            
            f.write("# Logging\n")
            f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n\n")
            
            f.write("# Notifications\n")
            if env_vars.get('WEBHOOK_URL'):
                f.write(f"WEBHOOK_URL={env_vars.get('WEBHOOK_URL')}\n")
            f.write(f"NOTIFICATION_TYPE={env_vars.get('NOTIFICATION_TYPE', 'webhook')}\n\n")
            
            f.write("# Performance Settings\n")
            f.write(f"MAX_CONCURRENT_MOVES_CACHE={env_vars.get('MAX_CONCURRENT_MOVES_CACHE', '5')}\n")
            f.write(f"MAX_CONCURRENT_MOVES_ARRAY={env_vars.get('MAX_CONCURRENT_MOVES_ARRAY', '2')}\n\n")
            
            f.write("# Media Settings\n")
            f.write(f"NUMBER_EPISODES={env_vars.get('NUMBER_EPISODES', '5')}\n")
            f.write(f"DAYS_TO_MONITOR={env_vars.get('DAYS_TO_MONITOR', '99')}\n")
            f.write(f"WATCHLIST_TOGGLE={env_vars.get('WATCHLIST_TOGGLE', 'true')}\n")
            f.write(f"WATCHLIST_EPISODES={env_vars.get('WATCHLIST_EPISODES', '1')}\n")
            f.write(f"WATCHLIST_CACHE_EXPIRY={env_vars.get('WATCHLIST_CACHE_EXPIRY', '6')}\n")
            f.write(f"WATCHED_MOVE={env_vars.get('WATCHED_MOVE', 'true')}\n")
            f.write(f"WATCHED_CACHE_EXPIRY={env_vars.get('WATCHED_CACHE_EXPIRY', '48')}\n")
            f.write(f"USERS_TOGGLE={env_vars.get('USERS_TOGGLE', 'true')}\n")
            f.write(f"EXIT_IF_ACTIVE_SESSION={env_vars.get('EXIT_IF_ACTIVE_SESSION', 'false')}\n\n")
            
            f.write("# New: Test Mode Configuration\n")
            f.write(f"TEST_MODE={env_vars.get('TEST_MODE', 'false')}\n")
            f.write(f"TEST_SHOW_FILE_SIZES={env_vars.get('TEST_SHOW_FILE_SIZES', 'true')}\n")
            f.write(f"TEST_SHOW_TOTAL_SIZE={env_vars.get('TEST_SHOW_TOTAL_SIZE', 'true')}\n")
            f.write(f"TEST_DRY_RUN={env_vars.get('TEST_DRY_RUN', 'true')}\n\n")
            
            f.write("# Debug Mode\n")
            f.write(f"DEBUG={env_vars.get('DEBUG', 'false')}\n")
        
        print(f"Environment file written to: {output_file}")
        return True
    except Exception as e:
        print(f"Error writing environment file: {e}")
        return False

def main():
    """Main migration function"""
    print("PlexCacheUltra Migration Tool")
    print("=" * 40)
    
    # Check for old settings file
    old_settings_file = "plexcache_settings.json"
    if not os.path.exists(old_settings_file):
        print(f"Old settings file not found: {old_settings_file}")
        print("Please ensure plexcache_settings.json is in the current directory.")
        sys.exit(1)
    
    print(f"Found old settings file: {old_settings_file}")
    
    # Load old settings
    old_settings = load_old_settings(old_settings_file)
    if not old_settings:
        print("Failed to load old settings. Exiting.")
        sys.exit(1)
    
    print("Successfully loaded old settings.")
    
    # Convert to environment variables
    env_vars = convert_to_env_vars(old_settings)
    print(f"Converted {len(env_vars)} settings to environment variables.")
    
    # Write .env file
    output_file = ".env"
    if write_env_file(env_vars, output_file):
        print("\nMigration completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Review the generated {output_file} file")
        print(f"2. Configure new features (optional):")
        print(f"   - CACHE_DESTINATION: Set custom destination for cached media")
        print(f"   - ADDITIONAL_SOURCES: Add comma-separated list of additional sources")
        print(f"   - TEST_MODE: Enable test mode for safe operation preview")
        print(f"3. Update any paths or settings as needed")
        print(f"4. Run 'docker-compose up -d' to start PlexCacheUltra")
        print(f"5. Access the web dashboard at http://your-server:5443")
        print(f"\nNew Features Available:")
        print(f"✨ Flexible destination paths for cached media")
        print(f"✨ Multiple source support for mounted shares")
        print(f"✨ Test mode for safe operation preview")
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
