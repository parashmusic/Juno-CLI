import os
from prompt_toolkit.completion import Completer, Completion
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class FileCompleter(Completer):
    """Custom completer that suggests files with @ prefix and handles nested directories"""
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Check if we're in a load command with @
        if text.startswith('load @'):
            prefix = text[6:]  # Get text after 'load @'
            current_dir = os.getcwd()
            
            # Find all files and directories recursively
            all_files = []
            all_dirs = []
            
            # Walk through all directories recursively
            for root, dirs, files in os.walk(current_dir):
                # Get relative path from current directory
                rel_root = os.path.relpath(root, current_dir)
                
                # Add files that match the prefix
                for file in files:
                    if file.startswith(prefix):
                        if rel_root == '.':
                            file_path = file
                        else:
                            file_path = os.path.join(rel_root, file)
                        all_files.append(file_path)
                
                # Add directories that match the prefix (for navigation)
                for dir_name in dirs:
                    if dir_name.startswith(prefix):
                        if rel_root == '.':
                            dir_path = dir_name + os.sep
                        else:
                            dir_path = os.path.join(rel_root, dir_name) + os.sep
                        all_dirs.append(dir_path)
            
            # Combine and sort files and directories
            all_items = sorted(all_dirs + all_files)
            
            for item in all_items:
                yield Completion(item, start_position=-len(prefix))
        
        # Also provide regular path completion without @
        elif text.startswith('load '):
            path_text = text[5:]
            if not path_text.startswith('@'):
                # Basic path completion for regular load commands
                current_dir = os.getcwd()
                if not path_text:
                    # Show all files and directories in current directory
                    for item in os.listdir(current_dir):
                        if os.path.isdir(item):
                            yield Completion(item + os.sep, start_position=0)
                        else:
                            yield Completion(item, start_position=0)
                else:
                    # Handle partial paths
                    if os.path.isdir(path_text):
                        # Show contents of the directory
                        for item in os.listdir(path_text):
                            full_path = os.path.join(path_text, item)
                            if os.path.isdir(full_path):
                                yield Completion(full_path + os.sep, start_position=-len(path_text))
                            else:
                                yield Completion(full_path, start_position=-len(path_text))

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
            
            # Find files starting with prefix (recursively)
            matching_files = []
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if file.startswith(prefix):
                        rel_path = os.path.relpath(os.path.join(root, file), current_dir)
                        matching_files.append(rel_path)
            
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
        
        # Check if it's a directory
        if os.path.isdir(path):
            console.print(f"[yellow]⚠ '{path}' is a directory, not a file.[/yellow]")
            console.print("[cyan]📁 Directory contents:[/cyan]")
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    console.print(f"  📁 {item}/")
                else:
                    console.print(f"  📄 {item}")
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
    
    def list_directory_contents(self, path="."):
        """List contents of a directory"""
        if not os.path.exists(path):
            console.print(f"[red]❌ Path '{path}' doesn't exist.[/red]")
            return
        
        if not os.path.isdir(path):
            console.print(f"[yellow]⚠ '{path}' is not a directory.[/yellow]")
            return
        
        console.print(f"[cyan]📁 Contents of '{path}':[/cyan]")
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                console.print(f"  📁 {item}/")
            else:
                console.print(f"  📄 {item}")