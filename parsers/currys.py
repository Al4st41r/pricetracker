"""
Currys parser for PriceTracker.

Supports: currys.co.uk
"""

domains = [
    'currys.co.uk',
    'www.currys.co.uk'
]

def parse(soup):
    """
    Parses the price from a Currys product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    selectors = [
        # Main price display
        '[data-component="Price"]',

        # Product price
        '.product-price',

        # Price now
        '.price-now',

        # Basket price
        '[data-testid="price"]',

        # Sale price
        '.sale-price',

        # Microdata price
        '[itemprop="price"]',

        # Generic price class
        '.price',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            if price_text:
                # Currys is UK-only, so currency is always GBP
                return {
                    'price': price_text,
                    'currency': 'GBP',
                    'selector': selector
                }

    return None
