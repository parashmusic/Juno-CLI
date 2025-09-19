from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from prompt_toolkit import PromptSession
from ai_handler import AIHandler
from file_manager import FileManager
from utils import show_banner, show_help, extract_pure_code
import re
import time

console = Console()

class AICodeAssistant:
    def __init__(self):
        self.ai_handler = AIHandler()
        self.file_manager = FileManager()
        self.session = PromptSession(completer=self.file_manager.get_completer())
        
    def run(self):
        show_banner()
        show_help()
        
        while True:
            try:
                user_input = self.session.prompt("You: ").strip()
                if not user_input:
                    continue
                    
                self.process_command(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[red]Exiting...[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    def process_command(self, user_input):
        # Exit
        if user_input.lower() == "quit":
            console.print("[bold red]👋 Goodbye![/bold red]")
            exit()
        
        # Show help
        elif user_input.lower() == "help":
            show_help()
        
        # Clear current file
        elif user_input.lower() == "clear":
            self.file_manager.clear_file()
        
        # Load a file
        elif user_input.startswith("load "):
            load_arg = user_input[5:].strip()
            new_file, new_content = self.file_manager.load_file(load_arg)
            if new_file:
                self.file_manager.current_file = new_file
                self.file_manager.file_content = new_content
        
        # Show current content
        elif user_input == "show":
            if self.file_manager.file_content is None:
                console.print("[yellow]⚠ No file loaded.[/yellow]")
            else:
                syntax = Syntax(self.file_manager.file_content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Current File: {self.file_manager.current_file}", border_style="cyan"))
        
        # Save changes
        elif user_input == "save":
            if self.file_manager.file_content:
                self.file_manager.save_file(self.file_manager.file_content)
            else:
                console.print("[yellow]⚠ No file loaded.[/yellow]")
        
        # Edit with instruction (with streaming)
        elif user_input.startswith("edit "):
            if self.file_manager.file_content is None:
                console.print("[yellow]⚠ No file loaded. Use 'load <file>' first or just type your question.[/yellow]")
                return
            
            instruction = user_input.split(" ", 1)[1]
            console.print("[cyan]⏳ Thinking about code changes...[/cyan]")
            
            # Use streaming for code editing
            def update_display(current_text):
                # Clean the text to extract only code
                clean_text = self.clean_streaming_output(current_text)
                syntax = Syntax(clean_text, "python", theme="monokai", line_numbers=True)
                return Panel(syntax, title="🔄 AI is writing code...", border_style="yellow")
            
            full_response = ""
            try:
                with Live(update_display(""), refresh_per_second=4, vertical_overflow="visible", transient=True) as live:
                    def streaming_callback(text):
                        nonlocal full_response
                        full_response = text
                        live.update(update_display(text))
                    
                    response = self.ai_handler.chat_stream(
                        instruction, 
                        is_code_context=True, 
                        current_code=self.file_manager.file_content,
                        callback=streaming_callback
                    )
            except Exception as e:
                console.print(f"[red]❌ Error during streaming: {str(e)}[/red]")
                return
            
            # Clear the live display area by printing empty lines
            console.print("\n" * 2)  # Add some space
            
            # Extract only the code part for file content
            pure_code = extract_pure_code(full_response)
            
            if pure_code:
                self.file_manager.file_content = pure_code
                syntax = Syntax(self.file_manager.file_content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="✅ Updated Code", border_style="green"))
                console.print(f"[green]Code length: {len(self.file_manager.file_content)} characters[/green]")
            else:
                console.print("[red]❌ Could not extract valid code from response[/red]")
                console.print(f"AI response: {full_response}")
        
        # General AI chat mode (with streaming)
        else:
            if self.file_manager.current_file:
                console.print("[yellow]💡 Tip: You have a file loaded. Use 'edit' for code changes or 'clear' to remove the file.[/yellow]")
            
            console.print("[cyan]⏳ Thinking...[/cyan]")
            
            # Use streaming for general chat
            def update_chat_display(current_text):
                return Panel.fit(
                    current_text,
                    title="🤖 AI is thinking...",
                    border_style="blue",
                    subtitle="Type 'help' for commands" if not self.file_manager.current_file else f"File: {self.file_manager.current_file}"
                )
            
            full_response = ""
            try:
                with Live(update_chat_display(""), refresh_per_second=4, vertical_overflow="visible", transient=True) as live:
                    def streaming_callback(text):
                        nonlocal full_response
                        full_response = text
                        live.update(update_chat_display(text))
                    
                    response = self.ai_handler.chat_stream(
                        user_input, 
                        is_code_context=False,
                        callback=streaming_callback
                    )
            except Exception as e:
                console.print(f"[red]❌ Error during streaming: {str(e)}[/red]")
                return
            
            # Clear the live display area
            console.print("\n" * 2)  # Add some space
            
            # Display the final response in a nice panel
            console.print(
                Panel.fit(
                    full_response,
                    title="🤖 AI Response",
                    border_style="blue",
                    subtitle="Type 'help' for commands" if not self.file_manager.current_file else f"File: {self.file_manager.current_file}"
                )
            )
    
    def clean_streaming_output(self, text):
        """Clean streaming output to extract only code"""
        # Remove markdown code blocks if present
        if "```" in text:
            # Extract content between first and last ```
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

def main():
    assistant = AICodeAssistant()
    assistant.run()

if __name__ == "__main__":
    main()