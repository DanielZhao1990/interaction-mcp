#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web Interface Implementation
Using Flask and SocketIO to implement a web-based interactive interface
"""

import asyncio
import threading
import webbrowser
from typing import List, Dict, Any, Optional, Union
from fastmcp import Context

try:
    from flask import Flask, render_template, request, jsonify
    from flask_socketio import SocketIO
except ImportError:
    # If Flask is not installed, provide a placeholder class
    class WebUI:
        """Web Interface Implementation Class (Flask not installed)"""
        
        def __init__(self):
            """Initialize Web interface"""
            print("Warning: Flask or Flask-SocketIO not installed, Web interface will not be available")
            self._web_available = False
        
        async def select_option(self, options, prompt="Please select one of the following options", allow_custom=True, ctx=None):
            """Placeholder method"""
            print("Error: Cannot use Web interface, Flask or Flask-SocketIO not installed")
            return {
                "selected_index": -1,
                "selected_option": None,
                "custom_input": "Flask or Flask-SocketIO not installed, interface unavailable",
                "is_custom": True
            }
        
        async def request_additional_info(self, prompt, ctx=None):
            """Placeholder method"""
            print("Error: Cannot use Web interface, Flask or Flask-SocketIO not installed")
            return "Flask or Flask-SocketIO not installed, interface unavailable"
else:
    # If Flask is installed, provide full implementation
    class WebUI:
        """Web Interface Implementation Class"""
        
        def __init__(self):
            """Initialize Web interface"""
            self._web_available = True
            self._app = None
            self._socketio = None
            self._server_thread = None
            self._server_running = False
            self._port = 5000
            self._host = "127.0.0.1"
            
            # Store requests and results with IDs for concurrent handling
            import uuid
            self._request_lock = asyncio.Lock()
            self._requests = {}  # request_id -> request_data
            self._results = {}   # request_id -> result_data
            self._events = {}    # request_id -> asyncio.Event
        
        def _find_available_port(self, start_port=5000, max_attempts=10):
            """Find an available port starting from start_port"""
            import socket
            
            for port in range(start_port, start_port + max_attempts):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind((self._host, port))
                        return port
                    except socket.error:
                        continue
            
            # If no available port found in range, try a random high port
            import random
            return random.randint(8000, 9000)
        
        def _ensure_server(self):
            """Ensure Web server is started"""
            if self._server_running:
                return
                
            # Find available port
            self._port = self._find_available_port()
            
            import os
            import logging
            logger = logging.getLogger('WebUI')
            logger.info(f"Starting web server on port {self._port}")
            
            # Create Flask application
            import os
            
            # Determine absolute paths for template and static folders
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            template_folder = os.path.join(base_dir, "web_templates")
            static_folder = os.path.join(base_dir, "web_static")
            
            self._app = Flask(__name__, 
                             template_folder=template_folder,
                             static_folder=static_folder)
            self._socketio = SocketIO(self._app, cors_allowed_origins="*")
            
            # Create necessary directories
            os.makedirs(template_folder, exist_ok=True)
            os.makedirs(static_folder, exist_ok=True)
            
            # Register routes
            @self._app.route('/')
            def index():
                return render_template('index.html')
            
            @self._app.route('/select/<request_id>')
            def select_page(request_id):
                return render_template('select.html', request_id=request_id)
            
            @self._app.route('/info/<request_id>')
            def info_page(request_id):
                return render_template('info.html', request_id=request_id)
            
            @self._app.route('/api/request/<request_id>', methods=['GET'])
            def get_request(request_id):
                if request_id in self._requests:
                    return jsonify(self._requests[request_id])
                return jsonify({"error": "Request not found"}), 404
            
            # Register SocketIO events
            @self._socketio.on('connect')
            def handle_connect():
                print("Client connected")
                logging.getLogger('WebUI').info("Client connected")
            
            @self._socketio.on('disconnect')
            def handle_disconnect():
                print("Client disconnected")
                logging.getLogger('WebUI').info("Client disconnected")
            
            @self._socketio.on('submit_selection')
            def handle_selection(data):
                print(f"Received selection data: {data}")
                logging.getLogger('WebUI').info(f"Received selection data: {data}")
                
                request_id = data.get('request_id')
                if not request_id:
                    logging.getLogger('WebUI').error(f"No request_id in selection data: {data}")
                    return
                    
                if request_id not in self._requests:
                    logging.getLogger('WebUI').error(f"Request ID not found: {request_id}")
                    return
                    
                if self._requests[request_id]['type'] != 'select_option':
                    logging.getLogger('WebUI').error(f"Wrong request type: {self._requests[request_id]['type']}")
                    return
                
                # Remove request_id from the data before storing result
                result_data = {k: v for k, v in data.items() if k != 'request_id'}
                self._results[request_id] = result_data
                
                # Set event to signal that result is available
                if request_id in self._events:
                    logging.getLogger('WebUI').info(f"Setting event for request: {request_id}")
                    self._events[request_id].set()
                else:
                    logging.getLogger('WebUI').error(f"No event for request: {request_id}")
                
                # Send confirmation to client
                self._socketio.emit(f'selection_received_{request_id}')
                logging.getLogger('WebUI').info(f"Sent confirmation for request: {request_id}")
            
            @self._socketio.on('submit_info')
            def handle_info(data):
                print(f"Received info data: {data}")
                logging.getLogger('WebUI').info(f"Received info data: {data}")
                
                request_id = data.get('request_id')
                if not request_id:
                    logging.getLogger('WebUI').error(f"No request_id in info data: {data}")
                    return
                    
                if request_id not in self._requests:
                    logging.getLogger('WebUI').error(f"Request ID not found: {request_id}")
                    return
                    
                if self._requests[request_id]['type'] != 'request_info':
                    logging.getLogger('WebUI').error(f"Wrong request type: {self._requests[request_id]['type']}")
                    return
                
                # Store the input text directly
                self._results[request_id] = data.get('text', '')
                
                # Set event to signal that result is available
                if request_id in self._events:
                    logging.getLogger('WebUI').info(f"Setting event for request: {request_id}")
                    self._events[request_id].set()
                else:
                    logging.getLogger('WebUI').error(f"No event for request: {request_id}")
                
                # Send confirmation to client
                self._socketio.emit(f'info_received_{request_id}')
                logging.getLogger('WebUI').info(f"Sent confirmation for request: {request_id}")
            
            # Start server thread
            def run_server():
                try:
                    self._socketio.run(self._app, host=self._host, port=self._port, debug=False, use_reloader=False)
                except Exception as e:
                    import logging
                    logging.getLogger('WebUI').error(f"Failed to start web server: {e}")
            
            self._server_thread = threading.Thread(target=run_server, daemon=True)
            self._server_thread.start()
            self._server_running = True
            
            # Wait for server to start
            import time
            time.sleep(1)
        
# 模板文件已抽离到web_templates目录中，不再在代码中存储
        
        def _open_browser(self, path):
            """Open browser to access specified path"""
            url = f"http://{self._host}:{self._port}{path}"
            print(f"Opening browser at: {url}")
            import logging
            logger = logging.getLogger('WebUI')
            logger.info(f"Opening browser at: {url}")
            webbrowser.open(url)
        
        async def select_option(
            self,
            options: List[Union[str, Dict[str, Any]]],
            prompt: str = "Please select one of the following options",
            allow_custom: bool = True,  # 保留参数但不使用
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            Present options to the user and get selection using Web interface

            Args:
                options: List of options
                prompt: Prompt message
                allow_custom: 已废弃，现在所有选择均默认允许自定义输入
                ctx: FastMCP context

            Returns:
                Selection result dictionary
            """
            import logging
            logger = logging.getLogger('WebUI')
            
            logger.info("select_option called")
            if not self._web_available:
                logger.error("Web UI not available")
                if ctx:
                    await ctx.error("Flask or Flask-SocketIO not installed, Web interface unavailable")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "Flask or Flask-SocketIO not installed, interface unavailable",
                    "is_custom": True
                }
            
            if ctx:
                await ctx.info("Displaying options using Web interface...")
            
            # Ensure server is started
            self._ensure_server()
            
            # Create a unique request ID
            import uuid
            request_id = str(uuid.uuid4())
            logger.info(f"Created request ID: {request_id}")
            
            # Create event object for waiting for result
            event = asyncio.Event()
            
            # Store request data and event
            async with self._request_lock:
                self._requests[request_id] = {
                    "type": "select_option",
                    "options": options,
                    "prompt": prompt,
                    "allow_custom": True  # 强制允许自定义
                }
                self._events[request_id] = event
                logger.info(f"Stored request data and event for ID: {request_id}")
            
            # Open browser with the request ID in the URL
            asyncio.get_event_loop().run_in_executor(None, self._open_browser, f"/select/{request_id}")
            
            # Wait for result
            logger.info(f"Waiting for event to be set for request ID: {request_id}")
            try:
                await asyncio.wait_for(event.wait(), timeout=60)
                logger.info(f"Event was set for request ID: {request_id}")
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for selection result for request ID: {request_id}")
                if ctx:
                    await ctx.error("Timeout waiting for selection result")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "Timeout waiting for selection result",
                    "is_custom": True
                }
            
            # Get result
            result = None
            async with self._request_lock:
                if request_id in self._results:
                    result = self._results[request_id]
                    # Clean up
                    del self._results[request_id]
                    del self._requests[request_id]
                    del self._events[request_id]
            
            if not result:
                if ctx:
                    await ctx.error("Failed to get selection result")
                return {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": "Failed to get selection result",
                    "is_custom": True
                }
            
            if ctx:
                if result["is_custom"]:
                    await ctx.info(f"User provided a custom answer: {result['custom_input']}")
                else:
                    await ctx.info(f"User selected option {result['selected_index'] + 1}")
            
            logger.info(f"Returning result from select_option: {result}")
            return result
        
        async def request_additional_info(
            self,
            prompt: str,
            ctx: Context = None
        ) -> str:
            """
            Request supplementary information from the user using Web interface

            Args:
                prompt: Prompt message
                ctx: FastMCP context

            Returns:
                User input information
            """
            import logging
            logger = logging.getLogger('WebUI')
            
            logger.info("request_additional_info called")
            
            if not self._web_available:
                logger.error("Web UI not available")
                if ctx:
                    await ctx.error("Flask or Flask-SocketIO not installed, Web interface unavailable")
                return "Flask or Flask-SocketIO not installed, interface unavailable"
            
            if ctx:
                await ctx.info("Requesting supplementary information using Web interface...")
            
            # Ensure server is started
            self._ensure_server()
            
            # Create a unique request ID
            import uuid
            request_id = str(uuid.uuid4())
            logger.info(f"Created request ID: {request_id}")
            
            # Create event object for waiting for result
            event = asyncio.Event()
            
            # Store request data and event
            async with self._request_lock:
                self._requests[request_id] = {
                    "type": "request_info",
                    "prompt": prompt
                }
                self._events[request_id] = event
                logger.info(f"Stored request data and event for ID: {request_id}")
            
            # Open browser with the request ID in the URL
            asyncio.get_event_loop().run_in_executor(None, self._open_browser, f"/info/{request_id}")
            
            # Wait for result
            logger.info(f"Waiting for event to be set for request ID: {request_id}")
            try:
                await asyncio.wait_for(event.wait(), timeout=60)
                logger.info(f"Event was set for request ID: {request_id}")
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for info result for request ID: {request_id}")
                if ctx:
                    await ctx.error("Timeout waiting for user input")
                return "Timeout waiting for user input"
            
            # Get result
            result = None
            async with self._request_lock:
                if request_id in self._results:
                    result = self._results[request_id]
                    logger.info(f"Got result for request ID: {request_id}, result: {result}")
                    # Clean up
                    del self._results[request_id]
                    del self._requests[request_id]
                    del self._events[request_id]
                    logger.info(f"Cleaned up request data for ID: {request_id}")
                else:
                    logger.error(f"No result found for request ID: {request_id}")
            
            if result is None:
                if ctx:
                    await ctx.error("Failed to get user input")
                return "Failed to get user input"
            
            if ctx:
                await ctx.info("User provided supplementary information")
            
            logger.info(f"Returning result from request_additional_info: {result}")
            return result
        
        def cleanup(self):
            """Clean up resources"""
            # Web server will automatically close when program exits
            pass
