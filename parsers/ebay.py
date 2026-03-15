"""
eBay parser for PriceTracker.

Supports: ebay.co.uk, ebay.com, ebay.de, etc.
"""

domains = [
    'ebay.co.uk',
    'ebay.com',
    'ebay.de',
    'ebay.fr',
    'ebay.es',
    'ebay.it'
]

def parse(soup):
    """
    Parses the price from an eBay product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    # eBay has different layouts for different product types
    selectors = [
        # Main price (newer layout)
        '.x-price-primary span.ux-textspans',
        '.x-price-primary .ux-textspans',

        # Buy It Now price
        '#prcIsum',
        '#mm-saleDscPrc',

        # Converted price
        '#convbinPrice',
        '#convbidPrice',

        # Price display
        '.notranslate.vi-VR-cvipPrice',

        # Bidding price
        '#prcIsum_bidPrice',

        # Original layout
        '#prcIsum',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            if price_text:
                # Detect currency
                currency = detect_currency(price_text, soup)

                return {
                    'price': price_text,
                    'currency': currency,
                    'selector': selector
                }

    return None


def detect_currency(price_text, soup):
    """
    Detects currency from price text or page metadata.

    Args:
        price_text: The price string
        soup: BeautifulSoup object for fallback detection

    Returns:
        Currency code (e.g., 'GBP', 'USD', 'EUR')
    """
    # Check for currency symbols in price text
    if '£' in price_text:
        return 'GBP'
    elif '$' in price_text:
        return 'USD'
    elif '€' in price_text:
        return 'EUR'

    # Look for itemprop price currency
    meta_currency = soup.find('meta', attrs={'itemprop': 'priceCurrency'})
    if meta_currency and meta_currency.get('content'):
        return meta_currency['content']

    # Check for data attributes
    price_wrapper = soup.find(attrs={'data-testid': 'x-price-primary'})
    if price_wrapper:
        # Try to extract currency from aria-label or data attributes
        aria_label = price_wrapper.get('aria-label', '')
        if 'GBP' in aria_label or '£' in aria_label:
            return 'GBP'
        elif 'USD' in aria_label or '$' in aria_label:
            return 'USD'
        elif 'EUR' in aria_label or '€' in aria_label:
            return 'EUR'

    # Default to GBP for .co.uk domains
    return 'GBP'
