# POD-Web

This repository contains the web service code for the POD-web project. POD-Web allows users to produce trained POD simulations for thermal modeling of computer chips without requiring direct access to the underlying mathematical code.

This service depends on the `pod-web-scheduler` repository for job submissions to function correctly.

The repostory for `pod-web-scheduler` can be found here: https://github.com/Hogeboontl/POD-web-scheduler

---

## Dependencies

- **MySQL** — used for storing user data
- **Redis** — used as the Celery message broker

### start-up order 
1. Redis
2. Slurm services
3. Celery worker (slurm_scheduler user)
4. Gunicorn (web user)
5. Nginx

### Python Environments

One  Python environment is required for this repository:

It can be created using:
```
python -m venv venv
pip install -r requirements.txt
```

### JavaScript

This webpage requires JavaScript to be enabled in the browser. Without it, the post-processing mesh viewer will not function.

---

## System Architecture

It is recommended that the web server runs inside a restricted user account seperate from the job scheduler repo. This separation prevents the web server user from having direct Slurm access. With this in place, ensure that both users are part of the same group, allowing them to access shared saved and uploaded data from the website. 

This can be done with the following commands:
```
sudo groupadd podweb_shared
sudo usermod -aG podweb_shared podwebuser
sudo usermod -aG podweb_shared slurmrunner
```

This was designed with both the web service and scheduler running on the head node.


---

## Setup

The `POD-web` folder should be placed in the user directory that will serve as the web host.

### Environment Configuration

A `.env` file must be created to store all sensitive data such as keys, passwords, and directories. The required variables are:

```
# Flask secret key for session
SECRET_KEY

# GitHub client ID and secret for OAuth
CLIENT_ID
CLIENT_SECRET

# Database config
DB
DB_USER
DB_PSSWD
DB_HOST

SLURM_RUNNER_DIR    # Location of the job scheduler code
CONFIG_DIR          # Config for the POD code simulation
UPLOAD_DIR          # User upload directory
SAVE_DIR            # User saved data directory
CELERY_LOCATION     # Location of the Celery worker

DISABLE_OAUTH_HTTPS # Allows OAuth to use HTTP (for development)
```

---

When configuring the upload and save directories, make sure both the Slurm user and the web host user have read and write access, with permissions set to propagate to subdirectories. Also ensure that this data is accessible from all compute nodes.

The upload and saved dirs can be created with the following command:

```
mkdir /path/to/uploadsorsaved && chgrp podweb_shared /path/to/uploadsorsaved  && chmod 2775 /path/to/uploadsorsaved
```


## OAuth Setup and Security

For the website to properly authenticate users and create accounts, the application needs to be registered under developer settings on an admin GitHub account. The client secret and ID must be stored in the .env file listed above.

---


## Gunicorn and Nginx

Nginx and Gunicorn are required for secure deployment. A gunicorn_config.py file is included in the repository, and a basic Nginx configuration template is provided below.

For initial installation and setup of the daemon, refer to: https://betterstack.com/community/guides/scaling-python/gunicorn-explained/

An example nginx config file is provided below:
```
server {
    listen 80;
    server_name _;

    return 301 https://$host$request_uri;
}


server {
    listen 443 ssl default_server;
    server_name _;

    ssl_certificate YOUR/CERT/KEY;
    ssl_certificate_key YOUR/CERT/KEY/PATH;
        
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    client_max_body_size 0;
    proxy_read_timeout 3000;
    proxy_connect_timeout 3000;
    proxy_send_timeout 3000;
    client_body_timeout 3000;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /job-status-stream  {
        proxy_pass http://127.0.0.1:8000;

        # Disable buffering - critical for SSE
        proxy_buffering off;
        proxy_cache off;

         # SSE headers
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding on;

        #Keep connection alive
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /static/ {
        alias /YOUR/STATIC/DIRECTORY;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}

```

This configuration extends connection timeouts (see proxy_read_timeout, proxy_send_timeout, etc.) and adds a /job-status-stream route for Server-Sent Events (SSE), both of which are not covered in the guide above.

The timeout values may need to be increased or decreased depending on the size and duration of requests. The status stream currently relies on extended timeouts rather than explicit keep-alive (heartbeat) messages.

The gunicorn_config.py file also defines a timeout, which may need to be adjusted depending on deployment requirements.

This configuration assumes HTTPS is enabled and requires an SSL certificate. Replace ssl_certificate and ssl_certificate_key with the appropriate paths for your environment.

For production deployments, using Certbot with a valid domain is recommended. For local development or testing, a self-signed certificate can be used instead, which can be made with mkcert.






---

## Running the Code

```bash
systemctl start gunicorn
systemctl start nginx
```

The config file will automatically determine the highest number of workers it can run. It is expected that the server hosting the website is not a compute node. If the number of workers needs to be set manually, adjust the value in `gunicorn_config.py`. 

---

### Known bugs
 * currently for linux and mac machines, the number forms allow for character inputs.

## Notes for Future Developers

More extensive notes on the code structure can be found in `dev_notes.md`.













