#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP Interactive 客户端工具
用于连接和调用 ai-interaction 服务的客户端
支持交互式选择可用方法和输入参数
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, Confirm

# 默认配置
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7888

console = Console()

async def get_available_tools(
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT
) -> List[Any]:
    """
    获取可用的MCP工具列表
    
    Args:
        host: 服务器主机
        port: 服务器端口
        
    Returns:
        可用工具对象列表
    """
    # 导入FastMCP相关模块
    from fastmcp import Client
    from fastmcp.client.transports import SSETransport
    
    # 设置SSE服务URL
    server_url = f"http://{host}:{port}/sse"
    
    console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
    
    # 创建客户端
    try:
        # 显式创建SSE传输
        transport = SSETransport(url=server_url)
        
        # 创建FastMCP客户端
        async with Client(transport) as client:
            try:
                # 列出可用工具
                tools_list = await client.list_tools()
                return tools_list
            except Exception as e:
                console.print(f"[bold red]获取可用工具列表失败: {str(e)}[/bold red]")
                return []
    except Exception as e:
        console.print(f"[bold red]连接MCP服务发生异常: {str(e)}[/bold red]")
        return []

async def call_mcp_method(
    method_name: str, 
    params: Optional[Dict[str, Any]] = None, 
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT,
    timeout: float = 60.0  # 添加超时参数但不使用它
) -> Dict[str, Any]:
    """
    调用MCP方法
    
    Args:
        method_name: 方法名
        params: 方法参数
        host: 服务器主机
        port: 服务器端口
    Returns:
        方法返回结果
    """
    if params is None:
        params = {}
    
    # 导入FastMCP相关模块
    from fastmcp import Client
    from fastmcp.client.transports import SSETransport
    
    # 设置SSE服务URL
    server_url = f"http://{host}:{port}/sse"
    
    console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
    console.print(f"[bold]调用方法: {method_name}[/bold]")
    console.print(Panel(
        Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="请求参数",
        border_style="blue"
    ))
    
    # 创建客户端
    try:
        # 显式创建SSE传输
        transport = SSETransport(url=server_url)
        
        # 创建FastMCP客户端
        async with Client(transport) as client:
            try:
                # 调用指定方法
                result = await client.call_tool(method_name, params)
                    
                # 处理返回结果
                if hasattr(result, 'json'):
                    # JSON结果
                    console.print(Panel(
                        Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
                        title="JSON结果",
                        border_style="green"
                    ))
                    return result.json
                elif hasattr(result, 'text'):
                    # 文本结果
                    console.print(Panel(result.text, title="文本结果", border_style="green"))
                    try:
                        return json.loads(result.text)
                    except:
                        return {"content": result.text}
                else:
                    # 其他类型结果
                    console.print(f"结果类型: {type(result)}")
                    console.print(str(result))
                    return {"content": str(result)}
            except Exception as e:
                console.print(f"[bold red]API调用发生异常: {str(e)}[/bold red]")
                return {"error": f"API调用错误: {str(e)}"}
    except Exception as e:
        console.print(f"[bold red]连接MCP服务发生异常: {str(e)}[/bold red]")
        return {"error": f"连接MCP服务失败: {str(e)}"}

def get_input_params_for_method(method_info: Any) -> Dict[str, Any]:
    """
    根据方法信息获取用户输入的参数
    
    Args:
        method_info: 方法信息对象
        
    Returns:
        方法参数字典
    """
    params = {}
    
    # 直接从方法描述中提取参数信息
    description = getattr(method_info, "description", "")
    
    # 显示方法信息
    console.print(Panel(
        f"方法: [bold]{method_info.name}[/bold]\n描述: {description}",
        title="参数输入",
        border_style="blue"
    ))
    
    # 根据方法名称设置默认参数
    if method_info.name == "select_option":
        # select_option 需要 options, prompt 参数
        options = []
        num_options = int(Prompt.ask("请输入选项数量", default="3"))
        
        for i in range(num_options):
            option_type = Prompt.ask(f"选项 {i+1} 类型", choices=["简单文本", "带描述"], default="简单文本")
            
            if option_type == "简单文本":
                option_text = Prompt.ask(f"选项 {i+1} 文本")
                options.append(option_text)
            else:
                title = Prompt.ask(f"选项 {i+1} 标题")
                description = Prompt.ask(f"选项 {i+1} 描述")
                options.append({"title": title, "description": description})
        
        params["options"] = options
        params["prompt"] = Prompt.ask("提示信息", default="请选择一个选项")
    
    elif method_info.name == "request_additional_info":
        # request_additional_info 需要 prompt, current_info 参数
        params["prompt"] = Prompt.ask("提示信息", default="请提供更多信息")
        params["current_info"] = Prompt.ask("当前信息", default="")
    
    else:
        # 其他方法，让用户手动输入JSON参数
        console.print("[请输入JSON格式的参数，例如: {\"key\": \"value\"}]")
        param_json = Prompt.ask("参数JSON", default="{}")
        
        try:
            params = json.loads(param_json)
        except json.JSONDecodeError:
            console.print("[警告: JSON格式错误，使用空参数]")
    
    return params

async def interactive_mcp_client(
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT,
    timeout: float = 60.0
):
    """
    交互式MCP客户端，显示可用方法并让用户选择
    
    Args:
        host: 服务器主机
        port: 服务器端口
        timeout: 超时时间（秒）
    """
    try:
        console.print(
            Panel.fit(
                f"MCP Interactive 交互式客户端\n连接到 {host}:{port}",
                title="客户端启动",
                border_style="green"
            )
        )
        
        console.print("正在获取可用的MCP方法...")
        tools = await get_available_tools(host, port)
        
        if not tools:
            console.print("[bold red]未找到可用的MCP方法，请检查服务器连接[/bold red]")
            return
        
        console.print(f"[bold green]成功连接到MCP服务器，找到 {len(tools)} 个可用方法[/bold green]")
        
        while True:
            # 创建方法表格
            table = Table(title="可用的MCP方法")
            table.add_column("序号", style="cyan")
            table.add_column("方法名", style="green")
            table.add_column("描述", style="blue")
            
            for i, tool in enumerate(tools):
                table.add_row(str(i+1), tool.name, tool.description or "无描述")
            
            console.print(table)
            
            choice = Prompt.ask(
                "选择要调用的方法",
                choices=[str(i+1) for i in range(len(tools))] + ["q"],
                default="q"
            )
            
            if choice.lower() == 'q':
                console.print("[bold green]退出交互式客户端[/bold green]")
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tools):
                    selected_tool = tools[idx]
                    
                    # 获取方法参数
                    params = get_input_params_for_method(selected_tool)
                    
                    # 调用方法
                    console.print(f"\n[bold]调用方法 '{selected_tool.name}'...[/bold]")
                    await call_mcp_method(selected_tool.name, params, host, port)
                else:
                    console.print(f"[bold red]错误: 请输入 1 到 {len(tools)} 之间的数字[/bold red]")
            except ValueError:
                console.print("[bold red]错误: 请输入有效的数字[/bold red]")
    
    except Exception as e:
        console.print(f"[bold red]交互式客户端发生异常: {str(e)}[/bold red]")

async def select_option_demo(
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT,
    timeout: float = 60.0
):
    """
    演示选项选择工具（使用固定参数）
    
    Args:
        host: 服务器主机
        port: 服务器端口
        timeout: 超时时间（秒）
    """
    console.print(Panel(Markdown("# 选项选择工具演示"), border_style="blue"))
    
    # 使用固定参数，无需用户输入
    options = [
        "选项 1: 使用 TensorFlow 实现神经网络",
        "选项 2: 使用 PyTorch 实现神经网络",
        {
            "title": "选项 3: 使用 JAX 实现神经网络",
            "description": "适用于研究目的，支持自动微分和 GPU/TPU 加速"
        }
    ]
    
    prompt = "请选择一种神经网络实现方式"
    
    # 显示固定参数
    console.print("[使用固定参数进行演示，无需手动输入]")
    console.print(Panel(
        Syntax(json.dumps({"options": options, "prompt": prompt}, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="固定参数",
        border_style="cyan"
    ))
    
    # 调用选项选择工具
    params = {
        "options": options,
        "prompt": prompt
    }
    
    # 直接调用方法，不经过 call_mcp_method 包装
    try:
        # 导入FastMCP相关模块
        from fastmcp import Client
        from fastmcp.client.transports import SSETransport
        
        # 设置SSE服务URL
        server_url = f"http://{host}:{port}/sse"
        
        console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
        console.print(f"[bold]调用方法: select_option[/bold]")
        
        # 显示参数
        console.print(Panel(
            Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
            title="请求参数",
            border_style="blue"
        ))
        
        # 创建客户端
        transport = SSETransport(url=server_url)
        
        # 创建FastMCP客户端
        async with Client(transport) as client:
            # 调用指定方法
            console.print("[正在调用选项选择工具...]")
            result = await client.call_tool("select_option", params)
            
            # 处理返回结果
            if hasattr(result, 'json'):
                # JSON结果
                console.print(Panel(
                    Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
                    title="JSON结果",
                    border_style="green"
                ))
            elif hasattr(result, 'text'):
                # 文本结果
                console.print(Panel(result.text, title="文本结果", border_style="green"))
            else:
                # 其他类型结果
                console.print(f"结果类型: {type(result)}")
                console.print(str(result))
    except Exception as e:
        console.print(f"[bold red]发生错误: {str(e)}[/bold red]")

async def request_info_demo(
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT,
    timeout: float = 60.0
):
    """
    演示信息补充工具（使用固定参数）
    
    Args:
        host: 服务器主机
        port: 服务器端口
        timeout: 超时时间（秒）
    """
    console.print(Panel(Markdown("# 信息补充工具演示"), border_style="green"))
    
    # 使用固定参数，无需用户输入
    current_info = "这是一个数据分析项目，需要处理大量结构化数据。"
    prompt = "请提供更多关于数据来源和分析目标的信息"
    
    # 显示固定参数
    console.print("[使用固定参数进行演示，无需手动输入]")
    console.print(Panel(
        Syntax(json.dumps({"current_info": current_info, "prompt": prompt}, indent=2, ensure_ascii=False), "json", theme="monokai"),
        title="固定参数",
        border_style="cyan"
    ))
    
    # 调用信息补充工具
    params = {
        "prompt": prompt,
        "current_info": current_info
    }
    
    # 直接调用方法，不经过 call_mcp_method 包装
    try:
        # 导入FastMCP相关模块
        from fastmcp import Client
        from fastmcp.client.transports import SSETransport
        
        # 设置SSE服务URL
        server_url = f"http://{host}:{port}/sse"
        
        console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
        console.print(f"[bold]调用方法: request_additional_info[/bold]")
        
        # 显示参数
        console.print(Panel(
            Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
            title="请求参数",
            border_style="blue"
        ))
        
        # 创建客户端
        transport = SSETransport(url=server_url)
        
        # 创建FastMCP客户端
        async with Client(transport) as client:
            # 调用指定方法
            console.print("[正在调用信息补充工具...]")
            result = await client.call_tool("request_additional_info", params)
            
            # 处理返回结果
            if hasattr(result, 'text'):
                # 文本结果
                console.print("[用户提供的补充信息:]")
                console.print(Panel(result.text, title="文本结果", border_style="green"))
            elif hasattr(result, 'json'):
                # JSON结果
                console.print(Panel(
                    Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
                    title="JSON结果",
                    border_style="green"
                ))
            else:
                # 其他类型结果
                console.print(f"结果类型: {type(result)}")
                console.print(str(result))
    except Exception as e:
        console.print(f"[bold red]发生错误: {str(e)}[/bold red]")

async def quick_test_menu(
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT,
    timeout: float = 60.0
):
    """
    简化的测试菜单，提供UI类型选择和方法选择
    
    Args:
        host: 服务器主机
        port: 服务器端口
        timeout: 超时时间（秒）
    """
    console.print(Panel(Markdown("# MCP Interactive 快速测试"), border_style="green"))
    
    # 首先选择UI类型
    ui_options = [
        {"title": "命令行界面 (CLI)", "value": "cli", "description": "简单的命令行交互界面"},
        {"title": "Tkinter界面", "value": "tkinter", "description": "基于Tkinter的图形界面"},
        {"title": "PyQt界面", "value": "pyqt", "description": "基于PyQt的图形界面"},
        {"title": "Web界面", "value": "web", "description": "基于Web的界面"}
    ]
    
    console.print(Panel(Markdown("## 第一步：选择UI类型"), border_style="blue"))
    
    # 显示UI选项
    table = Table(title="可用的UI类型")
    table.add_column("序号", style="cyan")
    table.add_column("UI类型", style="green")
    table.add_column("描述", style="blue")
    
    for i, option in enumerate(ui_options):
        table.add_row(str(i+1), option["title"], option["description"])
    
    console.print(table)
    
    ui_choice = Prompt.ask(
        "选择UI类型",
        choices=[str(i+1) for i in range(len(ui_options))],
        default="1"
    )
    
    ui_idx = int(ui_choice) - 1
    ui_type = ui_options[ui_idx]["value"]
    console.print(f"[bold]已选择UI类型: {ui_options[ui_idx]['title']}[/bold]")
    
    # 设置UI类型
    try:
        console.print(f"[bold blue]正在设置UI类型: {ui_type}[/bold blue]")
        set_ui_params = {
            "ui_type": ui_type
        }
        
        # 导入FastMCP相关模块
        from fastmcp import Client
        from fastmcp.client.transports import SSETransport
        
        # 设置SSE服务URL
        server_url = f"http://{host}:{port}/sse"
        
        # 创建客户端并设置UI类型
        transport = SSETransport(url=server_url)
        
        # 创建FastMCP客户端
        async with Client(transport) as client:
            # 调用方法设置UI类型
            await client.call_tool("set_ui_type", set_ui_params)
    except Exception as e:
        console.print(f"[bold yellow]警告: 无法设置UI类型: {str(e)}[/bold yellow]")
    
    # 循环测试，直到退出
    while True:
        console.print(Panel(Markdown("## 第二步：选择测试方法"), border_style="blue"))
        
        # 方法选项
        method_options = [
            {"title": "选项选择工具 (select_option)", "value": "select_option", "description": "测试选项选择交互"},
            {"title": "信息补充工具 (request_additional_info)", "value": "request_additional_info", "description": "测试信息补充交互"},
            {"title": "退出", "value": "exit", "description": "退出测试菜单"}
        ]
        
        # 显示方法选项
        table = Table(title="可用的测试方法")
        table.add_column("序号", style="cyan")
        table.add_column("方法", style="green")
        table.add_column("描述", style="blue")
        
        for i, option in enumerate(method_options):
            table.add_row(str(i+1), option["title"], option["description"])
        
        console.print(table)
        
        method_choice = Prompt.ask(
            "选择测试方法",
            choices=[str(i+1) for i in range(len(method_options))],
            default="1"
        )
        
        method_idx = int(method_choice) - 1
        method_name = method_options[method_idx]["value"]
        
        if method_name == "exit":
            console.print("[bold green]退出测试菜单[/bold green]")
            break
        
        console.print(f"[bold]已选择测试方法: {method_options[method_idx]['title']}[/bold]")
        
        # 选择参数预设
        console.print(Panel(Markdown("## 第三步：选择参数预设"), border_style="blue"))
        
        preset_options = [
            {"title": "默认参数", "value": "default", "description": "标准测试参数"},
            {"title": "简单参数", "value": "simple", "description": "简化的测试参数"},
            {"title": "复杂参数", "value": "complex", "description": "更复杂的测试参数"}
        ]
        
        # 显示预设选项
        table = Table(title="可用的参数预设")
        table.add_column("序号", style="cyan")
        table.add_column("预设", style="green")
        table.add_column("描述", style="blue")
        
        for i, option in enumerate(preset_options):
            table.add_row(str(i+1), option["title"], option["description"])
        
        console.print(table)
        
        preset_choice = Prompt.ask(
            "选择参数预设",
            choices=[str(i+1) for i in range(len(preset_options))],
            default="1"
        )
        
        preset_idx = int(preset_choice) - 1
        preset = preset_options[preset_idx]["value"]
        
        console.print(f"[bold]已选择参数预设: {preset_options[preset_idx]['title']}[/bold]")
        
        # 获取参数并执行测试
        params = get_preset_params(method_name, preset)
        
        # 显示参数
        console.print(Panel(
            Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
            title="测试参数",
            border_style="cyan"
        ))
        
        if Confirm.ask("确认开始测试?", default=True):
            # 直接调用方法
            try:
                # 设置SSE服务URL
                server_url = f"http://{host}:{port}/sse"
                
                console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
                
                # 创建客户端
                transport = SSETransport(url=server_url)
                
                # 创建FastMCP客户端
                async with Client(transport) as client:
                    # 调用指定方法
                    console.print(f"[正在调用 {method_name}...]")
                    result = await client.call_tool(method_name, params)
                    
                    # 处理返回结果
                    if hasattr(result, 'json'):
                        # JSON结果
                        console.print(Panel(
                            Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
                            title="JSON结果",
                            border_style="green"
                        ))
                    elif hasattr(result, 'text'):
                        # 文本结果
                        console.print("[收到文本结果:]")
                        console.print(Panel(result.text, title="文本结果", border_style="green"))
                    else:
                        # 其他类型结果
                        result_str = str(result)
                        console.print(f"结果类型: {type(result)}")
                        console.print(Panel(result_str, title="其他结果", border_style="green"))
                    
                    console.print(f"[bold green]测试完成: {method_name}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]测试过程中发生错误: {str(e)}[/bold red]")
                import traceback
                console.print(Panel(
                    traceback.format_exc(),
                    title="栈信息",
                    border_style="red"
                ))
        
        # 询问是否继续测试
        if not Confirm.ask("是否继续测试其他方法?", default=True):
            console.print("[bold green]退出测试菜单[/bold green]")
            break

def get_preset_params(method_name: str, preset: str) -> Dict[str, Any]:
    """
    获取预设参数集
    
    Args:
        method_name: 方法名称
        preset: 预设名称
        
    Returns:
        参数字典
    """
    # select_option 方法的预设参数
    select_option_presets = {
        "default": {
            "options": [
                "选项 1: 使用 TensorFlow 实现神经网络",
                "选项 2: 使用 PyTorch 实现神经网络",
                {"title": "选项 3: 使用 JAX 实现神经网络", "description": "适用于研究目的，支持自动微分和 GPU/TPU 加速"}
            ],
            "prompt": "请选择一种神经网络实现方式"
        },
        "simple": {
            "options": ["红色", "绿色", "蓝色"],
            "prompt": "请选择一种颜色"
        },
        "complex": {
            "options": [
                {"title": "方案 A", "description": "低成本但实现时间较长"},
                {"title": "方案 B", "description": "中等成本，实现时间适中"},
                {"title": "方案 C", "description": "高成本但实现时间短"}
            ],
            "prompt": "请选择一个项目实现方案"
        }
    }
    
    # request_additional_info 方法的预设参数
    request_info_presets = {
        "default": {
            "prompt": "请提供更多关于数据来源和分析目标的信息",
            "current_info": "这是一个数据分析项目，需要处理大量结构化数据。"
        },
        "simple": {
            "prompt": "请输入您的联系邮箱",
            "current_info": ""
        },
        "complex": {
            "prompt": "请详细描述您遇到的问题，包括错误信息和复现步骤",
            "current_info": "在运行程序时遇到了异常，但没有具体的错误信息。"
        }
    }
    
    # 根据方法名称选择预设参数集
    if method_name == "select_option":
        presets = select_option_presets
    elif method_name == "request_additional_info":
        presets = request_info_presets
    else:
        # 其他方法返回空参数
        return {}
    
    # 根据预设名称返回参数
    if preset in presets:
        return presets[preset]
    else:
        # 预设不存在，返回默认预设
        console.print(f"[bold yellow]警告: 预设 '{preset}' 不存在，使用默认预设[/bold yellow]")
        return presets["default"]

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MCP Interactive 客户端工具")
    
    # 基本连接参数
    parser.add_argument("--host", default=DEFAULT_HOST, help="服务器主机")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务器端口")
    parser.add_argument("--timeout", type=float, default=60.0, help="请求超时时间（秒）")
    parser.add_argument("--ui", choices=["cli", "tkinter", "pyqt", "web"], default="web", help="UI类型")
    
    # 解析参数
    args = parser.parse_args()
    
    try:
        # 显示欢迎信息
        console.print(
            Panel.fit(
                f"MCP Interactive 交互式客户端\n连接到 {args.host}:{args.port} (UI类型: {args.ui})",
                title="客户端启动",
                border_style="green"
            )
        )
        
        # 连接测试
        console.print("正在连接到服务器...")
        tools = await get_available_tools(args.host, args.port)
        
        if not tools:
            console.print("[bold red]未找到可用的MCP方法，请检查服务器连接[/bold red]")
            return
        
        console.print(f"[bold green]成功连接到MCP服务器，找到 {len(tools)} 个可用方法[/bold green]")
        
        # 设置UI类型
        try:
            console.print(f"[bold blue]正在设置UI类型: {args.ui}[/bold blue]")
            set_ui_params = {
                "ui_type": args.ui
            }
            
            # 导入FastMCP相关模块
            from fastmcp import Client
            from fastmcp.client.transports import SSETransport
            
            # 设置SSE服务URL
            server_url = f"http://{args.host}:{args.port}/sse"
            
            # 创建客户端并设置UI类型
            transport = SSETransport(url=server_url)
            
            # 创建FastMCP客户端
            async with Client(transport) as client:
                # 调用方法设置UI类型
                await client.call_tool("set_ui_type", set_ui_params)
                console.print(f"[bold green]UI类型已设置为: {args.ui}[/bold green]")
        except Exception as e:
            console.print(f"[bold yellow]警告: 无法设置UI类型: {str(e)}[/bold yellow]")
        
        # 循环测试，直到退出
        while True:
            # 选择测试方法
            console.print(Panel(Markdown("# 请选择测试方法"), border_style="blue"))
            
            # 方法选项
            method_options = [
                {"title": "选项选择工具 (select_option)", "value": "select_option", "description": "测试选项选择交互"},
                {"title": "信息补充工具 (request_additional_info)", "value": "request_additional_info", "description": "测试信息补充交互"},
                {"title": "退出程序", "value": "exit", "description": "退出客户端"}
            ]
            
            # 显示方法选项
            table = Table(title="可用的测试方法")
            table.add_column("序号", style="cyan")
            table.add_column("方法", style="green")
            table.add_column("描述", style="blue")
            
            for i, option in enumerate(method_options):
                table.add_row(str(i+1), option["title"], option["description"])
            
            console.print(table)
            
            method_choice = Prompt.ask(
                "选择测试方法",
                choices=[str(i+1) for i in range(len(method_options))],
                default="1"
            )
            
            method_idx = int(method_choice) - 1
            method_name = method_options[method_idx]["value"]
            
            if method_name == "exit":
                console.print("[bold green]退出程序[/bold green]")
                break
            
            console.print(f"[bold]已选择测试方法: {method_options[method_idx]['title']}[/bold]")
            
            # 选择参数预设
            console.print(Panel(Markdown("# 请选择参数预设"), border_style="blue"))
            
            preset_options = [
                {"title": "默认参数", "value": "default", "description": "标准测试参数"},
                {"title": "简单参数", "value": "simple", "description": "简化的测试参数"},
                {"title": "复杂参数", "value": "complex", "description": "更复杂的测试参数"}
            ]
            
            # 显示预设选项
            table = Table(title="可用的参数预设")
            table.add_column("序号", style="cyan")
            table.add_column("预设", style="green")
            table.add_column("描述", style="blue")
            
            for i, option in enumerate(preset_options):
                table.add_row(str(i+1), option["title"], option["description"])
            
            console.print(table)
            
            preset_choice = Prompt.ask(
                "选择参数预设",
                choices=[str(i+1) for i in range(len(preset_options))],
                default="1"
            )
            
            preset_idx = int(preset_choice) - 1
            preset = preset_options[preset_idx]["value"]
            
            console.print(f"[bold]已选择参数预设: {preset_options[preset_idx]['title']}[/bold]")
            
            # 获取参数并执行测试
            params = get_preset_params(method_name, preset)
            
            # 显示参数
            console.print(Panel(
                Syntax(json.dumps(params, indent=2, ensure_ascii=False), "json", theme="monokai"),
                title="测试参数",
                border_style="cyan"
            ))
            
            if Confirm.ask("确认开始测试?", default=True):
                # 直接调用方法
                try:
                    # 设置SSE服务URL
                    server_url = f"http://{args.host}:{args.port}/sse"
                    
                    console.print(f"[bold blue]连接FastMCP服务: {server_url}[/bold blue]")
                    
                    # 创建客户端
                    transport = SSETransport(url=server_url)
                    
                    # 创建FastMCP客户端
                    async with Client(transport) as client:
                        # 调用指定方法
                        console.print(f"[正在调用 {method_name}...]")
                        result = await client.call_tool(method_name, params)
                        
                        # 处理返回结果
                        if hasattr(result, 'json'):
                            # JSON结果
                            console.print(Panel(
                                Syntax(json.dumps(result.json, indent=2, ensure_ascii=False), "json", theme="monokai"),
                                title="JSON结果",
                                border_style="green"
                            ))
                        elif hasattr(result, 'text'):
                            # 文本结果
                            console.print("[收到文本结果:]")
                            console.print(Panel(result.text, title="文本结果", border_style="green"))
                        else:
                            # 其他类型结果
                            result_str = str(result)
                            console.print(f"结果类型: {type(result)}")
                            console.print(Panel(result_str, title="其他结果", border_style="green"))
                        
                        console.print(f"[bold green]测试完成: {method_name}[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]测试过程中发生错误: {str(e)}[/bold red]")
                    import traceback
                    console.print(Panel(
                        traceback.format_exc(),
                        title="栈信息",
                        border_style="red"
                    ))
            
            # 询问是否继续测试
            if not Confirm.ask("是否继续测试其他方法?", default=True):
                console.print("[bold green]退出程序[/bold green]")
                break
    
    except Exception as e:
        console.print(f"[bold red]程序异常: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]程序被用户中断[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]程序异常: {str(e)}[/bold red]")
        sys.exit(1)
