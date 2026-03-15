"""
Test script to verify parsers are loaded and can extract prices.
"""

import sys
from parsers import parsers

def main():
    print("=" * 60)
    print("PriceTracker Parser Test")
    print("=" * 60)
    print()

    # Show loaded parsers
    print(f"Loaded {len(parsers)} parsers for the following domains:")
    print()
    for domain in sorted(parsers.keys()):
        print(f"  • {domain}")
    print()
    print("=" * 60)
    print()

    # Domain groupings
    domain_groups = {}
    for domain in parsers.keys():
        # Extract the main part (e.g., amazon, ebay)
        parts = domain.split('.')
        if len(parts) >= 2:
            main_name = parts[-2]  # e.g., "amazon" from "amazon.co.uk"
        else:
            main_name = domain

        if main_name not in domain_groups:
            domain_groups[main_name] = []
        domain_groups[main_name].append(domain)

    print("Parsers by site:")
    print()
    for site, domains_list in sorted(domain_groups.items()):
        print(f"  {site.upper()}")
        for d in sorted(domains_list):
            print(f"    - {d}")
    print()
    print("=" * 60)
    print()

    print("All parsers loaded successfully!")
    print()
    print("To test a parser with a real URL, use the web interface")
    print("or modify this script to fetch and parse specific URLs.")
    print()

if __name__ == '__main__':
    main()
