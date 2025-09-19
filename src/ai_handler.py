from llama_cpp import Llama
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
import sys
import re

console = Console()
load_dotenv()

class AIHandler:
    def __init__(self):
        model_path = os.getenv("MODEL_PATH", "models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf")
        
        # Check if model file exists
        if not os.path.exists(model_path):
            console.print(f"[red]❌ Model file not found: {model_path}[/red]")
            console.print("[yellow]Please download a GGUF model and place it in the models/ directory[/yellow]")
            console.print("[cyan]Example commands to download a model:[/cyan]")
            console.print("mkdir -p models")
            console.print("wget -P models/ https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf")
            console.print("\n[green]Or use a different model from: https://huggingface.co/TheBloke[/green]")
            sys.exit(1)
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=int(os.getenv("N_CTX", 4096)),
                n_threads=int(os.getenv("N_THREADS", 4)),
                n_gpu_layers=int(os.getenv("N_GPU_LAYERS", 30)),
                chat_format=os.getenv("CHAT_FORMAT", "chatml")
            )
            # console.print(f"[green]✅ Model loaded successfully: {os.path.basename(model_path)}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Error loading model: {str(e)}[/red]")
            sys.exit(1)
    
    def chat(self, prompt, is_code_context=False, current_code=None):
        """Chat with the AI in general purpose mode"""
        
        if is_code_context and current_code:
            # Code editing mode
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Python programmer. Modify the given code according to the user's instruction. Return ONLY the complete updated Python code with no explanations, no markdown, and no additional text. Just the pure executable Python code.",
                },
                {
                    "role": "user",
                    "content": f"Current code:\n```python\n{current_code}\n```\n\nInstruction: {prompt}\n\nReturn ONLY the complete updated Python code:",
                },
            ]
            temperature = 0.1
        else:
            # General chat mode
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Provide clear, concise, and helpful responses to the user's questions and requests.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
            temperature = 0.7

        try:
            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=temperature,
                stop=["<|im_end|>", "###", "Instruction:", "User:"]
            )
            return output["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def chat_stream(self, prompt, is_code_context=False, current_code=None, callback=None):
        """Stream chat response with real-time updates"""
        
        if is_code_context and current_code:
            # Code editing mode
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Python programmer. Modify the given code according to the user's instruction. Return ONLY the complete updated Python code with no explanations, no markdown, and no additional text. Just the pure executable Python code.",
                },
                {
                    "role": "user",
                    "content": f"Current code:\n```python\n{current_code}\n```\n\nInstruction: {prompt}\n\nReturn ONLY the complete updated Python code:",
                },
            ]
            temperature = 0.1
        else:
            # General chat mode
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Provide clear, concise, and helpful responses to the user's questions and requests.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
            temperature = 0.7

        try:
            full_response = ""
            stream = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=temperature,
                stop=["<|im_end|>", "###", "Instruction:", "User:"],
                stream=True
            )
            
            for output in stream:
                if "content" in output["choices"][0]["delta"]:
                    token = output["choices"][0]["delta"]["content"]
                    full_response += token
                    if callback:
                        callback(full_response)
            
            return full_response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"