#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySimpleGUI Interface Implementation
"""

import asyncio
import sys
import logging
from typing import List, Dict, Any, Optional, Union
from fastmcp import Context

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger('PySimpleGUIUI')

try:
    import PySimpleGUI as sg
except ImportError:
    # If PySimpleGUI is not installed, provide a placeholder class
    class PySimpleGUIUIMissingDeps:
        """PySimpleGUI Interface Implementation Class (PySimpleGUI not installed)"""
        
        def __init__(self):
            """Initialize PySimpleGUI interface"""
            print("Warning: PySimpleGUI not installed, PySimpleGUI interface will not be available")
            self._psg_available = False
        
        async def select_option(self, options, prompt="Please select one of the following options", ctx=None):
            """Placeholder method"""
            print("Error: Cannot use PySimpleGUI interface, PySimpleGUI not installed")
            return {
                "selected_index": -1,
                "selected_option": None,
                "custom_input": "PySimpleGUI not installed, interface unavailable",
                "is_custom": True
            }
        
        async def request_additional_info(self, prompt, ctx=None):
            """Placeholder method"""
            print("Error: Cannot use PySimpleGUI interface, PySimpleGUI not installed")
            return "PySimpleGUI not installed, interface unavailable"
            
    # Assign placeholder class to PySimpleGUIUI
    PySimpleGUIUI = PySimpleGUIUIMissingDeps  # type: ignore
else:
    # If PySimpleGUI is installed, provide full implementation
    class PySimpleGUIUI:
        """PySimpleGUI Interface Implementation Class"""
        
        def __init__(self):
            """Initialize PySimpleGUI interface"""
            self._psg_available = True
            
        async def select_option(
            self,
            options: List[Union[str, Dict[str, Any]]],
            prompt: str = "Please select one of the following options",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Present options to the user and get selection using PySimpleGUI interface

            Args:
                options: List of options
                prompt: Prompt message
                ctx: FastMCP context

            Returns:
                Selection result dictionary
            """
            if not self._psg_available:
                print("Error: Cannot use PySimpleGUI interface, PySimpleGUI not installed")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "PySimpleGUI not installed, interface unavailable",
                    "is_custom": True
                }
            
            logger.debug(f"select_option called: options count={len(options)}")
            
            # Create event object for synchronization
            event = asyncio.Event()
            result_container = [None]  # Use list to store result for modification in callback
            
            # Define callback function
            def run_psg_window():
                try:
                    # Create a much simpler layout with buttons only
                    layout = [[sg.Text(prompt)]]
                    
                    # Add options as buttons
                    for i, opt in enumerate(options):
                        if isinstance(opt, dict):
                            title = opt.get('title', opt.get('name', ''))
                            desc = opt.get('description', '')
                            display_text = title
                            if desc:
                                display_text += f" - {desc}"
                        else:
                            display_text = str(opt)
                        
                        layout.append([sg.Button(display_text, key=f'OPT_{i}')])
                    
                    # Add custom input option
                    layout.append([sg.Text('-' * 40)])
                    layout.append([sg.Text('Custom input:')])
                    layout.append([sg.Input(key='CUSTOM_INPUT')])
                    layout.append([sg.Button('Submit Custom', key='SUBMIT_CUSTOM')])
                    layout.append([sg.Button('Cancel')])
                    
                    # Create window
                    window = sg.Window('Select Option', layout)
                    
                    # Event loop
                    while True:
                        event, values = window.read()
                        
                        if event == sg.WIN_CLOSED or event == 'Cancel':
                            # User cancelled
                            result = {
                                "selected_index": -1,
                                "selected_option": None,
                                "custom_input": "User cancelled selection",
                                "is_custom": True
                            }
                            break
                        
                        # Check if user selected a predefined option
                        if event.startswith('OPT_'):
                            # Get the option index from the event key
                            idx = int(event.split('_')[1])
                            result = {
                                "selected_index": idx,
                                "selected_option": options[idx],
                                "custom_input": "",
                                "is_custom": False
                            }
                            break
                        
                        # Check if user submitted custom input
                        if event == 'SUBMIT_CUSTOM':
                            custom_text = values['CUSTOM_INPUT'].strip()
                            if custom_text:
                                result = {
                                    "selected_index": -1,
                                    "selected_option": None,
                                    "custom_input": custom_text,
                                    "is_custom": True
                                }
                                break
                            else:
                                sg.popup_error('Please enter a custom input')
                    
                    window.close()
                    result_container[0] = result
                    event.set()
                    
                except Exception as e:
                    import traceback
                    logger.error(f"PySimpleGUI dialog error: {e}")
                    logger.error(traceback.format_exc())
                    result_container[0] = {
                        "selected_index": -1,
                        "selected_option": None,
                        "custom_input": f"Error: {str(e)}",
                        "is_custom": True
                    }
                    event.set()
            
            # Execute PySimpleGUI in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Displaying options using PySimpleGUI interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_psg_window)
                
                # Wait for event
                await event.wait()
                
                # Get result
                result = result_container[0]
                
                # Notify context
                if ctx:
                    if result["is_custom"]:
                        await ctx.info(f"User provided custom answer: {result['custom_input']}")
                    else:
                        await ctx.info(f"User selected option {result['selected_index'] + 1}")
                
                return result
                
            except Exception as e:
                logger.error(f"PySimpleGUI UI error: {e}")
                if ctx:
                    await ctx.error(f"PySimpleGUI UI error: {e}")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": f"PySimpleGUI interface error: {str(e)}",
                    "is_custom": True
                }
        
        async def request_additional_info(
            self,
            prompt: str,
            ctx: Context = None
        ) -> str:
            """
            Request supplementary information from the user using PySimpleGUI interface

            Args:
                prompt: Prompt message
                current_info: Current information
                ctx: FastMCP context

            Returns:
                User input information
            """
            if not self._psg_available:
                print("Error: Cannot use PySimpleGUI interface, PySimpleGUI not installed")
                return "PySimpleGUI not installed, interface unavailable"
            
            logger.debug(f"request_additional_info called: prompt={prompt}, current_info={current_info}")
            
            # Create event object for synchronization
            event = asyncio.Event()
            result = [""]  # Use list to store result for modification in callback
            
            # Define function for PySimpleGUI window
            def run_psg_window():
                try:
                    # Create a simple layout
                    layout = [[sg.Text(prompt)]]
                    
                    # Add current info if provided
                    if current_info:
                        layout.append([sg.Text("Current Information:")])
                        layout.append([sg.Text(current_info)])
                    
                    # Add input area
                    layout.append([sg.Text("Enter your information:")])
                    layout.append([sg.Input(key="INFO_INPUT", size=(60, 1))])
                    layout.append([sg.Button("Submit"), sg.Button("Cancel")])
                    
                    # Create window
                    window = sg.Window("Information Input", layout)
                    
                    # Event loop
                    while True:
                        event, values = window.read()
                        
                        if event == sg.WIN_CLOSED or event == "Cancel":
                            # User cancelled
                            result[0] = ""
                            break
                        
                        if event == "Submit":
                            result[0] = values["INFO_INPUT"].strip()
                            break
                    
                    window.close()
                    event.set()
                    
                except Exception as e:
                    import traceback
                    logger.error(f"PySimpleGUI dialog error: {e}")
                    logger.error(traceback.format_exc())
                    result[0] = f"Error: {str(e)}"
                    event.set()
            
            # Execute PySimpleGUI in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Requesting user input using PySimpleGUI interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_psg_window)
                
                # Wait for event
                await event.wait()
                
                # Notify context
                if ctx:
                    await ctx.info("User provided input information")
                
                return result[0]
                
            except Exception as e:
                logger.error(f"PySimpleGUI UI error: {e}")
                if ctx:
                    await ctx.error(f"PySimpleGUI UI error: {e}")
                return f"PySimpleGUI interface error: {str(e)}"
        
        def cleanup(self):
            """Clean up resources"""
            # PySimpleGUI will automatically clean up resources
            pass 