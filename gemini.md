# Price Tracker Web App Development Plan

This document outlines the plan for creating a web application that allows users to track the prices of items from online stores.

## 1. Project Overview

### Version: 0.5.2

The web app will enable users to select an item on a webpage, specify a target price, and receive alerts when the item's price drops to the target level.

### Core Features:

*   **Track New Item:** Users can initiate tracking for a new item by providing a URL.
*   **Interactive Element Selection:** Users can visually select the price element on the rendered webpage using an inspector-like tool.
*   **Price Confirmation:** The app will display the selected price for user confirmation.
*   **Target Price:** Users can set a target price for the item.
*   **Data Storage:** The tracked items, including product name, URL, price selector, current price, and target price, will be stored in a database.
*   **Daily Price Checks:** A scheduled task will check the prices of all tracked items daily.
*   **Alerts:** Users will be notified when an item's price reaches or falls below the target price.

## 2. Proposed Technology Stack

*   **Frontend:**
    *   HTML
    *   CSS
    *   JavaScript (Vanilla JS)
*   **Backend:**
    *   Python
    *   Flask
*   **Web Scraping:**
    *   `requests`
    *   `BeautifulSoup4`
*   **Scheduling:**
    *   `schedule`
*   **Data Storage:**
    *   SQLite

## 3. Project Structure

```
pricetracker/
├── app.py
├── requirements.txt
├── instance/
│   └── pricetracker.db
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── inspector.js
├── templates/
│   └── index.html
└── parsers/
    ├── __init__.py
    └── _template.py
```

*   `app.py`: The main Flask application file.
*   `requirements.txt`: A list of Python dependencies for the project.
*   `instance/pricetracker.db`: The SQLite database file.
*   `static/`: A folder for static assets like CSS and JavaScript.
*   `templates/`: A folder for HTML templates.
*   `parsers/`: A package for website-specific parsers.

## 4. Running the Application

To run the Flask application, use the following command:

```bash
uv run python app.py
```

This will start the development server on port 5012.

## 5. Deployment

The application is deployed on a Raspberry Pi and is accessible at `http://architools.duckdns.org/pricetracker`.

### Deployment Details:

*   **Web Server:** Nginx is used as a reverse proxy to forward requests to the application.
*   **Application Server:** Waitress is used as the WSGI server to run the Flask application.
*   **Process Management:** The application is managed as a `systemd` service, which ensures that it is always running.
*   **Static Files:** Static files (CSS, JavaScript) are served directly by Nginx from `/var/www/html/pricetracker/static/` for better performance.
*   **Application Root:** The application is configured to run under the `/pricetracker` sub-path.

### Restarting the Service

To apply changes to the application, you need to restart the `systemd` service:

```bash
sudo systemctl restart pricetracker.service
```

**Note:** After making changes to the `templates` or `static` directories, you must copy them to the `/var/www/html/pricetracker/` directory with `sudo` and then restart the `pricetracker.service`.

## 6. Installation

This section describes how to set up the Price Tracker application from scratch.

### 1. Install `uv`

`uv` is used for managing the Python virtual environment and packages. You can install it by following the official `uv` installation instructions.

### 2. Create a Virtual Environment

Create a new virtual environment in the project directory:

```bash
uv venv
```

### 3. Install Dependencies

Install the required Python packages using `uv`:

```bash
uv pip install -r requirements.txt
```

### 4. Set up the `systemd` Service

Create a `systemd` service to run the application in the background. Create a file named `pricetracker.service` with the following content:

```
[Unit]
Description=Pricetracker service using uv run
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/WebApps/pricetracker
ExecStart=/home/pi/.local/bin/uv run python /home/pi/WebApps/pricetracker/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then, move this file to the `systemd` directory and enable the service:

```bash
sudo mv pricetracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pricetracker.service
sudo systemctl start pricetracker.service
```

### 5. Configure `nginx`

Create an `nginx` configuration file to act as a reverse proxy for the application. Create a file named `pricetracker.conf` with the following content:

```nginx
server {
    listen 80;
    server_name architools.duckdns.org;

    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /pricetracker/ {
        proxy_pass http://127.0.0.1:5012/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /pricetracker/static/ {
        alias /var/www/html/pricetracker/static/;
    }
}
```

Move this file to the `nginx` sites-available directory, create a symbolic link, and reload `nginx`:

```bash
sudo mv pricetracker.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/pricetracker.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Application Configuration

After setting up the `systemd` service and `nginx`, you need to make a small change to the `app.py` file to ensure that Flask generates the correct URLs for the static files (CSS, JavaScript).

In `app.py`, modify the line where the Flask app is created to include the `static_url_path`:

**From:**
```python
app = Flask(__name__)
```

**To:**
```python
app = Flask(__name__, static_url_path='/pricetracker/static')
```

This will ensure that the application correctly loads the static files when running under the `/pricetracker` sub-path.

## 7. Backup

To create a backup of the application, use the `backup.sh` script. This script will create a zip archive of the application files and the database.

```bash
bash backup.sh <new_version>
```

-   `<new_version>`: The new version number to be updated in the `gemini.md` and `templates/index.html` files.

If you don't provide a new version number, the script will prompt you to enter one.

## Troubleshooting and Resolution

This section documents the issues encountered during deployment and their resolutions.

### 1. Incorrect URL Generation (Double Prefixing)

**Problem:** Links within the application were generating URLs with a double `/pricetracker` prefix (e.g., `/pricetracker/pricetracker/login`). This was caused by a conflict between Flask's `APPLICATION_ROOT` and a custom `url_for_prefixed` context processor.

**Resolution:**
*   **Flask Application (`app.py`):**
    *   Removed the custom `inject_url_for_prefixed` context processor.
    *   Removed `_external=True` from all `redirect(url_for(...))` calls.
*   **Templates:**
    *   Reverted all `url_for_prefixed` calls back to `url_for`.

### 2. Nginx Configuration Conflicts and Missing Headers

**Problem:** The application was not correctly routing requests, and the `X-Forwarded-Prefix` header was missing, leading to incorrect redirects and styling issues. This was due to conflicts with the default nginx site and an incomplete `pricetracker.conf`.

**Resolution:**
*   **Nginx Configuration (`/etc/nginx/sites-available/pricetracker.conf`):**
    *   Ensured `proxy_pass` has a trailing slash (`http://127.0.0.1:5012/`).
    *   Added `proxy_set_header X-Forwarded-Prefix /pricetracker;`.
    *   Added a `location /pricetracker/static` block with `alias /home/pi/WebApps/pricetracker/static;` to serve static files directly by nginx.
*   **Nginx Default Site (`/etc/nginx/sites-available/default`):**
    *   Removed `default_server` from the `listen` directives to prevent it from conflicting with `pricetracker.conf`.

### 3. Static File Access Permissions

**Problem:** Static files (CSS, JavaScript) were not loading, resulting in an unstyled page. This was due to insufficient permissions for the nginx process (`www-data` user) to access the application's static file directory.

**Resolution:**
*   **User Group Membership:** Added the `www-data` user to the `pi` group (`sudo usermod -a -G pi www-data`).
*   **Directory Permissions:** Changed directory permissions to allow group access:
    *   `sudo chmod 750 /home/pi`
    *   `sudo chmod -R 750 /home/pi/WebApps`

### 4. Application Server Management

**Problem:** Inconsistent application behavior due to multiple instances running or improper restarts.

**Resolution:**
*   Ensured the application is run with Gunicorn (`gunicorn --workers 3 --bind 0.0.0.0:5012 app:app &`) for robust process management.
*   Provided commands for graceful restarts (`pkill gunicorn` followed by the Gunicorn start command).

**General Advice:**
*   Always clear browser cache after making changes to web application files.
*   Restart/reload relevant services (nginx, Gunicorn) after configuration or code changes.

## Debugging

This project has a `debug` folder with a `debug.md` file that documents the available debugging tools and scripts. When you encounter an issue, please refer to this file to see if there are any existing tools that can help you diagnose the problem.

---

## Session State - 2025-10-12

### Current Status:

*   **Parser Infrastructure:** Implemented a new parser system to support website-specific price extraction. This makes the application more robust and easier to extend.
*   **Advanced Inspector:** Implemented an advanced inspector that automatically detects the price on a page using a set of heuristics. This makes the application much easier to use.
*   **Password Reset Script:** Improved the password reset script to use a relative path for the database and to accept the username and new password as command-line arguments.
*   **Documentation:** Updated the `gemini.md` file to reflect the current state of the project and to include deployment information.

### Next Steps:

*   Continue to improve the `autoDetectPrice` function by adding more heuristics.
*   Test the application to ensure that the new features are working correctly.

---

## Session State - 2025-09-14

### Current Status:

*   The basic project structure has been created in the `pricetracker` directory.
*   A Python virtual environment has been created using `uv` and is located at `pricetracker/.venv`.
*   The initial code for the Flask application (`app.py`), HTML (`templates/index.html`), CSS (`static/css/style.css`), and JavaScript (`static/js/main.js`) has been written.
*   A `requirements.txt` file with the project dependencies has been created.
*   The Flask application is running on port 5012.
*   Phase 1 (UI/UX Improvements) is complete:
    *   Price display is formatted with currency symbols.
    *   `alert()`, `prompt()`, and `confirm()` dialogs have been replaced with non-blocking toast messages and a custom modal.
    *   Visual feedback for the inspector has been confirmed as sufficient.
*   Phase 2 (Core Functionality & Data Management) is complete:
    *   Editing and deleting items from the table is implemented.
    *   Table sorting and filtering is implemented.
    *   Loading states for the table are implemented.
    *   Visual cues for price changes (up/down arrows) are implemented.
*   Phase 3 (Advanced Features & Infrastructure) is complete:
    *   Responsive Design: Implemented.
    *   About Page: Implemented.
    *   Deployment Documentation: Updated to include Nginx and Waitress.
    *   User Authentication: Implemented. All routes are now using the database and are protected.
*   Phase 4 (UI/UX Improvements) is complete:
    *   Improved the design of the login and register pages.
    *   Added flash messages for login/logout/registration.
    *   Improved the overall styling of the application.
*   Phase 5 (Advanced Features) is complete:
    *   Implemented email notifications for price alerts.
*   Bug Fixes:
    *   Fixed a bug where the application would crash if the user was not logged in.

### Next Steps:
*   Add more advanced features:
    *   Add support for more online stores.
    *   Implement a more advanced inspector.

## Future Improvements

Here's a list of potential future improvements for the Price Tracker application:

### UI/UX Enhancements:
*   **Better Feedback:** Use toast messages instead of `alert()` for success/failure. (Implemented)
*   **Clearer Price Display in Table:** Format the "Current Price" and "Target Price" in the table with currency symbols and consistent decimal places. (Implemented)
*   **Visual Feedback for Inspector:** When an element is clicked in the inspector, provide a clear visual indication that it has been selected (e.g., a persistent border, a checkmark icon). (Implemented)
*   **Responsive Design:** Ensure the application works well on mobile devices. (Implemented)
*   **Public Home Page:** A landing page for non-logged-in users.

### Core Functionality & Data Management:
*   **Per-Item Currency Tracking:** Automatically detect and store the currency (e.g., USD, GBP) when an item is first tracked. The application will then use the specific currency for each item's price checking and display. (Implemented)
*   **Table Sorting/Filtering:** Implement sorting by product name, current price, or target price. Add filtering options, including filtering by "sale" (if the price is lower than the target price). (Implemented)
*   **Edit/Delete Items:** Allow users to edit the target price or product name, or delete tracked items directly from the table. (Implemented)
*   **Loading States for Table:** Show a loading spinner or message when the tracked items list is being fetched. (Implemented)
*   **Visual Cues for Price Changes:** In the `check_prices` function, if the price changes, the table could visually indicate if it went up or down (e.g., a small arrow icon next to the price). (Implemented)

### User Account Management:
*   **User Settings Page:** Create a page where users can view their username and registered email address, and reset their password. (Implemented)
*   **Password Reset System:** Implement a system to send a password reset link to the user's registered email address. (Partially Implemented - manual script)
*   **Email Preference Setting:** A user setting for summary vs. individual alert emails. (Implemented)

### Deployment and Security:
*   **Set up HTTPS:** Configure the web server to use SSL/TLS to encrypt the traffic between the browser and the server.

### Advanced Features:
*   **User Authentication:** Implement user authentication to allow for multiple users, each with their own tracking list. (Implemented)
*   **About Page:** Create an "About" page showing how to use the application. (Implemented)
*   **Per-Item Email Alerts:** A checkbox next to each item to enable email alerts. (Implemented)

### Testing and Quality Assurance:
*   **Website Compatibility Testing:** Test and troubleshoot adding items from various websites.
*   **Email Alert Testing:** Verify the email alert functionality.

### delivery plan:

  Phase 1: Immediate UI/UX Improvements & Bug Fixes

   1. Clearer Price Display in Table: Format the "Current Price" and "Target Price" in the table with currency symbols and consistent decimal places. (Implemented).
   2. Better Feedback: Use toast messages instead of alert() for success/failure. (Implemented).
   3. Visual Feedback for Inspector: When an element is clicked in the inspector, provide a clear visual indication that it has been selected (e.g., a persistent border, a checkmark icon). (Implemented).

  Phase 2: Core Functionality & Data Management

   1. Edit/Delete Items: Allow users to edit the target price or product name, or delete tracked items directly from the table. (Implemented).
   2. Table Sorting/Filtering: Implement sorting by product name, current price, or target price. Add filtering options, including filtering by "sale" (if the price is lower than the target price). (Implemented).
   3. Loading States for Table: Show a loading spinner or message when the tracked items list is being fetched. (Implemented).
   4. Visual Cues for Price Changes: In the check_prices function, if the price changes, the table could visually indicate if it went up or down (e.g., a small arrow icon next to the price). (Implemented).

  Phase 3: Advanced Features & Infrastructure

   1. Responsive Design: Ensure the application works well on mobile devices. (Implemented).
   2. About Page: Create an "About" page showing how to use the application. (Implemented).
   3. User Authentication: Implement user authentication to allow for multiple users, each with their own tracking list. (Implemented).


### Other potential future developments:

   * **More Advanced Inspector:** The current inspector is basic. A more advanced one could allow users to select elements by dragging a box, or provide more detailed information about the selected element. (In Progress)
   6. Notifications: Implement notifications for price changes, either through email or in-app alerts. (Implemented)
   7. product search. search for products on multiple websites to pick them to find products to track or track multiple sites for the same product.
   8. Customizable Alerts: Allow users to set custom alerts for price changes, such as receiving an email when the price drops below a certain threshold.
   9. Price History Tracking: Keep a history of price changes for each item, allowing users to see how prices have changed over time.
   10. Integration with Payment Gateways: Allow users to purchase items directly from the application, using payment gateways like PayPal or Stripe.
   11. Affliate links to allow the website to be funded through affiliate systems.