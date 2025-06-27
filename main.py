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
import logging
from fastmcp import FastMCP
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Import UI modules
from ui.ui import select_option, request_additional_info, set_ui_type
# Import language management module
from lang_manager import set_language

# Define language type enum
class LangType(str, enum.Enum):
    ZH_CN = "zh_CN"
    EN_US = "en_US"

# Load environment variables
load_dotenv()

# 设置FastMCP内部日志系统
logging.basicConfig(level=logging.WARNING)
logging.getLogger('FastMCP').setLevel(logging.WARNING)
logging.getLogger('UI').setLevel(logging.WARNING)

# Create Rich console object
console = Console()

# Create FastMCP server instance - 仅传递必要的属性，避免警告
mcp = FastMCP(
    name="Cursor-MCP Interaction Service",
    description="Provides MCP service for interaction with AI tools",
    version="1.0.0"
)

# Register tool functions
mcp.tool()(select_option)
mcp.tool()(request_additional_info)

# Create command line application
app = typer.Typer(help="MCPInteractive")

# For storing server instance
server_instance = None

def signal_handler(sig, frame):
    """Handle termination signals"""
    console.print("\n[bold red]Received termination signal, shutting down service...[/bold red]")
    # If FastMCP is running, try to shut it down
    if server_instance and hasattr(server_instance, "shutdown"):
        try:
            server_instance.shutdown()
        except Exception as e:
            console.print(f"Error shutting down server: {e}", style="bold red")
    
    # Force exit program
    sys.exit(0)

@app.command()
def run(
    host: str = typer.Option("127.0.0.1", help="Server host address"),
    port: int = typer.Option(7888, help="Server port"),
    log_level: str = typer.Option("warning", help="Log level: debug, info, warning, error, critical"),
    transport: str = typer.Option("stdio", help="Transport protocol: simple, stdio, sse, streamable-http"),
    ui: str = typer.Option("pyqt", help="UI type: cli, pyqt, web"),
    lang: LangType = typer.Option(LangType.EN_US, help="Interface language: zh_CN, en_US")
):
    """
    Start MCPInteractive
    """
    global server_instance
    
    # Register signal handlers to capture SIGINT (Ctrl+C) and SIGTERM
    # Note: On Windows, only a subset of POSIX signals are supported
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
        # 设置日志级别
    try:
        logging_level = getattr(logging, log_level.upper())
        logging.getLogger().setLevel(logging_level)
        logging.getLogger('FastMCP').setLevel(logging_level)
        logging.getLogger('UI').setLevel(logging.WARNING)  # 保持UI模块在警告级别
    except AttributeError:
        console.print(f"[bold red]Invalid log level: {log_level}, using WARNING[/bold red]")
        logging.getLogger().setLevel(logging.WARNING)
    # 根据传输协议显示不同的启动信息
    if transport == "stdio":
        logging.info(
            f"Starting MCPInteractive v1.0.0\n"
            f"Transport protocol: {transport}\n"
            f"Log level: {log_level}"
        )
    else:
        console.print(
            Panel.fit(
                f"Starting [bold green]MCPInteractive[/bold green] v1.0.0\n"
                f"Address: [bold blue]http://{host}:{port}[/bold blue]\n"
                f"Transport protocol: [bold yellow]{transport}[/bold yellow]\n"
                f"Log level: [bold cyan]{log_level}[/bold cyan]",
                title="FastMCP Service",
                border_style="green"
            )
        )
    

    logging.info("Tip: Press Ctrl+C to terminate service")
    # Set UI type
    set_ui_type(ui)
    logging.info(f"Using UI type: [bold magenta]{ui}[/bold magenta]")
    
    # Set interface language
    set_language(lang)
    logging.info(f"Using interface language: [bold cyan]{lang}[/bold cyan]")
    
    # According to documentation, use the correct mcp.run() method and transport protocol
    try:
        server_instance = mcp  # Save server instance
        
        # 根据不同传输协议调用不同的启动方法
        if transport == "simple":
            # Simplest mode
            console.print("[bold green]Starting in simple mode...[/bold green]")
            try:
                mcp.run(log_level=log_level)
            except TypeError:
                # 如果log_level参数不支持，则不传
                mcp.run()
        elif transport == "stdio":
            # STDIO mode - 不支持大多数参数
            logging.info("[bold green]Starting in stdio mode...[/bold green]")
            mcp.run(transport="stdio")
        elif transport == "streamable-http":
            # Streamable HTTP mode
            try:
                mcp.run(
                    transport="streamable-http",
                    host=host,
                    port=port,
                    path="/mcp",
                    log_level=log_level
                )
            except TypeError:
                # 如果log_level参数不支持，则不传
                mcp.run(
                    transport="streamable-http",
                    host=host,
                    port=port,
                    path="/mcp"
                )
        else:
            # SSE mode (default)
            try:
                mcp.run(
                    transport="sse",
                    host=host,
                    port=port,
                    log_level=log_level
                )
            except TypeError:
                # 如果log_level参数不支持，则不传
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
    ui: str = typer.Option("cli", help="UI type: cli, pyqt, web"),
    lang: LangType = typer.Option(LangType.EN_US, help="Interface language: zh_CN, en_US")
):
    """
    Test tool functions
    """
    # 设置日志级别
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger('FastMCP').setLevel(logging.WARNING)
    logging.getLogger('UI').setLevel(logging.WARNING)
    
    # Set UI type
    set_ui_type(ui)
    console.print(f"Using UI type: [bold magenta]{ui}[/bold magenta]")
    
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
        prompt="Please provide more information\n"*100
    )
    console.print(f"User provided information: {result}")

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Received keyboard interrupt, shutting down service...[/bold yellow]")
    finally:
        console.print("[bold green]Service has been closed[/bold green]") 