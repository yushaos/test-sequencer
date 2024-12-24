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
        
        # Load config
        with open('startupGUI_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
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
            
            # Create style for fixed-size buttons
            button_style = ttk.Style()
            button_style.configure('Fixed.TButton', width=15)  # Set fixed width in characters
            
            # Create buttons
            for idx, item in enumerate(items):
                row = idx // 5
                col = idx % 5
                
                btn = ttk.Button(
                    tab_frame,
                    text=item['name'],
                    command=lambda i=item: self.launch_item(i),
                    style='Fixed.TButton'  # Apply the fixed-size style
                )
                btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew', ipadx=20, ipady=10)  # Add internal padding
    
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

def main():
    root = tk.Tk()
    root.geometry("800x400")  # Set initial window size
    app = StartupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 