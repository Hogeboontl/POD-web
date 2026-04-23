import multiprocessing

workers = 2 * multiprocessing.cpu_count() + 1 # Dynamically determine the optimal number of workers
worker_class = 'gevent' # Use gevent async workers
worker_connections = 1000  # Maximum concurrent connections per worker

# Gunicorn Configuration for Nginx
bind = "127.0.0.1:8000"  # Ensure it matches the Nginx proxy_pass setting
forwarded_allow_ips = "*"  # Allow requests from Nginx
proxy_protocol = True  # Enable proxy support

# Timeout Settings
timeout = 600  # Automatically restart workers if they take too long
graceful_timeout = 600  # Graceful shutdown for workers

# Worker Restart Settings
max_requests = 1000  # Restart workers after processing 1000 requests
max_requests_jitter = 50  # Add randomness to avoid mass restarts

# Keep-Alive Settings
keepalive = 2  # Keep connections alive for 2s


# Logging Settings
accesslog = "-"  # Send access logs to stdout
errorlog = "-"  # Send error logs to stdout
loglevel = "info"  # Adjust verbosity level
