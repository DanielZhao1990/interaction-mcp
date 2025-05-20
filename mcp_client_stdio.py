#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP Interactive 客户端工具 - STDIO 版本
用于通过 STDIO 协议连接和测试 FastMCP 服务
"""

import sys
import json
import asyncio
import argparse
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

async def test_stdio_client(
    script_path: str,
    test_type: str = "both",
    ui_type: str = "cli"
):
    """
    使用 stdio 协议测试 MCP 服务器
    
    Args:
        script_path: 服务器脚本路径
        test_type: 测试类型 (select_option, request_additional_info, both)
        ui_type: UI类型 (cli, pyqt, web)
    """
    try:
        from fastmcp import Client
        from fastmcp.client.transports import PythonStdioTransport
        
        console.print(
            Panel.fit(
                f"测试 [bold green]FastMCP STDIO[/bold green] 传输协议\n"
                f"服务器脚本: [bold blue]{script_path}[/bold blue]\n"
                f"测试类型: [bold yellow]{test_type}[/bold yellow]\n"
                f"UI类型: [bold magenta]{ui_type}[/bold magenta]",
                title="MCP STDIO 客户端测试",
                border_style="green"
            )
        )
        
        # 创建 STDIO 传输 - 包含 UI 类型参数
        transport = PythonStdioTransport(
            script_path=script_path,
            python_cmd=sys.executable,  # 指定 Python 解释器路径
            args=["run", "--transport", "stdio", f"--ui-type={ui_type}"]  # 传递给脚本的参数
        )
        
        # 创建客户端并连接
        async with Client(transport) as client:
            console.print("[bold green]连接成功！[/bold green]")
            
            # 获取可用工具列表
            tools = await client.list_tools()
            
            # 显示工具列表
            table = Table(title="可用的 MCP 工具")
            table.add_column("序号", style="cyan")
            table.add_column("工具名称", style="green")
            table.add_column("描述", style="blue")
            
            for i, tool in enumerate(tools):
                table.add_row(str(i+1), tool.name, tool.description or "无描述")
            
            console.print(table)
            
            # 测试工具
            tool_names = [tool.name for tool in tools]
            
            # 测试 set_ui_type 工具 (如果存在)
            if "set_ui_type" in tool_names:
                await test_set_ui_type(client, ui_type)
            
            # 测试 select_option 工具
            if (test_type in ["select_option", "both"]) and "select_option" in tool_names:
                await test_select_option(client)
            
            # 测试 request_additional_info 工具
            if (test_type in ["request_additional_info", "both"]) and "request_additional_info" in tool_names:
                await test_request_additional_info(client)
            
            console.print("[bold green]测试完成！[/bold green]")
    
    except Exception as e:
        console.print(f"[bold red]错误: {str(e)}[/bold red]")
        import traceback
        console.print(Panel(
            traceback.format_exc(),
            title="错误详情",
            border_style="red"
        ))

async def test_set_ui_type(client, ui_type: str):
    """测试 set_ui_type 工具"""
    console.print(f"\n[bold]测试 set_ui_type 工具 ({ui_type})...[/bold]")
    
    params = {
        "ui_type": ui_type
    }
    
    console.print(Panel(
        Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="请求参数",
        border_style="blue"
    ))
    
    # 调用 set_ui_type 工具
    try:
        result = await client.call_tool("set_ui_type", params)
        print_result(result)
        console.print(f"[bold green]UI 类型已设置为 {ui_type}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]设置 UI 类型失败: {str(e)}[/bold red]")

async def test_select_option(client):
    """测试 select_option 工具"""
    console.print("\n[bold]测试 select_option 工具...[/bold]")
    
    options = [
        "选项 1: 使用 TensorFlow",
        "选项 2: 使用 PyTorch",
        {"title": "选项 3: 使用 JAX", "description": "适用于研究目的"}
    ]
    
    params = {
        "options": options,
        "prompt": "请选择一个深度学习框架"
    }
    
    console.print(Panel(
        Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="请求参数",
        border_style="blue"
    ))
    
    # 调用 select_option 工具
    result = await client.call_tool("select_option", params)
    
    # 处理返回结果
    print_result(result)

async def test_request_additional_info(client):
    """测试 request_additional_info 工具"""
    console.print("\n[bold]测试 request_additional_info 工具...[/bold]")
    
    params = {
        "prompt": "请提供更多关于项目的信息",
        "current_info": "这是一个 FastMCP 测试项目"
    }
    
    console.print(Panel(
        Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="请求参数",
        border_style="blue"
    ))
    
    # 调用 request_additional_info 工具
    result = await client.call_tool("request_additional_info", params)
    
    # 处理返回结果
    print_result(result)

def print_result(result):
    """打印结果"""
    if hasattr(result, 'json'):
        console.print(Panel(
            Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
            title="JSON 结果",
            border_style="green"
        ))
    elif hasattr(result, 'text'):
        console.print(Panel(result.text, title="文本结果", border_style="green"))
    else:
        console.print(f"结果类型: {type(result)}")
        console.print(str(result))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FastMCP STDIO 客户端测试工具")
    
    parser.add_argument(
        "--script", 
        default="main.py", 
        help="服务器脚本路径，默认为 main.py"
    )
    
    parser.add_argument(
        "--test", 
        choices=["select_option", "request_additional_info", "both"], 
        default="both",
        help="要测试的工具"
    )
    
    parser.add_argument(        "--ui",         choices=["cli", "tkinter", "pyqt", "web"],         default="cli",        help="UI 类型"    )
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(test_stdio_client(args.script, args.test, args.ui))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]程序被用户中断[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]程序异常: {str(e)}[/bold red]")
        sys.exit(1) 