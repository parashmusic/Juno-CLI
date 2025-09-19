from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
import re

console = Console()

def show_banner():
    console.print(
        Panel.fit(
            "[bold magenta]⚡JUNO AI Assistant ⚡[/bold magenta]\n"
            "[cyan]CLI code assist agent for your projects  [/cyan]\n"
            "[yellow]Type 'help' for commands, 'quit' to exit[/yellow]\n"
            "[green]Tip: Use 'load @' + tab for file suggestions[/green]",
            title="[green]Multi-Mode AI CLI[/green]",
            border_style="magenta",
        )
    )

def show_help():
    table = Table(title="Available Commands", show_header=True, header_style="bold blue")
    table.add_column("Command", style="yellow", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("load <file_path> or @<prefix>", "Load a file to work with")
    # table.add_row("load ", "Show files starting with prefix (press Tab)")
    table.add_row("save", "Save changes to the current file")
    table.add_row("show", "Show the current file content")
    table.add_row("edit <instruction>", "Update the file using AI (file must be loaded)")
    table.add_row("clear", "Clear the current file from memory")
    table.add_row("help", "Show this help message")
    table.add_row("quit", "Exit the program")
    # table.add_row("<any other text>", "Chat with the AI (general purpose)")

    console.print(table)
    # console.print("\n[bold]Usage:[/bold]")
    # console.print("- Load a file first to use code editing features")
    # console.print("- Type anything else to chat with the AI normally")
    # console.print("- Use 'load @prefix' + Tab to see file suggestions")

def extract_pure_code(text):
    """Extract only the code from the model's response, removing explanations and markdown"""
    
    # Remove markdown code blocks
    if "```" in text:
        code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', text, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
    
    # If no markdown, try to find the actual code part
    lines = text.split('\n')
    code_lines = []
    
    for line in lines:
        # Look for lines that contain Python code patterns
        if (line.strip().startswith(('#', 'def ', 'import ', 'from ', 'class ')) or
            '=' in line or ':' in line or '(' in line or ')' in line or
            'return ' in line or 'print(' in line):
            code_lines.append(line)
        # Skip empty lines at the beginning
        elif code_lines and not line.strip():
            code_lines.append(line)
        # Skip explanatory text
        elif not code_lines and not line.strip():
            continue
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    # Fallback: return the original text but clean it up
    return text.strip()