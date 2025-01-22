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
        
        # Set program icon
        icon_path = r"C:\Users\yusha\Desktop\test sequencer\utility\data_process\MeasurementIcon.ico"
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # Set font sizes for GUI
        self.font_size = 12  # User can modify this value
        self.header_font_size = self.font_size
        self.value_font_size = self.font_size + 1
        
        self.default_font = ('TkDefaultFont', self.font_size)
        self.header_font = ('TkDefaultFont', self.header_font_size)
        self.value_font = ('TkDefaultFont', self.value_font_size)
        
        # Set table column width
        self.column_width = 130  # User can modify this value
        
        # Configure styles with font
        style = ttk.Style()
        style.configure('TLabel', font=self.default_font)
        style.configure('TButton', font=self.default_font)
        style.configure('TEntry', font=self.default_font)
        style.configure('Treeview', font=self.value_font)
        style.configure('Treeview.Heading', font=self.header_font)
        
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
        
        # Prepopulate table with empty columns
        self.initialize_table()

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
        
        # Add status label
        self.run_status = ttk.Label(run_frame, text="Ready")
        self.run_status.grid(row=0, column=1, padx=5)
        
        # Results summary frame
        self.summary_frame = ttk.Frame(run_frame)
        self.summary_frame.grid(row=0, column=2, padx=20)
        
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
        
        # Configure style for header and value rows
        style = ttk.Style()
        style.configure("Header.Treeview", font=self.header_font)
        style.configure("Value.Treeview", font=self.value_font)
        style.configure("Header.Treeview.Row", background="gray25", foreground="white")
        style.configure("Failed.Treeview.Row", background="yellow")
        
        # Configure columns with new order
        base_columns = ["Status", "req_id", "channel_name", "Result", "low_limit", "high_limit"]
        excluded_columns = ["Group"]  # Columns to skip
        
        # Add remaining config columns
        remaining_columns = [f"col{i}" for i in range(1, 16)]  # Padding columns
        columns = base_columns + remaining_columns
        self.tree.configure(columns=columns)
        
        # Configure each column with fixed width and center alignment
        for col in columns:
            self.tree.column(col, width=self.column_width, minwidth=self.column_width, stretch=False, anchor='center')
            self.tree.heading(col, text="")
        
        # Add results to table
        for req, (req_id, func_name, result) in zip(config["test_requirements"], results):
            # Create header values with new order
            headers = ["Status", "req_id", "channel_name", "Result", "low_limit", "high_limit"]
            
            # Add remaining headers except excluded ones
            for key in req.keys():
                if key not in headers and key not in excluded_columns:
                    headers.append(key)
            
            # Pad headers list to match number of columns
            headers.extend([""] * (len(columns) - len(headers)))
            
            # Insert header row with dark gray background and white text
            header_item = self.tree.insert("", "end", values=headers, tags=("header",))
            self.tree.tag_configure("header", background="gray25", foreground="white")
            
            # Determine result status and value
            if isinstance(result, tuple):
                status = "PASS" if result[0] else "FAIL"
                result_value = str(result[1])
            else:
                status = "ERROR"
                result_value = str(result)
            
            # Create values list with new order
            values = [status]  # Status
            values.append(req.get("req_id", ""))  # req_id
            values.append(req.get("channel_name", ""))  # channel_name
            values.append(result_value)  # Result
            values.append(str(req.get("low_limit", "")))  # low_limit
            values.append(str(req.get("high_limit", "")))  # high_limit
            
            # Add remaining values except excluded ones
            for key in req.keys():
                if key not in ["req_id", "channel_name", "low_limit", "high_limit", "Group"]:
                    values.append(str(req.get(key, "")))
            
            # Pad values list to match number of columns
            values.extend([""] * (len(columns) - len(values)))
            
            # Insert value row with conditional highlighting
            value_item = self.tree.insert("", "end", values=values, tags=("value",))
            self.tree.tag_configure("value", font=self.value_font)  # Apply larger font to value rows
            if status != "PASS":
                self.tree.tag_configure("failed", background="yellow", font=self.value_font)
                self.tree.item(value_item, tags=("failed",))

    def run_process(self):
        tdms_path = self.tdms_entry.get()
        config_path = self.config_entry.get()
        
        if not os.path.exists(tdms_path) or not os.path.exists(config_path):
            tk.messagebox.showerror("Error", "Invalid file paths")
            return
            
        try:
            # Update status to Running
            self.run_status.configure(text="Running...")
            self.root.update()  # Force GUI update
            
            # Load config
            with open(config_path) as f:
                config = json.load(f)
            
            # Process requirements
            with Pool(processes=cpu_count()) as pool:
                dpm.tdms_file = TdmsFile(tdms_path)
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
        finally:
            # Reset status to Ready
            self.run_status.configure(text="Ready")

    def initialize_table(self):
        # Configure base columns with new order
        base_columns = ["Status", "req_id", "channel_name", "Result", "low_limit", "high_limit"]
        remaining_columns = [f"col{i}" for i in range(1, 16)]  # Padding columns
        columns = base_columns + remaining_columns
        self.tree.configure(columns=columns)
        
        # Configure each column with fixed width and center alignment
        for col in columns:
            self.tree.column(col, width=self.column_width, minwidth=self.column_width, stretch=False, anchor='center')
            self.tree.heading(col, text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataProcessGUI(root)
    root.mainloop() 