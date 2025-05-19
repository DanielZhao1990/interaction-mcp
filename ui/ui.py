#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Implementation Module
Provides various interface implementation options
Including Command Line Interface, PyQt Interface and Web Interface
"""

from typing import List, Dict, Any, Optional, Union, Callable
from fastmcp import Context
from abc import ABC, abstractmethod
import asyncio

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
            ctx: FastMCP context object
            
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

# Import concrete implementation classes
from .ui_cli import CommandLineUI

# Try to import other UI implementations, provide placeholder classes if import fails
try:
    from .ui_tkinter import TkinterUI
except ImportError:
    class TkinterUI:
        def __init__(self):
            print("Warning: Tkinter UI initialization failed")
            
        async def select_option(self, *args, **kwargs):
            print("Error: Tkinter UI not available")
            return {"selected_index": -1, "selected_option": None, "custom_input": "Tkinter UI not available", "is_custom": True}
            
        async def request_additional_info(self, *args, **kwargs):
            print("Error: Tkinter UI not available")
            return "Tkinter UI not available"

try:
    from .ui_pyqt import PyQtUI
except ImportError:
    class PyQtUI:
        def __init__(self):
            print("Warning: PyQt UI initialization failed")
            
        async def select_option(self, *args, **kwargs):
            print("Error: PyQt UI not available")
            return {"selected_index": -1, "selected_option": None, "custom_input": "PyQt UI not available", "is_custom": True}
            
        async def request_additional_info(self, *args, **kwargs):
            print("Error: PyQt UI not available")
            return "PyQt UI not available"

try:
    from .ui_web import WebUI
except (ImportError, TypeError) as e:
    print(f"Warning: Web UI import failed - {e}")
    class WebUI:
        def __init__(self):
            print("Warning: Web UI initialization failed")
            
        async def select_option(self, *args, **kwargs):
            print("Error: Web UI not available")
            return {"selected_index": -1, "selected_option": None, "custom_input": "Web UI not available", "is_custom": True}
            
        async def request_additional_info(self, *args, **kwargs):
            print("Error: Web UI not available")
            return "Web UI not available"

# UI factory class
class UIFactory:
    """UI factory class, used to create different types of UI instances"""
    
    @staticmethod
    def create_ui(ui_type: str) -> BaseUI:
        """
        Create a UI instance of the specified type
        
        Args:
            ui_type: UI type, possible values: cli, tkinter, pyqt, web
            
        Returns:
            UI instance
        """
        ui_map = {
            "cli": CommandLineUI,
            "tkinter": TkinterUI,
            "pyqt": PyQtUI,
            "web": WebUI
        }
        
        if ui_type not in ui_map:
            raise ValueError(f"Unsupported UI type: {ui_type}, possible values: {', '.join(ui_map.keys())}")
        
        return ui_map[ui_type]()

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
    Request supplementary information from the user using the currently set UI
    
    Args:
        prompt: Prompt for requesting information
        current_info: Current information, displayed to users as reference
        ctx: FastMCP context object
        
    Returns:
        The supplementary information input by the user
    """
    ui = get_ui_instance()
    return await ui.request_additional_info(prompt, current_info, ctx)
