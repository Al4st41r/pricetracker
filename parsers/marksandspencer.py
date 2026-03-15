"""
Marks & Spencer parser for PriceTracker.

Supports: marksandspencer.com
"""

domains = [
    'marksandspencer.com',
    'www.marksandspencer.com'
]

def parse(soup):
    """
    Parses the price from a Marks & Spencer product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    selectors = [
        # Main price display
        '.product-price',

        # Current price
        '.current-price',

        # Price element
        '[data-testid="product-price"]',

        # Sale price
        '.price-now',

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
                # M&S is UK-only, so currency is always GBP
                return {
                    'price': price_text,
                    'currency': 'GBP',
                    'selector': selector
                }

    return None
