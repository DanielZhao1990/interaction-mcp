#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQt Interface Implementation
"""

import asyncio
import sys
import logging
import traceback
from typing import List, Dict, Any, Optional, Union
from fastmcp import Context

# Import language manager
try:
    from lang_manager import get_text
except ImportError:
    # Fallback if lang_manager is not available
    def get_text(key):
        return key

# Import PyQt5 modules (if available)
try:
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
        QListWidget, QListWidgetItem, QCheckBox, QLineEdit, QTextEdit, QPlainTextEdit,
        QGroupBox, QRadioButton, QButtonGroup, QScrollArea, QWidget, QDesktopWidget
    )
    from PyQt5.QtCore import QObject, pyqtSignal, Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger('PyQtUI')

# Define Context type alias, making it optional
ContextType = Optional[Context]

# If PyQt5 is not installed, provide a placeholder class
if not PYQT_AVAILABLE:
    class PyQtUIMissingDeps:
        """PyQt Interface Implementation Class (PyQt5 not installed)"""
        
        def __init__(self):
            """Initialize PyQt interface"""
            print(f"Warning: {get_text('pyqt_not_installed')}")
            self._pyqt_available = False
        
        async def select_option(self, options, prompt="Please select one of the following options", ctx=None):
            """Placeholder method"""
            print(get_text("pyqt_not_installed"))
            return {
                "selected_index": -1,
                "selected_option": None,
                "custom_input": get_text("pyqt_interface_unavailable"),
                "is_custom": True
            }
        
        async def request_additional_info(self, prompt, current_info="", ctx=None):
            """Placeholder method"""
            print(get_text("pyqt_not_installed"))
            return get_text("pyqt_interface_unavailable")
            
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
                print(get_text("pyqt_not_installed"))
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": get_text("pyqt_interface_unavailable"),
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
                    app = None
                    if not QApplication.instance():
                        app = QApplication([])
                    
                    class OptionDialog(QDialog):
                        def __init__(self, options, prompt):
                            super().__init__()
                            
                            # Get available screen size (excludes taskbar, etc.)
                            desktop = QDesktopWidget()
                            available_rect = desktop.availableGeometry()  # Use available area instead of full screen
                            window_height = max(600, int(available_rect.height() * 0.7))  # Use 70% of available height, max 600px
                            window_width = max(800, int(available_rect.width() * 0.6))  # Max 800px or 60% of available width
                            
                            # Set window properties with fixed size
                            self.setWindowTitle(get_text("select_dialog_title"))
                            self.setFixedSize(window_width, window_height)  # Use fixed size for consistency
                            
                            # Center the window on screen
                            self.move(
                                available_rect.x() + (available_rect.width() - window_width) // 2,
                                available_rect.y() + (available_rect.height() - window_height) // 2
                            )
                            
                            # Options list
                            self.options = options
                            
                            # Create main layout
                            main_layout = QVBoxLayout()
                            
                            # Create scrollable content area
                            scroll_area = QScrollArea()
                            scroll_area.setWidgetResizable(True)
                            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                            
                            # Create content widget for scrollable area
                            content_widget = QWidget()
                            content_layout = QVBoxLayout()
                            
                            # Add prompt label
                            prompt_label = QLabel(prompt)
                            prompt_label.setWordWrap(True)
                            prompt_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin: 10px;")
                            content_layout.addWidget(prompt_label)
                            
                            # Options group
                            self.option_group = QButtonGroup(self)
                            self.option_group.setExclusive(True)  # Radio selection
                            
                            option_container = QGroupBox(get_text("available_options"))
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
                                # Note: QRadioButton doesn't have setWordWrap, but text will wrap naturally in layout
                                self.option_group.addButton(option_button, i)
                                option_layout.addWidget(option_button)
                                
                            option_container.setLayout(option_layout)
                            content_layout.addWidget(option_container)
                            
                            # Custom input area (always allowed)
                            custom_group = QGroupBox(get_text("custom_input_group"))
                            custom_layout = QVBoxLayout()
                            
                            self.custom_radio = QRadioButton(get_text("custom_answer"))
                            self.option_group.addButton(self.custom_radio, -1)
                            custom_layout.addWidget(self.custom_radio)
                            
                            # Changed from QLineEdit to QPlainTextEdit for multi-line input
                            self.custom_input = QPlainTextEdit()
                            self.custom_input.setPlaceholderText(get_text("custom_input_placeholder"))
                            self.custom_input.setEnabled(False)  # Initially disabled
                            self.custom_input.setMinimumHeight(100)  # Set minimum height for multi-line input
                            self.custom_input.setMaximumHeight(150)  # Limit height to prevent excessive growth
                            
                            # Connect custom radio button event
                            self.custom_radio.toggled.connect(self.toggle_custom_input)
                            
                            custom_layout.addWidget(self.custom_input)
                            custom_group.setLayout(custom_layout)
                            content_layout.addWidget(custom_group)
                            
                            # Set content widget layout and add to scroll area
                            content_widget.setLayout(content_layout)
                            scroll_area.setWidget(content_widget)
                            
                            # Add scroll area to main layout
                            main_layout.addWidget(scroll_area)
                            
                            # Button area - fixed at bottom
                            button_layout = QHBoxLayout()
                            submit_button = QPushButton(get_text("submit_button"))
                            submit_button.clicked.connect(self.accept)
                            submit_button.setMinimumHeight(35)  # Ensure button is easily clickable
                            button_layout.addStretch()
                            button_layout.addWidget(submit_button)
                            
                            main_layout.addLayout(button_layout)
                            
                            # Set main layout
                            self.setLayout(main_layout)
                        
                        def toggle_custom_input(self, enabled):
                            """Enable/disable custom input field"""
                            self.custom_input.setEnabled(enabled)
                            if enabled:
                                self.custom_input.setFocus()
                                
                        def get_selection(self):
                            """Get user selection"""
                            selected_id = self.option_group.checkedId()
                            
                            if selected_id == -1 and self.custom_radio.isChecked():
                                # User chose custom input - get text from QPlainTextEdit
                                return {
                                    "selected_index": -1,
                                    "selected_option": None,
                                    "custom_input": self.custom_input.toPlainText(),
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
                                    "custom_input": get_text("no_option_selected"),
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
                            "custom_input": get_text("user_cancelled_selection"),
                            "is_custom": True
                        })
                    
                    # Clean up resources
                    if app:
                        app.quit()
                    
                except Exception as e:
                    logger.error(f"{get_text('pyqt_dialog_error')}: {e}")
                    logger.error(traceback.format_exc())
                    on_selection_completed({
                        "selected_index": -1,
                        "selected_option": None,
                        "custom_input": f"{get_text('pyqt_dialog_error')}: {str(e)}",
                        "is_custom": True
                    })
            
            # Execute QT dialog in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info(get_text("wait_user_select"))
                    
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
                        await ctx.info(f"{get_text('user_provided_info')}: {result['custom_input']}")
                    else:
                        await ctx.info(f"{get_text('user_selected')} {result['selected_index'] + 1}")
                
                return result
                
            except Exception as e:
                logger.error(f"{get_text('pyqt_ui_error')}: {e}")
                if ctx:
                    await ctx.error(f"{get_text('pyqt_ui_error')}: {e}")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": f"{get_text('pyqt_interface_error')}: {str(e)}",
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
                print(get_text("pyqt_not_installed"))
                return get_text("pyqt_interface_unavailable")
            
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
                    app = None
                    if not QApplication.instance():
                        app = QApplication([])
                    
                    class InputDialog(QDialog):
                        def __init__(self, prompt, current_info=""):
                            super().__init__()
                            
                            # Get available screen size (excludes taskbar, etc.)
                            desktop = QDesktopWidget()
                            available_rect = desktop.availableGeometry()  # Use available area instead of full screen
                            window_height = max(600, int(available_rect.height() * 0.7))  # Use 70% of available height, max 600px
                            window_width = max(800, int(available_rect.width() * 0.6))  # Max 800px or 60% of available width
                            
                            # Set window properties with fixed size
                            self.setWindowTitle(get_text("info_request_title"))
                            self.setFixedSize(window_width, window_height)  # Use fixed size for consistency
                            
                            # Center the window on screen
                            self.move(
                                available_rect.x() + (available_rect.width() - window_width) // 2,
                                available_rect.y() + (available_rect.height() - window_height) // 2
                            )
                            
                            # Create main layout
                            main_layout = QVBoxLayout()
                            main_layout.setSpacing(10)  # Set spacing between groups
                            main_layout.setContentsMargins(15, 15, 15, 15)  # Set margins
                            
                            # Calculate available height for each group (minus button area and spacing)
                            button_area_height = 50  # Button area height
                            total_spacing = 4 * 10 + 30  # Total spacing (4 spacings + margins)
                            available_height = window_height - button_area_height - total_spacing
                            group_height = available_height // 3  # Divide into three equal groups
                            
                            # First group: Prompt information
                            prompt_label = QLabel(get_text("prompt_label") + ":")
                            prompt_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
                            prompt_label.setFixedHeight(25)  # Fixed height for small label
                            main_layout.addWidget(prompt_label)
                            
                            self.prompt_edit = QPlainTextEdit(prompt)
                            self.prompt_edit.setReadOnly(True)
                            self.prompt_edit.setFixedHeight(group_height - 25)  # Minus label height
                            self.prompt_edit.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
                            main_layout.addWidget(self.prompt_edit)
                            
                            # Second group: Current information (only show if current_info is provided)
                            if current_info and current_info.strip():
                                info_label = QLabel(get_text("current_info_title") + ":")
                                info_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
                                info_label.setFixedHeight(25)  # Fixed height for small label
                                main_layout.addWidget(info_label)

                                self.info_edit = QPlainTextEdit(current_info)
                                self.info_edit.setReadOnly(True)
                                self.info_edit.setFixedHeight(group_height - 25)  # Minus label height
                                self.info_edit.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
                                main_layout.addWidget(self.info_edit)
                            else:
                                # If no current_info, allocate more space to input field
                                group_height = available_height // 2  # Divide into two groups instead of three
                            
                            # Third group: User input
                            input_label = QLabel(get_text("user_input_label") + ":")
                            input_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #2c5aa0;")
                            input_label.setFixedHeight(25)  # Fixed height for small label
                            main_layout.addWidget(input_label)
                            
                            self.input_field = QPlainTextEdit()
                            self.input_field.setPlaceholderText(get_text("input_placeholder"))
                            self.input_field.setFixedHeight(group_height - 25)  # Minus label height
                            self.input_field.setStyleSheet("border: 2px solid #2c5aa0; border-radius: 4px;")
                            self.input_field.setFocus()  # Default focus on input field
                            main_layout.addWidget(self.input_field)
                            
                            # Add buttons - fixed at bottom
                            button_layout = QHBoxLayout()
                            submit_button = QPushButton(get_text("submit_button"))
                            submit_button.clicked.connect(self.accept)
                            submit_button.setMinimumHeight(35)  # Ensure button is easily clickable
                            submit_button.setStyleSheet("QPushButton { background-color: #2c5aa0; color: white; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #1e3d6f; }")
                            button_layout.addStretch()
                            button_layout.addWidget(submit_button)
                            
                            main_layout.addLayout(button_layout)
                            
                            # Apply main layout
                            self.setLayout(main_layout)
                        
                        def get_input(self):
                            """Get user input from the text field"""
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
                    logger.error(f"{get_text('pyqt_dialog_error')}: {e}")
                    logger.error(traceback.format_exc())
                    on_input_completed(f"{get_text('pyqt_dialog_error')}: {str(e)}")
            
            # Execute QT dialog in thread pool
            try:
                # Notify context
                if ctx:
                    await ctx.info(get_text("wait_user_input"))
                    
                # Start thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, run_qt_dialog)
                
                # Wait for event
                await event.wait()
                
                # Return result
                if ctx:
                    await ctx.info(get_text("user_provided_info"))
                
                return result[0]
                
            except Exception as e:
                logger.error(f"{get_text('pyqt_ui_error')}: {e}")
                if ctx:
                    await ctx.error(f"{get_text('pyqt_ui_error')}: {e}")
                return f"{get_text('pyqt_interface_error')}: {str(e)}"
        
        def cleanup(self):
            """Clean up resources"""
            # PyQt application will automatically clean up when program exits
            pass
