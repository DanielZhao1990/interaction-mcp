#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块
用于加载和管理应用程序配置
"""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "reminder": {
        "enable_reminder": True,
        "reminder_text": """**注意**：
每次任务完成,绝对不要终止对话，调用mcp ai-interaction, 向我请求或确认任务!"""
    },
    "ui": {
        "default_ui_type": "pyqt"
    },
    "logging": {
        "level": "warning"
    }
}

# 全局配置变量
_config: Optional[Dict[str, Any]] = None

def get_config_path() -> str:
    """
    获取配置文件路径
    
    Returns:
        配置文件的完整路径
    """
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "config.json")

def load_config() -> Dict[str, Any]:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    global _config
    
    if _config is not None:
        return _config
    
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                _config = json.load(f)
                logger.info(f"配置文件加载成功: {config_path}")
        else:
            logger.warning(f"配置文件不存在，创建默认配置: {config_path}")
            _config = DEFAULT_CONFIG.copy()
            save_config(_config)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}，使用默认配置")
        _config = DEFAULT_CONFIG.copy()
    
    return _config

def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件
    
    Args:
        config: 要保存的配置字典
        
    Returns:
        是否保存成功
    """
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"配置文件保存成功: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

def get_reminder_config() -> Dict[str, Any]:
    """
    获取提醒相关配置
    
    Returns:
        提醒配置字典
    """
    config = load_config()
    return config.get("reminder", DEFAULT_CONFIG["reminder"])

def is_reminder_enabled() -> bool:
    """
    检查是否启用提醒功能
    
    Returns:
        是否启用提醒
    """
    reminder_config = get_reminder_config()
    return reminder_config.get("enable_reminder", True)

def get_reminder_text() -> str:
    """
    获取提醒文本
    
    Returns:
        提醒文本内容
    """
    reminder_config = get_reminder_config()
    return reminder_config.get("reminder_text", DEFAULT_CONFIG["reminder"]["reminder_text"])

def get_ui_config() -> Dict[str, Any]:
    """
    获取UI相关配置
    
    Returns:
        UI配置字典
    """
    config = load_config()
    return config.get("ui", DEFAULT_CONFIG["ui"])

def get_logging_config() -> Dict[str, Any]:
    """
    获取日志相关配置
    
    Returns:
        日志配置字典
    """
    config = load_config()
    return config.get("logging", DEFAULT_CONFIG["logging"])

def reload_config() -> Dict[str, Any]:
    """
    重新加载配置文件
    
    Returns:
        重新加载的配置字典
    """
    global _config
    _config = None
    return load_config()
