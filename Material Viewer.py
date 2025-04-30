import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import struct
import re
import colorsys
from pathlib import Path
import shutil
import tempfile
import threading
from functools import partial
import io

# Try to import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    dnd_support = True
except ImportError:
    dnd_support = False
    print("Drag and drop not available. Install tkinterdnd2 for this feature.")

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    pil_support = True
except ImportError:
    pil_support = False
    print("Image display not available. Install pillow for this feature.")

class MaterialViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Material Viewer")
        self.root.geometry("1200x800")
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top frame for file selection
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=5)
        
        # Create label for current file
        self.file_label = ttk.Label(self.top_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        # Create game folder path entry
        ttk.Label(self.top_frame, text="Game Data Folder:").pack(side=tk.LEFT, padx=(20, 5))
        self.game_path = tk.StringVar()
        self.game_path_entry = ttk.Entry(self.top_frame, textvariable=self.game_path, width=40)
        self.game_path_entry.pack(side=tk.LEFT, padx=5)
        
        # Browse button for game folder
        browse_folder_btn = ttk.Button(self.top_frame, text="Browse...", command=self.browse_game_folder)
        browse_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Apply path button
        apply_path_btn = ttk.Button(self.top_frame, text="Apply Path", command=self.apply_game_path)
        apply_path_btn.pack(side=tk.LEFT, padx=5)
        
        # Create browse button
        self.browse_button = ttk.Button(self.top_frame, text="Open XBM...", command=self.open_file)
        self.browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Create a frame for file list
        self.file_list_frame = ttk.LabelFrame(self.main_frame, text="Files in Directory")
        self.file_list_frame.pack(fill=tk.X, pady=5)
        
        # Create file list
        self.file_list = ttk.Treeview(self.file_list_frame, height=4)
        self.file_list["columns"] = ("material",)
        self.file_list.heading("#0", text="File")
        self.file_list.heading("material", text="Material Name")
        self.file_list.column("#0", width=200)
        self.file_list.column("material", width=200)
        self.file_list.pack(fill=tk.X, expand=True, padx=5, pady=5)
        self.file_list.bind("<Double-1>", self.on_file_select)
        
        # Setup drag and drop if available
        if dnd_support:
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self.on_drop)
            
        # Add scrollbar to file list
        file_list_scrollbar = ttk.Scrollbar(self.file_list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        file_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.configure(yscrollcommand=file_list_scrollbar.set)
        
        # Create content frame with paned window
        self.content_frame = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create left frame for material tree
        self.material_frame = ttk.Frame(self.content_frame)
        self.content_frame.add(self.material_frame, weight=1)
        
        # Create material label
        ttk.Label(self.material_frame, text="Material Information").pack(anchor=tk.W, padx=5, pady=2)
        
        # Create material tree with right-click menu for copying
        self.material_tree = ttk.Treeview(self.material_frame)
        self.material_tree["columns"] = ("value")
        self.material_tree.heading("#0", text="Property")
        self.material_tree.heading("value", text="Value")
        self.material_tree.pack(fill=tk.BOTH, expand=True)
        self.material_tree.bind("<Button-3>", self.show_context_menu)
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.material_tree, tearoff=0)
        self.context_menu.add_command(label="Copy Value", command=self.copy_value)
        
        # Add scrollbar to material tree
        material_scrollbar = ttk.Scrollbar(self.material_frame, orient=tk.VERTICAL, command=self.material_tree.yview)
        material_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.material_tree.configure(yscrollcommand=material_scrollbar.set)
        
        # Create right frame for textures and colors
        self.right_frame = ttk.Notebook(self.content_frame)
        self.content_frame.add(self.right_frame, weight=2)
        
        # Create texture list tab
        self.texture_list_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.texture_list_frame, text="Texture List")
        
        # Create texture tree
        self.texture_tree = ttk.Treeview(self.texture_list_frame)
        self.texture_tree["columns"] = ("type", "path")
        self.texture_tree.heading("#0", text="Name")
        self.texture_tree.heading("type", text="Type")
        self.texture_tree.heading("path", text="Path")
        self.texture_tree.column("#0", width=150)
        self.texture_tree.column("type", width=150)
        self.texture_tree.column("path", width=500)
        self.texture_tree.pack(fill=tk.BOTH, expand=True)
        self.texture_tree.bind("<Button-3>", self.show_context_menu)
        self.texture_tree.bind("<Double-1>", self.view_texture_from_list)
        
        # Add scrollbar to texture tree
        texture_scrollbar = ttk.Scrollbar(self.texture_list_frame, orient=tk.VERTICAL, command=self.texture_tree.yview)
        texture_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.texture_tree.configure(yscrollcommand=texture_scrollbar.set)
        
        # Create texture viewer tab
        self.texture_viewer_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.texture_viewer_frame, text="Texture Viewer")
        
        # Setup texture viewer
        self.setup_texture_viewer()
        
        # Create material preview tab
        self.material_preview_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.material_preview_frame, text="Material Preview")
        
        # Setup material preview
        self.setup_material_preview()
        
        # Create colors tab
        self.color_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.color_frame, text="Colors")
        
        # Create color view with two subtabs
        self.color_notebook = ttk.Notebook(self.color_frame)
        self.color_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create raw colors tab
        self.raw_color_frame = ttk.Frame(self.color_notebook)
        self.color_notebook.add(self.raw_color_frame, text="Raw Colors")
        
        # Create raw color tree
        self.raw_color_tree = ttk.Treeview(self.raw_color_frame)
        self.raw_color_tree["columns"] = ("r", "g", "b", "a")
        self.raw_color_tree.heading("#0", text="Color Name")
        self.raw_color_tree.heading("r", text="R")
        self.raw_color_tree.heading("g", text="G")
        self.raw_color_tree.heading("b", text="B")
        self.raw_color_tree.heading("a", text="A")
        self.raw_color_tree.column("#0", width=200)
        self.raw_color_tree.column("r", width=100)
        self.raw_color_tree.column("g", width=100)
        self.raw_color_tree.column("b", width=100)
        self.raw_color_tree.column("a", width=100)
        self.raw_color_tree.pack(fill=tk.BOTH, expand=True)
        self.raw_color_tree.bind("<Button-3>", self.show_context_menu)
        self.raw_color_tree.bind("<Double-1>", self.show_color_details)
        
        # Add scrollbar to raw color tree
        raw_color_scrollbar = ttk.Scrollbar(self.raw_color_frame, orient=tk.VERTICAL, command=self.raw_color_tree.yview)
        raw_color_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.raw_color_tree.configure(yscrollcommand=raw_color_scrollbar.set)
        
        # Create normalized colors tab
        self.norm_color_frame = ttk.Frame(self.color_notebook)
        self.color_notebook.add(self.norm_color_frame, text="Normalized Colors")
        
        # Create normalized color tree
        self.norm_color_tree = ttk.Treeview(self.norm_color_frame)
        self.norm_color_tree["columns"] = ("r", "g", "b", "a")
        self.norm_color_tree.heading("#0", text="Color Name")
        self.norm_color_tree.heading("r", text="R")
        self.norm_color_tree.heading("g", text="G")
        self.norm_color_tree.heading("b", text="B")
        self.norm_color_tree.heading("a", text="A")
        self.norm_color_tree.column("#0", width=200)
        self.norm_color_tree.column("r", width=100)
        self.norm_color_tree.column("g", width=100)
        self.norm_color_tree.column("b", width=100)
        self.norm_color_tree.column("a", width=100)
        self.norm_color_tree.pack(fill=tk.BOTH, expand=True)
        self.norm_color_tree.bind("<Button-3>", self.show_context_menu)
        self.norm_color_tree.bind("<Double-1>", self.show_color_details)
        
        # Add scrollbar to normalized color tree
        norm_color_scrollbar = ttk.Scrollbar(self.norm_color_frame, orient=tk.VERTICAL, command=self.norm_color_tree.yview)
        norm_color_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.norm_color_tree.configure(yscrollcommand=norm_color_scrollbar.set)
        
        # Create color viewer tab
        self.color_viewer_frame = ttk.Frame(self.color_notebook)
        self.color_notebook.add(self.color_viewer_frame, text="Color Viewer")
        
        # Create color viewer
        self.setup_color_viewer()
        
        # Create raw values tab
        self.raw_values_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.raw_values_frame, text="Raw Values")
        
        # Create raw values tree
        self.raw_values_tree = ttk.Treeview(self.raw_values_frame)
        self.raw_values_tree["columns"] = ("hex", "float", "int")
        self.raw_values_tree.heading("#0", text="Property")
        self.raw_values_tree.heading("hex", text="Hex Value")
        self.raw_values_tree.heading("float", text="As Float")
        self.raw_values_tree.heading("int", text="As Integer")
        self.raw_values_tree.column("#0", width=200)
        self.raw_values_tree.column("hex", width=100)
        self.raw_values_tree.column("float", width=150)
        self.raw_values_tree.column("int", width=100)
        self.raw_values_tree.pack(fill=tk.BOTH, expand=True)
        self.raw_values_tree.bind("<Button-3>", self.show_context_menu)
        
        # Add scrollbar to raw values tree
        raw_values_scrollbar = ttk.Scrollbar(self.raw_values_frame, orient=tk.VERTICAL, command=self.raw_values_tree.yview)
        raw_values_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.raw_values_tree.configure(yscrollcommand=raw_values_scrollbar.set)
        
        # Create hex view tab
        self.hex_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.hex_frame, text="Hex View")
        
        # Create hex view text area
        self.hex_text = scrolledtext.ScrolledText(self.hex_frame, wrap=tk.WORD, font=("Courier", 10))
        self.hex_text.pack(fill=tk.BOTH, expand=True)
        
        # Create debug tab for troubleshooting
        self.debug_frame = ttk.Frame(self.right_frame)
        self.right_frame.add(self.debug_frame, text="Debug")
        
        # Create debug log
        self.debug_log = scrolledtext.ScrolledText(self.debug_frame, wrap=tk.WORD, font=("Courier", 10))
        self.debug_log.pack(fill=tk.BOTH, expand=True)
        
        # Add a "Save Raw Texture" button for debugging
        ttk.Button(self.debug_frame, text="Save Raw XBT", command=self.save_raw_xbt).pack(pady=5)
        
        # Add a "Dump Raw Data" button for debugging
        ttk.Button(self.debug_frame, text="Dump Current File", command=self.dump_raw_file).pack(pady=5)
        
        # Initialize status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # Initialize material cache
        self.material_cache = {}
        
        # Initialize texture cache
        self.texture_cache = {}
        
        # Initialize current material
        self.current_material = None
        self.current_material_data = None
        
        # Initialize temp directory for texture extraction
        self.temp_dir = tempfile.mkdtemp()
        
        # Try to load game path from config file
        self.load_config()
        
        # Check for .xbm files in current directory
        self.check_current_directory()
    
    def log_debug(self, message):
        """Add message to debug log"""
        self.debug_log.insert(tk.END, f"{message}\n")
        self.debug_log.see(tk.END)
        print(message)  # Also print to console
    
    def dump_raw_file(self):
        """Dump the currently loaded file to a text file"""
        if not self.current_material or not self.current_material_data:
            messagebox.showinfo("No File Loaded", "Please load a material file first")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")]
        )
        
        if save_path:
            try:
                # Create a readable hexdump of the file
                with open(save_path, 'w') as f:
                    data = self.current_material_data
                    for i in range(0, len(data), 16):
                        chunk = data[i:i+16]
                        hex_values = ' '.join(f"{b:02X}" for b in chunk)
                        ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                        f.write(f"{i:08X}:  {hex_values:<48}  {ascii_values}\n")
                
                messagebox.showinfo("Saved", f"File dumped to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def save_raw_xbt(self):
        """Save a raw XBT file for debugging"""
        if not self.current_texture["path"]:
            messagebox.showinfo("No Texture", "Please load a texture first")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".raw",
            filetypes=[("Raw Binary", "*.raw"), ("All Files", "*.*")]
        )
        
        if save_path:
            try:
                # Copy the raw XBT file
                with open(self.current_texture["path"], 'rb') as src:
                    with open(save_path, 'wb') as dst:
                        dst.write(src.read())
                messagebox.showinfo("Saved", f"Raw XBT file saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def apply_game_path(self):
        """Apply the game path and verify it works"""
        game_path = self.game_path.get()
        
        self.log_debug(f"Applying game path: {game_path}")
        
        if not game_path or not os.path.exists(game_path):
            messagebox.showerror("Invalid Path", "Please specify a valid game data folder path")
            return
            
        # Check for graphics folder
        graphics_path = os.path.join(game_path, "graphics")
        self.log_debug(f"Checking for graphics folder at: {graphics_path}")
        
        if not os.path.exists(graphics_path):
            messagebox.showerror("Invalid Path", 
                               f"Graphics folder not found at {graphics_path}\n\n"
                               f"Please make sure you select the folder that contains 'graphics' folder.\n"
                               f"For Avatar, this is usually the 'Data' folder inside 'Data_Win32'.")
            return
            
        # Save configuration
        self.save_config()
        
        # If a material is loaded, try to reload textures
        if self.current_material:
            self.reload_material_textures()
            
        self.status_bar.config(text=f"Game path applied: {game_path}")
    
    def reload_material_textures(self):
        """Reload textures for the current material"""
        self.log_debug("Reloading material textures")
        
        # Clear texture viewer list
        for item in self.texture_list_viewer.get_children():
            self.texture_list_viewer.delete(item)
            
        # Populate texture viewer list with textures from this material
        found_textures = 0
        for item in self.texture_tree.get_children():
            texture_name = self.texture_tree.item(item, "text")
            texture_type = self.texture_tree.item(item, "values")[0]
            texture_path = self.texture_tree.item(item, "values")[1]
            
            # Normalize the path for display
            display_path = texture_path.replace('\\', '/')
            
            self.log_debug(f"Checking texture: {texture_name} | {texture_type} | {display_path}")
            
            # Check if the texture exists in the game folder
            game_path = self.game_path.get()
            if game_path and os.path.exists(game_path):
                # Use correct path format for the OS
                if os.name == 'nt':  # Windows
                    path_components = display_path.split('/')
                    full_path = os.path.join(game_path, *path_components)
                else:  # Unix-like
                    full_path = os.path.join(game_path, display_path)
                
                self.log_debug(f"Looking for texture at: {full_path}")
                
                if os.path.exists(full_path):
                    # Texture found
                    self.log_debug(f"Texture FOUND: {full_path}")
                    self.texture_list_viewer.insert("", tk.END, text=texture_name, 
                                                  values=(texture_type, "✓"))
                    found_textures += 1
                    
                    # If this is the first texture, automatically load it
                    if found_textures == 1:
                        self.log_debug(f"Auto-loading first texture: {texture_name}")
                        self.load_texture(full_path, texture_name, texture_type)
                else:
                    # Texture not found
                    self.log_debug(f"Texture NOT FOUND: {full_path}")
                    self.texture_list_viewer.insert("", tk.END, text=texture_name, 
                                                  values=(texture_type, "❌"))
            else:
                self.texture_list_viewer.insert("", tk.END, text=texture_name, 
                                              values=(texture_type, "?"))
    
    def fix_texture_path(self, texture_path):
        """Convert texture path to the correct format for the OS"""
        game_path = self.game_path.get()
        
        # Normalize path (use forward slashes)
        texture_path = texture_path.replace('\\', '/')
        
        # Split into components and join using OS-specific method
        path_components = texture_path.split('/')
        full_path = os.path.join(game_path, *path_components)
        
        self.log_debug(f"Fixed texture path: {full_path}")
        self.status_bar.config(text=f"Looking for texture: {full_path}")
        return full_path
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists("materialviewer_config.txt"):
                with open("materialviewer_config.txt", "r") as f:
                    game_path = f.read().strip()
                    if os.path.exists(game_path):
                        self.game_path.set(game_path)
                        self.log_debug(f"Loaded game path from config: {game_path}")
        except Exception as e:
            self.log_debug(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open("materialviewer_config.txt", "w") as f:
                f.write(self.game_path.get())
                self.log_debug(f"Saved game path to config: {self.game_path.get()}")
        except Exception as e:
            self.log_debug(f"Error saving config: {e}")
    
    def browse_game_folder(self):
        """Browse for game data folder"""
        folder_path = filedialog.askdirectory(title="Select Game Data Folder")
        if folder_path:
            self.game_path.set(folder_path)
            self.log_debug(f"Selected game folder: {folder_path}")
    
    def setup_texture_viewer(self):
        """Set up the texture viewer panel"""
        # Create split view
        paned_window = ttk.PanedWindow(self.texture_viewer_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - texture list
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # Create a list of textures
        ttk.Label(left_frame, text="Available Textures:").pack(fill=tk.X, padx=5, pady=5)
        
        # Texture list
        self.texture_list_viewer = ttk.Treeview(left_frame, columns=("type", "status"), height=10)
        self.texture_list_viewer.heading("#0", text="Texture Name")
        self.texture_list_viewer.heading("type", text="Type")
        self.texture_list_viewer.heading("status", text="Status")
        self.texture_list_viewer.column("#0", width=150)
        self.texture_list_viewer.column("type", width=100)
        self.texture_list_viewer.column("status", width=50)
        self.texture_list_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.texture_list_viewer.bind("<Double-1>", self.load_selected_texture)
        
        # Add texture path debugging
        self.texture_path_debug = ttk.Entry(left_frame, state='readonly', width=30)
        self.texture_path_debug.pack(fill=tk.X, padx=5, pady=5)
        
        # Add fit to view button
        ttk.Button(left_frame, text="Fit to View", command=self.fit_texture_to_view).pack(fill=tk.X, padx=5, pady=5)
        
        # Right panel - texture display
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=3)
        
        # Control panel
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Channel checkboxes
        self.channel_var = {
            "r": tk.BooleanVar(value=True),
            "g": tk.BooleanVar(value=True), 
            "b": tk.BooleanVar(value=True)
        }
        
        ttk.Label(control_frame, text="Channels:").pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(control_frame, text="R", variable=self.channel_var["r"], 
                        command=self.update_texture_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(control_frame, text="G", variable=self.channel_var["g"], 
                        command=self.update_texture_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(control_frame, text="B", variable=self.channel_var["b"], 
                        command=self.update_texture_view).pack(side=tk.LEFT, padx=5)
        
        # Zoom controls
        ttk.Label(control_frame, text="Zoom:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.zoom_level = tk.DoubleVar(value=1.0)
        ttk.Scale(control_frame, from_=0.1, to=4.0, variable=self.zoom_level, 
                 orient=tk.HORIZONTAL, length=150, command=self.update_texture_view).pack(side=tk.LEFT, padx=5)
        
        # Show zoom percentage
        self.zoom_label = ttk.Label(control_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        # Save button
        ttk.Button(control_frame, text="Save As...", command=self.save_texture).pack(side=tk.RIGHT, padx=5)
        
        # Create a frame for the canvas with scrollbars
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create horizontal scrollbar
        self.x_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create vertical scrollbar
        self.y_scrollbar = ttk.Scrollbar(canvas_frame)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas with dark background for better visibility
        self.texture_canvas = tk.Canvas(canvas_frame, bg="grey20", 
                                       xscrollcommand=self.x_scrollbar.set, 
                                       yscrollcommand=self.y_scrollbar.set)
        self.texture_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.x_scrollbar.config(command=self.texture_canvas.xview)
        self.y_scrollbar.config(command=self.texture_canvas.yview)
        
        # Configure canvas for mouse wheel and drag navigation
        self.texture_canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.texture_canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.texture_canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down
        self.texture_canvas.bind("<Button-1>", self.start_pan)
        self.texture_canvas.bind("<B1-Motion>", self.pan_image)
        self.texture_canvas.bind("<ButtonRelease-1>", self.stop_pan)
        
        # Initialize drag variables
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Status label
        self.texture_status = ttk.Label(right_frame, text="No texture loaded")
        self.texture_status.pack(fill=tk.X, padx=5, pady=5)
        
        # Store references to currently loaded texture
        self.current_texture = {
            "path": None,
            "image": None,
            "photo": None,
            "canvas_image": None,
            "original_size": (0, 0),  # Store original size for scaling
            "canvas_size": (0, 0)     # Store canvas size for auto-fitting
        }
        
        # Configure canvas resize event
        self.texture_canvas.bind("<Configure>", self.on_canvas_resize)
    
    def fit_texture_to_view(self):
        """Fit the current texture to the canvas view"""
        if not self.current_texture["image"]:
            return
            
        # Get current canvas dimensions
        canvas_width = self.texture_canvas.winfo_width()
        canvas_height = self.texture_canvas.winfo_height()
        
        # Get original image dimensions
        img_width, img_height = self.current_texture["original_size"]
        
        if img_width <= 0 or img_height <= 0 or canvas_width <= 0 or canvas_height <= 0:
            return
            
        # Calculate scale factor to fit image to canvas while maintaining aspect ratio
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        
        # Use the smaller ratio to ensure the entire image fits
        scale = min(width_ratio, height_ratio) * 0.9  # 90% of fit to add some padding
        
        # Update zoom level
        self.zoom_level.set(scale)
        
        # Update zoom label
        self.zoom_label.config(text=f"{int(scale * 100)}%")
        
        # Update texture view
        self.update_texture_view()
        
        # Center the image
        self.center_image()
    
    def center_image(self):
        """Center the image in the canvas"""
        if not self.current_texture["canvas_image"]:
            return
            
        self.texture_canvas.update_idletasks()  # Ensure canvas is updated
        
        # Get canvas dimensions
        canvas_width = self.texture_canvas.winfo_width()
        canvas_height = self.texture_canvas.winfo_height()
        
        # Get current scroll region
        region = self.texture_canvas.bbox(tk.ALL)
        if not region:
            return
            
        img_width = region[2] - region[0]
        img_height = region[3] - region[1]
        
        # Calculate center position
        x = max(0, (canvas_width - img_width) // 2)
        y = max(0, (canvas_height - img_height) // 2)
        
        # Center the image by moving it
        self.texture_canvas.coords(self.current_texture["canvas_image"], x, y)
        
        # Update scroll region to accommodate the image
        new_region = (0, 0, max(canvas_width, img_width + x), max(canvas_height, img_height + y))
        self.texture_canvas.configure(scrollregion=new_region)
    
    def on_canvas_resize(self, event):
        """Handle canvas resize event"""
        if self.current_texture["image"]:
            # Store new canvas size
            self.current_texture["canvas_size"] = (event.width, event.height)
            
            # Automatically resize and center image if it's smaller than the canvas
            current_zoom = self.zoom_level.get()
            img_width, img_height = self.current_texture["original_size"]
            
            scaled_width = int(img_width * current_zoom)
            scaled_height = int(img_height * current_zoom)
            
            if scaled_width <= event.width and scaled_height <= event.height:
                # If image is smaller than canvas, center it
                self.center_image()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel events for zooming"""
        if not self.current_texture["image"]:
            return
            
        # Determine direction of scroll
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # Scroll up - zoom in
            delta = 0.1
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # Scroll down - zoom out
            delta = -0.1
        else:
            return
            
        # Get current zoom level
        current_zoom = self.zoom_level.get()
        
        # Calculate new zoom level (constrained)
        new_zoom = max(0.1, min(4.0, current_zoom + delta))
        
        # Get mouse position
        mouse_x = self.texture_canvas.canvasx(event.x)
        mouse_y = self.texture_canvas.canvasy(event.y)
        
        # Get current image position
        img_x, img_y = self.texture_canvas.coords(self.current_texture["canvas_image"])
        
        # Calculate relative mouse position on the image
        rel_x = (mouse_x - img_x) / current_zoom
        rel_y = (mouse_y - img_y) / current_zoom
        
        # Update zoom level
        self.zoom_level.set(new_zoom)
        
        # Update zoom label
        self.zoom_label.config(text=f"{int(new_zoom * 100)}%")
        
        # Update the texture view (this will resize the image)
        self.update_texture_view()
        
        # Get new image position
        img_x, img_y = self.texture_canvas.coords(self.current_texture["canvas_image"])
        
        # Calculate new target position to maintain mouse point
        target_x = mouse_x - (rel_x * new_zoom)
        target_y = mouse_y - (rel_y * new_zoom)
        
        # Move image to maintain focal point
        self.texture_canvas.move(self.current_texture["canvas_image"], 
                               target_x - img_x, target_y - img_y)
        
        # Update scroll region
        self.update_scroll_region()
    
    def start_pan(self, event):
        """Start panning the image"""
        if not self.current_texture["canvas_image"]:
            return
            
        # Save starting coordinates
        self.texture_canvas.scan_mark(event.x, event.y)
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Change cursor to indicate panning
        self.texture_canvas.config(cursor="fleur")
    
    def pan_image(self, event):
        """Pan the image with mouse drag"""
        if not self.current_texture["canvas_image"]:
            return
            
        # Calculate the delta movement
        delta_x = event.x - self.pan_start_x
        delta_y = event.y - self.pan_start_y
        
        # Perform the drag
        self.texture_canvas.scan_dragto(event.x, event.y, gain=1)
        
        # Update start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def stop_pan(self, event):
        """Stop panning the image"""
        # Reset cursor
        self.texture_canvas.config(cursor="")
    
    def update_scroll_region(self):
        """Update the scroll region to match image size"""
        if not self.current_texture["canvas_image"]:
            return
            
        # Get image bounds
        bbox = self.texture_canvas.bbox(self.current_texture["canvas_image"])
        if not bbox:
            return
            
        # Get canvas size
        canvas_width = self.texture_canvas.winfo_width()
        canvas_height = self.texture_canvas.winfo_height()
        
        # Calculate new scroll region
        scroll_region = (0, 0, 
                        max(canvas_width, bbox[2]), 
                        max(canvas_height, bbox[3]))
        
        # Update canvas scroll region
        self.texture_canvas.config(scrollregion=scroll_region)
    
    def setup_material_preview(self):
        """Set up the material preview panel"""
        # Add a simple message for now
        ttk.Label(self.material_preview_frame, 
                 text="Material preview not implemented yet.").pack(padx=20, pady=20)
        
        # Future implementation would combine diffuse, normal, specular maps
        # to create a realistic material preview
    
    def setup_color_viewer(self):
        """Set up the color viewer panel"""
        # Create frames
        top_frame = ttk.Frame(self.color_viewer_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        bottom_frame = ttk.Frame(self.color_viewer_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Color selection dropdown
        ttk.Label(top_frame, text="Select Color:").pack(side=tk.LEFT, padx=5)
        self.color_selector = ttk.Combobox(top_frame, width=30)
        self.color_selector.pack(side=tk.LEFT, padx=5)
        self.color_selector.bind("<<ComboboxSelected>>", self.update_color_display)
        
        # Format selector
        ttk.Label(top_frame, text="Format:").pack(side=tk.LEFT, padx=5)
        self.format_selector = ttk.Combobox(top_frame, width=15, values=["RGB (0-1)", "RGB (0-255)", "HEX", "HSL"])
        self.format_selector.current(0)
        self.format_selector.pack(side=tk.LEFT, padx=5)
        self.format_selector.bind("<<ComboboxSelected>>", self.update_color_display)
        
        # Color display canvas
        self.color_canvas = tk.Canvas(bottom_frame, width=200, height=200, bg="white")
        self.color_canvas.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Color values frame
        values_frame = ttk.LabelFrame(bottom_frame, text="Color Values")
        values_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Color value displays with labels and copy buttons
        self.color_value_displays = {}
        
        for i, (name, label_text) in enumerate([
            ("r", "R:"), ("g", "G:"), ("b", "B:"), 
            ("a", "A:"), ("hex", "Hex:"), ("hsl", "HSL:")
        ]):
            frame = ttk.Frame(values_frame)
            frame.pack(fill=tk.X, pady=5)
            
            label = ttk.Label(frame, text=label_text, width=5)
            label.pack(side=tk.LEFT, padx=5)
            
            value = ttk.Entry(frame)
            value.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            copy_btn = ttk.Button(frame, text="Copy", 
                                command=lambda v=value: self.root.clipboard_clear() or self.root.clipboard_append(v.get()))
            copy_btn.pack(side=tk.RIGHT, padx=5)
            
            self.color_value_displays[name] = value
        
        # Current color data
        self.current_color = {
            "name": None,
            "r": 0,
            "g": 0,
            "b": 0,
            "a": 1
        }
    
    def update_color_display(self, event=None):
        """Update the color display based on selected color and format"""
        # Get selected color from dropdown
        color_name = self.color_selector.get()
        if not color_name:
            return
        
        format_type = self.format_selector.get()
        r, g, b, a = self.current_color["r"], self.current_color["g"], self.current_color["b"], self.current_color["a"]
        
        # Update canvas color
        # Clamp RGB values to 0-1 range for display
        display_r = max(0, min(1, r))
        display_g = max(0, min(1, g))
        display_b = max(0, min(1, b))
        
        # Convert to hex for canvas
        hex_color = f"#{int(display_r*255):02x}{int(display_g*255):02x}{int(display_b*255):02x}"
        self.color_canvas.configure(bg=hex_color)
        
        # Update value displays based on format
        if format_type == "RGB (0-1)":
            self.color_value_displays["r"].delete(0, tk.END)
            self.color_value_displays["r"].insert(0, f"{r:.6f}")
            
            self.color_value_displays["g"].delete(0, tk.END)
            self.color_value_displays["g"].insert(0, f"{g:.6f}")
            
            self.color_value_displays["b"].delete(0, tk.END)
            self.color_value_displays["b"].insert(0, f"{b:.6f}")
            
        elif format_type == "RGB (0-255)":
            self.color_value_displays["r"].delete(0, tk.END)
            self.color_value_displays["r"].insert(0, f"{int(r * 255)}")
            
            self.color_value_displays["g"].delete(0, tk.END)
            self.color_value_displays["g"].insert(0, f"{int(g * 255)}")
            
            self.color_value_displays["b"].delete(0, tk.END)
            self.color_value_displays["b"].insert(0, f"{int(b * 255)}")
            
        elif format_type == "HEX":
            self.color_value_displays["r"].delete(0, tk.END)
            self.color_value_displays["r"].insert(0, f"{int(r * 255):02X}")
            
            self.color_value_displays["g"].delete(0, tk.END)
            self.color_value_displays["g"].insert(0, f"{int(g * 255):02X}")
            
            self.color_value_displays["b"].delete(0, tk.END)
            self.color_value_displays["b"].insert(0, f"{int(b * 255):02X}")
            
        elif format_type == "HSL":
            h, l, s = colorsys.rgb_to_hls(display_r, display_g, display_b)
            
            self.color_value_displays["r"].delete(0, tk.END)
            self.color_value_displays["r"].insert(0, f"H: {h*360:.1f}°")
            
            self.color_value_displays["g"].delete(0, tk.END)
            self.color_value_displays["g"].insert(0, f"S: {s*100:.1f}%")
            
            self.color_value_displays["b"].delete(0, tk.END)
            self.color_value_displays["b"].insert(0, f"L: {l*100:.1f}%")
        
        # Always show alpha
        self.color_value_displays["a"].delete(0, tk.END)
        self.color_value_displays["a"].insert(0, f"{a:.6f}")
        
        # Show hex
        self.color_value_displays["hex"].delete(0, tk.END)
        self.color_value_displays["hex"].insert(0, hex_color)
        
        # Show HSL
        h, l, s = colorsys.rgb_to_hls(display_r, display_g, display_b)
        self.color_value_displays["hsl"].delete(0, tk.END)
        self.color_value_displays["hsl"].insert(0, f"H:{h*360:.1f}° S:{s*100:.1f}% L:{l*100:.1f}%")
    
    def show_color_details(self, event):
        """Show color details when double-clicking a color in the tree"""
        tree = event.widget
        item = tree.selection()[0]
        
        color_name = tree.item(item, "text")
        r = float(tree.item(item, "values")[0])
        g = float(tree.item(item, "values")[1])
        b = float(tree.item(item, "values")[2])
        a = float(tree.item(item, "values")[3])
        
        # Update current color
        self.current_color = {
            "name": color_name,
            "r": r,
            "g": g,
            "b": b,
            "a": a
        }
        
        # Update color selector dropdown
        if color_name not in self.color_selector["values"]:
            colors = list(self.color_selector["values"]) if self.color_selector["values"] else []
            colors.append(color_name)
            self.color_selector["values"] = colors
        
        self.color_selector.set(color_name)
        
        # Switch to color viewer tab
        self.color_notebook.select(self.color_viewer_frame)
        
        # Update display
        self.update_color_display()
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def copy_value(self):
        """Copy selected value to clipboard"""
        for tree in [self.material_tree, self.texture_tree, self.raw_color_tree, 
                    self.norm_color_tree, self.raw_values_tree]:
            if tree.selection():
                item = tree.selection()[0]
                values = tree.item(item, "values")
                if values:
                    # For material tree and raw values, copy the first value
                    if tree in [self.material_tree, self.raw_values_tree]:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(str(values[0]))
                    # For texture tree, copy the path
                    elif tree == self.texture_tree:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(str(values[1]))
                    # For color trees, copy R,G,B values as comma separated
                    else:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(f"{values[0]}, {values[1]}, {values[2]}")
                    return
    
    def on_drop(self, event):
        """Handle files dropped into the application"""
        file_path = event.data
        
        # Remove curly braces if present (Windows)
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
            
        # Handle multiple files
        for path in file_path.split():
            if os.path.exists(path) and os.path.isfile(path):
                if path.lower().endswith('.xbm'):
                    self.open_specific_file(path)
                    return
    
    def on_file_select(self, event):
        """Handle file selection from the file list"""
        item = self.file_list.selection()[0]
        file_path = self.file_list.item(item, "text")
        full_path = os.path.join(os.getcwd(), file_path)
        self.open_specific_file(full_path)
    
    def view_texture_from_list(self, event):
        """Handle double-click on texture in texture list"""
        item = self.texture_tree.selection()[0]
        texture_path = self.texture_tree.item(item, "values")[1]
        texture_type = self.texture_tree.item(item, "values")[0]
        texture_name = self.texture_tree.item(item, "text")
        
        # Switch to texture viewer tab
        self.right_frame.select(self.texture_viewer_frame)
        
        # Load the texture
        if self.game_path.get():
            # Try to find the texture in the game folder
            full_path = self.fix_texture_path(texture_path)
            
            # Show path in debug field
            self.texture_path_debug.configure(state='normal')
            self.texture_path_debug.delete(0, tk.END)
            self.texture_path_debug.insert(0, full_path)
            self.texture_path_debug.configure(state='readonly')
            
            self.log_debug(f"View texture from list: {texture_name} at {full_path}")
            
            if os.path.exists(full_path):
                self.load_texture(full_path, texture_name, texture_type)
            else:
                self.log_debug(f"Texture not found: {full_path}")
                self.texture_status.config(text=f"Texture not found: {full_path}")
                messagebox.showerror("Texture Not Found", 
                                   f"Could not find texture at:\n{full_path}\n\n"
                                   f"Make sure your game path is set correctly.")
        else:
            self.texture_status.config(text="Game data folder not set. Please set it and try again.")
            messagebox.showinfo("Game Path Required", 
                              "Please set the game data folder path and click 'Apply Path'.")
    
    def load_selected_texture(self, event):
        """Load the texture selected in the texture list"""
        selection = self.texture_list_viewer.selection()
        if not selection:
            return
            
        item = selection[0]
        texture_name = self.texture_list_viewer.item(item, "text")
        texture_type = self.texture_list_viewer.item(item, "values")[0]
        
        self.log_debug(f"Load selected texture: {texture_name} | {texture_type}")
        
        # Find the texture path from the main texture tree
        for item in self.texture_tree.get_children():
            if self.texture_tree.item(item, "text") == texture_name:
                texture_path = self.texture_tree.item(item, "values")[1]
                
                # Load the texture
                if self.game_path.get():
                    full_path = self.fix_texture_path(texture_path)
                    
                    # Show path in debug field
                    self.texture_path_debug.configure(state='normal')
                    self.texture_path_debug.delete(0, tk.END)
                    self.texture_path_debug.insert(0, full_path)
                    self.texture_path_debug.configure(state='readonly')
                    
                    self.log_debug(f"Loading texture from path: {full_path}")
                    
                    if os.path.exists(full_path):
                        self.load_texture(full_path, texture_name, texture_type)
                    else:
                        self.log_debug(f"Texture not found: {full_path}")
                        self.texture_status.config(text=f"Texture not found: {full_path}")
                        messagebox.showerror("Texture Not Found", 
                                           f"Could not find texture at:\n{full_path}\n\n"
                                           f"Make sure your game path is set correctly.")
                else:
                    self.texture_status.config(text="Game data folder not set. Please set it and try again.")
                    messagebox.showinfo("Game Path Required", 
                                      "Please set the game data folder path and click 'Apply Path'.")
                return
    
    def convert_xbt_to_image(self, file_path):
        """Convert an XBT file to a PIL Image by removing the header"""
        try:
            with open(file_path, 'rb') as f:
                xbt_data = f.read()
                
            # Log the first bytes to debug
            self.log_debug(f"First 50 bytes of XBT: {' '.join(f'{b:02X}' for b in xbt_data[:50])}")
            
            # Check if this has an XBT header (TBX)
            if xbt_data[:3] == b'TBX':
                self.log_debug("TBX header found, removing first 32 bytes")
                dds_data = xbt_data[32:]  # Skip XBT header (32 bytes)
            else:
                self.log_debug("No TBX header found, trying full data as DDS")
                dds_data = xbt_data
                
            # Save the DDS data to a temporary file
            temp_dds_path = os.path.join(self.temp_dir, os.path.basename(file_path) + ".dds")
            with open(temp_dds_path, 'wb') as f:
                f.write(dds_data)
                
            self.log_debug(f"Saved DDS data to {temp_dds_path}")
            
            # Simple fallback: convert DDS to PNG using PIL
            if pil_support:
                try:
                    # Try to directly load the DDS file
                    self.log_debug("Attempting to load DDS with PIL")
                    image = Image.open(temp_dds_path)
                    return image
                except Exception as e:
                    self.log_debug(f"PIL failed to load DDS: {e}")
                    
                    # If PIL fails to load directly, try with a different approach
                    try:
                        # Make sure it's actually a DDS file (check for signature)
                        with open(temp_dds_path, 'rb') as f:
                            if f.read(4) == b'DDS ':
                                self.log_debug("Valid DDS file signature found")
                            else:
                                self.log_debug("DDS signature not found, trying with 32-byte offset")
                                # Try again with different offset
                                if len(xbt_data) > 64:
                                    dds_data = xbt_data[32:]
                                    with open(temp_dds_path, 'wb') as f:
                                        f.write(dds_data)
                        
                        # Try loading again
                        image = Image.open(temp_dds_path)
                        return image
                    except Exception as err:
                        self.log_debug(f"All loading attempts failed: {err}")
                        # Last resort, create a placeholder image
                        return Image.new("RGB", (256, 256), color=(50, 50, 50))
            else:
                self.log_debug("PIL not available, creating placeholder image")
                # If PIL is not available, create a dummy image
                return Image.new("RGB", (256, 256), color=(50, 50, 50))
                
        except Exception as e:
            self.log_debug(f"Error converting XBT to image: {e}")
            # Return a placeholder image if conversion fails
            return Image.new("RGB", (256, 256), color=(50, 50, 50))
    
    def load_texture(self, file_path, texture_name, texture_type):
        """Load and display a texture file (.xbt)"""
        if not pil_support:
            self.texture_status.config(text="PIL/Pillow not installed. Cannot load textures.")
            return
            
        try:
            self.log_debug(f"Loading texture: {file_path}")
            
            # Check if texture is already in cache
            if file_path in self.texture_cache:
                image = self.texture_cache[file_path]
                self.log_debug("Using cached texture")
            else:
                # Convert XBT to image
                image = self.convert_xbt_to_image(file_path)
                self.log_debug(f"Converted image: {image.mode} {image.size}")
                
                # Cache the image
                self.texture_cache[file_path] = image
            
            # Store current texture info
            self.current_texture["path"] = file_path
            self.current_texture["image"] = image
            self.current_texture["original_size"] = image.size
            
            # Update zoom label
            zoom = self.zoom_level.get()
            self.zoom_label.config(text=f"{int(zoom * 100)}%")
            
            # Update the texture view
            self.update_texture_view()
            
            # Try to auto-fit the texture
            self.fit_texture_to_view()
            
            # Update status
            self.texture_status.config(text=f"Loaded: {texture_name} [{texture_type}] - {image.width}x{image.height}")
            self.status_bar.config(text=f"Loaded texture: {texture_name}")
            
        except Exception as e:
            import traceback
            self.log_debug(f"Error loading texture: {e}")
            self.log_debug(traceback.format_exc())
            self.texture_status.config(text=f"Error loading texture: {e}")
            
            # Show more user-friendly error
            messagebox.showerror("Error Loading Texture", 
                               f"Failed to load texture: {texture_name}\n\n"
                               f"Error: {e}\n\n"
                               "You can try using the 'Save Raw XBT' button in the Debug tab to save\n"
                               "the raw texture file for external conversion.")
    
    def update_texture_view(self, *args):
        """Update the texture view with current channel settings"""
        if not self.current_texture["image"]:
            return
            
        try:
            # Get original image
            image = self.current_texture["image"].copy()
            self.log_debug(f"Updating texture view for image: {image.mode} {image.size}")
            
            # Get channel settings
            r_enabled = self.channel_var["r"].get()
            g_enabled = self.channel_var["g"].get()
            b_enabled = self.channel_var["b"].get()
            
            # Split into channels
            if hasattr(image, 'split'):
                try:
                    channels = list(image.split())
                    self.log_debug(f"Split image into {len(channels)} channels")
                    
                    # If RGB image
                    if len(channels) >= 3:
                        # Mask channels by booleans (set to zero if disabled)
                        if not r_enabled:
                            channels[0] = Image.new("L", channels[0].size, 0)
                        if not g_enabled:
                            channels[1] = Image.new("L", channels[1].size, 0)
                        if not b_enabled:
                            channels[2] = Image.new("L", channels[2].size, 0)
                        
                        # Merge channels back
                        if len(channels) == 3:
                            image = Image.merge("RGB", channels)
                        else:
                            # RGBA image
                            image = Image.merge("RGBA", channels)
                except Exception as e:
                    self.log_debug(f"Error splitting/merging channels: {e}")
            
            # Apply zoom
            zoom = self.zoom_level.get()
            if zoom != 1.0:
                new_size = (int(image.width * zoom), int(image.height * zoom))
                image = image.resize(new_size, Image.LANCZOS)
                
                # Update zoom label
                self.zoom_label.config(text=f"{int(zoom * 100)}%")
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update canvas
            self.texture_canvas.delete("all")
            canvas_image = self.texture_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            
            # Store reference to prevent garbage collection
            self.current_texture["photo"] = photo
            self.current_texture["canvas_image"] = canvas_image
            
            # Update scroll region
            self.update_scroll_region()
            
        except Exception as e:
            import traceback
            self.log_debug(f"Error updating texture view: {e}")
            self.log_debug(traceback.format_exc())
            self.texture_status.config(text=f"Error updating texture view: {e}")
    
    def save_texture(self):
        """Save the currently viewed texture to a file"""
        if not self.current_texture["image"]:
            return
            
        try:
            # Get the image name
            texture_name = os.path.basename(self.current_texture["path"])
            texture_name = os.path.splitext(texture_name)[0]
            
            # Ask for save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")],
                initialfile=texture_name
            )
            
            if save_path:
                # Apply channels
                image = self.current_texture["image"].copy()
                
                # Get channel settings
                r_enabled = self.channel_var["r"].get()
                g_enabled = self.channel_var["g"].get()
                b_enabled = self.channel_var["b"].get()
                
                # Split into channels
                if hasattr(image, 'split'):
                    channels = list(image.split())
                    
                    # If RGB image
                    if len(channels) >= 3:
                        # Mask channels by booleans (set to zero if disabled)
                        if not r_enabled:
                            channels[0] = Image.new("L", channels[0].size, 0)
                        if not g_enabled:
                            channels[1] = Image.new("L", channels[1].size, 0)
                        if not b_enabled:
                            channels[2] = Image.new("L", channels[2].size, 0)
                        
                        # Merge channels back
                        if len(channels) == 3:
                            image = Image.merge("RGB", channels)
                        else:
                            # RGBA image
                            image = Image.merge("RGBA", channels)
                
                # Save the image
                image.save(save_path)
                self.texture_status.config(text=f"Saved texture to: {save_path}")
                self.status_bar.config(text=f"Saved texture to: {save_path}")
        except Exception as e:
            import traceback
            self.log_debug(f"Error saving texture: {e}")
            self.log_debug(traceback.format_exc())
            self.texture_status.config(text=f"Error saving texture: {e}")
    
    def check_current_directory(self):
        """Check for .xbm files in current directory"""
        current_dir = os.getcwd()
        xbm_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.xbm')]
        
        # Clear file list
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        if xbm_files:
            # For each .xbm file, get material name and add to list
            for file_name in xbm_files:
                file_path = os.path.join(current_dir, file_name)
                
                # Check if material name is cached
                if file_path in self.material_cache:
                    material_name = self.material_cache[file_path]
                else:
                    material_name = self.get_material_name_from_file(file_path)
                    self.material_cache[file_path] = material_name
                
                self.file_list.insert("", tk.END, text=file_name, values=(material_name,))
            
            # Open the first file
            self.open_specific_file(os.path.join(current_dir, xbm_files[0]))
        else:
            self.file_label.config(text="No .xbm files found in current directory. Please use Browse button.")
    
    def get_material_name_from_file(self, file_path):
        """Extract just the material name from a file without loading everything"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(1024)  # Just read the first 1KB which should contain the material name
                
                # Look for a pattern like "DUMPTRUCK_PART\x00..."
                for match in re.finditer(b'[A-Z0-9_]{5,}\\x00', data):
                    name = match.group(0)[:-1].decode('ascii', errors='ignore')
                    if '_PART' in name or '_WINGS' in name or len(name) > 8:
                        return name
            return "Unknown"
        except Exception:
            return "Error"
    
    def open_file(self):
        """Open file dialog to select a .xbm file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("XBM files", "*.xbm"), ("All files", "*.*")]
        )
        
        if file_path:
            self.open_specific_file(file_path)
            
            # Update file list in case we opened a file from another directory
            if os.path.dirname(file_path) == os.getcwd():
                self.check_current_directory()
    
    def open_specific_file(self, file_path):
        """Open and parse a specific file"""
        self.file_label.config(text=f"File: {os.path.basename(file_path)}")
        
        # Clear previous data
        self.clear_all_trees()
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Store current material file path and data
            self.current_material = file_path
            self.current_material_data = data
            
            # Display hex view
            self.display_hex_view(data)
            
            # Parse and display the file data
            self.parse_file(data)
            
            # Reset color selector
            self.color_selector["values"] = []
            self.color_selector.set("")
            
            # Reset texture viewer list
            for item in self.texture_list_viewer.get_children():
                self.texture_list_viewer.delete(item)
                
            # Populate texture viewer list with textures from this material
            game_path = self.game_path.get()
            if game_path and os.path.exists(game_path):
                self.reload_material_textures()
            else:
                # No game path set, still populate the list but without status
                for item in self.texture_tree.get_children():
                    texture_name = self.texture_tree.item(item, "text")
                    texture_type = self.texture_tree.item(item, "values")[0]
                    self.texture_list_viewer.insert("", tk.END, text=texture_name, 
                                                  values=(texture_type, "?"))
            
            # Update status bar
            self.status_bar.config(text=f"Loaded material: {os.path.basename(file_path)}")
            
        except Exception as e:
            import traceback
            self.log_debug(f"Error opening file: {e}")
            self.log_debug(traceback.format_exc())
            self.material_tree.insert("", tk.END, text="Error", values=(f"Failed to open file: {e}",))
    
    def clear_all_trees(self):
        """Clear all treeviews"""
        for tree in [self.material_tree, self.texture_tree, self.raw_color_tree, 
                    self.norm_color_tree, self.raw_values_tree, self.texture_list_viewer]:
            for item in tree.get_children():
                tree.delete(item)
        self.hex_text.delete(1.0, tk.END)
        
        # Clear texture viewer
        self.texture_canvas.delete("all")
        self.current_texture = {
            "path": None,
            "image": None,
            "photo": None,
            "canvas_image": None,
            "original_size": (0, 0),
            "canvas_size": (0, 0)
        }
        self.texture_status.config(text="No texture loaded")
        
        # Clear texture path debug
        self.texture_path_debug.configure(state='normal')
        self.texture_path_debug.delete(0, tk.END)
        self.texture_path_debug.configure(state='readonly')
    
    def display_hex_view(self, data):
        """Display hex view of the file data"""
        hex_dump = ""
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_values = ' '.join(f"{b:02X}" for b in chunk)
            ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            
            # Pad hex values to align ASCII column
            hex_values = f"{hex_values:<48}"
            
            hex_dump += f"{i:08X}:  {hex_values}  {ascii_values}\n"
        
        self.hex_text.insert(tk.END, hex_dump)
    
    def parse_file(self, data):
        """Parse the entire file"""
        # First, check if this is a valid file
        if len(data) < 8:
            self.material_tree.insert("", tk.END, text="Error", values=("File too small to be valid",))
            return
        
        # Extract material name
        self.extract_material_name(data)
        
        # Extract textures
        self.extract_textures(data)
        
        # Extract all properties
        self.extract_all_properties(data)
    
    def extract_material_name(self, data):
        """Extract the material name from the file"""
        # Look for a pattern like "DUMPTRUCK_PART\x00..."
        for match in re.finditer(b'[A-Z0-9_]{5,}\\x00', data):
            name = match.group(0)[:-1].decode('ascii', errors='ignore')
            if '_PART' in name or '_WINGS' in name or len(name) > 8:
                self.material_tree.insert("", tk.END, text="Material Name", values=(name,))
                # Look for Generic type following material name
                generic_pos = data.find(b'Generic', match.end(), match.end() + 20)
                if generic_pos != -1:
                    self.material_tree.insert("", tk.END, text="Material Type", values=("Generic",))
                return
    
    def extract_textures(self, data):
        """Extract texture information from the file"""
        # Look for texture paths pattern (more robust)
        textures_found = 0
        
        # First, identify typical texture path patterns
        texture_patterns = []
        
        # Find all occurrences of graphics\ followed by a path and .xbt
        i = 0
        while i < len(data) - 20:
            # Look for patterns like "graphics\" or "graphics/"
            if (data[i:i+9] == b'graphics\\' or data[i:i+9] == b'graphics/'):
                path_start = i
                # Find the end of the path (null terminator)
                path_end = data.find(b'\x00', path_start)
                
                if path_end != -1 and path_end - path_start < 100:
                    # Extract the path
                    path = data[path_start:path_end].decode('ascii', errors='ignore')
                    
                    if path.endswith('.xbt'):
                        self.log_debug(f"Found texture path: {path}")
                        texture_patterns.append((path_start, path_end, path))
                        textures_found += 1
                
                i = max(path_end, i + 1)
            else:
                i += 1
        
        self.log_debug(f"Found {textures_found} texture paths")
        
        # Now extract the texture types
        for idx, (path_start, path_end, path) in enumerate(texture_patterns):
            texture_name = os.path.basename(path)
            self.log_debug(f"Processing texture {idx+1}: {texture_name}")
            
            # Look for the texture type that should follow after the path
            type_start = path_end + 1
            
            # Skip any null bytes
            while type_start < len(data) and data[type_start] == 0:
                type_start += 1
            
            # Find the end of the type string (null terminator)
            if type_start < len(data):
                type_end = data.find(b'\x00', type_start)
                
                if type_end != -1 and type_end - type_start < 30:
                    # Try to decode the type
                    try:
                        # Skip non-ASCII characters at the beginning
                        offset = 0
                        while type_start + offset < type_end and (data[type_start + offset] < 32 or data[type_start + offset] > 126):
                            offset += 1
                        
                        if type_start + offset < type_end:
                            # Extract the type string
                            type_bytes = data[type_start + offset:type_end]
                            try:
                                texture_type = type_bytes.decode('ascii', errors='ignore')
                                self.log_debug(f"Raw type bytes: {' '.join(f'{b:02X}' for b in type_bytes)}")
                                self.log_debug(f"Decoded type: {texture_type}")
                            except:
                                texture_type = "Unknown"
                                self.log_debug(f"Failed to decode type bytes: {' '.join(f'{b:02X}' for b in type_bytes)}")
                            
                            # Look ahead to find a known texture type pattern
                            known_types = ["DiffuseTexture", "NormalTexture", "SpecularTexture", "MaskTexture", "IlluminationTexture"]
                            for known_type in known_types:
                                known_pos = data.find(known_type.encode('ascii'), type_end, type_end + 100)
                                if known_pos != -1:
                                    # Found a known type after this texture path
                                    known_end = data.find(b'\x00', known_pos)
                                    if known_end != -1:
                                        known_type_full = data[known_pos:known_end].decode('ascii', errors='ignore')
                                        self.log_debug(f"Found known type: {known_type_full}")
                                        texture_type = known_type_full
                                        break
                        else:
                            texture_type = "Unknown"
                            self.log_debug("No valid ASCII characters in type string")
                            
                            # Look ahead for known texture types
                            for known_start in range(type_end, min(type_end + 100, len(data))):
                                if 32 <= data[known_start] <= 126:  # ASCII character
                                    known_end = data.find(b'\x00', known_start)
                                    if known_end != -1 and known_end - known_start < 30:
                                        potential_type = data[known_start:known_end].decode('ascii', errors='ignore')
                                        if any(t in potential_type for t in ["Texture", "Map"]):
                                            self.log_debug(f"Found potential type: {potential_type}")
                                            texture_type = potential_type
                                            break
                    except:
                        texture_type = "Unknown"
                        self.log_debug(f"Exception processing type at offset {type_start}")
                
                    # Add the texture to the tree view
                    self.texture_tree.insert("", tk.END, text=texture_name, values=(texture_type, path))
                    self.log_debug(f"Added texture {idx+1}: {texture_name} ({texture_type})")
                else:
                    # Type string too long or not found, use default
                    self.texture_tree.insert("", tk.END, text=texture_name, values=("Unknown", path))
                    self.log_debug(f"Added texture {idx+1} with unknown type: {texture_name}")
            else:
                # No type information found, use default
                self.texture_tree.insert("", tk.END, text=texture_name, values=("Unknown", path))
                self.log_debug(f"Added texture {idx+1} with no type data: {texture_name}")
        
        # If no textures found with standard pattern, look harder
        if textures_found == 0:
            self.log_debug("No textures found with standard pattern, trying looser search")
            i = 0
            while i < len(data) - 20:
                # Look for .xbt file extension
                if data[i:i+4] == b'.xbt':
                    # Try to find the start of the path
                    path_end = i + 4
                    path_start = max(0, i - 100)  # Look up to 100 chars back
                    
                    # Find potential start of path
                    for j in range(i-1, path_start, -1):
                        if data[j] < 32 or data[j] > 126:  # Non-printable ASCII
                            path_start = j + 1
                            break
                    
                    if path_end - path_start > 10:  # Reasonable path length
                        path = data[path_start:path_end].decode('ascii', errors='ignore')
                        self.log_debug(f"Found potential path: {path}")
                        
                        texture_name = os.path.basename(path)
                        self.texture_tree.insert("", tk.END, text=texture_name, values=("Unknown", path))
                        textures_found += 1
                
                i += 1
        
        self.log_debug(f"Total textures found and added: {textures_found}")
    
    def extract_all_properties(self, data):
        """Extract all properties from the file by scanning for ASCII text patterns"""
        # Scan through the file looking for potential property names
        i = 0
        while i < len(data) - 5:  # Need at least 5 bytes for a minimal property
            # Check if this could be the start of an ASCII property name
            if all(32 <= b <= 126 for b in data[i:i+5]):
                # Try to find the end of the property name (null terminator)
                name_end = data.find(b'\x00', i)
                if name_end != -1 and name_end - i < 50:  # Reasonable property name length
                    try:
                        # Extract the property name
                        prop_name = data[i:name_end].decode('ascii')
                        
                        # Skip if it's not a valid property name pattern
                        if not re.match(r'^[A-Za-z0-9_]+$', prop_name) or len(prop_name) < 3:
                            i += 1
                            continue
                        
                        # Value starts right after the null terminator
                        val_pos = name_end + 1
                        
                        # Only process if there are at least 4 bytes for the value
                        if val_pos + 4 <= len(data):
                            # Extract the property value bytes
                            val_bytes = data[val_pos:val_pos+4]
                            hex_val = ' '.join(f"{b:02X}" for b in val_bytes)
                            
                            # Try to interpret as different types
                            try:
                                float_val = struct.unpack("<f", val_bytes)[0]
                                int_val = struct.unpack("<i", val_bytes)[0]
                                
                                # Add to raw values tree for debugging
                                self.raw_values_tree.insert("", tk.END, text=prop_name, 
                                                         values=(hex_val, f"{float_val:.6f}", f"{int_val}"))
                                
                                # Determine property type based on name and value
                                if "Color" in prop_name:
                                    # This is a color property - expect 3 or 4 float values (RGB or RGBA)
                                    self.extract_color_property(data, prop_name, val_pos)
                                elif "Enabled" in prop_name or prop_name == "TwoSided":
                                    # This is a boolean property - first byte should be 0 or 1
                                    bool_val = data[val_pos] == 1
                                    self.material_tree.insert("", tk.END, text=prop_name, values=(f"{bool_val}",))
                                elif "Tiling" in prop_name or "Power" in prop_name:
                                    # This is likely a float property with a reasonable value
                                    if abs(float_val) < 1e10 and not (abs(float_val) < 1e-10 and float_val != 0):
                                        self.material_tree.insert("", tk.END, text=prop_name, values=(f"{float_val:.2f}",))
                                elif "Priority" in prop_name or "Id" in prop_name or "Channel" in prop_name:
                                    # This is likely an integer property
                                    self.material_tree.insert("", tk.END, text=prop_name, values=(f"{int_val}",))
                                else:
                                    # Best guess based on the value
                                    if abs(float_val) < 1000 and not (abs(float_val) < 0.001 and float_val != 0):
                                        # Looks like a reasonable float
                                        self.material_tree.insert("", tk.END, text=prop_name, values=(f"{float_val:.6f}",))
                                    elif 0 <= int_val < 1000:
                                        # Looks like a reasonable integer
                                        self.material_tree.insert("", tk.END, text=prop_name, values=(f"{int_val}",))
                            except Exception as e:
                                self.log_debug(f"Error parsing property {prop_name}: {e}")
                            
                            # Move past this property
                            i = val_pos
                        else:
                            i += 1
                    except:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
    
    def extract_color_property(self, data, color_name, val_pos):
        """Extract a color property that has RGB or RGBA values"""
        try:
            if val_pos + 12 <= len(data):  # Need at least 12 bytes for RGB
                # Read RGB values as float32
                r = struct.unpack("<f", data[val_pos:val_pos+4])[0]
                g = struct.unpack("<f", data[val_pos+4:val_pos+8])[0]
                b = struct.unpack("<f", data[val_pos+8:val_pos+12])[0]
                
                # Try to read alpha if present
                a = 1.0
                if val_pos + 16 <= len(data):
                    try:
                        a_val = struct.unpack("<f", data[val_pos+12:val_pos+16])[0]
                        if 0 <= a_val <= 1.0 or a_val == 0:
                            a = a_val
                    except:
                        pass
                
                # Add to raw color tree
                self.raw_color_tree.insert("", tk.END, text=color_name, 
                                         values=(f"{r:.6f}", f"{g:.6f}", f"{b:.6f}", f"{a:.6f}"))
                
                # Calculate normalized values
                max_val = max(r, g, b, 1.0)
                nr = r / max_val if max_val > 0 else 0
                ng = g / max_val if max_val > 0 else 0
                nb = b / max_val if max_val > 0 else 0
                
                # Add to normalized color tree
                self.norm_color_tree.insert("", tk.END, text=color_name, 
                                          values=(f"{nr:.6f}", f"{ng:.6f}", f"{nb:.6f}", f"{a:.6f}"))
                
                # Add to color selector dropdown
                colors = list(self.color_selector["values"]) if self.color_selector["values"] else []
                colors.append(color_name)
                self.color_selector["values"] = colors
        except Exception as e:
            self.log_debug(f"Error extracting color property {color_name}: {e}")
    
    def __del__(self):
        """Clean up temp files when the application exits"""
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

def main():
    # Use TkinterDnD.Tk for drag and drop support if available
    if dnd_support:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = MaterialViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()