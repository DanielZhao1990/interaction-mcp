#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastMCP service main program, creates server and registers tool functions
"""

import asyncio
import typer
import enum
import signal
import sys
import os
import time
import psutil
from fastmcp import FastMCP
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Import UI modules
from ui.ui import select_option, request_additional_info, set_ui_type
# Import language management module
from lang_manager import set_language

# Define UI type enum
class UIType(str, enum.Enum):
    CLI = "cli"
    PYQT = "pyqt"
    WEB = "web"

# Define language type enum
class LangType(str, enum.Enum):
    ZH_CN = "zh_CN"
    EN_US = "en_US"

# Load environment variables
load_dotenv()

# Create Rich console object
console = Console()

# Service PID file path
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.pid")

# Create FastMCP server instance
mcp = FastMCP(
    name="Cursor-MCP Interaction Service",
    description="Provides MCP service for interaction with AI tools like Cursor, Windsurf",
    version="1.0.0"
)

# Register tool functions
mcp.tool()(select_option)
mcp.tool()(request_additional_info)

# Create command line application
app = typer.Typer(help="MCPInteractive")

# For storing server instance
server_instance = None

def save_pid():
    """Save current process PID to file"""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    console.print(f"[bold blue]Service PID saved to: {PID_FILE}[/bold blue]")

def signal_handler(sig, frame):
    """Handle termination signals"""
    console.print("\n[bold red]Received termination signal, shutting down service...[/bold red]")
    # If FastMCP is running, try to shut it down
    if server_instance and hasattr(server_instance, "shutdown"):
        try:
            server_instance.shutdown()
        except Exception as e:
            console.print(f"Error shutting down server: {e}", style="bold red")
    
    # Clean up PID file
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except Exception as e:
            console.print(f"Error deleting PID file: {e}", style="bold red")
    
    # Force exit program
    sys.exit(0)

@app.command()
def run(
    host: str = typer.Option("127.0.0.1", help="Server host address"),
    port: int = typer.Option(7888, help="Server port"),
    log_level: str = typer.Option("info", help="Log level: debug, info, warning, error, critical"),
    transport: str = typer.Option("sse", help="Transport protocol: simple, stdio, sse, streamable-http"),
    ui_type: UIType = typer.Option(UIType.CLI, help="UI type: cli, tkinter, pyqt, web"),
    lang: LangType = typer.Option(LangType.EN_US, help="Interface language: zh_CN, en_US")
):
    """
    Start MCPInteractive
    """
    global server_instance
    
    # Save process PID
    save_pid()
    
    # Register signal handlers to capture SIGINT (Ctrl+C) and SIGTERM
    # Note: On Windows, only a subset of POSIX signals are supported
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # No longer trying to register CTRL_C_EVENT on Windows, it can't be used with signal.signal()
    
    console.print(
        Panel.fit(
            f"Starting [bold green]MCPInteractive[/bold green] v1.0.0\n"
            f"Address: [bold blue]http://{host}:{port}[/bold blue]\n"
            f"Transport protocol: [bold yellow]{transport}[/bold yellow]",
            title="FastMCP Service",
            border_style="green"
        )
    )
    
    console.print("[bold yellow]Tip: Press Ctrl+C to terminate service or run 'python main.py stop' command[/bold yellow]")
    
    # Set UI type
    set_ui_type(ui_type)
    console.print(f"Using UI type: [bold magenta]{ui_type}[/bold magenta]")
    
    # Set interface language
    set_language(lang)
    console.print(f"Using interface language: [bold cyan]{lang}[/bold cyan]")
    
    # According to documentation, use the correct mcp.run() method and transport protocol
    try:
        server_instance = mcp  # Save server instance
        
        if transport == "simple":
            # Simplest mode, no parameters passed
            console.print("[bold green]Starting in simple mode...[/bold green]")
            mcp.run()
        elif transport == "stdio":
            # STDIO mode
            mcp.run(transport="stdio")
        elif transport == "streamable-http":
            # Streamable HTTP mode
            mcp.run(
                transport="streamable-http",
                host=host,
                port=port,
                path="/mcp"
            )
        else:
            # SSE mode (default)
            mcp.run(
                transport="sse",
                host=host,
                port=port
            )
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Received keyboard interrupt, shutting down service...[/bold yellow]")
    except Exception as e:
        console.print(f"Service startup failed: {e}", style="bold red")
        console.print("\nPossible solutions:", style="yellow")
        console.print("1. Ensure the port is not in use", style="blue")
        console.print("2. Ensure correct versions of dependencies are installed", style="blue")
        console.print("3. Try the simplest startup method: --transport=simple", style="blue")
        console.print("4. Try other transport protocols: --transport=stdio|sse|streamable-http", style="blue")
        return
    finally:
        # Clean up PID file
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception as e:
                console.print(f"[bold red]Error cleaning up PID file: {e}[/bold red]")

@app.command()
def stop():
    """
    Stop running MCPInteractive
    """
    # Check if PID file exists
    if not os.path.exists(PID_FILE):
        console.print("[bold red]MCP service is not running[/bold red]")
        return
    
    try:
        # Read PID
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        if not psutil.pid_exists(pid):
            console.print("[bold red]PID file exists, but service process does not exist[/bold red]")
            os.remove(PID_FILE)
            return
        
        # Get process information
        process = psutil.Process(pid)
        process_name = process.name()
        
        console.print(f"[bold yellow]Stopping MCP service (PID: {pid}, Process name: {process_name})...[/bold yellow]")
        
        # Send termination signal
        try:
            # On Windows, SIGTERM might not work, so we use terminate()
            process.terminate()
            
            # Wait for process to terminate
            gone, alive = psutil.wait_procs([process], timeout=5)
            if process in alive:
                console.print("[bold red]Service did not respond to termination signal, attempting to force kill...[/bold red]")
                process.kill()
            
            # Delete PID file
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            
            console.print("[bold green]MCP service has been stopped[/bold green]")
        except psutil.NoSuchProcess:
            console.print("[bold yellow]Service process no longer exists[/bold yellow]")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception as e:
            console.print(f"[bold red]Error stopping service: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error stopping service: {e}[/bold red]")
        
        # Delete PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

@app.command("list-tools")
def list_tools():
    """
    List all available tools
    """
    # Directly list implemented tools
    tools_info = [
        {"name": "select_option", "description": "Display a list of options to the user and let them choose by inputting numbers or providing custom answers"},
        {"name": "request_additional_info", "description": "Request additional information from the user"}
    ]
    
    console.print(
        Panel.fit(
            "\n".join([f"[bold]{tool['name']}[/bold]: {tool['description']}" for tool in tools_info]),
            title=f"可用工具 ({len(tools_info)})",
            border_style="blue"
        )
    )

@app.command()
def test(
    tool_name: str = typer.Argument(None, help="Name of the tool to test"),
    ui_type: UIType = typer.Option(UIType.CLI, help="UI type: cli, tkinter, pyqt, web"),
    lang: LangType = typer.Option(LangType.EN_US, help="Interface language: zh_CN, en_US")
):
    """
    Test tool functions
    """
    # Set UI type
    set_ui_type(ui_type)
    console.print(f"Using UI type: [bold magenta]{ui_type}[/bold magenta]")
    
    # Set interface language
    set_language(lang)
    console.print(f"Using interface language: [bold cyan]{lang}[/bold cyan]")
    
    # Define available tool names and corresponding test functions
    available_tools = {
        "select_option": _test_select_option,
        "request_additional_info": _test_request_additional_info
    }
    
    if not tool_name:
        console.print("Please specify the name of the tool to test", style="bold red")
        console.print(f"Available tools: {', '.join(available_tools.keys())}", style="blue")
        return
    
    if tool_name not in available_tools:
        console.print(f"Tool '{tool_name}' does not exist", style="bold red")
        console.print(f"Available tools: {', '.join(available_tools.keys())}", style="blue")
        return
    
    console.print(f"Testing tool: [bold green]{tool_name}[/bold green]")
    
    # Run the corresponding test based on the tool name
    asyncio.run(available_tools[tool_name]())

@app.command()
def status():
    """
    Check the running status of MCPInteractive
    """
    if not os.path.exists(PID_FILE):
        console.print("[bold red]MCP service is not running[/bold red]")
        return
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Verify if PID exists
        if not psutil.pid_exists(pid):
            console.print("[bold red]PID file exists, but service process does not exist[/bold red]")
            os.remove(PID_FILE)
            return
        
        # Get process information
        process = psutil.Process(pid)
        created_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(process.create_time()))
        
        console.print(
            Panel.fit(
                f"Process ID: [bold green]{pid}[/bold green]\n"
                f"Start time: [bold blue]{created_time}[/bold blue]\n"
                f"Memory usage: [bold yellow]{process.memory_info().rss / 1024 / 1024:.2f} MB[/bold yellow]\n"
                f"Status: [bold green]Running[/bold green]",
                title="MCP Service Status",
                border_style="green"
            )
        )
    except Exception as e:
        console.print(f"[bold red]Error getting service status: {e}[/bold red]")
        # Try to clean up PID file
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except:
                pass
        console.print("[bold red]MCP service may not be running properly[/bold red]")

async def _test_select_option():
    """Test option selection tool"""
    options = [
        "Option 1: Using string option",
        {"title": "Option 2", "description": "Using dictionary option with description"},
        {"name": "Option 3", "value": 3},
    ]
    result = await select_option(options, prompt="Test option list")
    console.print(result)

async def _test_request_additional_info():
    """Test information supplement tool"""
    result = await request_additional_info(
        prompt="Please provide more information",
        current_info="This is the current information, needs supplement"
    )
    console.print(f"User provided information: {result}")

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Received keyboard interrupt, shutting down service...[/bold yellow]")
    finally:
        console.print("[bold green]Service has been closed[/bold green]") 