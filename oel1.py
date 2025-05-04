import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import os
import pickle
import time
from datetime import datetime
import shutil
import sys
import subprocess

# Modern color scheme
COLORS = {
    "primary": "#4361ee",
    "secondary": "#3a0ca3",
    "background": "#f8f9fa",
    "sidebar": "#2b2d42",
    "text": "#495057",
    "highlight": "#f72585"
}

class FileSystemManager:
    def __init__(self):
        self.current_dir = os.path.expanduser("~")
        self.data_file = "filesystem_data.bin"
        self.file_structure = {}
        self.load_data()
        
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    self.file_structure = pickle.load(f)
            except:
                self.file_structure = {}
        else:
            self.file_structure = {}
    
    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.file_structure, f)
    
    def get_file_info(self, path):
        if path in self.file_structure:
            return self.file_structure[path]
        
        try:
            stat = os.stat(path)
            file_info = {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_dir': os.path.isdir(path),
                'tags': []
            }
            self.file_structure[path] = file_info
            return file_info
        except:
            return None
    
    def add_tag(self, path, tag):
        if path in self.file_structure:
            if tag not in self.file_structure[path]['tags']:
                self.file_structure[path]['tags'].append(tag)
                self.save_data()
    
    def remove_tag(self, path, tag):
        if path in self.file_structure:
            if tag in self.file_structure[path]['tags']:
                self.file_structure[path]['tags'].remove(tag)
                self.save_data()

class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FileSphere • Modern File Manager")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        self.fs = FileSystemManager()
        self.selected_files = []
        self.current_dir = self.fs.current_dir
        self.clipboard = None
        
        # Initialize UI components first
        self.main_frame = None
        self.sidebar = None
        self.content_frame = None
        self.toolbar = None
        self.tree_frame = None
        self.tree = None
        self.status_bar = None
        self.status_label = None
        self.ops_panel = None
        self.tabview = None
        
        self.setup_ui()
        self.load_directory(self.current_dir)
        
    def setup_ui(self):
        # Configure modern theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Main container with modern layout
        self.main_frame = ctk.CTkFrame(self.root, fg_color=COLORS["background"])
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Modern sidebar with accent color
        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            width=280,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # App logo with modern typography
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.pack(pady=(30, 40), padx=20, fill="x")
        
        ctk.CTkLabel(
            self.logo_frame,
            text="FileSphere",
            font=ctk.CTkFont(size=24, weight="bold", family="Helvetica"),
            text_color="white"
        ).pack(side="left")
        
        # Modern navigation with icons
        nav_items = [
            ("Dashboard", "📊"),
            ("Files", "📁"),
            ("Shared", "👥"),
            ("Favorites", "⭐"),
            ("Memory Map", "🧠"),
            ("Settings", "⚙️")
        ]
        
        for text, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {text}",
                font=ctk.CTkFont(size=14),
                anchor="w",
                fg_color="transparent",
                hover_color="#3a3b3c",
                text_color="white",
                height=40,
                corner_radius=8
            )
            btn.pack(fill="x", padx=12, pady=4)
        
        # Main content area with card-based layout
        self.content_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["background"]
        )
        self.content_frame.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Modern toolbar with floating effect
        self.toolbar = ctk.CTkFrame(
            self.content_frame,
            height=70,
            fg_color="white",
            border_width=1,
            border_color="#e9ecef",
            corner_radius=12
        )
        self.toolbar.pack(fill="x", padx=20, pady=20)
        
        # Action buttons with modern icons
        actions = [
            ("➕ Create", self.create_file),
            ("🗑️ Delete", self.delete_selected),  # Changed to match actual method name
            ("📂 Folder", self.create_dir),
            ("🔍 Open", self.open_file),
            ("🚚 Move", self.move_file),
            ("🗺️ Map", self.show_memory_map)
        ]
                
        for i, (text, command) in enumerate(actions):
            btn = ctk.CTkButton(
                self.toolbar,
                text=text,
                width=100,
                font=ctk.CTkFont(size=13),
                command=command,
                fg_color=COLORS["primary"],
                hover_color=COLORS["secondary"],
                corner_radius=8
            )
            btn.grid(row=0, column=i, padx=8, pady=10)
        
        # Modern search bar
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.grid(row=0, column=len(actions), padx=10, sticky="e")
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search files...",
            width=220,
            height=36,
            border_width=1,
            corner_radius=8,
            fg_color="white"
        )
        self.search_entry.pack(side="left")
        
        search_btn = ctk.CTkButton(
            self.search_frame,
            text="🔍",
            width=36,
            height=36,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            corner_radius=8
        )
        search_btn.pack(side="left", padx=5)
        
        # Modern file explorer with card container
        self.explorer_card = ctk.CTkFrame(
            self.content_frame,
            fg_color="white",
            border_width=1,
            border_color="#e9ecef",
            corner_radius=12
        )
        self.explorer_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # File explorer header
        header = ctk.CTkFrame(self.explorer_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header,
            text="File Explorer",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left")
        
        # Modern treeview with better styling
        self.tree_frame = ctk.CTkFrame(self.explorer_card, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
            background="white",
            foreground=COLORS["text"],
            fieldbackground="white",
            borderwidth=0,
            font=('Helvetica', 11)
        )
        style.configure("Treeview.Heading",
            background="#f8f9fa",
            foreground=COLORS["text"],
            font=('Helvetica', 12, 'bold'),
            padding=10,
            borderwidth=0
        )
        style.map("Treeview",
            background=[('selected', '#e6f2ff')],
            foreground=[('selected', COLORS["primary"])]
        )
        
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("size", "type", "modified"),
            show="tree headings",
            selectmode="extended"
        )
        
        # Configure columns with modern look
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.heading("modified", text="Modified", anchor="w")
        
        self.tree.column("#0", width=300, anchor="w")
        self.tree.column("size", width=120, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("modified", width=180, anchor="w")
        
        # Add tag configuration
        self.tree.tag_configure("folder", foreground="#3a0ca3")
        self.tree.tag_configure("file", foreground="#495057")
        self.tree.tag_configure("selected", background="#e6f2ff")
        
        # Modern scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.tree.bind("<Double-1>", self.on_file_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Status bar with modern design
        self.status_bar = ctk.CTkFrame(
            self.content_frame,
            height=40,
            fg_color="white",
            border_width=1,
            border_color="#e9ecef",
            corner_radius=8
        )
        self.status_bar.pack(fill="x", padx=20, pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready • 0 items selected • 1.2GB available",
            text_color="#6c757d",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=15)
        
        # Modern operations panel (initially hidden)
        self.ops_panel = ctk.CTkFrame(
            self.content_frame,
            height=220,
            fg_color="white",
            border_width=1,
            border_color="#e9ecef",
            corner_radius=12
        )
        self.ops_panel.pack_propagate(False)
        
        # Tab view with modern styling
        self.tabview = ctk.CTkTabview(
            self.ops_panel,
            segmented_button_fg_color=COLORS["primary"],
            segmented_button_selected_color=COLORS["secondary"],
            segmented_button_selected_hover_color=COLORS["secondary"],
            text_color="white"
        )
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add modern tabs
        tabs = ["📄 Read", "✏️ Write", "↔️ Move", "✂️ Truncate"]
        for tab in tabs:
            self.tabview.add(tab)
        
        # Configure tabs with modern UI
        self.setup_read_tab()
        self.setup_write_tab()
        self.setup_move_tab()
        self.setup_truncate_tab()
    
    def load_directory(self, path):
        """Load directory contents into the treeview"""
        self.current_dir = path
        self.tree.delete(*self.tree.get_children())
        
        # Add parent directory link
        parent = os.path.dirname(path)
        if os.path.exists(parent) and parent:  # Ensure parent exists and isn't root
            self.tree.insert("", "end", text="..", 
                        values=("--", "Parent", ""), 
                        tags=("folder",), 
                        iid=parent)
        
        try:
            for item in sorted(os.listdir(path)):
                full_path = os.path.join(path, item)
                file_info = self.fs.get_file_info(full_path)
                
                if file_info:
                    size = self.format_size(file_info['size']) if not file_info['is_dir'] else "--"
                    file_type = "Folder" if file_info['is_dir'] else os.path.splitext(item)[1][1:].upper() + " File"
                    modified = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
                    
                    tags = ("folder",) if file_info['is_dir'] else ("file",)
                    
                    self.tree.insert("", "end", text=item, 
                                    values=(size, file_type, modified), 
                                    tags=tags, 
                                    iid=full_path)
                    
        except PermissionError:
            messagebox.showerror("Error", f"Permission denied: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load directory: {e}")
        
        self.update_status()
    
    def format_size(self, size):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def on_file_select(self, event):
        """Handle file selection"""
        self.selected_files = [self.tree.item(iid)['text'] for iid in self.tree.selection()]
        self.update_status()
    
    def on_file_double_click(self, event):
        """Handle double-click on file/folder"""
        item = self.tree.focus()
        if item:
            if os.path.isdir(item):
                self.load_directory(item)
            else:
                self.open_file(item)
    
    def update_status(self):
        """Update status bar with current information"""
        total_size = 0
        selected_count = len(self.selected_files)
        
        for item in self.tree.get_children():
            try:
                full_path = self.tree.item(item)['iid']
                if os.path.isfile(full_path):
                    file_info = self.fs.get_file_info(full_path)
                    if file_info:
                        total_size += file_info['size']
            except KeyError:
                continue  # Skip items that don't have an 'iid' (like the parent directory "..")
        
        # Get disk usage info
        try:
            stat = os.statvfs(self.current_dir)
            total_space = stat.f_frsize * stat.f_blocks
            free_space = stat.f_frsize * stat.f_bfree
            used_space = total_space - free_space
            free_percent = (free_space / total_space) * 100
            
            status_text = (f"{selected_count} item(s) selected • "
                        f"Directory: {self.format_size(total_size)} • "
                        f"Free: {self.format_size(free_space)} ({free_percent:.1f}%)")
        except:
            status_text = f"{selected_count} item(s) selected • {self.current_dir}"
        
        self.status_label.configure(text=status_text)
    
    def show_context_menu(self, event):
        """Show context menu for right-click"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        menu = ctk.CTkMenu(self.root, tearoff=0)
        
        if os.path.isdir(item):
            menu.add_command(label="Open", command=lambda: self.load_directory(item))
            menu.add_command(label="New File", command=self.create_file)
            menu.add_command(label="New Folder", command=self.create_dir)
        else:
            menu.add_command(label="Open", command=lambda: self.open_file(item))
            menu.add_command(label="Edit", command=lambda: self.edit_file(item))
        
        menu.add_separator()
        menu.add_command(label="Copy", command=lambda: self.copy_to_clipboard(item))
        menu.add_command(label="Paste", command=self.paste_from_clipboard)
        menu.add_command(label="Delete", command=self.delete_selected)
        menu.add_separator()
        menu.add_command(label="Properties", command=lambda: self.show_properties(item))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    # File operations
    def create_file(self):
        dialog = ctk.CTkInputDialog(
            text="Enter new file name:",
            title="Create File",
            fg_color="white",
            button_fg_color=COLORS["primary"],
            button_hover_color=COLORS["secondary"]
        )
        fname = dialog.get_input()
        if fname:
            try:
                full_path = os.path.join(self.current_dir, fname)
                with open(full_path, 'w') as f:
                    pass
                self.load_directory(self.current_dir)
                messagebox.showinfo("Success", f"Created new file: {fname}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")
    
    def create_dir(self):
        dialog = ctk.CTkInputDialog(
            text="Enter new folder name:",
            title="Create Folder",
            fg_color="white",
            button_fg_color=COLORS["primary"],
            button_hover_color=COLORS["secondary"]
        )
        dname = dialog.get_input()
        if dname:
            try:
                full_path = os.path.join(self.current_dir, dname)
                os.mkdir(full_path)
                self.load_directory(self.current_dir)
                messagebox.showinfo("Success", f"Created new folder: {dname}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {e}")
    
    def delete_selected(self):
        if not self.selected_files:
            return
            
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {len(self.selected_files)} item(s)?",
            parent=self.root
        )
        
        if not confirm:
            return
            
        for item in self.tree.selection():
            full_path = self.tree.item(item)['iid']
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {full_path}: {e}")
        
        self.load_directory(self.current_dir)
    
    def copy_to_clipboard(self, item):
        self.clipboard = {
            'type': 'copy',
            'path': item
        }
    
    def paste_from_clipboard(self):
        if not self.clipboard:
            return
            
        source = self.clipboard['path']
        dest = os.path.join(self.current_dir, os.path.basename(source))
        
        try:
            if self.clipboard['type'] == 'copy':
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
            else:  # move
                shutil.move(source, dest)
            
            self.load_directory(self.current_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste: {e}")
    
    def open_file(self, path):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            else:  # macOS and Linux
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def edit_file(self, path):
        try:
            if os.name == 'nt':  # Windows
                os.system(f'notepad "{path}"')
            else:  # macOS and Linux
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit file: {e}")
    
    def show_properties(self, path):
        file_info = self.fs.get_file_info(path)
        if not file_info:
            return
            
        props = [
            f"Name: {os.path.basename(path)}",
            f"Type: {'Folder' if file_info['is_dir'] else 'File'}",
            f"Size: {self.format_size(file_info['size'])}",
            f"Created: {datetime.fromtimestamp(file_info['created']).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Modified: {datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Location: {os.path.dirname(path)}"
        ]
        
        messagebox.showinfo("Properties", "\n".join(props))
    
    # Tab operations
    def setup_read_tab(self):
        tab = self.tabview.tab("📄 Read")
        
        ctk.CTkLabel(tab, text="Read Options", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.read_mode = ctk.CTkSegmentedButton(
            tab,
            values=["Sequential Read", "Positional Read"],
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["secondary"]
        )
        self.read_mode.pack(pady=5)
        
        self.read_start = ctk.CTkEntry(tab, placeholder_text="Start position", height=36)
        self.read_size = ctk.CTkEntry(tab, placeholder_text="Size (bytes)", height=36)
        
        self.read_btn = ctk.CTkButton(
            tab,
            text="Read File",
            command=self.dummy_read,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            height=36
        )
        self.read_btn.pack(pady=10)
        
        self.read_output = ctk.CTkTextbox(
            tab,
            height=80,
            border_width=1,
            border_color="#e9ecef",
            fg_color="white",
            corner_radius=8
        )
        self.read_output.pack(fill="x", padx=5, pady=5)
    
    def setup_write_tab(self):
        tab = self.tabview.tab("✏️ Write")
        
        ctk.CTkLabel(tab, text="Write Options", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.write_mode = ctk.CTkSegmentedButton(
            tab,
            values=["Append", "Write At"],
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["secondary"]
        )
        self.write_mode.pack(pady=5)
        
        self.write_pos = ctk.CTkEntry(tab, placeholder_text="Position (bytes)", height=36)
        self.write_content = ctk.CTkTextbox(
            tab,
            height=80,
            border_width=1,
            border_color="#e9ecef",
            fg_color="white",
            corner_radius=8
        )
        
        self.write_btn = ctk.CTkButton(
            tab,
            text="Write Content",
            command=self.dummy_write,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            height=36
        )
        
        self.write_content.pack(fill="x", padx=5, pady=5)
        self.write_pos.pack(fill="x", padx=5, pady=5)
        self.write_btn.pack(pady=10)
    
    def setup_move_tab(self):
        tab = self.tabview.tab("↔️ Move")
        
        ctk.CTkLabel(tab, text="Move Content Within File", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.move_from = ctk.CTkEntry(tab, placeholder_text="From Position", height=36)
        self.move_to = ctk.CTkEntry(tab, placeholder_text="To Position", height=36)
        self.move_size = ctk.CTkEntry(tab, placeholder_text="Size (bytes)", height=36)
        
        fields = [
            ("From Position", self.move_from),
            ("To Position", self.move_to),
            ("Size (bytes)", self.move_size)
        ]
        
        for label, entry in fields:
            frame = ctk.CTkFrame(tab, fg_color="transparent")
            frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(frame, text=label, width=100).pack(side="left")
            entry.pack(side="right", fill="x", expand=True)
        
        self.move_btn = ctk.CTkButton(
            tab,
            text="Move Content",
            command=self.dummy_move,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            height=36
        )
        self.move_btn.pack(pady=10)
    
    def setup_truncate_tab(self):
        tab = self.tabview.tab("✂️ Truncate")
        
        ctk.CTkLabel(tab, text="Truncate File", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(tab, text="New File Size (bytes):").pack(pady=(5, 0))
        self.truncate_size = ctk.CTkEntry(tab, height=36)
        self.truncate_size.pack(fill="x", padx=5, pady=5)
        
        self.truncate_btn = ctk.CTkButton(
            tab,
            text="Truncate File",
            command=self.dummy_truncate,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            height=36
        )
        self.truncate_btn.pack(pady=10)
    
    def dummy_read(self):
        selected = self.tree.selection()
        if not selected:
            self.read_output.delete("1.0", "end")
            self.read_output.insert("1.0", "No file selected")
            return
            
        path = selected[0]
        if os.path.isdir(path):
            self.read_output.delete("1.0", "end")
            self.read_output.insert("1.0", "Cannot read a directory")
            return
            
        try:
            with open(path, 'r') as f:
                content = f.read(1000)  # Read first 1000 chars
                self.read_output.delete("1.0", "end")
                self.read_output.insert("1.0", content)
        except Exception as e:
            self.read_output.delete("1.0", "end")
            self.read_output.insert("1.0", f"Error reading file: {e}")
    
    def dummy_write(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "No file selected")
            return
            
        path = selected[0]
        if os.path.isdir(path):
            messagebox.showerror("Error", "Cannot write to a directory")
            return
            
        content = self.write_content.get("1.0", "end-1c")
        if not content:
            messagebox.showerror("Error", "No content to write")
            return
            
        try:
            mode = 'a' if self.write_mode.get() == "Append" else 'w'
            with open(path, mode) as f:
                f.write(content)
            messagebox.showinfo("Success", "Content written to file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file: {e}")
    
    def dummy_move(self):
        messagebox.showinfo("Info", "Move content within file will be implemented in future version")
    
    def dummy_truncate(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "No file selected")
            return
            
        path = selected[0]
        if os.path.isdir(path):
            messagebox.showerror("Error", "Cannot truncate a directory")
            return
            
        try:
            size = int(self.truncate_size.get())
            with open(path, 'r+') as f:
                f.truncate(size)
            messagebox.showinfo("Success", f"File truncated to {size} bytes")
            self.load_directory(self.current_dir)  # Refresh view
        except ValueError:
            messagebox.showerror("Error", "Invalid size value")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to truncate file: {e}")
    
    def move_file(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "No file selected")
            return
            
        path = selected[0]
        dest = filedialog.askdirectory(initialdir=self.current_dir)
        if dest:
            try:
                shutil.move(path, dest)
                self.load_directory(self.current_dir)
                messagebox.showinfo("Success", "File moved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move file: {e}")
    
    def show_memory_map(self):
        messagebox.showinfo("Memory Map", "Visual memory map will be displayed here")

if __name__ == "__main__":
    root = ctk.CTk()
    app = FileManagerApp(root)
    root.mainloop()