# Deployment Guide

This guide provides instructions on how to deploy the Price Tracker application in a production environment on a Linux server using nginx and waitress.

## 1. Directory Structure

For a standard and secure setup, we recommend the following directory structure:

*   **/opt/pricetracker**: This directory will contain the application code (the Python files, `requirements.txt`, etc.).
*   **/var/www/html/pricetracker**: This directory will contain the static assets (CSS, JavaScript) that will be served directly by nginx.

## 2. Prerequisites

Before you begin, ensure you have the following installed on your server:

*   Python 3.8 or higher
*   `git`
*   `nginx`

## 3. Installation

1.  **Clone the application code:**

    ```bash
    sudo git clone <repository_url> /opt/pricetracker # Replace with your repo URL
    cd /opt/pricetracker
    ```

2.  **Create a virtual environment:**

    ```bash
    sudo python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    sudo pip install uv
    sudo uv pip install -r requirements.txt
    ```

4.  **Copy static files:**

    Copy the `static` directory to the location where nginx will serve it from.

    ```bash
    sudo cp -r /opt/pricetracker/static /var/www/html/pricetracker
    ```

5.  **Set permissions:**

    Ensure that your user has the correct permissions for the application directory.

    ```bash
    sudo chown -R <your_username>:<your_username> /opt/pricetracker
    ```

## 4. Configure and Run the Application

We will use `waitress` as the WSGI server to run the Python application and `nginx` as a reverse proxy to handle incoming requests and serve static files.

### 4.1. Running with Waitress

We will run `waitress` as a systemd service.

1.  **Create a service file:**

    ```bash
    sudo nano /etc/systemd/system/pricetracker.service
    ```

2.  **Add the following content:**

    ```ini
    [Unit]
    Description=Price Tracker WSGI Application
    After=network.target

    [Service]
    User=<your_username>
    Group=<your_username>
    WorkingDirectory=/opt/pricetracker
    ExecStart=/opt/pricetracker/.venv/bin/waitress-serve --host 127.0.0.1 --port 5012 app:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

### 4.2. Configuring Nginx

1.  **Create an nginx configuration file:**

    ```bash
    sudo nano /etc/nginx/sites-available/pricetracker
    ```

2.  **Add the following server block:**

    ```nginx
    server {
        listen 80;
        server_name your_domain.com; # Replace with your domain or server IP

        location /static {
            alias /var/www/html/pricetracker/static;
        }

        location / {
            proxy_pass http://127.0.0.1:5012;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
    ```

3.  **Enable the site:**

    ```bash
    sudo ln -s /etc/nginx/sites-available/pricetracker /etc/nginx/sites-enabled/
    ```

4.  **Test and restart nginx:**

    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```

## 5. Start the Application

Now you can start the Price Tracker application service:

```bash
sudo systemctl start pricetracker.service
sudo systemctl enable pricetracker.service # To start on boot
```

Your application should now be accessible at `http://your_domain.com`.