import os
import sys
import shutil
import string
from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Determine base path depending on whether running as EXE or script
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

libs_path = os.path.join(base_path, "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

CURRENT_HOTLIST_FOLDER = os.path.basename(os.getcwd())
HOTLIST_FILE = "hotlist.txt"
IMG_DIR = "imgs"

os.makedirs(IMG_DIR, exist_ok=True)

CATEGORIES = [
    "Fighter",
    "Bomber",
    "Attack",
    "Transport",
    "Tanker",
    "Helicopter",
    "UAV",
    "Trainer",
    "Reconnaissance",
    "Civilian",
    "Other",
]

# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def safe_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").lower()

def load_hotlist():
    data = {}
    if not os.path.exists(HOTLIST_FILE):
        return data
    with open(HOTLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            name, cat = line.strip().split("|", 1)
            data[name.strip()] = cat.strip()
    return data

def save_hotlist(data):
    with open(HOTLIST_FILE, "w", encoding="utf-8") as f:
        for name, cat in data.items():
            f.write(f"{name} | {cat}\n")

# ---------------------------------------------------------
# Dark Theme
# ---------------------------------------------------------

def setup_dark_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except:
        pass

    bg = "#202020"
    panel = "#2d2d2d"
    text = "#e6e6e6"
    accent = "#0078d7"

    root.configure(bg=bg)

    style.configure(".", background=bg, foreground=text, fieldbackground=panel)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=text)
    style.configure("TButton", background=panel, foreground=text, padding=5)
    style.map("TButton",
              background=[("active", accent)],
              foreground=[("active", text)])
    style.configure("Treeview",
                    background=panel,
                    foreground=text,
                    fieldbackground=panel,
                    rowheight=22)
    style.map("Treeview",
              background=[("selected", accent)],
              foreground=[("selected", text)])
    style.configure("TCombobox",
                    fieldbackground=panel,
                    background=panel,
                    foreground=text)
    style.map("TCombobox",
              fieldbackground=[("readonly", panel)],
              foreground=[("readonly", text)])

# ---------------------------------------------------------
# Main App
# ---------------------------------------------------------

class HotlistManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VACR Hotlist & Image Manager")
        self.root.geometry("1100x600")

        setup_dark_theme(root)

        self.hotlist = load_hotlist()
        self.current_name = None
        self.current_thumbnail = None

        self.build_ui()
        self.refresh_aircraft_list()

    # -----------------------------------------------------
    # UI Layout
    # -----------------------------------------------------

    def build_ui(self):
        main_pane = ttk.Panedwindow(self.root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=8, pady=8)

        # Left pane
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)

        # Right pane
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=3)

        self.hotlist_label = ttk.Label(left_frame, text=f"Hotlist Loaded: {CURRENT_HOTLIST_FOLDER}")
        self.hotlist_label.pack(anchor="w", pady=(0, 5))

        # Left: Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x", pady=(0, 5))

        ttk.Button(btn_frame, text="Add Aircraft", command=self.add_aircraft).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete Aircraft", command=self.delete_aircraft).pack(side="left", padx=2)

        ttk.Button(btn_frame, text="Export Set", command=self.export_set).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="Import Set", command=self.import_set).pack(side="right", padx=2)

        # Left: Aircraft list
        self.tree = ttk.Treeview(left_frame, columns=("Name",), show="headings", selectmode="browse")
        self.tree.heading("Name", text="Aircraft Name")
        self.tree.column("Name", width=250, anchor="w")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_aircraft)

        # Right: Details
        details = ttk.Frame(right_frame)
        details.pack(fill="both", expand=True)

        # Name
        name_row = ttk.Frame(details)
        name_row.pack(fill="x", pady=(0, 5))
        ttk.Label(name_row, text="Name:").pack(side="left")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_row, textvariable=self.name_var)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Category
        cat_row = ttk.Frame(details)
        cat_row.pack(fill="x", pady=(0, 5))
        ttk.Label(cat_row, text="Category:").pack(side="left")
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(cat_row, textvariable=self.cat_var, values=CATEGORIES, state="readonly")
        self.cat_combo.pack(side="left", fill="x", expand=True, padx=5)

        # Save button
        save_row = ttk.Frame(details)
        save_row.pack(fill="x", pady=(0, 10))
        ttk.Button(save_row, text="Save Changes", command=self.save_changes).pack(side="left")

        # Images label
        ttk.Label(details, text="Images:").pack(anchor="w")

        # Split image list + preview
        img_split = ttk.Panedwindow(details, orient="horizontal")
        img_split.pack(fill="both", expand=True)

        # Left: Listbox
        img_list_frame = ttk.Frame(img_split)
        img_split.add(img_list_frame, weight=1)

        self.img_listbox = tk.Listbox(
            img_list_frame,
            bg="#2d2d2d",
            fg="#e6e6e6",
            selectbackground="#0078d7",
            activestyle="none",
            highlightthickness=0,
        )
        img_scroll = ttk.Scrollbar(img_list_frame, orient="vertical", command=self.img_listbox.yview)
        self.img_listbox.config(yscrollcommand=img_scroll.set)

        self.img_listbox.pack(side="left", fill="both", expand=True)
        img_scroll.pack(side="right", fill="y")

        self.img_listbox.bind("<<ListboxSelect>>", self.update_thumbnail)

        # Drag & Drop support
        self.img_listbox.drop_target_register(DND_FILES)
        self.img_listbox.dnd_bind("<<Drop>>", self.handle_drop)

        # Right: Thumbnail preview
        self.preview_frame = ttk.Frame(img_split)
        img_split.add(self.preview_frame, weight=2)

        self.preview_label = tk.Label(self.preview_frame, bg="#202020")
        self.preview_label.pack(fill="both", expand=True)

        # Image buttons
        img_btns = ttk.Frame(details)
        img_btns.pack(fill="x", pady=5)

        ttk.Button(img_btns, text="Add Image", command=self.add_image).pack(side="left", padx=2)
        ttk.Button(img_btns, text="Remove Image", command=self.remove_image).pack(side="left", padx=2)

    # -----------------------------------------------------
    # Drag & Drop Handler
    # -----------------------------------------------------

    def handle_drop(self, event):
        if not self.current_name:
            messagebox.showwarning("No selection", "Select an aircraft first.")
            return

        paths = self.root.splitlist(event.data)
        valid_ext = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
        paths = [p for p in paths if p.lower().endswith(valid_ext)]

        if not paths:
            return

        sname = safe_name(self.current_name)

        existing = [
            f for f in os.listdir(IMG_DIR)
            if f.lower().startswith(sname.lower() + "__")
        ]

        used_letters = set()
        for f in existing:
            suffix = f.split("__", 1)[1].split(".", 1)[0]
            used_letters.add(suffix)

        alphabet = list(string.ascii_lowercase)
        next_letters = [c for c in alphabet if c not in used_letters]

        for i, src in enumerate(paths):
            if i >= len(next_letters):
                messagebox.showerror("Error", "Ran out of letter suffixes.")
                break

            letter = next_letters[i]
            ext = os.path.splitext(src)[1]
            dst = os.path.join(IMG_DIR, f"{sname}__{letter}{ext}")
            shutil.copy(src, dst)

        self.refresh_images()

    # -----------------------------------------------------
    # Aircraft List
    # -----------------------------------------------------

    def refresh_aircraft_list(self):
        self.tree.delete(*self.tree.get_children())
        for name in sorted(self.hotlist.keys()):
            self.tree.insert("", "end", iid=name, values=(name,))
        self.clear_details()

    def clear_details(self):
        self.current_name = None
        self.name_var.set("")
        self.cat_var.set("")
        self.img_listbox.delete(0, tk.END)
        self.preview_label.config(image="", text="")
        self.current_thumbnail = None

    def load_details(self, name):
        self.current_name = name
        self.name_var.set(name)
        self.cat_var.set(self.hotlist.get(name, ""))
        self.refresh_images()

    # -----------------------------------------------------
    # Image List + Thumbnail
    # -----------------------------------------------------

    def refresh_images(self):
        self.img_listbox.delete(0, tk.END)
        self.preview_label.config(image="", text="")
        self.current_thumbnail = None

        if not self.current_name:
            return

        sname = safe_name(self.current_name)

        for file in sorted(os.listdir(IMG_DIR)):
            if file.lower().startswith((sname + "__").lower()):
                self.img_listbox.insert(tk.END, file)

    def update_thumbnail(self, event=None):
        sel = self.img_listbox.curselection()
        if not sel:
            self.preview_label.config(image="", text="")
            self.current_thumbnail = None
            return

        filename = self.img_listbox.get(sel[0])
        path = os.path.join(IMG_DIR, filename)

        if not os.path.exists(path):
            self.preview_label.config(image="", text="")
            self.current_thumbnail = None
            return

        try:
            img = Image.open(path)

            self.preview_frame.update_idletasks()
            frame_w = self.preview_frame.winfo_width()
            frame_h = self.preview_frame.winfo_height()

            if frame_w < 10 or frame_h < 10:
                return

            img.thumbnail((frame_w, frame_h), Image.LANCZOS)

            self.current_thumbnail = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.current_thumbnail, text="")

        except Exception as e:
            self.preview_label.config(text=f"Error loading image:\n{e}")
            self.current_thumbnail = None

    # -----------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------

    def on_select_aircraft(self, event):
        sel = self.tree.selection()
        if not sel:
            self.clear_details()
            return
        name = sel[0]
        self.load_details(name)

    # -----------------------------------------------------
    # Aircraft Operations
    # -----------------------------------------------------

    def add_aircraft(self):
        name = self.simple_prompt("New Aircraft", "Enter aircraft name:")
        if not name:
            return
        if name in self.hotlist:
            messagebox.showerror("Error", "Aircraft already exists.")
            return

        cat = self.simple_prompt("Category", "Enter category:", default="Fighter")
        if not cat:
            return

        self.hotlist[name] = cat
        save_hotlist(self.hotlist)
        self.refresh_aircraft_list()
        self.tree.selection_set(name)
        self.tree.focus(name)
        self.load_details(name)

    def delete_aircraft(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select an aircraft first.")
            return
        name = sel[0]

        if not messagebox.askyesno("Confirm", f"Delete '{name}' and its images?"):
            return

        sname = safe_name(name)
        for file in os.listdir(IMG_DIR):
            if file.lower().startswith(sname.lower() + "__"):
                os.remove(os.path.join(IMG_DIR, file))

        del self.hotlist[name]
        save_hotlist(self.hotlist)
        self.refresh_aircraft_list()

    def save_changes(self):
        if not self.current_name:
            messagebox.showwarning("No selection", "Select an aircraft first.")
            return

        old_name = self.current_name
        new_name = self.name_var.get().strip()
        new_cat = self.cat_var.get().strip()

        if not new_name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return
        if not new_cat:
            messagebox.showerror("Error", "Category cannot be empty.")
            return

        if new_name != old_name and new_name in self.hotlist:
            messagebox.showerror("Error", "Another aircraft with that name already exists.")
            return

        if new_name != old_name:
            old_safe = safe_name(old_name)
            new_safe = safe_name(new_name)

            for file in os.listdir(IMG_DIR):
                if file.lower().startswith(old_safe.lower() + "__"):
                    old_path = os.path.join(IMG_DIR, file)
                    new_file = file.replace(old_safe, new_safe, 1)
                    new_path = os.path.join(IMG_DIR, new_file)
                    os.rename(old_path, new_path)

            del self.hotlist[old_name]
            self.hotlist[new_name] = new_cat
            self.current_name = new_name
        else:
            self.hotlist[old_name] = new_cat

        save_hotlist(self.hotlist)
        self.refresh_aircraft_list()
        self.tree.selection_set(self.current_name)
        self.tree.focus(self.current_name)
        self.load_details(self.current_name)

    # -----------------------------------------------------
    # Image Operations
    # -----------------------------------------------------

    def add_image(self):
        if not self.current_name:
            messagebox.showwarning("No selection", "Select an aircraft first.")
            return

        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif")]
        )
        if not paths:
            return

        sname = safe_name(self.current_name)

        existing = [
            f for f in os.listdir(IMG_DIR)
            if f.lower().startswith(sname.lower() + "__")
        ]

        used_letters = set()
        for f in existing:
            suffix = f.split("__", 1)[1].split(".", 1)[0]
            used_letters.add(suffix)

        alphabet = list(string.ascii_lowercase)
        next_letters = [c for c in alphabet if c not in used_letters]

        for i, src in enumerate(paths):
            if i >= len(next_letters):
                messagebox.showerror("Error", "Ran out of letter suffixes.")
                break

            letter = next_letters[i]
            ext = os.path.splitext(src)[1]
            dst = os.path.join(IMG_DIR, f"{sname}__{letter}{ext}")
            shutil.copy(src, dst)

        self.refresh_images()

    def remove_image(self):
        if not self.current_name:
            messagebox.showwarning("No selection", "Select an aircraft first.")
            return

        sel = self.img_listbox.curselection()
        if not sel:
            return

        file = self.img_listbox.get(sel[0])
        full = os.path.join(IMG_DIR, file)
        if os.path.exists(full):
            os.remove(full)

        self.refresh_images()

    # -----------------------------------------------------
    # Export / Import
    # -----------------------------------------------------

    def export_set(self):
        global CURRENT_HOTLIST_FOLDER
        target_dir = filedialog.askdirectory(title="Select export folder")
        if not target_dir:
            return

        folder_name = self.simple_prompt("Export Hotlist", "Enter a name for this hotlist:", default=CURRENT_HOTLIST_FOLDER)
        if not folder_name:
            return

        export_root = os.path.join(target_dir, folder_name)

        if os.path.exists(export_root):
            if not messagebox.askyesno("Overwrite", f"{folder_name} already exists. Overwrite?"):
                return
            shutil.rmtree(export_root)

        os.makedirs(export_root, exist_ok=True)
        os.makedirs(os.path.join(export_root, "imgs"), exist_ok=True)

        with open(os.path.join(export_root, "hotlist.txt"), "w", encoding="utf-8") as f:
            for name, cat in self.hotlist.items():
                f.write(f"{name} | {cat}\n")

        for file in os.listdir(IMG_DIR):
            shutil.copy(os.path.join(IMG_DIR, file),
                        os.path.join(export_root, "imgs", file))

        CURRENT_HOTLIST_FOLDER = folder_name
        self.hotlist_label.config(text=f"Hotlist Loaded: {folder_name}")

        messagebox.showinfo("Export Complete", f"Exported to:\n{export_root}")

    def import_set(self):
        source_dir = filedialog.askdirectory(title="Select folder containing hotlist.txt and imgs/")
        if not source_dir:
            return

        hotlist_path = os.path.join(source_dir, "hotlist.txt")
        imgs_path = os.path.join(source_dir, "imgs")

        if not os.path.exists(hotlist_path) or not os.path.isdir(imgs_path):
            messagebox.showerror("Error", "Folder must contain hotlist.txt and imgs/")
            return

        if self.hotlist:
            merge = messagebox.askyesno(
                "Merge or Replace",
                "Yes = Merge with existing hotlist\nNo = Replace current hotlist"
            )
        else:
            merge = True

        imported = {}
        with open(hotlist_path, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line:
                    continue
                name, cat = line.strip().split("|", 1)
                imported[name.strip()] = cat.strip()

        if merge:
            self.hotlist.update(imported)
        else:
            self.hotlist = imported

        save_hotlist(self.hotlist)

        for file in os.listdir(imgs_path):
            shutil.copy(os.path.join(imgs_path, file),
                        os.path.join(IMG_DIR, file))

        self.refresh_aircraft_list()

        imported_folder_name = os.path.basename(source_dir)
        self.hotlist_label.config(text=f"Hotlist Loaded: {imported_folder_name}")

        messagebox.showinfo("Import Complete", "Hotlist imported.")

    # -----------------------------------------------------
    # Prompt Utility
    # -----------------------------------------------------

    def simple_prompt(self, title, prompt, default=""):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=prompt).pack(padx=10, pady=(10, 5), anchor="w")
        var = tk.StringVar(value=default)
        entry = ttk.Entry(dialog, textvariable=var)
        entry.pack(padx=10, pady=5, fill="x")
        entry.focus_set()

        result = {"value": None}

        def on_ok():
            result["value"] = var.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)

        dialog.wait_window()
        return result["value"]

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = HotlistManagerApp(root)
    root.mainloop()
