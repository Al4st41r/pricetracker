# Root conftest.py - sets environment variables before any test module is imported.
import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('JS_APP_ROOT', '')
