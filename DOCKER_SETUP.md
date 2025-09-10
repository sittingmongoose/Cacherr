# Docker Setup for Cacherr

## Volume Mounts Required for Settings Persistence

For settings to persist after Docker restart, you MUST mount the `/config` directory to a persistent location on your host.

### Unraid Template
The provided `my-cacherr.xml` template already includes the proper configuration:

```
Config Directory: /config -> /mnt/user/appdata/cacherr/
```

### Docker Run Example
```bash
docker run -d \
  --name cacherr \
  --platform linux/amd64 \
  -p 5445:5445 \
  -v /mnt/user/Media/:/media:ro \
  -v /mnt/user/Transcode/Cacherr/:/cache:rw \
  -v /mnt/user/appdata/cacherr/:/config:rw \
  -e PLEX_URL="http://192.168.1.10:32400" \
  -e PLEX_TOKEN="your_plex_token" \
  sittingmongoose/cacherr:dev
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  cacherr:
    image: sittingmongoose/cacherr:dev
    platform: linux/amd64
    container_name: cacherr
    ports:
      - "5445:5445"
    volumes:
      - /mnt/user/Media/:/media:ro
      - /mnt/user/Transcode/Cacherr/:/cache:rw  
      - /mnt/user/appdata/cacherr/:/config:rw
    environment:
      - PLEX_URL=http://192.168.1.10:32400
      - PLEX_TOKEN=your_plex_token
      - TZ=UTC
    restart: unless-stopped
```

## Troubleshooting Settings Persistence

### Settings Don't Save
1. Check that `/config` is properly mounted to a writable host directory
2. Verify the host directory has correct permissions (readable/writable by the container user)
3. Check container logs for permission errors:
   ```bash
   docker logs cacherr
   ```

### Settings Reset After Restart
- The `/config` directory is not mounted or is mounted to a temporary location
- Mount `/config` to a persistent host directory like `/mnt/user/appdata/cacherr/`

### Configuration File Location
Inside the container, settings are stored in:
- `/config/cacherr_config.json`

On the host (with proper mount), this becomes:
- `/mnt/user/appdata/cacherr/cacherr_config.json`

## Security Best Practices

1. **Use dedicated directories**: Don't map system directories to container volumes
2. **Read-only media**: Mount media directories as read-only (`:ro`)
3. **Principle of least privilege**: Only mount what's necessary
4. **Secure tokens**: Use the WebGUI to configure tokens instead of environment variables when possible

## WebGUI Configuration

Once the container is running with proper mounts:
1. Access WebGUI at `http://your-server-ip:5445`
2. Go to Settings
3. Configure Plex connection and other settings
4. Click "Save Changes" 
5. Settings will persist in the mounted `/config` directory

## File Structure
```
/config/
├── cacherr_config.json    # Main configuration file
├── logs/                  # Application logs (if configured)
└── data/                  # Runtime data (if needed)
```