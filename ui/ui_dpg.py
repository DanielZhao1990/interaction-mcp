#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DearPyGui Interface Implementation
"""

import asyncio
import sys
import logging
import traceback
from typing import List, Dict, Any, Optional, Union
from fastmcp import Context

# Import DearPyGui modules (if available)
try:
    import dearpygui.dearpygui as dpg
    import sys
    # DearPyGui 2.0版本不再有__version__属性，改用其他方式检测
    print(f"DearPyGui successfully imported")
    print(f"Python version: {sys.version}")
    DPG_AVAILABLE = True
except ImportError:
    print("DearPyGui import error: package not installed")
    DPG_AVAILABLE = False
except Exception as e:
    print(f"DearPyGui initialization error: {e}")
    DPG_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger('DearPyGuiUI')

# Define Context type alias, making it optional
ContextType = Optional[Context]

# If DearPyGui is not installed, provide a placeholder class
if not DPG_AVAILABLE:
    class DearPyGuiUIMissingDeps:
        """DearPyGui Interface Implementation Class (DearPyGui not installed)"""
        
        def __init__(self):
            """Initialize DearPyGui interface"""
            print("Warning: DearPyGui not installed, DearPyGui interface will not be available")
            self._dpg_available = False
        
        async def select_option(self, options, prompt="Please select one of the following options", ctx=None):
            """Placeholder method"""
            print("Error: Cannot use DearPyGui interface, DearPyGui not installed")
            return {
                "selected_index": -1,
                "selected_option": None,
                "custom_input": "DearPyGui not installed, interface unavailable",
                "is_custom": True
            }
        
        async def request_additional_info(self, prompt, ctx=None):
            """Placeholder method"""
            print("Error: Cannot use DearPyGui interface, DearPyGui not installed")
            return "DearPyGui not installed, interface unavailable"
            
    # Assign placeholder class to DearPyGuiUI
    DearPyGuiUI = DearPyGuiUIMissingDeps  # type: ignore
else:
    # If DearPyGui is installed, provide full implementation
    class DearPyGuiUI:
        """DearPyGui Interface Implementation Class"""
        
        def __init__(self):
            """Initialize DearPyGui interface"""
            self._dpg_available = True
            self._context_created = False
            
        def _ensure_context(self):
            """Ensure DPG context is created"""
            if not self._context_created:
                if dpg.is_dearpygui_running():
                    # DearPyGui is already running
                    pass
                else:
                    # Create DearPyGui context
                    dpg.create_context()
                    self._context_created = True
        
        async def select_option(
            self,
            options: List[Union[str, Dict[str, Any]]],
            prompt: str = "Please select one of the following options",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Present options to the user and get selection using DearPyGui interface

            Args:
                options: List of options
                prompt: Prompt message
                ctx: FastMCP context

            Returns:
                Selection result dictionary
            """
            if not self._dpg_available:
                print("Error: Cannot use DearPyGui interface, DearPyGui not installed")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "DearPyGui not installed, interface unavailable",
                    "is_custom": True
                }
            
            logger.debug(f"select_option called: options count={len(options)}")
            print("DearPyGui select_option called with options:", options)
            
            # Create event object for synchronization
            event = asyncio.Event()
            result_container = [None]  # Use list to store result for modification in callback
            
            # Define callback function, called when window closes with result
            def on_selection_completed(selection_result):
                print("Selection completed with result:", selection_result)
                result_container[0] = selection_result
                event.set()
            
            # Run DPG window in separate thread
            def run_dpg_window():
                try:
                    print("Starting DPG window thread")
                    # Ensure context is created
                    self._ensure_context()
                    print("DPG context created")
                    
                    # Store selection result
                    selection_result = {
                        "selected_index": -1,
                        "selected_option": None,
                        "custom_input": "",
                        "is_custom": False
                    }
                    
                    # Create viewport if not exists
                    try:
                        if not dpg.does_item_exist("viewport"):
                            print("Creating DPG viewport")
                            dpg.create_viewport(title="Select Option", width=600, height=400)
                            print("Setting up DearPyGui")
                            dpg.setup_dearpygui()
                            print("DearPyGui setup completed")
                    except Exception as viewport_error:
                        print(f"Error creating viewport: {viewport_error}")
                        raise
                    
                    # Create main window with selection dialog
                    print("Creating selection window")
                    try:
                        with dpg.window(label="Select Option", width=580, height=380, pos=(10, 10), 
                                      no_collapse=True, no_close=True, no_move=True, tag="selection_window"):
                            # Add prompt text
                            dpg.add_text(prompt, wrap=550)
                            dpg.add_spacer(height=10)
                            
                            # Create radio button group for options
                            selected_option = {"value": -1}  # Use dict to store reference to selected option
                            
                            # Helper function to handle option selection
                            def select_radio(sender, app_data, user_data):
                                print(f"Radio option selected: {user_data}")
                                selected_option["value"] = user_data
                            
                            # Add option group
                            with dpg.group(label="Options"):
                                # Add predefined options
                                for i, opt in enumerate(options):
                                    if isinstance(opt, dict):
                                        title = opt.get('title', f"Option {i+1}")
                                        desc = opt.get('description', '')
                                        text = title
                                        if desc:
                                            text += f" - {desc}"
                                    else:
                                        text = str(opt)
                                    
                                    print(f"Adding option {i}: {text}")
                                    dpg.add_radio_button(items=[text], callback=select_radio, user_data=i)
                            
                            dpg.add_separator()
                            dpg.add_spacer(height=5)
                            
                            # Add custom input option
                            dpg.add_checkbox(label="Provide custom answer", callback=lambda s, a: 
                                            dpg.configure_item("custom_input", enabled=a))
                            
                            # Custom input textbox
                            dpg.add_input_text(label="Custom input", multiline=True, width=550, height=100, 
                                               enabled=False, tag="custom_input")
                            
                            dpg.add_spacer(height=10)
                            
                            # Add submit button
                            def submit_callback():
                                print("Submit button clicked")
                                # Check if custom input is selected
                                if dpg.get_value("custom_input") and dpg.is_item_enabled("custom_input"):
                                    # User chose custom input
                                    selection_result["selected_index"] = -1
                                    selection_result["selected_option"] = None
                                    selection_result["custom_input"] = dpg.get_value("custom_input")
                                    selection_result["is_custom"] = True
                                    print("Custom input selected:", selection_result["custom_input"])
                                elif selected_option["value"] >= 0:
                                    # User chose predefined option
                                    selection_result["selected_index"] = selected_option["value"]
                                    selection_result["selected_option"] = options[selected_option["value"]]
                                    selection_result["custom_input"] = ""
                                    selection_result["is_custom"] = False
                                    print("Predefined option selected:", selection_result["selected_index"])
                                else:
                                    # User didn't select any option
                                    selection_result["selected_index"] = -1
                                    selection_result["selected_option"] = None
                                    selection_result["custom_input"] = "No option selected"
                                    selection_result["is_custom"] = True
                                    print("No option selected")
                                
                                # Close window and return result
                                print("Closing window and returning result")
                                dpg.delete_item("selection_window")
                                dpg.stop_dearpygui()
                                on_selection_completed(selection_result)
                            
                            with dpg.group(horizontal=True):
                                dpg.add_spacer(width=450)
                                dpg.add_button(label="Submit", callback=submit_callback)
                    except Exception as window_error:
                        print(f"Error creating window: {window_error}")
                        raise
                    
                    # Show viewport and start DearPyGui
                    print("Showing viewport and starting DearPyGui")
                    try:
                        dpg.show_viewport()
                        print("Viewport shown, starting main loop")
                        dpg.start_dearpygui()
                        print("DearPyGui stopped")
                    except Exception as run_error:
                        print(f"Error running DearPyGui: {run_error}")
                        raise
                    
                    # Cleanup resources after window is closed
                    try:
                        dpg.destroy_context()
                        self._context_created = False
                        print("DPG context destroyed")
                    except Exception as cleanup_error:
                        print(f"Error cleaning up DPG context: {cleanup_error}")
                    
                except Exception as e:
                    print(f"DearPyGui window error: {e}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"Error traceback: {error_trace}")
                    logger.error(f"DearPyGui window error: {e}")
                    logger.error(error_trace)
                    on_selection_completed({
                        "selected_index": -1,
                        "selected_option": None,
                        "custom_input": f"Error: {str(e)}",
                        "is_custom": True
                    })
                    
                print("DPG window thread completed")
            
            # Execute DPG window in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Displaying options using DearPyGui interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_dpg_window)
                
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
                logger.error(f"DearPyGui UI error: {e}")
                if ctx:
                    await ctx.error(f"DearPyGui UI error: {e}")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": f"DearPyGui interface error: {str(e)}",
                    "is_custom": True
                }
        
        async def request_additional_info(
            self,
            prompt: str,
            ctx: Context = None
        ) -> str:
            """
            Request supplementary information from the user using DearPyGui interface

            Args:
                prompt: Prompt message
                current_info: Current information
                ctx: FastMCP context

            Returns:
                User input information
            """
            if not self._dpg_available:
                print("Error: Cannot use DearPyGui interface, DearPyGui not installed")
                return "DearPyGui not installed, interface unavailable"
            
            logger.debug(f"request_additional_info called: prompt={prompt}, current_info={current_info}")
            
            # Create event object for synchronization
            event = asyncio.Event()
            result = [""]  # Use list to store result for modification in callback
            
            # Define callback function, called when window closes with result
            def on_input_completed(text):
                result[0] = text
                event.set()
            
            # Run DPG window in separate thread
            def run_dpg_window():
                try:
                    # Ensure context is created
                    self._ensure_context()
                    
                    # Create viewport if not exists
                    if not dpg.does_item_exist("viewport"):
                        dpg.create_viewport(title="Information Input", width=600, height=400)
                        dpg.setup_dearpygui()
                    
                    # Create main window with input dialog
                    with dpg.window(label="Information Input", width=580, height=380, pos=(10, 10), 
                                    no_collapse=True, no_close=True, no_move=True, tag="input_window"):
                        # Add prompt text
                        dpg.add_text(prompt, wrap=550)
                        dpg.add_spacer(height=10)
                        
                        # Add current information (if any)
                        if current_info:
                            dpg.add_text("Current Information:", color=[220, 220, 0])
                            with dpg.child_window(width=550, height=100, border=True):
                                dpg.add_text(current_info, wrap=540)
                        
                        dpg.add_spacer(height=10)
                        dpg.add_text("Please enter information:")
                        
                        # Input textbox
                        dpg.add_input_text(multiline=True, width=550, height=150, tag="input_text")
                        
                        dpg.add_spacer(height=10)
                        
                        # Add submit button
                        def submit_callback():
                            # Get input text
                            input_text = dpg.get_value("input_text")
                            
                            # Close window and return result
                            dpg.delete_item("input_window")
                            dpg.stop_dearpygui()
                            on_input_completed(input_text)
                        
                        with dpg.group(horizontal=True):
                            dpg.add_spacer(width=450)
                            dpg.add_button(label="Submit", callback=submit_callback)
                    
                    # Show viewport and start DearPyGui
                    dpg.show_viewport()
                    dpg.start_dearpygui()
                    
                    # Cleanup resources after window is closed
                    dpg.destroy_context()
                    self._context_created = False
                    
                except Exception as e:
                    logger.error(f"DearPyGui window error: {e}")
                    logger.error(traceback.format_exc())
                    on_input_completed(f"Error: {str(e)}")
            
            # Execute DPG window in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Displaying input dialog using DearPyGui interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_dpg_window)
                
                # Wait for event
                await event.wait()
                
                # Get result
                input_result = result[0]
                
                # Notify context
                if ctx:
                    await ctx.info("User provided input information")
                
                return input_result
                
            except Exception as e:
                logger.error(f"DearPyGui UI error: {e}")
                if ctx:
                    await ctx.error(f"DearPyGui UI error: {e}")
                return f"DearPyGui interface error: {str(e)}"
        
        def cleanup(self):
            """Cleanup DearPyGui resources"""
            if self._dpg_available and self._context_created:
                if dpg.is_dearpygui_running():
                    dpg.stop_dearpygui()
                dpg.destroy_context()
                self._context_created = False 