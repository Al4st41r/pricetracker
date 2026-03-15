"""
ASOS parser for PriceTracker.

Supports: asos.com
"""

domains = [
    'asos.com',
    'www.asos.com'
]

def parse(soup):
    """
    Parses the price from an ASOS product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    selectors = [
        # Main price display (newer layout)
        '[data-testid="current-price"]',

        # Product price
        '.product-price',

        # Current price
        '.current-price',

        # Price element
        '[data-id="current-price"]',

        # Microdata price
        '[itemprop="price"]',

        # Generic price
        '.price',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            if price_text:
                # Detect currency from text
                currency = detect_currency(price_text)

                return {
                    'price': price_text,
                    'currency': currency,
                    'selector': selector
                }

    return None


def detect_currency(price_text):
    """
    Detects currency from price text.

    Args:
        price_text: The price string

    Returns:
        Currency code (e.g., 'GBP', 'USD', 'EUR')
    """
    if '£' in price_text:
        return 'GBP'
    elif '$' in price_text:
        return 'USD'
    elif '€' in price_text:
        return 'EUR'

    # Default to GBP
    return 'GBP'
