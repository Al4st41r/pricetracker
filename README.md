# Price Tracker

A Flask web application that monitors product prices from online stores and alerts users when prices drop below target thresholds.

**Version:** 0.5.2

## Features

- Track product prices from various online retailers
- Automatic daily price checks (midnight)
- Email notifications when target prices are reached
- Browser emulation to bypass bot protection (Playwright)
- Visual price element selector with auto-detection
- Multi-currency support (USD, EUR, GBP)
- Website-specific parsers for automatic price extraction
- User authentication and settings management

## Quick Start

### Development Server

```bash
# Run the development server
uv run python app.py
```

The development server runs on port 5012.

### Production Deployment

The application is deployed at `http://architools.duckdns.org/pricetracker` using:
- **Nginx** as reverse proxy
- **systemd** service for process management
- **uv** for Python environment management

```bash
# Restart the production service after Python code changes
sudo systemctl restart pricetracker.service

# View service logs
journalctl -u pricetracker.service -f
```

**Important:** Static files and templates are symlinked to `/var/www/html/pricetracker/`, so changes are immediately reflected. After modifying CSS/JS/HTML, hard-refresh your browser (Ctrl+Shift+R) to clear cached files. Only Python code changes require a service restart.

## Project Structure

```
pricetracker/
├── app.py                  # Main Flask application
├── static/
│   ├── css/
│   │   └── style.css       # Application styles
│   └── js/
│       ├── main.js         # Main application logic
│       └── inspector.js    # Price element detection
├── templates/
│   ├── index.html          # Main tracking interface
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── settings.html       # User settings
│   └── about.html          # Usage instructions
├── parsers/                # Website-specific parsers
│   ├── __init__.py
│   ├── _template.py
│   └── [various parser files]
├── debug/                  # Debugging tools
└── instance/
    └── pricetracker.db     # SQLite database
```

## Database Management

```bash
# Query tracked items
python query_items.py

# Count users
python count_users.py

# Print all users
python print_users.py

# Reset user password
python debug/reset_.py <username> <new_password>
```

## Backup

```bash
# Create backup with version update
bash backup.sh <new_version>
```

Backups are stored in `~/WebApps/pricetracker/backups/` with format `YYYYMMDD-VERSION-COMMENT`.

## Phase 2: Browser Emulation

The application uses Playwright headless browser to bypass bot protection on websites that block automated scraping.

**Endpoint:** `/discover_price` (POST)

**Features:**
- Chromium headless browser with 1280x720 viewport
- Automatic price detection using heuristics
- Screenshot capture for visual confirmation
- Handles JavaScript-heavy sites and Cloudflare protection

**Test Results:** See `PHASE2_TEST_RESULTS.md` for performance metrics.

## Adding New Parser

Create a new parser file in `parsers/` directory:

```python
# parsers/example.py
domains = ['example.com']

def parse(soup):
    """Extract price from BeautifulSoup object"""
    price_elem = soup.select_one('.price')
    if price_elem:
        return {
            'price': price_elem.text.strip(),
            'currency': 'GBP',
            'selector': '.price'
        }
    return None
```

The parser will be automatically loaded at startup.

## Security Considerations

- Database: SQLite at `instance/pricetracker.db`
- Passwords: Hashed using Werkzeug security functions
- Authentication: All routes except login/register require `@login_required`
- **TODO:** Move SECRET_KEY to environment variable

## Known Issues

- **Browser cache:** Users must hard-refresh (Ctrl+Shift+R) after deployment to load new JavaScript/CSS
- **Timeout:** Pages taking >30 seconds to load will timeout
- **Email notifications:** Currently a placeholder function (not implemented)

## Dependencies

- Flask - Web framework
- Flask-Login - User session management
- Flask-SQLAlchemy - Database ORM
- BeautifulSoup4 - HTML parsing
- Playwright - Browser automation
- Schedule - Daily price check scheduler

## Documentation

- `CLAUDE.md` - Development guide for AI assistants
- `DEPLOYMENT.md` - Deployment instructions
- `gemini.md` - Project history and requirements
- `debug/debug.md` - Debugging tools documentation
- `PHASE2_TEST_RESULTS.md` - Browser emulation test results

## Support

For issues or questions, consult the documentation files or check the service logs.
