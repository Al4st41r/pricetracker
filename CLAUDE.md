# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Price Tracker is a Flask web application that monitors product prices from online stores and alerts users when prices drop below target thresholds. Version: 0.5.2 (as documented in gemini.md).

## Key Commands

### Development

```bash
# Run the development server
uv run python app.py
```

The development server runs on port 5012.

### Deployment (Raspberry Pi Production)

The application is deployed at `http://architools.duckdns.org/pricetracker` using:
- **Nginx** as reverse proxy
- **uv** for virtual environment management
- **systemd** service for process management

```bash
# Restart the production service after Python code changes
sudo systemctl restart pricetracker.service

# View service logs
journalctl -u pricetracker.service -f
```

**Note**: Static files and templates are symlinked from `/home/pi/WebApps/pricetracker/` to `/var/www/html/pricetracker/`, so changes to CSS/JS/HTML are immediately reflected. Only Python code changes require a service restart.

### Database Management

```bash
# Query tracked items
python query_items.py

# Count users
python count_users.py

# Print all users
python print_users.py

# Reset user password (manual script)
python debug/reset_.py <username> <new_password>
```

### Backup

```bash
# Create backup with version update
bash backup.sh <new_version>
```

## Architecture

### Core Application Structure

**app.py**: Main Flask application file containing:
- All route handlers (login, register, track_item, etc.)
- Database models: `User` and `TrackedItem`
- Price checking scheduler (runs daily at midnight via `schedule` library)
- Email notification system (currently a placeholder function)
- **Phase 2: `/discover_price` endpoint** - Playwright browser emulation for bot protection bypass (lines 197-336)

### Database Models

**User Model**:
- Fields: id, username, email, password_hash, email_notifications
- Relationship: one-to-many with TrackedItem
- Uses Flask-Login for session management

**TrackedItem Model**:
- Fields: id, product_name, url, css_selector, current_price, target_price, price_change_status, currency, user_id
- Tracks price history with up/down/same status indicators
- Per-item currency support (USD, EUR, GBP)

### Parser System

**parsers/** directory contains website-specific price extraction logic:
- `__init__.py`: Dynamically loads all parsers at startup, mapping domains to parser functions
- `_template.py`: Template for creating new parsers (not loaded)
- Each parser file must define:
  - `domains` list: domain names the parser supports
  - `parse(soup)` function: returns dict with `{'price': str, 'currency': str, 'selector': str}` or None

**Parser Workflow**:
1. When tracking an item, check if URL domain has a registered parser
2. If parser exists, use it to extract price automatically (no CSS selector needed from user)
3. If no parser, fall back to user-provided CSS selector
4. Daily price checks use the same logic

### Frontend Architecture

**Static Files** (served directly by Nginx in production):
- `static/js/main.js`: Main application logic, table management, AJAX calls
- `static/js/inspector.js`: Advanced price element detection with automatic heuristics
- `static/css/style.css`: Application styling

**Templates**:
- `index.html`: Main tracking interface
- `login.html`, `register.html`: Authentication pages
- `settings.html`: User settings (email notifications, password reset)
- `about.html`: Usage instructions

**Inspector Feature**: Client-side tool that allows users to visually select price elements on webpages. Uses auto-detection heuristics to suggest price elements.

### Background Tasks

Price checking runs in a separate daemon thread using the `schedule` library:
- Scheduled for midnight daily (`schedule.every().day.at("00:00")`)
- Runs `check_prices()` function within Flask app context
- Updates database with new prices and sends email alerts when target prices are met

### Deployment-Specific Configuration

**ProxyFix Middleware**: Required for running under `/pricetracker` sub-path:
```python
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```

**Static Files**: In production, Nginx serves static files from `/var/www/html/pricetracker/static/` for performance. After modifying static files or templates, they must be manually copied to this location with `sudo` permissions.

## Phase 2: Playwright Browser Emulation (Current Implementation)

**Status**: ✅ Implemented and tested (December 2025)

### Overview
Phase 2 replaces simple HTTP requests with headless browser automation to bypass bot protection on websites that block automated scraping (403 Forbidden errors, Cloudflare, etc.).

### Implementation Details

**Endpoint**: `/discover_price` (POST, @login_required)
- **Location**: app.py lines 197-336
- **Method**: Uses Playwright's Chromium headless browser
- **Browser Config**:
  - Viewport: 1280x720
  - User Agent: Chrome 120.0.0.0 on Windows 10
  - Wait Strategy: `networkidle` + 2000ms delay

**Price Detection Algorithm**:
The endpoint runs JavaScript in the browser context to auto-detect prices:
1. Searches for `itemprop="price"` attributes (+10 score)
2. Identifies elements with "price" in class names (+5 score)
3. Scans for currency symbols (£, $, €) (+1 score)
4. Ranks by score (prioritises shorter text = fewer extraneous characters)
5. Returns highest-scoring element with price, selector, and screenshot

**Response Format**:
```json
{
  "success": true,
  "price": "£4.99",
  "selector": ".price",
  "page_title": "Product Name",
  "screenshot": "base64_encoded_image"
}
```

### Testing

**Test Script**: `test_playwright.py`
- Standalone script to verify Playwright without full web interface
- Tests bot-protected sites and reports detection results
- Run with: `uv run python test_playwright.py`

**Test Results**: Documented in `PHASE2_TEST_RESULTS.md`
- ✅ gear4music.com: Successfully bypassed bot protection (previously 403 Forbidden)
- ✅ Detected price: £4.99 with `.price` selector
- ✅ Screenshot capture: ~190KB
- ✅ Detection score: 5.1667

### Frontend Integration

**main.js** (line 355):
```javascript
fetch(`${APPLICATION_ROOT}/discover_price`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: url})
})
```

**User Workflow**:
1. User enters product URL
2. Frontend shows "Loading page with browser emulation..." message
3. Backend launches Playwright, loads page, detects price, captures screenshot
4. Frontend displays screenshot + detected price (or manual entry form if detection fails)
5. User confirms/edits price details
6. Item tracked with detected CSS selector

### Known Issues

**Browser Cache**: Users must hard-refresh (Ctrl+Shift+R) after deployment to get updated JavaScript. Old cached versions may attempt to use deprecated `/proxy` endpoint.

**Timeout Handling**: Pages that take >30 seconds to load will timeout. Error message returned to user.

### Phase 2 vs Phase 1 Comparison

**Phase 1 (Deprecated)**:
- Simple HTTP requests with BeautifulSoup
- Failed on bot-protected sites (403 errors)
- No JavaScript rendering
- `/proxy` endpoint (removed)

**Phase 2 (Current)**:
- Playwright headless browser
- Bypasses bot protection
- Full JavaScript rendering
- Auto-detection with visual confirmation
- `/discover_price` endpoint

### Dependencies
- `playwright` - Browser automation library
- Chromium browser installed via: `playwright install chromium`

### Performance
- Page load time: 3-5 seconds typical
- Screenshot size: ~190KB average
- Detection success rate: High on standard e-commerce sites

## Important Notes

### URL Generation Issues (Historical)
The application previously had double-prefixing issues (`/pricetracker/pricetracker/...`). This was resolved by:
- Removing custom `url_for_prefixed` context processor
- Using standard Flask `url_for()` in templates
- Relying on ProxyFix middleware for correct URL generation

### Static File Permissions
Nginx user (`www-data`) requires read access to application files:
- `www-data` added to `pi` group
- Directory permissions: `chmod 750` for `/home/pi` and `/home/pi/WebApps`

### Security Considerations
- Database uses SQLite at `instance/pricetracker.db`
- SECRET_KEY is hardcoded in app.py - should be changed in production
- Passwords are hashed using Werkzeug's security functions
- All routes except login/register require authentication (`@login_required`)

## Debugging Tools

Located in `debug/` directory:
- `debug.md`: Documentation for available debugging tools
- `check_website.js`: Playwright script for headless browser testing and screenshots
- `reset_.py`: Password reset utility

**Root directory**:
- `test_playwright.py`: Standalone Playwright test script for verifying bot protection bypass without web interface
- `PHASE2_TEST_RESULTS.md`: Documentation of Phase 2 test results and performance metrics

## Development Workflow

1. Make changes to code in `/home/pi/WebApps/pricetracker`
2. Test locally using `uv run python app.py`
3. **For Python code changes only**: Restart systemd service: `sudo systemctl restart pricetracker.service`
4. **For static/template changes**: No deployment needed (files are symlinked)
5. **CRITICAL**: Hard-refresh browser cache (Ctrl+Shift+R) to load new JavaScript/CSS
6. Check logs: `journalctl -u pricetracker.service -f`

**File Structure**:
- `/var/www/html/pricetracker/static/` → symlinked to `/home/pi/WebApps/pricetracker/static/`
- `/var/www/html/pricetracker/templates/` → symlinked to `/home/pi/WebApps/pricetracker/templates/`

**Note**: Browser cache issues are common after updates. If users report errors like "HTTP 0 error" or requests to old endpoints (e.g., `/proxy`), instruct them to hard-refresh their browser.

## Current Status (29 December 2025)

**Phase 2 Implementation**: ✅ Complete and deployed
- `/discover_price` endpoint implemented with Playwright browser emulation
- Successfully tested with gear4music.com (bypassed bot protection)
- Service running on port 5012, accessible at `http://architools.duckdns.org/pricetracker`
- Frontend updated to use new endpoint

**Recent Testing**:
- ✅ gear4music.com: Successfully detected £4.99 with `.price` selector
- ⚠️ Clarks.com: User reported "HTTP 0 error" - diagnosed as browser cache issue
- **Action Required**: User needs to hard-refresh browser (Ctrl+Shift+R) to clear cached JavaScript

**Next Steps for Validation**:
1. Confirm hard-refresh resolves Clarks URL issue
2. Test additional protected sites (Amazon UK, other retailers from parser list)
3. Verify screenshot display quality in web interface
4. Test end-to-end confirmation workflow

**Phase 3 Considerations** (after Phase 2 validation):
- Implement intelligent fallback system: Playwright → Parser → Manual
- Add caching for repeated price checks
- Optimise screenshot size/quality
- Consider Chromium headless shell for faster performance

## Future Considerations

As documented in gemini.md, planned improvements include:
- HTTPS/SSL setup
- Enhanced parser system for more websites
- More advanced price detection heuristics
- Password reset via email (currently manual script)
- Product search across multiple websites
