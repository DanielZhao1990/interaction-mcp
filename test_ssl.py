#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSL module import and functionality test
This script can be run before or after packaging to ensure SSL-related functions work properly
"""

import sys
import os

def test_ssl_import():
    """Test if SSL module can be imported correctly"""
    print("Python version:", sys.version)
    print("Python path:", sys.executable)
    
    try:
        import ssl
        print("Successfully imported SSL module")
        print("SSL version:", ssl.OPENSSL_VERSION)
        return True
    except ImportError as e:
        print("Failed to import SSL module:", str(e))
        return False

def test_https_request():
    """Test if HTTPS requests work properly"""
    try:
        import urllib.request
        # Try to access an HTTPS website
        response = urllib.request.urlopen('https://www.python.org')
        print("HTTPS request successful")
        print("Response status:", response.status)
        return True
    except Exception as e:
        print("HTTPS request failed:", str(e))
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Starting SSL test")
    print("=" * 50)
    
    ssl_import_ok = test_ssl_import()
    https_request_ok = test_https_request()
    
    print("=" * 50)
    print("Test results:")
    print("SSL module import:", "Success" if ssl_import_ok else "Failed")
    print("HTTPS request:", "Success" if https_request_ok else "Failed")
    print("=" * 50)
    
    # If any test fails, exit with code 1
    if not (ssl_import_ok and https_request_ok):
        sys.exit(1)
    
    sys.exit(0)
