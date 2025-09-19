import os
from prompt_toolkit.completion import Completer, Completion
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class FileCompleter(Completer):
    """Custom completer that suggests files with @ prefix"""
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Check if we're in a load command with @
        if text.startswith('load @'):
            prefix = text[6:]  # Get text after 'load @'
            current_dir = os.getcwd()
            
            # Find all files and directories
            all_files = []
            for item in os.listdir(current_dir):
                if os.path.isfile(item) and item.startswith(prefix):
                    all_files.append(item)
            
            # Also check in subdirectories if no prefix or partial match
            if not prefix or len(all_files) < 5:
                for root, dirs, files in os.walk(current_dir):
                    for file in files:
                        if file.startswith(prefix):
                            rel_path = os.path.relpath(os.path.join(root, file), current_dir)
                            all_files.append(rel_path)
                    break  # Only first level for now
            
            # Remove duplicates and sort
            all_files = sorted(set(all_files))
            
            for file in all_files:
                yield Completion(file, start_position=-len(prefix))

class FileManager:
    def __init__(self):
        self.current_file = None
        self.file_content = None
        self.completer = FileCompleter()
    
    def get_completer(self):
        return self.completer
    
    def load_file(self, load_arg):
        """Process load command with @ prefix support and auto-create if file doesn't exist"""
        if load_arg.startswith('@'):
            # Remove @ prefix and use as filter
            prefix = load_arg[1:]
            current_dir = os.getcwd()
            
            # Find files starting with prefix
            matching_files = []
            for item in os.listdir(current_dir):
                if os.path.isfile(item) and item.startswith(prefix):
                    matching_files.append(item)
            
            if not matching_files:
                console.print(f"[yellow]⚠ No files found starting with '{prefix}'[/yellow]")
                return None, None
            
            if len(matching_files) == 1:
                # Auto-select if only one match
                selected_file = matching_files[0]
                console.print(f"[cyan]📁 Auto-selected: {selected_file}[/cyan]")
            else:
                # Show selection menu
                console.print("[cyan]📁 Matching files:[/cyan]")
                for i, file in enumerate(matching_files, 1):
                    console.print(f"  {i}. {file}")
                
                try:
                    choice = console.input("[cyan]Select file number (or Enter to cancel): [/cyan]").strip()
                    if not choice:
                        return None, None
                    selected_file = matching_files[int(choice) - 1]
                except (ValueError, IndexError):
                    console.print("[red]❌ Invalid selection[/red]")
                    return None, None
            
            path = selected_file
        else:
            path = load_arg
        
        # Check if file exists
        if not os.path.exists(path):
            # File doesn't exist, ask to create it
            console.print(f"[yellow]⚠ File '{path}' doesn't exist.[/yellow]")
            if Confirm.ask(f"[cyan]Create new file '{path}'?[/cyan]", default=True):
                try:
                    # Create directory if needed (only if path contains subdirectories)
                    dir_path = os.path.dirname(path)
                    if dir_path and not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        console.print(f"[cyan]📁 Created directory: {dir_path}[/cyan]")
                    
                    # Create empty file
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("# New file created by AI Code Assistant\n\n")
                    
                    console.print(f"[green]✅ Created new file: '{path}'[/green]")
                    return path, "# New file created by AI Code Assistant\n\n"
                except Exception as e:
                    console.print(f"[red]❌ Error creating file: {str(e)}[/red]")
                    return None, None
            else:
                console.print("[yellow]File creation cancelled.[/yellow]")
                return None, None
        
        # File exists, load it
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            console.print(f"[green]✅ File '{path}' loaded.[/green]")
            console.print(f"[cyan]📄 File size: {len(content)} characters[/cyan]")
            return path, content
        except Exception as e:
            console.print(f"[red]❌ Error loading file: {str(e)}[/red]")
            return None, None
    
    def save_file(self, content):
        """Save content to current file"""
        if not self.current_file:
            console.print("[yellow]⚠ No file loaded.[/yellow]")
            return False
        
        try:
            # Create directory if it doesn't exist (only if path contains subdirectories)
            dir_path = os.path.dirname(self.current_file)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                console.print(f"[cyan]📁 Created directory: {dir_path}[/cyan]")
            
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[bold green]💾 Changes saved to '{self.current_file}'.[/bold green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error saving file: {str(e)}[/red]")
            return False
    
    def clear_file(self):
        """Clear current file from memory"""
        if self.current_file:
            console.print(f"[yellow]🗑️ Cleared file: {self.current_file}[/yellow]")
            self.current_file = None
            self.file_content = None
        else:
            console.print("[yellow]⚠ No file loaded.[/yellow]")
    
    def create_new_file(self, file_path, initial_content="# New file\n\n"):
        """Create a new file with optional initial content"""
        try:
            # Create directory if needed (only if path contains subdirectories)
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                console.print(f"[cyan]📁 Created directory: {dir_path}[/cyan]")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(initial_content)
            
            console.print(f"[green]✅ Created new file: '{file_path}'[/green]")
            return file_path, initial_content
        except Exception as e:
            console.print(f"[red]❌ Error creating file: {str(e)}[/red]")
            return None, None