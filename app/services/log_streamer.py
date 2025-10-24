"""
Log Streaming Service for Real-time Debug Panel

This service captures application logs and streams them to connected clients
via Server-Sent Events (SSE). This enables the frontend debug panel to show
actual backend logs in real-time.
"""

import logging
import queue
import threading
from typing import Set
from datetime import datetime


class LogStreamHandler(logging.Handler):
    """
    Custom logging handler that captures logs and broadcasts them to subscribers.
    """
    
    def __init__(self):
        super().__init__()
        self.subscribers: Set[queue.Queue] = set()
        self._lock = threading.Lock()
    
    def emit(self, record: logging.LogRecord):
        """
        Called when a log record is emitted.
        Broadcasts the log to all subscribers.
        """
        try:
            # Filter out noisy HTTP logs
            if record.name in ('httpx', 'httpcore', 'qdrant_client') and record.levelno < logging.WARNING:
                return
            
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record)
            }
            
            # Broadcast to all subscribers
            with self._lock:
                dead_queues = set()
                for subscriber_queue in self.subscribers:
                    try:
                        # Non-blocking put with small timeout
                        subscriber_queue.put_nowait(log_entry)
                    except queue.Full:
                        # Queue is full, mark for removal
                        dead_queues.add(subscriber_queue)
                
                # Remove dead queues
                self.subscribers -= dead_queues
                
        except Exception:
            self.handleError(record)
    
    def subscribe(self) -> queue.Queue:
        """
        Subscribe to log stream.
        Returns a queue that will receive log entries.
        """
        subscriber_queue = queue.Queue(maxsize=100)
        with self._lock:
            self.subscribers.add(subscriber_queue)
        return subscriber_queue
    
    def unsubscribe(self, subscriber_queue: queue.Queue):
        """
        Unsubscribe from log stream.
        """
        with self._lock:
            self.subscribers.discard(subscriber_queue)


# Global log stream handler
_log_stream_handler = None


def get_log_stream_handler() -> LogStreamHandler:
    """
    Get or create the global log stream handler.
    """
    global _log_stream_handler
    if _log_stream_handler is None:
        _log_stream_handler = LogStreamHandler()
        _log_stream_handler.setLevel(logging.INFO)
        
        # Use simple format for streaming
        formatter = logging.Formatter('%(message)s')
        _log_stream_handler.setFormatter(formatter)
        
        # Attach ONLY to root logger - it will capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(_log_stream_handler)
        
        # Don't attach to child loggers - they propagate to root
        # This prevents duplicate logs
    
    return _log_stream_handler


def subscribe_to_logs() -> queue.Queue:
    """
    Subscribe to application logs.
    Returns a queue that will receive log entries.
    """
    handler = get_log_stream_handler()
    return handler.subscribe()


def unsubscribe_from_logs(subscriber_queue: queue.Queue):
    """
    Unsubscribe from application logs.
    """
    handler = get_log_stream_handler()
    handler.unsubscribe(subscriber_queue)
