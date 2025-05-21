#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试SSL模块导入和功能是否正常工作
这个脚本可以在打包前或打包后运行，以确保SSL相关功能正常工作
"""

import sys
import os

def test_ssl_import():
    """测试SSL模块是否可以正常导入"""
    print("Python版本:", sys.version)
    print("Python路径:", sys.executable)
    
    try:
        import ssl
        print("成功导入SSL模块")
        print("SSL版本:", ssl.OPENSSL_VERSION)
        return True
    except ImportError as e:
        print("SSL模块导入失败:", str(e))
        return False

def test_https_request():
    """测试HTTPS请求是否可以正常工作"""
    try:
        import urllib.request
        # 尝试访问一个HTTPS网站
        response = urllib.request.urlopen('https://www.python.org')
        print("HTTPS请求成功")
        print("响应状态:", response.status)
        return True
    except Exception as e:
        print("HTTPS请求失败:", str(e))
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("开始SSL测试")
    print("=" * 50)
    
    ssl_import_ok = test_ssl_import()
    https_request_ok = test_https_request()
    
    print("=" * 50)
    print("测试结果:")
    print("SSL模块导入:", "成功" if ssl_import_ok else "失败")
    print("HTTPS请求:", "成功" if https_request_ok else "失败")
    print("=" * 50)
    
    # 如果任一测试失败，则程序退出码为1
    if not (ssl_import_ok and https_request_ok):
        sys.exit(1)
    
    sys.exit(0)
