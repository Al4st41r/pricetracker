
"""
This is a template for creating a new parser.

To create a new parser, follow these steps:

1.  **Copy this file** and rename it to something descriptive, e.g., `amazon_parser.py`.
2.  **Update the `domains` list** with the domain(s) of the website(s) this parser supports.
    For example: `domains = ['amazon.com', 'amazon.co.uk']`
3.  **Implement the `parse` function**.
    - This function takes a BeautifulSoup object (`soup`) as input.
    - It should find the price element on the page and extract the price as a string.
    - It should return the price string, or `None` if the price cannot be found.

**Parser Logic Guidelines:**

- **Be specific:** Use CSS selectors that are as specific as possible to the price element.
- **Be robust:** Try to handle different page layouts and variations.
- **Use multiple selectors:** If a website has multiple layouts, you can use a list of selectors and try them in order.
- **Handle dynamic content:** If the price is loaded with JavaScript, you may need to use a different approach (e.g., look for the price in a script tag).
- **Return a clean price:** The returned price string should be as clean as possible, containing only the numerical value and the currency symbol.
"""

# A list of domain names that this parser supports.
# This is used to map a URL to the correct parser.
domains = ['example.com']

def parse(soup):
    """
    Parses the price from a BeautifulSoup object.

    Args:
        soup: A BeautifulSoup object representing the page.

    Returns:
        The price as a string, or None if the price cannot be found.
    """

    # --- IMPLEMENT YOUR PARSING LOGIC HERE ---

    # Example:
    # price_element = soup.select_one('#priceblock_ourprice')
    # if price_element:
    #     return price_element.get_text(strip=True)

    return None
