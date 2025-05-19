#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Test Script
Used for testing different UI implementations
"""

import asyncio
import argparse
import logging
from ui.ui import set_ui_type, select_option, request_additional_info
from lang_manager import set_language

# Import LangType enum from main.py
try:
    from main import LangType
except ImportError:
    # If import fails, define the same enum class
    import enum
    class LangType(str, enum.Enum):
        ZH_CN = "zh_CN"
        EN_US = "en_US"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('UI_Test')

async def test_select_option(ui_type, lang=LangType.EN_US):
    """Test option selection functionality"""
    logger.info(f"Using {ui_type} interface to test option selection")
    
    # Set UI type
    set_ui_type(ui_type)
    
    # Set interface language
    set_language(lang)
    logger.info(f"Using interface language: {lang}")
    
    # Prepare test options
    if lang == LangType.EN_US:
        options = [
            "Option 1: Using string option",
            {"title": "Option 2", "description": "Using dictionary option with description"},
            {"name": "Option 3", "value": 3},
        ]
    else:
        options = [
            "选项1：使用字符串选项",
            {"title": "选项2", "description": "使用字典选项，包含描述"},
            {"name": "选项3", "value": 3},
        ]
    
    # Call option selection function
    logger.info("Starting select_option function call")
    prompt_text = "Test option list" if lang == LangType.EN_US else "测试选项列表"
    
    try:
        result = await select_option(options, prompt=prompt_text)
        logger.info(f"Selection result: {result}")
    except Exception as e:
        logger.error(f"Option selection test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def test_request_info(ui_type, lang=LangType.EN_US):
    """Test information supplement functionality"""
    logger.info(f"Using {ui_type} interface to test information supplement")
    
    # Set UI type
    set_ui_type(ui_type)
    
    # Set interface language
    set_language(lang)
    logger.info(f"Using interface language: {lang}")
    
    # Call information supplement function
    logger.info("Starting request_additional_info function call")
    
    if lang == LangType.EN_US:
        prompt_text = "Please provide more information"
        current_info_text = "This is the current information, needs supplement"
    else:
        prompt_text = "请提供更多信息"
        current_info_text = "这是当前信息，需要补充"
    
    try:
        result = await request_additional_info(
            prompt=prompt_text,
            current_info=current_info_text
        )
        logger.info(f"Additional information result: {result}")
    except Exception as e:
        logger.error(f"Information supplement test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UI Test Script")
    parser.add_argument("--ui-type", choices=["cli", "pyqt", "web"], default="cli", help="UI type")
    parser.add_argument("--test", choices=["select", "info", "all"], default="all", help="Test type")
    parser.add_argument("--lang", choices=[lang.value for lang in LangType], default=LangType.EN_US.value, help="Interface language")
    args = parser.parse_args()
    
    logger.info(f"Starting test for {args.ui_type} interface")
    
    # Execute different tests based on test type
    if args.test == "select" or args.test == "all":
        await test_select_option(args.ui_type, args.lang)
    
    # Add a short delay between tests to ensure proper window cleanup
    if args.test == "all":
        logger.info("Waiting for 1 second...")
        await asyncio.sleep(1)
    
    if args.test == "info" or args.test == "all":
        await test_request_info(args.ui_type, args.lang)
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
