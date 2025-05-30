#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Implementation Module
Provides various interface implementation options
Including Command Line Interface, PyQt Interface and Web Interface
"""

from typing import List, Dict, Any, Union
from fastmcp import Context
from abc import ABC, abstractmethod
import importlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UI')

class BaseUI(ABC):
    """Base UI class, defines methods that must be implemented by all interfaces"""
    
    @abstractmethod
    async def select_option(
        self,
        options: List[Union[str, Dict[str, Any]]],
        prompt: str = "Please select one of the following options",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Present a set of options to the user for selection
        
        Args:
            options: List of options, can be a list of strings or dictionaries
            prompt: Prompt message displayed to the user
            
        Returns:
            Dictionary containing the selection result
        """
        pass
    
    @abstractmethod
    async def request_additional_info(
        self,
        prompt: str,
        current_info: str = "",
        ctx: Context = None
    ) -> str:
        """
        Request supplementary information from the user
        
        Args:
            prompt: Prompt for requesting information
            current_info: Current information, displayed to users as reference
            ctx: FastMCP context object
            
        Returns:
            User input information
        """
        pass


# 占位类，用于在无法加载特定UI时提供错误信息
class PlaceholderUI(BaseUI):
    """Placeholder UI implementation for when a UI type is not available"""
    
    def __init__(self, ui_type: str):
        """Initialize placeholder UI with UI type name"""
        self.ui_type = ui_type
        print(f"警告: {ui_type} UI 初始化失败，该界面类型不可用")
        
    async def select_option(self, options, prompt="Please select one of the following options", ctx=None):
        """Placeholder method"""
        print(f"错误: {self.ui_type} UI 不可用")
        return {
            "selected_index": -1, 
            "selected_option": None, 
            "custom_input": f"{self.ui_type} UI 不可用", 
            "is_custom": True
        }
        
    async def request_additional_info(self, prompt, current_info="", ctx=None):
        """Placeholder method"""
        print(f"错误: {self.ui_type} UI 不可用")
        return f"{self.ui_type} UI 不可用"


# UI实现的延迟加载映射表
UI_IMPLEMENTATIONS = {
    "cli": ("ui.ui_cli", "CommandLineUI"),
    "tkinter": ("ui.ui_tkinter", "TkinterUI"),
    "pyqt": ("ui.ui_pyqt", "PyQtUI"),
    "psg": ("ui.ui_psg", "PySimpleGUIUI"),
    "web": ("ui.ui_web", "WebUI"),
    "dpg": ("ui.ui_dpg", "DearPyGuiUI")
}


# UI factory class
class UIFactory:
    """UI factory class, used to create different types of UI instances"""
    
    @staticmethod
    def create_ui(ui_type: str) -> BaseUI:
        """
        Create a UI instance of the specified type
        
        Args:
            ui_type: UI type, possible values: cli, tkinter, pyqt, psg, web
            
        Returns:
            UI instance
        """
        if ui_type not in UI_IMPLEMENTATIONS:
            raise ValueError(f"不支持的UI类型: {ui_type}, 可用选项: {', '.join(UI_IMPLEMENTATIONS.keys())}")
        
        module_path, class_name = UI_IMPLEMENTATIONS[ui_type]
        
        try:
            # 只有在真正需要时才导入对应的模块
            logger.info(f"正在导入 {ui_type} UI 模块: {module_path}")
            module = importlib.import_module(module_path)
            ui_class = getattr(module, class_name)
            return ui_class()
        except (ImportError, AttributeError) as e:
            # 导入失败时创建占位类
            logger.warning(f"导入 {ui_type} UI 模块失败: {e}")
            return PlaceholderUI(ui_type)


# Global UI instance
_ui_instance = None

def get_ui_instance(ui_type: str = "cli") -> BaseUI:
    """
    Get UI instance (singleton pattern)
    
    Args:
        ui_type: UI type
        
    Returns:
        UI instance
    """
    global _ui_instance
    if _ui_instance is None:
        _ui_instance = UIFactory.create_ui(ui_type)
    return _ui_instance

def set_ui_type(ui_type: str):
    """
    Set UI type
    
    Args:
        ui_type: UI type
    """
    global _ui_instance
    _ui_instance = UIFactory.create_ui(ui_type)

# Tool function wrappers, exposed to FastMCP
async def select_option(
    options: List[Union[str, Dict[str, Any]]],
    prompt: str = "Please select one of the following options",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Present a set of options to the user for selection using the currently set UI
    
    Args:
        options: List of options, can be a list of strings or dictionaries
        prompt: Prompt message displayed to the user
        ctx: FastMCP context object
        
    Returns:
        Dictionary containing the selection result
    """
    ui = get_ui_instance()
    return await ui.select_option(options, prompt, ctx)

async def request_additional_info(
    prompt: str,
    current_info: str = "",
    ctx: Context = None
) -> str:
    """
    Request user supplementary information
    Args:
        prompt: Prompt for requesting information
        current_info: Current information, displayed to users as reference
    Returns:
        The supplementary information input by the user
    """
    ui = get_ui_instance()
    return await ui.request_additional_info(prompt, current_info, ctx)
