
import os
import importlib

# A dictionary to hold the parser functions, keyed by domain name
parsers = {}

# Get the directory of the current package
pkg_dir = os.path.dirname(__file__)

# Iterate over all the .py files in the package directory
for filename in os.listdir(pkg_dir):
    if filename.endswith('.py') and not filename.startswith('__') and not filename.startswith('_template'):
        # Import the module
        module_name = filename[:-3] # remove the .py extension
        module = importlib.import_module(f'.{module_name}', package=__name__)

        # The domain(s) the parser supports
        if hasattr(module, 'domains'):
            for domain in module.domains:
                if hasattr(module, 'parse'):
                    # Register the domain as provided
                    parsers[domain] = module.parse
                    
                    # Also register with/without www. for convenience
                    if domain.startswith('www.'):
                        parsers[domain[4:]] = module.parse
                    else:
                        parsers[f'www.{domain}'] = module.parse
