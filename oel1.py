import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import uuid

class FileSystem:
    def __init__(self, data_file="sample.dat"):
        self.data_file = data_file
        self.current_dir = "/"
        self.fs_structure = {
            "/": {"type": "directory", "contents": {}, "created": str(datetime.now())}
        }
        self.open_files = {}  # Tracks open file objects
        self.memory_map = {}  # Tracks file data blocks
        self.load_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump({"structure": self.fs_structure, "memory_map": self.memory_map}, f)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.fs_structure = data["structure"]
                self.memory_map = data.get("memory_map", {})

    def get_full_path(self, name):
        if name.startswith("/"):
            return name
        return os.path.join(self.current_dir, name).replace("\\", "/")

    def create(self, fName):
        full_path = self.get_full_path(fName)
        parent_path = os.path.dirname(full_path)
        fname = os.path.basename(full_path)

        parent = self.get_directory(parent_path)
        if not parent:
            return "Parent directory does not exist"
        if fname in parent["contents"]:
            return "File/directory already exists"

        parent["contents"][fname] = {
            "type": "file",
            "size": 0,
            "created": str(datetime.now()),
            "data_id": str(uuid.uuid4())
        }
        self.memory_map[parent["contents"][fname]["data_id"]] = ""
        self.save_data()
        return f"File {fName} created"

    def delete(self, fName):
        full_path = self.get_full_path(fName)
        parent_path = os.path.dirname(full_path)
        fname = os.path.basename(full_path)

        parent = self.get_directory(parent_path)
        if not parent or fname not in parent["contents"]:
            return "File/directory does not exist"

        if parent["contents"][fname]["type"] == "file":
            data_id = parent["contents"][fname]["data_id"]
            del self.memory_map[data_id]
        del parent["contents"][fname]
        self.save_data()
        return f"{fName} deleted"

    def mkdir(self, dirName):
        full_path = self.get_full_path(dirName)
        parent_path = os.path.dirname(full_path)
        dirname = os.path.basename(full_path)

        parent = self.get_directory(parent_path)
        if not parent:
            return "Parent directory does not exist"
        if dirname in parent["contents"]:
            return "Directory already exists"

        parent["contents"][dirname] = {
            "type": "directory",
            "contents": {},
            "created": str(datetime.now())
        }
        self.save_data()
        return f"Directory {dirName} created"

    def chdir(self, dirName):
        full_path = self.get_full_path(dirName)
        directory = self.get_directory(full_path)
        if not directory or directory["type"] != "directory":
            return "Directory does not exist"
        self.current_dir = full_path
        return f"Changed to {dirName}"

    def move(self, source_fName, target_fName):
        source_path = self.get_full_path(source_fName)
        target_path = self.get_full_path(target_fName)
        source_parent = os.path.dirname(source_path)
        target_parent = os.path.dirname(target_path)
        source_name = os.path.basename(source_path)
        target_name = os.path.basename(target_path)

        src_parent = self.get_directory(source_parent)
        tgt_parent = self.get_directory(target_parent)

        if not src_parent or source_name not in src_parent["contents"]:
            return "Source does not exist"
        if not tgt_parent:
            return "Target directory does not exist"
        if target_name in tgt_parent["contents"]:
            return "Target already exists"

        tgt_parent["contents"][target_name] = src_parent["contents"][source_name]
        del src_parent["contents"][source_name]
        self.save_data()
        return f"Moved {source_fName} to {target_fName}"

    def get_directory(self, path):
        if path == "/":
            return self.fs_structure["/"]
        parts = path.strip("/").split("/")
        current = self.fs_structure["/"]
        for part in parts:
            if part not in current["contents"] or current["contents"][part]["type"] != "directory":
                return None
            current = current["contents"][part]
        return current

    def open(self, fName, mode):
        full_path = self.get_full_path(fName)
        parent_path = os.path.dirname(full_path)
        fname = os.path.basename(full_path)

        parent = self.get_directory(parent_path)
        if not parent:
            return None, "Parent directory does not exist"

        if fname not in parent["contents"] or parent["contents"][fname]["type"] != "file":
            if mode in ["w", "a"]:
                result = self.create(fName)
                if "created" not in result:
                    return None, result
                parent = self.get_directory(parent_path)  # Refresh parent
            else:
                return None, "File does not exist"

        file_obj = FileObject(self, parent["contents"][fname]["data_id"], mode, full_path)
        self.open_files[full_path] = file_obj
        return file_obj, f"File {fName} opened in {mode} mode"

    def close(self, fName):
        full_path = self.get_full_path(fName)
        if full_path in self.open_files:
            del self.open_files[full_path]
            self.save_data()
            return f"File {fName} closed"
        return "File not open"

    def show_memory_map(self):
        result = "Memory Map:\n"
        
        def find_file_path(data_id, current_path="/", current_dir=None):
            if current_dir is None:
                current_dir = self.fs_structure["/"]
            
            for name, info in current_dir["contents"].items():
                full_path = os.path.join(current_path, name).replace("\\", "/")
                if info["type"] == "file" and info["data_id"] == data_id:
                    return full_path
                elif info["type"] == "directory":
                    sub_result = find_file_path(data_id, full_path, info)
                    if sub_result:
                        return sub_result
            return None

        for data_id, content in self.memory_map.items():
            file_path = find_file_path(data_id)
            if file_path:
                result += f"Block {data_id}: {len(content)} bytes (File: {file_path})\n"
            else:
                result += f"Block {data_id}: {len(content)} bytes (File: <not found>)\n"
        
        return result

    def list_dir(self, dir_path=None):
        if dir_path is None:
            dir_path = self.current_dir
        full_path = self.get_full_path(dir_path)
        directory = self.get_directory(full_path)
        if not directory or directory["type"] != "directory":
            return "Directory does not exist"
        
        result = f"Contents of {full_path}:\n"
        for name, info in directory["contents"].items():
            item_type = info["type"].capitalize()
            created = info["created"]
            size = info.get("size", 0) if info["type"] == "file" else "-"
            result += f"{item_type:<10} {name:<20} Size: {size:<10} Created: {created}\n"
        return result

class FileObject:
    def __init__(self, fs, data_id, mode, full_path):
        self.fs = fs
        self.data_id = data_id
        self.mode = mode
        self.full_path = full_path

    def write_to_file(self, text, write_at=None):
        if self.mode not in ["w", "a"]:
            return "Invalid mode for writing"
        content = self.fs.memory_map[self.data_id]
        if self.mode == "w" and write_at is None:
            content = text  # Overwrite entire content in write mode
        elif write_at is None:
            content += text  # Append text in append mode
        else:
            content = content[:write_at] + text + content[write_at + len(text):]  # Write at specific position
        self.fs.memory_map[self.data_id] = content
        
        # Update file size in fs_structure
        parent_path = os.path.dirname(self.full_path)
        fname = os.path.basename(self.full_path)
        parent = self.fs.get_directory(parent_path)
        if parent and fname in parent["contents"]:
            parent["contents"][fname]["size"] = len(content)
        
        self.fs.save_data()
        return "Write successful"

    def read_from_file(self, start=None, size=None):
        content = self.fs.memory_map[self.data_id]
        content_length = len(content)
        
        if start is None:
            return content
        start = max(0, int(start))
        if start >= content_length:
            return ""  # Return empty string if start is beyond content length
        
        if size is None:
            return content[start:]
        size = int(size)
        if size <= 0:
            return ""
        return content[start:min(start + size, content_length)]

    def move_within_file(self, start, size, target):
        content = self.fs.memory_map[self.data_id]
        if start < 0 or size < 0 or target < 0 or start + size > len(content):
            return "Invalid move parameters"
        data = content[start:start + size]
        content = content[:start] + content[start + size:]
        content = content[:target] + data + content[target:]
        self.fs.memory_map[self.data_id] = content
        
        # Update file size
        parent_path = os.path.dirname(self.full_path)
        fname = os.path.basename(self.full_path)
        parent = self.fs.get_directory(parent_path)
        if parent and fname in parent["contents"]:
            parent["contents"][fname]["size"] = len(content)
        
        self.fs.save_data()
        return "Move successful"

    def truncate_file(self, maxSize):
        if maxSize < 0:
            return "Invalid truncate size"
        content = self.fs.memory_map[self.data_id][:maxSize]
        self.fs.memory_map[self.data_id] = content
        
        # Update file size
        parent_path = os.path.dirname(self.full_path)
        fname = os.path.basename(self.full_path)
        parent = self.fs.get_directory(parent_path)
        if parent and fname in parent["contents"]:
            parent["contents"][fname]["size"] = len(content)
        
        self.fs.save_data()
        return "Truncate successful"

class FileSystemGUI:
    def __init__(self, root):
        self.fs = FileSystem()
        self.root = root
        self.root.title("Distributed File Management System")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f5f5f5")

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=5)
        self.style.configure("TEntry", font=("Segoe UI", 10), padding=5)
        self.style.configure("TNotebook", background="#f5f5f5")
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[10, 5])
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        
        # Main container
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.header_frame, text="Distributed File System", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Current directory display
        self.current_dir_frame = ttk.Frame(self.main_container)
        self.current_dir_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.current_dir_label = ttk.Label(
            self.current_dir_frame, 
            text=f"Current Directory: {self.fs.current_dir}",
            background="#e1e1e1",
            padding=(10, 5),
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.current_dir_label.pack(fill=tk.X)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # File Operations Tab
        self.file_ops_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.file_ops_tab, text="File Operations")
        
        # File Operations Frame
        self.file_ops_frame = ttk.LabelFrame(
            self.file_ops_tab, 
            text="File/Directory Operations",
            padding=(15, 10)
        )
        self.file_ops_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Name entry
        ttk.Label(self.file_ops_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(self.file_ops_frame, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Operation buttons
        button_frame = ttk.Frame(self.file_ops_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Create File", command=self.create_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Directory", command=self.create_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Change Directory", command=self.change_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="List Directory", command=self.list_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Show Memory Map", command=self.show_memory_map).pack(side=tk.LEFT, padx=5)
        
        # Move operation
        ttk.Label(self.file_ops_frame, text="Move Target:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.target_entry = ttk.Entry(self.file_ops_frame, width=40)
        self.target_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(
            self.file_ops_frame, 
            text="Move File/Directory", 
            command=self.move_file,
            style="Accent.TButton"
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
        # File Content Tab
        self.file_content_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.file_content_tab, text="File Content")
        
        # File Content Frame
        self.file_content_frame = ttk.LabelFrame(
            self.file_content_tab, 
            text="File Content Operations",
            padding=(15, 10)
        )
        self.file_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File selection
        ttk.Label(self.file_content_frame, text="File Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.file_name_entry = ttk.Entry(self.file_content_frame, width=40)
        self.file_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Mode selection
        ttk.Label(self.file_content_frame, text="Mode:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.mode_var = tk.StringVar(value="r")
        mode_frame = ttk.Frame(self.file_content_frame)
        mode_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Read", variable=self.mode_var, value="r").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Write", variable=self.mode_var, value="w").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Append", variable=self.mode_var, value="a").pack(side=tk.LEFT)
        
        # Open/Close buttons
        button_frame2 = ttk.Frame(self.file_content_frame)
        button_frame2.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame2, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Close File", command=self.close_file).pack(side=tk.LEFT, padx=5)
        
        # Write section
        write_frame = ttk.LabelFrame(
            self.file_content_frame, 
            text="Write to File",
            padding=(10, 5)
        )
        write_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        ttk.Label(write_frame, text="Text:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.write_text = ttk.Entry(write_frame, width=40)
        self.write_text.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(write_frame, text="Position (optional):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.write_at = ttk.Entry(write_frame, width=10)
        self.write_at.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(write_frame, text="Write", command=self.write_file).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Read section
        read_frame = ttk.LabelFrame(
            self.file_content_frame, 
            text="Read from File",
            padding=(10, 5)
        )
        read_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        ttk.Label(read_frame, text="Start (optional):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.read_start = ttk.Entry(read_frame, width=10)
        self.read_start.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(read_frame, text="Size (optional):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.read_size = ttk.Entry(read_frame, width=10)
        self.read_size.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(read_frame, text="Read", command=self.read_file).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Advanced operations
        advanced_frame = ttk.LabelFrame(
            self.file_content_frame, 
            text="Advanced Operations",
            padding=(10, 5)
        )
        advanced_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        # Move within file
        ttk.Label(advanced_frame, text="Move Data Within File:").grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Label(advanced_frame, text="Start:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.move_start = ttk.Entry(advanced_frame, width=10)
        self.move_start.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(advanced_frame, text="Size:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.move_size = ttk.Entry(advanced_frame, width=10)
        self.move_size.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(advanced_frame, text="Target:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.move_target = ttk.Entry(advanced_frame, width=10)
        self.move_target.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Button(advanced_frame, text="Move Within File", command=self.move_within_file).grid(
            row=4, column=0, columnspan=2, pady=5)
        
        # Truncate
        ttk.Label(advanced_frame, text="Truncate File:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.truncate_size = ttk.Entry(advanced_frame, width=10)
        self.truncate_size.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(advanced_frame, text="Truncate", command=self.truncate_file).grid(
            row=6, column=0, columnspan=2, pady=5)
        
        # Output console
        console_frame = ttk.LabelFrame(
            self.main_container, 
            text="Output Console",
            padding=(10, 5)
        )
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.output_text = tk.Text(
            console_frame, 
            height=10, 
            width=80, 
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg="#2d2d2d",
            fg="#f0f0f0",
            insertbackground="white"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for output text
        scrollbar = ttk.Scrollbar(self.output_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)
        
        # Status bar
        self.status_bar = ttk.Label(
            self.main_container, 
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 5)
        )
        self.status_bar.pack(fill=tk.X)
        
        # Create an accent style for important buttons
        self.style.configure("Accent.TButton", background="#4a90e2", foreground="white")
        
        # Set focus to name entry
        self.name_entry.focus()
        
    def update_status(self, message):
        self.status_bar.config(text=message)
        
    def create_file(self):
        name = self.name_entry.get()
        if not name:
            self.update_status("Error: Please enter a file name")
            messagebox.showerror("Error", "Please enter a file name")
            return
            
        result = self.fs.create(name)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("File created successfully")
        messagebox.showinfo("Success", result)
        
    def create_dir(self):
        name = self.name_entry.get()
        if not name:
            self.update_status("Error: Please enter a directory name")
            messagebox.showerror("Error", "Please enter a directory name")
            return
            
        result = self.fs.mkdir(name)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("Directory created successfully")
        messagebox.showinfo("Success", result)
        
    def delete(self):
        name = self.name_entry.get()
        if not name:
            self.update_status("Error: Please enter a file/directory name")
            messagebox.showerror("Error", "Please enter a file/directory name")
            return
            
        result = self.fs.delete(name)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("File/directory deleted successfully")
        messagebox.showinfo("Success", result)
        
    def change_dir(self):
        name = self.name_entry.get()
        if not name:
            self.update_status("Error: Please enter a directory name")
            messagebox.showerror("Error", "Please enter a directory name")
            return
            
        result = self.fs.chdir(name)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("Directory changed successfully")
        messagebox.showinfo("Success", result)
        
    def move_file(self):
        source = self.name_entry.get()
        target = self.target_entry.get()
        
        if not source or not target:
            self.update_status("Error: Please enter both source and target paths")
            messagebox.showerror("Error", "Please enter both source and target paths")
            return
            
        result = self.fs.move(source, target)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("File/directory moved successfully")
        messagebox.showinfo("Success", result)
        
    def open_file(self):
        name = self.file_name_entry.get()
        if not name:
            self.update_status("Error: Please enter a file name")
            messagebox.showerror("Error", "Please enter a file name")
            return
            
        mode = self.mode_var.get()
        file_obj, result = self.fs.open(name, mode)
        if file_obj:
            self.output_text.insert(tk.END, result + "\n")
            self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
            self.update_status(f"File opened in {mode} mode")
            messagebox.showinfo("Success", result)
        else:
            self.output_text.insert(tk.END, result + "\n")
            self.update_status("Error: Could not open file")
            messagebox.showerror("Error", result)
        
    def close_file(self):
        name = self.file_name_entry.get()
        if not name:
            self.update_status("Error: Please enter a file name")
            messagebox.showerror("Error", "Please enter a file name")
            return
            
        result = self.fs.close(name)
        self.output_text.insert(tk.END, result + "\n")
        self.current_dir_label.config(text=f"Current Directory: {self.fs.current_dir}")
        self.update_status("File closed successfully")
        messagebox.showinfo("Success", result)
        
    def write_file(self):
        # Get input values
        name = self.file_name_entry.get()
        text = self.write_text.get()
        if not name or not text:
            self.update_status("Error: Please enter file name and text to write")
            messagebox.showerror("Error", "Please enter file name and text to write")
            return

        # Verify mode is valid for writing
        mode = self.mode_var.get()
        if mode not in ["w", "a"]:
            self.update_status("Error: Invalid mode selected for writing")
            messagebox.showerror("Error", "Invalid mode selected for writing")
            return

        # Open file in specified mode (creates file if it doesn't exist)
        file_obj, result = self.fs.open(name, mode)
        if file_obj:
            try:
                write_at = self.write_at.get()
                if write_at:
                    result = file_obj.write_to_file(text, int(write_at))  # Write at specific position
                else:
                    result = file_obj.write_to_file(text)  # Write based on mode (w: overwrite, a: append)
                self.output_text.insert(tk.END, result + "\n")
                self.fs.close(name)
                self.update_status("Text written to file successfully")
                messagebox.showinfo("Success", result)
            except ValueError:
                self.update_status("Error: Position must be a number")
                messagebox.showerror("Error", "Position must be a number")
            except Exception as e:
                self.update_status(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        else:
            self.output_text.insert(tk.END, result + "\n")
            self.update_status("Error: Could not open file")
            messagebox.showerror("Error", result)
        
    def read_file(self):
        name = self.file_name_entry.get()
        if not name:
            self.update_status("Error: Please enter a file name")
            messagebox.showerror("Error", "Please enter a file name")
            return
            
        file_obj, result = self.fs.open(name, "r")
        if file_obj:
            try:
                start = self.read_start.get().strip()
                size = self.read_size.get().strip()
                
                # Convert inputs to integers if provided, else None
                start_val = int(start) if start else None
                size_val = int(size) if size else None
                
                # Read based on provided parameters
                content = file_obj.read_from_file(start_val, size_val)
                
                # Handle empty or no content
                if content == "":
                    content_display = "<No content or read beyond file length>"
                else:
                    content_display = content
                
                # Show content in popup
                content_window = tk.Toplevel(self.root)
                content_window.title(f"Contents of {name}")
                content_window.geometry("400x300")
                
                text_area = tk.Text(
                    content_window,
                    wrap=tk.WORD,
                    font=("Consolas", 10),
                    bg="#2d2d2d",
                    fg="#f0f0f0"
                )
                text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_area.insert(tk.END, content_display)
                text_area.config(state='disabled')
                
                ttk.Button(
                    content_window,
                    text="Close",
                    command=content_window.destroy
                ).pack(pady=5)
                
                self.fs.close(name)
                self.output_text.insert(tk.END, f"Read operation completed for {name}\n")
                self.update_status("File read successfully")
                messagebox.showinfo("Success", "File read successfully")
            except ValueError:
                self.update_status("Error: Start and size must be valid numbers")
                messagebox.showerror("Error", "Start and size must be valid numbers")
            except Exception as e:
                self.update_status(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        else:
            self.output_text.insert(tk.END, result + "\n")
            self.update_status("Error: Could not open file")
            messagebox.showerror("Error", result)
        
    def move_within_file(self):
        name = self.file_name_entry.get()
        start = self.move_start.get()
        size = self.move_size.get()
        target = self.move_target.get()
        
        if not name or not start or not size or not target:
            self.update_status("Error: Please fill all fields for move operation")
            messagebox.showerror("Error", "Please fill all fields for move operation")
            return
            
        file_obj, result = self.fs.open(name, "w")
        if file_obj:
            try:
                result = file_obj.move_within_file(int(start), int(size), int(target))
                self.output_text.insert(tk.END, result + "\n")
                self.fs.close(name)
                self.update_status("Data moved within file successfully")
                messagebox.showinfo("Success", result)
            except ValueError:
                self.update_status("Error: Positions must be numbers")
                messagebox.showerror("Error", "Positions must be numbers")
            except Exception as e:
                self.update_status(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        else:
            self.output_text.insert(tk.END, result + "\n")
            self.update_status("Error: Could not open file")
            messagebox.showerror("Error", result)
        
    def truncate_file(self):
        name = self.file_name_entry.get()
        size = self.truncate_size.get()
        
        if not name or not size:
            self.update_status("Error: Please enter file name and size")
            messagebox.showerror("Error", "Please enter file name and size")
            return
            
        file_obj, result = self.fs.open(name, "w")
        if file_obj:
            try:
                result = file_obj.truncate_file(int(size))
                self.output_text.insert(tk.END, result + "\n")
                self.fs.close(name)
                self.update_status("File truncated successfully")
                messagebox.showinfo("Success", result)
            except ValueError:
                self.update_status("Error: Size must be a number")
                messagebox.showerror("Error", "Size must be a number")
            except Exception as e:
                self.update_status(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        else:
            self.output_text.insert(tk.END, result + "\n")
            self.update_status("Error: Could not open file")
            messagebox.showerror("Error", result)
        
    def show_memory_map(self):
        result = self.fs.show_memory_map()
        self.output_text.insert(tk.END, result + "\n")
        self.update_status("Memory map displayed")
        messagebox.showinfo("Memory Map", result)
    
    def list_directory(self):
        name = self.name_entry.get() or None
        result = self.fs.list_dir(name)
        self.output_text.insert(tk.END, result + "\n")
        self.update_status("Directory contents listed")
        messagebox.showinfo("Directory Contents", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSystemGUI(root)
    root.mainloop()