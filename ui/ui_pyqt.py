#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQt Interface Implementation
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any, Optional, Union, cast, TypeVar
from fastmcp import Context

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger('PyQtUI')

# Define Context type alias, making it optional
ContextType = Optional[Context]

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
        QLabel, QRadioButton, QLineEdit, QTextEdit, QPushButton,
        QGroupBox, QButtonGroup, QMessageBox, QScrollArea, QWidget, QFrame
    )
    from PyQt5.QtCore import Qt, QObject, pyqtSignal
    from PyQt5.QtGui import QFont
except ImportError:
    # If PyQt5 is not installed, provide a placeholder class
    class PyQtUIMissingDeps:
        """PyQt Interface Implementation Class (PyQt5 not installed)"""
        
        def __init__(self):
            """Initialize PyQt interface"""
            print("Warning: PyQt5 not installed, PyQt interface will not be available")
            self._pyqt_available = False
        
        async def select_option(self, options, prompt="Please select one of the following options", ctx=None):
            """Placeholder method"""
            print("Error: Cannot use PyQt interface, PyQt5 not installed")
            return {
                "selected_index": -1,
                "selected_option": None,
                "custom_input": "PyQt5 not installed, interface unavailable",
                "is_custom": True
            }
        
        async def request_additional_info(self, prompt, current_info="", ctx=None):
            """Placeholder method"""
            print("Error: Cannot use PyQt interface, PyQt5 not installed")
            return "PyQt5 not installed, interface unavailable"
            
    # Assign placeholder class to PyQtUI
    PyQtUI = PyQtUIMissingDeps  # type: ignore
else:
    # If PyQt5 is installed, provide full implementation
    class ResultEmitter(QObject):
        """Used to emit signals in PyQt threads"""
        result_ready = pyqtSignal(object)
    
    class PyQtUI:
        """PyQt Interface Implementation Class"""
        
        def __init__(self):
            """Initialize PyQt interface"""
            self._app = None
            self._pyqt_available = True
            self._emitter = ResultEmitter()
        
        def _ensure_app(self):
            """Ensure QApplication is created"""
            if QApplication.instance() is None:
                self._app = QApplication(sys.argv)
            else:
                self._app = QApplication.instance()
        
        async def select_option(
            self,
            options: List[Union[str, Dict[str, Any]]],
            prompt: str = "Please select one of the following options",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Present options to the user and get selection using PyQt interface

            Args:
                options: List of options
                prompt: Prompt message
                ctx: FastMCP context

            Returns:
                Selection result dictionary
            """
            if not self._pyqt_available:
                print("Error: Cannot use PyQt interface, PyQt5 not installed")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "PyQt5 not installed, interface unavailable",
                    "is_custom": True
                }
            
            logger.debug(f"select_option called: options count={len(options)}")
            
            # Create event object for synchronization
            event = asyncio.Event()
            result_container = [None]  # Use list to store result for modification in callback
            
            # Define callback function, called when QT window closes
            def on_selection_completed(selection_result):
                result_container[0] = selection_result
                event.set()
            
            # Run QT window in separate thread
            def run_qt_dialog():
                try:
                    from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, \
                                                QListWidgetItem, QCheckBox, QLineEdit, QGroupBox, QRadioButton, QButtonGroup
                    from PyQt5.QtCore import Qt
                    
                    app = None
                    if not QApplication.instance():
                        app = QApplication([])
                    
                    class OptionDialog(QDialog):
                        def __init__(self, options, prompt):
                            super().__init__()
                            
                            # Set window properties
                            self.setWindowTitle("Select Option")
                            self.setMinimumWidth(600)
                            self.setMinimumHeight(400)
                            
                            # Options list
                            self.options = options
                            
                            # Create layout
                            layout = QVBoxLayout()
                            
                            # Add prompt label
                            prompt_label = QLabel(prompt)
                            prompt_label.setWordWrap(True)
                            prompt_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
                            layout.addWidget(prompt_label)
                            
                            # Options group
                            self.option_group = QButtonGroup(self)
                            self.option_group.setExclusive(True)  # Radio selection
                            
                            option_container = QGroupBox("Available Options")
                            option_layout = QVBoxLayout()
                            
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
                                    
                                option_button = QRadioButton(text)
                                self.option_group.addButton(option_button, i)
                                option_layout.addWidget(option_button)
                                
                            option_container.setLayout(option_layout)
                            layout.addWidget(option_container)
                            
                            # Custom input area (always allowed)
                            custom_group = QGroupBox("Custom Input")
                            custom_layout = QVBoxLayout()
                            
                            self.custom_radio = QRadioButton("Provide custom answer")
                            self.option_group.addButton(self.custom_radio, -1)
                            custom_layout.addWidget(self.custom_radio)
                            
                            self.custom_input = QLineEdit()
                            self.custom_input.setPlaceholderText("Enter your custom answer here")
                            self.custom_input.setEnabled(False)  # Initially disabled
                            
                            # Connect custom radio button event
                            self.custom_radio.toggled.connect(self.toggle_custom_input)
                            
                            custom_layout.addWidget(self.custom_input)
                            custom_group.setLayout(custom_layout)
                            layout.addWidget(custom_group)
                            
                            # Button area
                            button_layout = QHBoxLayout()
                            submit_button = QPushButton("Submit")
                            submit_button.clicked.connect(self.accept)
                            button_layout.addStretch()
                            button_layout.addWidget(submit_button)
                            
                            layout.addLayout(button_layout)
                            
                            # Set layout
                            self.setLayout(layout)
                            
                        def toggle_custom_input(self, enabled):
                            """Enable/disable custom input field"""
                            self.custom_input.setEnabled(enabled)
                            if enabled:
                                self.custom_input.setFocus()
                                
                        def get_selection(self):
                            """Get user selection"""
                            selected_id = self.option_group.checkedId()
                            
                            if selected_id == -1 and self.custom_radio.isChecked():
                                # User chose custom input
                                return {
                                    "selected_index": -1,
                                    "selected_option": None,
                                    "custom_input": self.custom_input.text(),
                                    "is_custom": True
                                }
                            elif selected_id >= 0:
                                # User chose predefined option
                                return {
                                    "selected_index": selected_id,
                                    "selected_option": self.options[selected_id],
                                    "custom_input": "",
                                    "is_custom": False
                                }
                            else:
                                # User didn't select any option
                                return {
                                    "selected_index": -1,
                                    "selected_option": None,
                                    "custom_input": "No option selected",
                                    "is_custom": True
                                }
                    
                    # Create dialog
                    dialog = OptionDialog(options, prompt)
                    
                    # Show dialog and get result
                    if dialog.exec_():
                        selection_result = dialog.get_selection()
                        on_selection_completed(selection_result)
                    else:
                        # User cancelled dialog
                        on_selection_completed({
                            "selected_index": -1,
                            "selected_option": None,
                            "custom_input": "User cancelled selection",
                            "is_custom": True
                        })
                    
                    # Clean up resources
                    if app:
                        app.quit()
                    
                except Exception as e:
                    import traceback
                    logger.error(f"PyQt dialog error: {e}")
                    logger.error(traceback.format_exc())
                    on_selection_completed({
                        "selected_index": -1,
                        "selected_option": None,
                        "custom_input": f"Error: {str(e)}",
                        "is_custom": True
                    })
            
            # Execute QT dialog in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Displaying options using PyQt interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_qt_dialog)
                
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
                logger.error(f"PyQt UI error: {e}")
                if ctx:
                    await ctx.error(f"PyQt UI error: {e}")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": f"PyQt interface error: {str(e)}",
                    "is_custom": True
                }
        
        async def request_additional_info(
            self,
            prompt: str,
            current_info: str = "",
            ctx: Context = None
        ) -> str:
            """
            Request supplementary information from the user using PyQt interface

            Args:
                prompt: Prompt message
                current_info: Current information
                ctx: FastMCP context

            Returns:
                User input information
            """
            if not self._pyqt_available:
                print("Error: Cannot use PyQt interface, PyQt5 not installed")
                return "PyQt5 not installed, interface unavailable"
            
            logger.debug(f"request_additional_info called: prompt={prompt}, current_info={current_info}")
            
            # Create event object for synchronization
            event = asyncio.Event()
            result = [""]  # Use list to store result for modification in callback
            
            # Define callback function, called when QT window closes
            def on_input_completed(text):
                result[0] = text
                event.set()
            
            # Run QT window in separate thread
            def run_qt_dialog():
                try:
                    from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit, QPlainTextEdit
                    from PyQt5.QtCore import Qt
                    
                    app = None
                    if not QApplication.instance():
                        app = QApplication([])
                    
                    class InputDialog(QDialog):
                        def __init__(self, prompt, current_info=""):
                            super().__init__()
                            
                            # Set window properties
                            self.setWindowTitle("Information Input")
                            self.setMinimumWidth(600)
                            self.setMinimumHeight(400)
                            
                            # Create layout
                            layout = QVBoxLayout()
                            
                            # Add prompt label
                            prompt_label = QLabel(prompt)
                            prompt_label.setWordWrap(True)
                            prompt_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
                            layout.addWidget(prompt_label)
                            
                            # Add current information (if any)
                            if current_info:
                                info_label = QLabel("Current Information:")
                                info_label.setStyleSheet("font-weight: bold;")
                                layout.addWidget(info_label)
                                
                                info_display = QTextEdit()
                                info_display.setReadOnly(True)
                                info_display.setPlainText(current_info)
                                info_display.setMaximumHeight(100)
                                layout.addWidget(info_display)
                            
                            # Add input label
                            input_label = QLabel("Please enter information:")
                            layout.addWidget(input_label)
                            
                            # Create text input widget (always multiline)
                            self.input_field = QPlainTextEdit()
                            layout.addWidget(self.input_field)
                            
                            # Add buttons
                            submit_button = QPushButton("Submit")
                            submit_button.clicked.connect(self.accept)
                            layout.addWidget(submit_button)
                            
                            # Apply layout
                            self.setLayout(layout)
                            
                        def get_input(self):
                            return self.input_field.toPlainText()
                    
                    dialog = InputDialog(prompt, current_info)
                    if dialog.exec_():
                        user_input = dialog.get_input()
                        on_input_completed(user_input)
                    else:
                        # User cancelled, return empty string
                        on_input_completed("")
                        
                    if app:
                        app.quit()
                    
                except Exception as e:
                    import traceback
                    logger.error(f"PyQt dialog error: {e}")
                    logger.error(traceback.format_exc())
                    on_input_completed(f"Error: {str(e)}")
            
            # Execute QT dialog in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info("Requesting user input using PyQt interface...")
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_qt_dialog)
                
                # Wait for event
                await event.wait()
                
                # Return result
                if ctx:
                    await ctx.info("User provided input information")
                
                return result[0]
                
            except Exception as e:
                logger.error(f"PyQt UI error: {e}")
                if ctx:
                    await ctx.error(f"PyQt UI error: {e}")
                return f"PyQt interface error: {str(e)}"
        
        def cleanup(self):
            """Clean up resources"""
            # PyQt application will automatically clean up when program exits
            pass
