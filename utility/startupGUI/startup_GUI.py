import json
import tkinter as tk
from tkinter import ttk
import subprocess
import os
from pathlib import Path

class StartupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Startup GUI")
        
        # Configuration variables
        self.BUTTON_FONT_SIZE = 15  # Adjust this value to change font size
        self.BUTTON_WIDTH = 15      # Characters per line for wrapping
        
        # Load config
        with open('startupGUI_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Create custom style
        self.style = ttk.Style()
        self.style.configure(
            'Fixed.TButton',
            width=self.BUTTON_WIDTH,
            wraplength=120,  # Pixels for text wrapping
            font=('TkDefaultFont', self.BUTTON_FONT_SIZE),
            justify='center',  # Center align text
            anchor='center'    # Center the text block in button
        )
        
        # Create tabs and buttons
        self.create_tabs()
        
    def create_tabs(self):
        for tab_name, items in self.config.items():
            # Create frame for this tab
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            
            # Configure grid
            for i in range(4):  # 4 rows
                tab_frame.grid_rowconfigure(i, weight=1)
            for i in range(5):  # 5 columns
                tab_frame.grid_columnconfigure(i, weight=1)
            
            # Create buttons
            for idx, item in enumerate(items):
                row = idx // 5
                col = idx % 5
                
                btn = ttk.Button(
                    tab_frame,
                    text=self.wrap_text(item['name']),
                    command=lambda i=item: self.launch_item(i),
                    style='Fixed.TButton'
                )
                btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew', ipadx=20, ipady=10)
    
    def launch_item(self, item):
        path = item['path']
        item_type = item['type']
        
        if item_type == 'explorer':
            os.startfile(path)
            
        elif item_type == 'python':
            anaconda_python = r"C:\ProgramData\anaconda3\python.exe"
            subprocess.Popen([anaconda_python, path])
            
        elif item_type == 'exe':
            subprocess.Popen([path])

    def wrap_text(self, text):
        """Helper function to add newlines for long text"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > self.BUTTON_WIDTH:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)

def main():
    root = tk.Tk()
    root.geometry("800x400")  # Set initial window size
    app = StartupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 