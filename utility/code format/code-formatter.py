import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

class CodeFormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Code Formatter")
        
        # Configure main window
        self.root.geometry("1000x600")
        
        # Create main container
        main_container = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create left frame
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        # Create right frame
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # Left panel components
        ttk.Label(left_frame, text="Input Code:").pack(anchor=tk.W, pady=(0, 5))
        self.input_text = ScrolledText(left_frame, wrap=tk.NONE, height=30)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel components
        ttk.Label(right_frame, text="Formatted Code:").pack(anchor=tk.W, pady=(0, 5))
        self.output_text = ScrolledText(right_frame, wrap=tk.NONE, height=30)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Create buttons frame
        buttons_frame = ttk.Frame(root)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons
        ttk.Button(buttons_frame, text="Format Code", command=self.format_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Copy Formatted", command=self.copy_formatted).pack(side=tk.LEFT, padx=5)
        
    def format_code(self):
        try:
            # Get input code
            input_code = self.input_text.get("1.0", tk.END)
            
            # Format the code
            formatted_lines = []
            for line in input_code.splitlines():
                # Keep only non-empty lines (lines with actual content)
                if line.strip():
                    formatted_lines.append(line.rstrip())
            
            # Join the formatted lines
            formatted_code = "\n".join(formatted_lines)
            
            # Clear the output text and insert formatted code
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", formatted_code)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while formatting: {str(e)}")
    
    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
    
    def copy_formatted(self):
        formatted_code = self.output_text.get("1.0", tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(formatted_code)
        messagebox.showinfo("Success", "Formatted code copied to clipboard!")

def main():
    root = tk.Tk()
    app = CodeFormatterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
