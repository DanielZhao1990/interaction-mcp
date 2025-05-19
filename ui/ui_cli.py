#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command Line Interface Implementation
"""

from typing import List, Dict, Any, Optional, Union
from fastmcp import Context
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import subprocess
import sys
import os
import tempfile
import json
import asyncio
import time
from lang_manager import get_text

END_MARKER = get_text("input_end_marker")
if END_MARKER == "NotDefined":
    END_MARKER = "END"
print("CLI END_MARKER", END_MARKER)
class CommandLineUI:
    """Command Line Interface Implementation Class"""
    
    def __init__(self):
        """Initialize command line interface"""
        self.console = Console()
    
    async def select_option(
        self,
        options: List[Union[str, Dict[str, Any]]],
        prompt: str = "Please select one of the following options",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Present a set of options to the user for selection by entering numbers or providing custom answers.
        Will pop up a new command line window to display options and get user input.

        Args:
            options: List of options, can be a list of strings or dictionaries
            prompt: Prompt message displayed to the user
            ctx: FastMCP context object

        Returns:
            Dictionary containing the selection result, in the format:
            {
                "selected_index": int,  # Index of the user's selection, -1 if custom answer
                "selected_option": Any,  # Content of the user's selected option
                "custom_input": str,    # User's custom input, if any
                "is_custom": bool       # Whether it's a custom answer
            }
        """
        if ctx:
            await ctx.info("Displaying options using command line interface...")
        
        try:
            # Create temporary data file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as data_file:
                data_path = data_file.name
                # Prepare text dictionary to pass to the temporary script
                ui_texts = {
                    'custom_input_tip': get_text('custom_input_tip'),
                    'input_option': get_text('input_option'),
                    'invalid_option': get_text('invalid_option'),
                    'custom_input': get_text('custom_input'),
                    'multiline_tip': get_text('multiline_tip'),
                    'end_marker': END_MARKER
                }
                
                # Write options and configuration to temporary file
                json.dump({
                    'options': options,
                    'prompt': prompt,
                    'allow_custom': True,  # 始终允许自定义输入
                    'ui_texts': ui_texts
                }, data_file)
            
            # Create temporary result file path
            result_path = f"{data_path}.result"
            
            # Create temporary script file
            script_content = """
import json
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def main():
    console = Console()
    
    # Read data file
    data_path = sys.argv[1]
    result_path = sys.argv[2]
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    options = data['options']
    prompt = data['prompt']
    allow_custom = data['allow_custom']
    ui_texts = data.get('ui_texts', {})
    end_marker = ui_texts.get('end_marker', 'END')
    
    # Format options
    formatted_options = []
    for i, option in enumerate(options, 1):
        if isinstance(option, dict):
            # If option is a dictionary, try to get title or description
            title = option.get("title", option.get("name", option.get("description", f"Option {i}")))
            description = option.get("description", "")
            formatted_option = f"{title}"
            if description:
                formatted_option += f"\\n   {description}"
            formatted_options.append(formatted_option)
        else:
            # If option is a string, use directly
            formatted_options.append(str(option))
    
    # Use Rich to display panel
    md_content = f"# {prompt}\\n\\n"
    for i, option in enumerate(formatted_options, 1):
        md_content += f"{i}. {option}\\n\\n"
    
    if allow_custom:
        md_content += f"*{ui_texts.get('custom_input_tip', 'Enter 0 to provide a custom answer')}*"
    
    console.print(Panel(Markdown(md_content), border_style="green"))
    
    # Get user input
    while True:
        try:
            user_choice = input(f"{ui_texts.get('input_option', 'Enter your choice')}: ").strip()
            
            # Handle custom input
            if user_choice == "0" and allow_custom:
                console.print(f"{ui_texts.get('custom_input', 'Enter your custom answer')}")
                console.print(f"{ui_texts.get('multiline_tip', 'You can enter multiple lines. Enter ' + end_marker + ' on a separate line to finish.')}")
                
                # Get multiline input
                input_lines = []
                while True:
                    line = input()
                    if line.strip() == end_marker:
                        break
                    input_lines.append(line)
                
                custom_input = "\\n".join(input_lines)
                
                user_input = {
                    "selected_index": -1,
                    "selected_option": None,
                    "custom_input": custom_input,
                    "is_custom": True
                }
                break
            
            # Handle numeric choice
            choice_index = int(user_choice) - 1
            if 0 <= choice_index < len(options):
                selected_option = options[choice_index]
                user_input = {
                    "selected_index": choice_index,
                    "selected_option": selected_option,
                    "custom_input": "",
                    "is_custom": False
                }
                break
            else:
                console.print(ui_texts.get('invalid_option', 'Invalid option, please try again'), style="bold red")
        except ValueError:
            console.print(ui_texts.get('invalid_option', 'Invalid option, please try again'), style="bold red")
    
    # Write result to file
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(user_input, f)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        data_path = sys.argv[1]
        result_path = sys.argv[2]
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(f"Error: {str(e)}", f)
    # 自动关闭窗口，不需要用户手动按回车
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as script_file:
                script_path = script_file.name
                script_file.write(script_content)
            
            if ctx:
                await ctx.info(f"Starting new command line window...")
            
            # Start new command line window to execute script
            if sys.platform == 'win32':
                # Windows platform
                cmd = f'start cmd /c "python {script_path} {data_path} {result_path}"'
                process = subprocess.Popen(cmd, shell=True)
            else:
                # Linux/Mac platform
                if sys.platform == 'darwin':  # macOS
                    cmd = ['osascript', '-e', f'tell app "Terminal" to do script "python {script_path} {data_path} {result_path}"']
                else:  # Linux
                    cmd = ['x-terminal-emulator', '-e', f'python {script_path} {data_path} {result_path}']
                process = subprocess.Popen(cmd)
            
            if ctx:
                await ctx.info(f"Waiting for user input in new window...")
            
            # Wait for user input in new window
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            
            # Wait for result file to appear
            while not os.path.exists(result_path):
                await asyncio.sleep(0.5)
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout waiting for user input")
            
            # Wait for file writing to complete
            await asyncio.sleep(0.5)
            
            # Read results
            with open(result_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Clean up temporary files
            try:
                os.remove(script_path)
                os.remove(data_path)
                os.remove(result_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to start new window: {str(e)}")
            
            # Fall back to original command line implementation
            self.console.print(f"Failed to start new window, falling back to current window: {str(e)}", style="bold red")
            
            # Display options
            md_content = f"# {prompt}\n\n"
            for i, option in enumerate(options, 1):
                if isinstance(option, dict):
                    title = option.get("title", option.get("name", option.get("description", f"Option {i}")))
                    description = option.get("description", "")
                    formatted_option = f"{title}"
                    if description:
                        formatted_option += f"\n   {description}"
                    md_content += f"{i}. {formatted_option}\n\n"
                else:
                    md_content += f"{i}. {option}\n\n"
            
            # 始终允许自定义输入
            md_content += f"*{get_text('custom_input_tip')}*"
            
            self.console.print(Panel(Markdown(md_content), border_style="green"))
            
            # Get user input
            while True:
                try:
                    user_choice = input(f"{get_text('input_option')}: ").strip()
                    
                    # Handle custom input - always allow custom input
                    if user_choice == "0":
                        self.console.print(f"{get_text('custom_input')}")
                        self.console.print(f"{get_text('multiline_tip')}")
                        
                        # Get multiline input
                        input_lines = []
                        while True:
                            line = input()
                            if line.strip() == END_MARKER:
                                break
                            input_lines.append(line)
                        
                        custom_input = "\n".join(input_lines)
                        
                        return {
                            "selected_index": -1,
                            "selected_option": None,
                            "custom_input": custom_input,
                            "is_custom": True
                        }
                    
                    # Handle numeric choice
                    choice_index = int(user_choice) - 1
                    if 0 <= choice_index < len(options):
                        selected_option = options[choice_index]
                        return {
                            "selected_index": choice_index,
                            "selected_option": selected_option,
                            "custom_input": "",
                            "is_custom": False
                        }
                    else:
                        self.console.print(get_text('invalid_option'), style="bold red")
                except ValueError:
                    self.console.print(get_text('invalid_option'), style="bold red")
    
    async def request_additional_info(
        self,
        prompt: str,
        current_info: str = "",
        ctx: Context = None
    ) -> str:
        """
        Request supplementary information from the user using CLI interface

        Args:
            prompt: Prompt message
            current_info: Current information
            ctx: FastMCP context

        Returns:
            User input information
        """
        if ctx:
            await ctx.info("Requesting information using command line interface...")
        
        try:
            # Create temporary data file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as data_file:
                data_path = data_file.name
                # Prepare text dictionary to pass to the temporary script
                ui_texts = {
                    'multiline_tip': get_text('multiline_tip'),
                    'current_info': get_text('current_info'),
                    'input_prompt': get_text('input_prompt'),
                    'end_marker': END_MARKER
                }
                
                # Write options and configuration to temporary file
                json.dump({
                    'prompt': prompt,
                    'current_info': current_info,
                    'ui_texts': ui_texts
                }, data_file)
            
            # Create temporary result file path
            result_path = f"{data_path}.result"
            
            # Create temporary script file
            script_content = """
import json
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def main():
    console = Console()
    
    # Read data file
    data_path = sys.argv[1]
    result_path = sys.argv[2]
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompt = data['prompt']
    current_info = data['current_info']
    ui_texts = data.get('ui_texts', {})
    end_marker = ui_texts.get('end_marker', 'END')
    
    # Build markdown content
    md_content = f"### {prompt}\\n\\n"
    if current_info:
        md_content += f"**{ui_texts.get('current_info', 'Current Information')}**:\\n\\n{current_info}\\n\\n"
    
    # Add multiline input tip
    md_content += f"\\n{ui_texts.get('multiline_tip', 'You can enter multiple lines. Enter ' + end_marker + ' on a separate line to finish.')}\\n"
    
    # Display content
    console.print(Markdown(md_content))
    
    # Get user input (multiline)
    print(f"{ui_texts.get('input_prompt', 'Input')}: ", end="", flush=True)
    
    input_lines = []
    while True:
        line = input()
        if line.strip() == end_marker:
            break
        input_lines.append(line)
    
    user_input = "\\n".join(input_lines)
    
    # Write result to file
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(user_input, f)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        data_path = sys.argv[1]
        result_path = sys.argv[2]
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(f"Error: {str(e)}", f)
    # 自动关闭窗口，不需要用户手动按回车
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as script_file:
                script_path = script_file.name
                script_file.write(script_content)
            
            if ctx:
                await ctx.info(f"Starting new command line window...")
            
            # Start new command line window to execute script
            if sys.platform == 'win32':
                # Windows platform
                cmd = f'start cmd /c "python {script_path} {data_path} {result_path}"'
                process = subprocess.Popen(cmd, shell=True)
            else:
                # Linux/Mac platform
                if sys.platform == 'darwin':  # macOS
                    cmd = ['osascript', '-e', f'tell app "Terminal" to do script "python {script_path} {data_path} {result_path}"']
                else:  # Linux
                    cmd = ['x-terminal-emulator', '-e', f'python {script_path} {data_path} {result_path}']
                process = subprocess.Popen(cmd)
            
            if ctx:
                await ctx.info(f"Waiting for user input in new window...")
            
            # Wait for user input in new window
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            
            # Wait for result file to appear
            while not os.path.exists(result_path):
                await asyncio.sleep(0.5)
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout waiting for user input")
            
            # Wait for file writing to complete
            await asyncio.sleep(0.5)
            
            # Read results
            with open(result_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Clean up temporary files
            try:
                os.remove(script_path)
                os.remove(data_path)
                os.remove(result_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to start new window: {str(e)}")
            
            # Fall back to original command line implementation
            self.console.print(f"Failed to start new window, falling back to current window: {str(e)}", style="bold red")
            
            # Build markdown content
            md_content = f"### {prompt}\n\n"
            if current_info:
                md_content += f"**{get_text('current_info')}**:\n\n{current_info}\n\n"
            
            # Add multiline input tip
            md_content += f"\n{get_text('multiline_tip')}\n"
            
            # Display content
            self.console.print(Markdown(md_content))
            
            # Get user input (multiline)
            print(f"{get_text('input_prompt')}: ", end="", flush=True)
            
            input_lines = []
            while True:
                line = input()
                if line.strip() == END_MARKER:
                    break
                input_lines.append(line)
            
            return "\n".join(input_lines)
