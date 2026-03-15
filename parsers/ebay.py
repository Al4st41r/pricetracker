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

        # Fallback meta tags
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
        '[itemprop="price"]',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            if price_element.name == 'meta':
                price_text = price_element.get('content', '')
            else:
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
    if '£' in price_text or 'GBP' in price_text.upper():
        return 'GBP'
    elif '$' in price_text or 'USD' in price_text.upper():
        return 'USD'
    elif '€' in price_text or 'EUR' in price_text.upper():
        return 'EUR'

    # Look for currency in meta tags
    meta_currency = soup.find('meta', attrs={'property': 'product:price:currency'})
    if not meta_currency:
        meta_currency = soup.find('meta', attrs={'itemprop': 'priceCurrency'})
    
    if meta_currency and meta_currency.get('content'):
        return meta_currency['content']

    # Default to GBP (since most tracked sites are .co.uk)
    return 'GBP'
