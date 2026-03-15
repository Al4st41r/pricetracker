# CSS Iframe & Modal Size Verification

## Test Date: 2025-12-29

## Landing Page Screenshot
✓ Successfully captured screenshot (screenshot_landing.png)
- Site is running correctly
- Title shows "PriceTracker" (emoji removed as requested)
- Navigation is clean and functional

## CSS Rules Verified

### Iframe Size Rules (app.css)
```css
.page-iframe {
    width: 100% !important;
    min-width: 600px !important;
    height: 800px !important;
    min-height: 600px !important;
    border: none;
    display: block;
    background: white;
}
```

### Iframe Container (app.css)
```css
#page-content {
    margin-top: var(--spacing-xl);
    border: 2px solid var(--color-border);
    overflow: auto;
    min-width: 600px !important;
    min-height: 600px !important;
    width: 100% !important;
}
```

### Mobile Override (app.css)
```css
@media screen and (max-width: 768px) {
    .page-iframe {
        min-width: 600px !important;
        min-height: 600px !important;
        width: 100% !important;
        height: 800px !important;
    }
}
```

### Modal Overlay (app.css)
```css
.modal {
    display: none;
    position: fixed !important;
    z-index: 10000 !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    height: 100% !important;
    overflow: auto;
    background-color: rgba(0, 0, 0, 0.5) !important;
}
```

## Expected Behavior

### Iframe
- **Minimum size:** 600px × 600px (enforced with !important)
- **Default size:** 100% width × 800px height
- **On mobile:** Still maintains 600px × 600px minimum (scrollable if screen is smaller)
- **Background:** White
- **Border:** None

### Modal
- **Position:** Fixed overlay (covers entire viewport)
- **Z-index:** 10,000 (well above navigation at 100)
- **Background:** Semi-transparent black (50% opacity)
- **Behavior:** Centered, scrolls to top when opened

## JavaScript Enhancements

### showModal() Function
```javascript
modal.style.cssText = 'display: block !important;';
window.scrollTo(0, 0);  // Scroll to top
```

### hideModal() Function
```javascript
modal.style.cssText = 'display: none !important;';
```

## Static Files
✓ Static files are symlinked: `/var/www/html/pricetracker/static -> /home/pi/WebApps/pricetracker/static`
✓ Changes to CSS/JS files are immediately available (no copy needed)

## Browser Cache Issue

⚠️ **IMPORTANT:** If changes aren't visible, the browser has cached the old CSS/JS files.

**Solution: Hard Refresh**
- Firefox/Chrome: `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)
- Or clear browser cache completely

## Verification Status

✅ CSS file contains all !important rules
✅ Iframe minimum size: 600px × 600px
✅ Modal overlay: position fixed with z-index 10000
✅ JavaScript uses cssText with !important
✅ Mobile responsive rules in place
✅ Static files symlinked correctly
✅ Service running on port 5012

## If Still Seeing Issues

1. **Clear browser cache** (most common issue)
2. Check browser developer tools:
   - Inspect the `.page-iframe` element
   - Look at "Computed" styles
   - Check if any other CSS is overriding
3. Check browser console for errors
4. Verify you're viewing the correct URL (not a cached version)
