import json
import logging
import requests
from typing import Optional

try:
    from ..config.settings import Config
except ImportError:
    # Fallback for testing
    from config.settings import Config

class NotificationManager:
    """Manages notifications for PlexCacheUltra"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.webhook_url = config.notifications.webhook_url
        self.webhook_headers = config.notifications.webhook_headers
        self._rate_limit_registry = {}
    
    def send_notification(self, message: str, level: str = "info") -> bool:
        """Send a notification using the configured method"""
        try:
            if self.webhook_url:
                return self._send_webhook_notification(message, level)
            else:
                self.logger.info(f"Notification: {message}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def send_summary_notification(self, message: str) -> bool:
        """Send a summary notification"""
        return self.send_notification(f"📊 {message}", "summary")
    
    # Note: unified below to accept optional details for test compatibility
    
    def send_warning_notification(self, message: str) -> bool:
        """Send a warning notification"""
        return self.send_notification(f"⚠️ {message}", "warning")
    
    def send_success_notification(self, message: str) -> bool:
        """Send a success notification"""
        return self.send_notification(f"✅ {message}", "success")
    
    def _send_webhook_notification(self, message: str, level: str = "info") -> bool:
        """Send notification via webhook (Discord, Slack, etc.)"""
        if not self.webhook_url:
            return False
        
        try:
            # Create payload based on level
            if level == "error":
                color = 0xFF0000  # Red
                title = "PlexCacheUltra Error"
            elif level == "warning":
                color = 0xFFA500  # Orange
                title = "PlexCacheUltra Warning"
            elif level == "success":
                color = 0x00FF00  # Green
            elif level == "summary":
                color = 0x0099FF  # Blue
                title = "PlexCacheUltra Summary"
            else:
                color = 0x808080  # Gray
                title = "PlexCacheUltra Info"
            
            # Discord-style embed
            embed = {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": self._get_timestamp()
            }
            
            payload = {
                "embeds": [embed]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={**headers, **self.get_webhook_headers()},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.logger.debug(f"Webhook notification sent successfully: {message}")
                return True
            else:
                self.logger.warning(f"Webhook notification failed with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Webhook request failed: {e}")
            return False

    # --- Compatibility helpers expected by tests ---
    def send_webhook(self, data: dict) -> bool:
        """Send a raw webhook payload. Returns True on 200/204."""
        if not self.webhook_url:
            return False
        try:
            headers = {"Content-Type": "application/json", **self.get_webhook_headers()}
            response = requests.post(self.webhook_url, data=json.dumps(data), headers=headers, timeout=10)
            return response.status_code in [200, 204]
        except Exception as e:
            self.logger.error(f"Webhook send error: {e}")
            return False

    def send_cache_operation_notification(self, operation_type: str, details: dict) -> bool:
        """Send a structured cache operation notification via webhook if configured."""
        message = self.format_notification_message(
            "Cache operation {op} | files: {files_count} | total: {total_size} | dest: {destination}",
            {
                'op': operation_type,
                'files_count': details.get('files_count', 0),
                'total_size': details.get('total_size', '0B'),
                'destination': details.get('destination', '')
            }
        )
        return self.send_webhook({'message': message, 'type': 'cache_operation'})

    def send_error_notification(self, message: str, details: Optional[dict] = None) -> bool:  # type: ignore[override]
        """Send an error notification (accepts optional details for compatibility)."""
        if details:
            message = f"{message} | details: {json.dumps(details)}"
        return self.send_notification(f"❌ {message}", "error")

    def send_watcher_notification(self, event_type: str, user: str, media_title: str) -> bool:
        """Send a watcher event notification."""
        return self.send_webhook({'event': event_type, 'user': user, 'title': media_title})

    def format_notification_message(self, template: str, data: dict) -> str:
        try:
            return template.format(**data)
        except Exception:
            return template

    def get_webhook_headers(self) -> dict:
        """Return configured custom webhook headers."""
        return dict(self.webhook_headers or {})

    def validate_webhook_config(self) -> bool:
        """Validate webhook configuration is present and non-empty."""
        return bool(self.webhook_url)

    # Optional rate limiting helpers (no-op if unused in tests)
    def is_rate_limited(self, key: str) -> bool:
        return False
    
    def mark_notification_sent(self, key: str) -> None:
        self._rate_limit_registry[key] = True
    
    def _send_unraid_notification(self, message: str, level: str = "info") -> bool:
        """Send notification via Unraid notification system"""
        try:
            # Map levels to Unraid notification types
            level_mapping = {
                "error": "alert",
                "warning": "warning", 
                "success": "normal",
                "info": "normal",
                "summary": "normal"
            }
            
            icon = level_mapping.get(level, "normal")
            
            # Use Unraid's notify command
            import subprocess
            cmd = [
                "/usr/local/emhttp/webGui/scripts/notify",
                "-e", "PlexCacheUltra",
                "-s", level.title(),
                "-d", message,
                "-i", icon
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.debug(f"Unraid notification sent successfully: {message}")
                return True
            else:
                self.logger.warning(f"Unraid notification failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Unraid notification: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
