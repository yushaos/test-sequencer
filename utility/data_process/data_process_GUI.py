import tkinter as tk
from tkinter import ttk, filedialog
from nptdms import TdmsFile
import json
import data_process_main as dpm
from multiprocessing import Pool, cpu_count
import os

class DataProcessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Process GUI")
        
        # Make window fullscreen
        self.root.state('zoomed')
        
        # Configure root window to expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection frame
        self.create_file_selection_frame()
        
        # Run button and results frame
        self.create_run_frame()
        
        # Results table
        self.create_results_table()
        
        # Initialize variables
        self.tdms_file_path = tk.StringVar()
        self.config_file_path = tk.StringVar()
        self.results = []

    def create_file_selection_frame(self):
        # TDMS file selection
        ttk.Label(self.main_frame, text="TDMS File:").grid(row=0, column=0, sticky=tk.W)
        self.tdms_entry = ttk.Entry(self.main_frame, width=100)
        self.tdms_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(self.main_frame, text="TDMS File", command=self.select_tdms).grid(row=0, column=2, padx=5)

        # Config file selection
        ttk.Label(self.main_frame, text="Config File:").grid(row=1, column=0, sticky=tk.W)
        self.config_entry = ttk.Entry(self.main_frame, width=100)
        self.config_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        ttk.Button(self.main_frame, text="Measurement Config", command=self.select_config).grid(row=1, column=2, padx=5)

    def create_run_frame(self):
        run_frame = ttk.Frame(self.main_frame)
        run_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(run_frame, text="RUN", command=self.run_process).grid(row=0, column=0, padx=5)
        
        # Results summary frame
        self.summary_frame = ttk.Frame(run_frame)
        self.summary_frame.grid(row=0, column=1, padx=20)
        
        self.pass_count = ttk.Label(self.summary_frame, text="Pass: 0")
        self.pass_count.grid(row=0, column=0, padx=5)
        
        self.fail_count = ttk.Label(self.summary_frame, text="Fail: 0")
        self.fail_count.grid(row=0, column=1, padx=5)
        
        self.total_count = ttk.Label(self.summary_frame, text="Total: 0")
        self.total_count.grid(row=0, column=2, padx=5)
        
        # Status LED
        self.status_frame = ttk.Frame(self.summary_frame)
        self.status_frame.grid(row=0, column=3, padx=20)
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20)
        self.status_canvas.grid(row=0, column=0)
        self.status_label = ttk.Label(self.status_frame, text="Not Run")
        self.status_label.grid(row=0, column=1, padx=5)
        self.draw_led("gray")

    def create_results_table(self):
        # Configure main frame to expand
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create table frame with scrollbars
        table_frame = ttk.Frame(self.main_frame)
        table_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure table frame to expand
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(table_frame, show='headings')
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout with proper sticky settings
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))

    def select_tdms(self):
        filename = filedialog.askopenfilename(filetypes=[("TDMS files", "*.tdms")])
        if filename:
            self.tdms_entry.delete(0, tk.END)
            self.tdms_entry.insert(0, filename)

    def select_config(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, filename)

    def draw_led(self, color):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black")

    def update_results_table(self, config, results):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Configure multiple columns instead of single column
        columns = ["col1", "col2", "col3", "col4", "col5", "col6", "col7", "col8", "col9", "col10", 
                  "col11", "col12", "col13", "col14", "col15"]  # Add more if needed
        self.tree.configure(columns=columns)
        
        # Configure each column with fixed width and center alignment
        for col in columns:
            self.tree.column(col, width=120, anchor='center')
            self.tree.heading(col, text="")
        
        # Style for different row types
        style = ttk.Style()
        style.configure("Header.Treeview.Row", background="gray90")
        style.configure("Failed.Treeview.Row", background="yellow")
        
        # Add results to table
        for req, (req_id, func_name, result) in zip(config["test_requirements"], results):
            # Create header values
            headers = list(req.keys())
            # Pad headers list to match number of columns
            headers.extend([""] * (len(columns) - len(headers)))
            
            # Insert header row with gray background
            header_item = self.tree.insert("", "end", values=headers, tags=("header",))
            self.tree.tag_configure("header", background="gray90")
            
            # Create values list
            values = [str(value) for value in req.values()]
            # Pad values list to match number of columns
            values.extend([""] * (len(columns) - len(values)))
            
            # Determine result status
            if isinstance(result, tuple):
                status = "PASS" if result[0] else "FAIL"
                result_value = str(result[1])
            else:
                status = "ERROR"
                result_value = str(result)
            
            # Insert value row with conditional highlighting
            value_item = self.tree.insert("", "end", values=values)
            if status != "PASS":
                self.tree.tag_configure("failed", background="yellow")
                self.tree.item(value_item, tags=("failed",))

    def run_process(self):
        tdms_path = self.tdms_entry.get()
        config_path = self.config_entry.get()
        
        if not os.path.exists(tdms_path) or not os.path.exists(config_path):
            tk.messagebox.showerror("Error", "Invalid file paths")
            return
            
        try:
            # Load config
            with open(config_path) as f:
                config = json.load(f)
            
            # Process requirements
            with Pool(processes=cpu_count()) as pool:
                dpm.tdms_file = TdmsFile(tdms_path)  # Set the tdms_file for processing
                results = pool.map(dpm.process_requirement, config["test_requirements"])
            
            # Update results display
            pass_count = sum(1 for _, _, r in results if isinstance(r, tuple) and r[0])
            fail_count = len(results) - pass_count
            
            self.pass_count.configure(text=f"Pass: {pass_count}")
            self.fail_count.configure(text=f"Fail: {fail_count}")
            self.total_count.configure(text=f"Total: {len(results)}")
            
            if fail_count == 0:
                self.draw_led("green")
                self.status_label.configure(text="All Pass")
            else:
                self.draw_led("red")
                self.status_label.configure(text="Failed")
            
            # Update results table
            self.update_results_table(config, results)
            
        except Exception as e:
            tk.messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = DataProcessGUI(root)
    root.mainloop() 