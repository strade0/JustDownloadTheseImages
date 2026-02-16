"""
Just Download these Images
A simple desktop app to collect images from clipboard and batch download them.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sys
import os


class ImageCollector:
    def __init__(self, root):
        self.root = root
        self.root.title("Just Download these Images")
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        
        # Store collected images (PIL Image objects)
        self.images = []
        # Store custom names for each image
        self.image_names = []
        # Store thumbnail references (to prevent garbage collection)
        self.thumbnail_refs = []
        
        # Thumbnail size
        self.thumb_size = (120, 120)
        
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container with extra padding for breathing room
        main_frame = tk.Frame(self.root, bg="#1e1e1e", padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with instructions and image count
        top_frame = tk.Frame(main_frame, bg="#1e1e1e")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Instructions label
        self.status_label = tk.Label(
            top_frame, 
            text="Press Ctrl+V to paste images from clipboard",
            font=("Segoe UI", 10),
            bg="#1e1e1e", fg="#aaaaaa",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Image count label
        self.count_label = tk.Label(
            top_frame,
            text="Images: 0",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e", fg="#cccccc"
        )
        self.count_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Scrollable canvas for thumbnails — rounded feel via border frame
        canvas_border = tk.Frame(main_frame, bg="#353535", padx=1, pady=1)
        canvas_border.pack(fill=tk.BOTH, expand=True)
        
        canvas_frame = tk.Frame(canvas_border, bg="#232323")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#232323", highlightthickness=0, bd=0)
        self.scrollbar_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        
        # Don't pack scrollbars initially — they appear dynamically when needed
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar_y_visible = False
        self._scrollbar_x_visible = False
        
        # Frame inside canvas to hold thumbnails
        self.thumb_frame = tk.Frame(self.canvas, bg="#232323")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.thumb_frame, anchor=tk.NW)
        
        # Placeholder text drawn directly on canvas (centered)
        self._placeholder_id = self.canvas.create_text(
            0, 0,
            text="No images yet\n\nCopy an image (right-click → Copy Image)\nthen press  Ctrl+V  here to add it",
            font=("Segoe UI", 13),
            fill="#666666",
            justify=tk.CENTER,
            anchor=tk.CENTER
        )
        self._placeholder_visible = True
        
        # Bottom button bar
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, pady=(12, 0))
        
        # Custom flat buttons with dark semi-transparent look
        btn_cfg = dict(
            font=("Segoe UI", 10),
            bg="#383838", fg="#dddddd",
            activebackground="#4a4a4a", activeforeground="#ffffff",
            bd=0, relief=tk.FLAT,
            padx=20, pady=10,
            cursor="hand2"
        )
        
        self.clear_btn = tk.Button(
            button_frame,
            text="🗑  Clear All",
            command=self.clear_all,
            **btn_cfg
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.download_btn = tk.Button(
            button_frame,
            text="💾  Download All",
            command=self.download_all,
            **btn_cfg
        )
        self.download_btn.pack(side=tk.RIGHT)
        
        # Subtle hover effects on buttons
        for btn in (self.clear_btn, self.download_btn):
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#4a4a4a"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#383838"))
        
        # Bind canvas resize
        self.thumb_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
    
    def setup_bindings(self):
        """Set up keyboard bindings."""
        self.root.bind("<Control-v>", self.paste_image)
        self.root.bind("<Control-V>", self.paste_image)
    
    def on_frame_configure(self, event=None):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar_visibility()
    
    def on_canvas_configure(self, event=None):
        """Reflow thumbnails when canvas is resized."""
        # Keep placeholder centered in the canvas
        if self._placeholder_visible:
            cx = self.canvas.winfo_width() // 2
            cy = self.canvas.winfo_height() // 2
            self.canvas.coords(self._placeholder_id, cx, cy)
        if self.images:
            self.refresh_thumbnails()
        self._update_scrollbar_visibility()
    
    def _update_scrollbar_visibility(self):
        """Show/hide scrollbars based on whether content overflows the canvas."""
        bbox = self.canvas.bbox("all")
        if not bbox:
            if self._scrollbar_y_visible:
                self.scrollbar_y.pack_forget()
                self._scrollbar_y_visible = False
            if self._scrollbar_x_visible:
                self.scrollbar_x.pack_forget()
                self._scrollbar_x_visible = False
            return
        
        content_h = bbox[3] - bbox[1]
        content_w = bbox[2] - bbox[0]
        canvas_h = self.canvas.winfo_height()
        canvas_w = self.canvas.winfo_width()
        
        # Vertical scrollbar
        if content_h > canvas_h and not self._scrollbar_y_visible:
            self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y, before=self.canvas)
            self._scrollbar_y_visible = True
        elif content_h <= canvas_h and self._scrollbar_y_visible:
            self.scrollbar_y.pack_forget()
            self._scrollbar_y_visible = False
        
        # Horizontal scrollbar
        if content_w > canvas_w and not self._scrollbar_x_visible:
            self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            self._scrollbar_x_visible = True
        elif content_w <= canvas_w and self._scrollbar_x_visible:
            self.scrollbar_x.pack_forget()
            self._scrollbar_x_visible = False
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling only when vertical scrollbar is visible."""
        if self._scrollbar_y_visible:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def paste_image(self, event=None):
        """Paste image from clipboard."""
        try:
            # Try to get image from clipboard using PIL
            from PIL import ImageGrab
            
            img = ImageGrab.grabclipboard()
            
            if img is None:
                self.status_label.config(text="⚠ No image in clipboard!", fg="#e8a838")
                self.root.after(2000, lambda: self.status_label.config(
                    text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
                return
            
            if isinstance(img, list):
                # It's a list of file paths, not an image
                self.status_label.config(text="⚠ Please copy an image, not a file!", fg="#e8a838")
                self.root.after(2000, lambda: self.status_label.config(
                    text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
                return
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add to collection
            self.images.append(img)
            self.image_names.append(f"image_{len(self.images):03d}")
            self.refresh_thumbnails()
            self.update_count()
            
            self.status_label.config(text="✓ Image added!", fg="#5cb85c")
            self.root.after(1500, lambda: self.status_label.config(
                text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
            
        except Exception as e:
            self.status_label.config(text=f"⚠ Error: {str(e)}", fg="#d9534f")
            self.root.after(3000, lambda: self.status_label.config(
                text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
    
    def refresh_thumbnails(self):
        """Refresh the thumbnail display."""
        # Clear existing thumbnails
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnail_refs.clear()
        
        if not self.images:
            # Show the canvas placeholder text
            self.canvas.itemconfigure(self._placeholder_id, state=tk.NORMAL)
            self._placeholder_visible = True
            # Re-center it
            cx = self.canvas.winfo_width() // 2
            cy = self.canvas.winfo_height() // 2
            self.canvas.coords(self._placeholder_id, cx, cy)
            return
        
        # Hide placeholder when images exist
        self.canvas.itemconfigure(self._placeholder_id, state=tk.HIDDEN)
        self._placeholder_visible = False
        
        # Calculate how many thumbnails per row based on canvas width
        canvas_width = self.canvas.winfo_width()
        thumb_total = self.thumb_size[0] + 20  # thumbnail + padding
        cols = max(1, canvas_width // thumb_total)
        
        # Center the grid horizontally
        total_grid_width = cols * thumb_total
        left_pad = max(0, (canvas_width - total_grid_width) // 2)
        self.thumb_frame.configure(padx=left_pad)
        
        # Create thumbnail grid
        for idx, img in enumerate(self.images):
            row = idx // cols
            col = idx % cols
            
            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail(self.thumb_size, Image.Resampling.LANCZOS)
            
            # Add padding to make all thumbnails same size
            padded = Image.new('RGB', self.thumb_size, (35, 35, 35))
            offset = ((self.thumb_size[0] - thumb.width) // 2, 
                     (self.thumb_size[1] - thumb.height) // 2)
            padded.paste(thumb, offset)
            
            photo = ImageTk.PhotoImage(padded)
            self.thumbnail_refs.append(photo)
            
            # Thumbnail container with subtle border
            thumb_container = tk.Frame(self.thumb_frame, bg="#333333", padx=2, pady=2)
            thumb_container.grid(row=row, column=col, padx=6, pady=6)
            
            # Image label
            label = tk.Label(thumb_container, image=photo, bg="#232323", cursor="hand2")
            label.pack()
            
            # Name label — clickable to rename
            name = self.image_names[idx] if idx < len(self.image_names) else f"image_{idx+1:03d}"
            idx_label = tk.Label(
                thumb_container, 
                text=name, 
                bg="#333333", 
                fg="#aaaaaa",
                font=("Segoe UI", 8),
                cursor="xterm"
            )
            idx_label.pack()
            idx_label.bind("<Button-1>", lambda e, i=idx, lbl=idx_label, tc=thumb_container: self._start_rename(i, lbl, tc))
            
            # Hover & click bindings
            label.bind("<Button-1>", lambda e, i=idx: self.remove_image(i))
            label.bind("<Enter>", lambda e, tc=thumb_container: (
                tc.configure(bg="#e05555"),
                self.status_label.config(text="Click to remove this image", fg="#aaaaaa")
            ))
            label.bind("<Leave>", lambda e, tc=thumb_container: (
                tc.configure(bg="#333333"),
                self.status_label.config(text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa")
            ))
        
        self.on_frame_configure()
    
    def _start_rename(self, index, label_widget, container):
        """Replace the name label with an editable Entry field."""
        label_widget.pack_forget()
        
        entry = tk.Entry(
            container,
            font=("Segoe UI", 8),
            bg="#2a2a2a", fg="#ffffff",
            insertbackground="#ffffff",
            bd=0, relief=tk.FLAT,
            width=14,
            justify=tk.CENTER
        )
        entry.insert(0, self.image_names[index])
        entry.pack(pady=(1, 0))
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        def _finish_rename(event=None):
            new_name = entry.get().strip()
            if new_name:
                self.image_names[index] = new_name
            entry.destroy()
            label_widget.config(text=self.image_names[index])
            label_widget.pack()
        
        entry.bind("<Return>", _finish_rename)
        entry.bind("<FocusOut>", _finish_rename)
        entry.bind("<Escape>", lambda e: (entry.destroy(), label_widget.pack()))
    
    def remove_image(self, index):
        """Remove an image from the collection."""
        if 0 <= index < len(self.images):
            del self.images[index]
            del self.image_names[index]
            self.refresh_thumbnails()
            self.update_count()
            self.status_label.config(text="✓ Image removed!", fg="#5cb85c")
            self.root.after(1500, lambda: self.status_label.config(
                text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
    
    def update_count(self):
        """Update the image count label."""
        count = len(self.images)
        self.count_label.config(text=f"Images: {count}")
    
    def clear_all(self):
        """Clear all images after confirmation."""
        if not self.images:
            messagebox.showinfo("Clear All", "No images to clear!")
            return
        
        if messagebox.askyesno("Clear All", 
                              f"Are you sure you want to remove all {len(self.images)} images?\n\nThis cannot be undone."):
            self.images.clear()
            self.image_names.clear()
            self.refresh_thumbnails()
            self.update_count()
            self.status_label.config(text="✓ All images cleared!", fg="#5cb85c")
            self.root.after(1500, lambda: self.status_label.config(
                text="Press Ctrl+V to paste images from clipboard", fg="#aaaaaa"))
    
    def download_all(self):
        """Download all images to a selected folder."""
        if not self.images:
            messagebox.showinfo("Download All", "No images to download!")
            return
        
        # Ask for folder
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            mustexist=True
        )
        
        if not folder:
            return  # User cancelled
        
        # Save images
        success_count = 0
        errors = []
        
        for idx, img in enumerate(self.images):
            # Use custom name, sanitize for filesystem
            base_name = self.image_names[idx] if idx < len(self.image_names) else f"image_{idx+1:03d}"
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in base_name).strip()
            if not safe_name:
                safe_name = f"image_{idx+1:03d}"
            filename = f"{safe_name}.jpg"
            filepath = os.path.join(folder, filename)
            
            try:
                # Handle existing files
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{safe_name}_{counter}.jpg"
                    filepath = os.path.join(folder, filename)
                    counter += 1
                
                img.save(filepath, "JPEG", quality=95)
                success_count += 1
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        
        # Show result
        if errors:
            messagebox.showwarning(
                "Download Complete",
                f"Saved {success_count} images.\n\nErrors:\n" + "\n".join(errors)
            )
        else:
            messagebox.showinfo(
                "Download Complete",
                f"Successfully saved {success_count} images to:\n{folder}"
            )
            
            # Ask if user wants to clear
            if messagebox.askyesno("Clear Images?", 
                                  "Would you like to clear the collected images now?"):
                self.images.clear()
                self.image_names.clear()
                self.refresh_thumbnails()
                self.update_count()


def main():
    root = tk.Tk()
    
    # Set window icon (works both in dev and PyInstaller-bundled mode)
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # Set dark theme colors
    root.configure(bg="#1e1e1e")
    
    style = ttk.Style()
    style.theme_use("clam")
    
    # Configure dark theme — only scrollbars use ttk now
    style.configure(".", background="#1e1e1e", foreground="#cccccc", fieldbackground="#2b2b2b")
    style.configure("TFrame", background="#232323")
    style.configure("Vertical.TScrollbar", background="#3a3a3a", troughcolor="#232323",
                    bordercolor="#232323", arrowcolor="#888888")
    style.configure("Horizontal.TScrollbar", background="#3a3a3a", troughcolor="#232323",
                    bordercolor="#232323", arrowcolor="#888888")
    
    app = ImageCollector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
