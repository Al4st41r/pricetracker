"""
John Lewis parser for PriceTracker.

Supports: johnlewis.com
"""

domains = [
    'johnlewis.com',
    'www.johnlewis.com'
]

def parse(soup):
    """
    Parses the price from a John Lewis product page.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        A dictionary with 'price', 'currency', and 'selector' keys,
        or None if the price cannot be found.
    """

    selectors = [
        # Main price display
        '.price.price--large',
        '.price',

        # Product price
        '[data-test="product-price"]',

        # Price now
        '.price-now',

        # Offer price
        '.offer-price',

        # Microdata price
        '[itemprop="price"]',
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)

            if price_text:
                # John Lewis is UK-only, so currency is always GBP
                return {
                    'price': price_text,
                    'currency': 'GBP',
                    'selector': selector
                }

    return None
