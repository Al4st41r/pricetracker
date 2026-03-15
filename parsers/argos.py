"""
Argos parser for PriceTracker.

Supports: argos.co.uk
"""

domains = [
    'argos.co.uk',
    'www.argos.co.uk'
]

def parse(soup):
    """
    Parses the price from an Argos product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    selectors = [
        # Main price display
        '[data-test="product-price"]',

        # Price element
        '.product-price',

        # Now price (sale price)
        '[data-test="price-now"]',

        # Was/Now pricing
        '.price-now',

        # Microdata price
        '[itemprop="price"]',

        # Alternative selectors
        '.pdp-price',
        '.price',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            if price_text:
                # Argos is UK-only, so currency is always GBP
                return {
                    'price': price_text,
                    'currency': 'GBP',
                    'selector': selector
                }

    return None
