import os
import datetime
import threading
import urllib.request
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

GITHUB_CSV_URL = "https://raw.githubusercontent.com/retrobone/Cricket07ReDir/refs/heads/main/C07Files_Complete.csv" 

# Core logic
import rename_core

class CricketRecovererApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cricket 07 File Renamer")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Variables
        self.target_folder = tk.StringVar()
        self.run_csv = tk.BooleanVar(value=True)
        self.run_face = tk.BooleanVar(value=True)
        self.run_bat = tk.BooleanVar(value=True)
        self.run_stadium = tk.BooleanVar(value=True)
        self.run_backup = tk.BooleanVar(value=False)
        self.dry_run = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
        # Start the silent background check on startup
        threading.Thread(target=self.check_csv_update, args=(False,), daemon=True).start()

    # TOOLBAR ACTIONS
    def action_open_folder(self):
        folder = self.target_folder.get()
        if folder and os.path.isdir(folder):
            os.startfile(folder)
        else:
            messagebox.showwarning("Warning", "Please select a valid game folder first.")

    def action_view_log(self):
        folder = self.target_folder.get()
        if not folder:
            messagebox.showwarning("Warning", "Please select a game folder first to view its log.")
            return
        
        log_path = os.path.join(folder, "rename.log")
        dry_log_path = os.path.join(folder, "rename_dryrun.log")
        
        if os.path.exists(log_path):
            os.startfile(log_path)
        elif os.path.exists(dry_log_path):
            os.startfile(dry_log_path)
        else:
            messagebox.showinfo("Not Found", "No log file found in the selected folder yet.")

    def action_clear_console(self):
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.config(state="disabled")

    def action_about(self):
        about_text = (
            "Cricket 07 File Renamer\n\n"
            "Automatically recovers and renames hashed faces, bats, stadiums, "
            "and menu textures into their correct game folders.\n\n"
            "Back up your files in case of any discrepancies"
        )
        messagebox.showinfo("About", about_text)

    # UPDATE CSV
    def action_check_csv_update(self):
        self.log("Checking GitHub for CSV updates...")
        threading.Thread(target=self.check_csv_update, args=(True,), daemon=True).start()

    def check_csv_update(self, manual=False):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_csv_path = os.path.join(script_dir, "C07Files_Complete.csv")

        try:
            # Fetch remote CSV data
            req = urllib.request.Request(GITHUB_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote_data = response.read()
            
            # Normalize line endings
            remote_text = remote_data.decode('utf-8', errors='ignore').replace('\r\n', '\n')
            remote_hash = hashlib.md5(remote_text.encode('utf-8')).hexdigest()
            remote_lines = len(remote_text.strip().split('\n'))

            # Get local CSV data
            if os.path.exists(local_csv_path):
                with open(local_csv_path, 'rb') as f:
                    local_text = f.read().decode('utf-8', errors='ignore').replace('\r\n', '\n')
                local_hash = hashlib.md5(local_text.encode('utf-8')).hexdigest()
                local_lines = len(local_text.strip().split('\n'))
            else:
                local_hash = ""
                local_lines = 0

            # Compare and Popup
            if remote_hash == local_hash:
                if manual:
                    self.root.after(0, lambda: messagebox.showinfo("Update Check", "Your file is up-to-date. No need to update!"))
                    self.log("[UPDATE] CSV is already up-to-date.")
            elif local_lines >= remote_lines and local_hash != "":
                if manual:
                    self.root.after(0, lambda: messagebox.showinfo("Update Check", "Your local mapping file has custom edits or is newer.\n\nNo need to update!"))
                    self.log("[UPDATE] Local CSV is custom/newer. Skipping update.")
            else:
                self.root.after(0, self.prompt_csv_update, remote_data, local_csv_path)

        except Exception as e:
            if manual:
                self.root.after(0, lambda err=e: messagebox.showerror(
                    "Update Check Failed", 
                    f"Could not reach GitHub to check for updates.\n\nPlease check your internet connection.\n\nError: {err}"
                ))
                self.log(f"[ERROR] Update check failed: {e}")

    def prompt_csv_update(self, remote_data, local_csv_path):
        msg = "A newer version is available online.\n\nDo you want to download and use the latest version?"
        if not os.path.exists(local_csv_path):
            msg = "The required mapping file (C07Files_Complete.csv) is missing, but was found online.\n\nDo you want to download it now?"
            
        if messagebox.askyesno("CSV Update Available", msg):
            try:
                with open(local_csv_path, 'wb') as f:
                    f.write(remote_data)
                self.log("[UPDATE] Successfully downloaded the latest C07Files_Complete.csv from GitHub.")
                messagebox.showinfo("Success", "The CSV file was successfully updated!")
            except Exception as e:
                self.log(f"[ERROR] Failed to save updated CSV: {e}")
                messagebox.showerror("Error", f"Failed to save the file:\n{e}")

    # INTERFACE
    def setup_ui(self):
        
        # Menu Bar
        menubar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Game Folder", command=self.action_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="View Last Log", command=self.action_view_log)
        tools_menu.add_command(label="Clear Console", command=self.action_clear_console)
        tools_menu.add_separator() 
        tools_menu.add_command(label="Check for CSV Update", command=self.action_check_csv_update)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.action_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

        # Main Layout
        frame_top = ttk.LabelFrame(self.root, text="Directory Configuration", padding=10)
        frame_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_top, text="Game Folder (Source & Output):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_top, textvariable=self.target_folder, width=70, state="readonly").grid(row=0, column=1, padx=10)
        ttk.Button(frame_top, text="Browse", command=self.browse_folder).grid(row=0, column=2)

        frame_mid = ttk.LabelFrame(self.root, text="Modules & Options", padding=10)
        frame_mid.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(frame_mid, text="CSV Organizer", variable=self.run_csv).grid(row=0, column=0, padx=20, sticky="w")
        ttk.Checkbutton(frame_mid, text="Face Renamer", variable=self.run_face).grid(row=0, column=1, padx=20, sticky="w")
        ttk.Checkbutton(frame_mid, text="Bat Renamer (0-256)", variable=self.run_bat).grid(row=0, column=2, padx=20, sticky="w")
        ttk.Checkbutton(frame_mid, text="Stadiums' Models & Texture Renamer", variable=self.run_stadium).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        ttk.Checkbutton(frame_mid, text="Create Backup Before Moving", variable=self.run_backup).grid(row=1, column=1, padx=20, pady=5, sticky="w")
        ttk.Checkbutton(frame_mid, text="DRY RUN (Preview only)", variable=self.dry_run).grid(row=1, column=2, padx=20, pady=5, sticky="w")

        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="x", padx=10)

        self.btn_start = ttk.Button(frame_action, text="Start Processing", command=self.start_processing)
        self.btn_start.pack(fill="x", ipady=5)

        frame_log = ttk.LabelFrame(self.root, text="Process Log", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_area = ScrolledText(frame_log, wrap="word", state="disabled", bg="white", fg="black", font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Cricket 07 Patch Folder")
        if folder:
            self.target_folder.set(folder)

    def log(self, message):
        def append():
            self.log_area.config(state="normal")
            self.log_area.insert("end", message + "\n")
            self.log_area.see("end")
            self.log_area.config(state="disabled")
        self.root.after(0, append)

    def start_processing(self):
        folder = self.target_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid game folder first.")
            return

        self.btn_start.config(state="disabled")
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.config(state="disabled")

        thread = threading.Thread(target=self.execute_workflow, args=(folder,))
        thread.daemon = True
        thread.start()

    def execute_workflow(self, folder):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        is_dry = self.dry_run.get()
        manifest = []
        backup_root = None
        
        self.log("CRICKET 07 FILE RENAMER")
        self.log(f"Target Directory: {folder}")
        self.log(f"DRY_RUN Mode: {is_dry}\n")

        if not is_dry and self.run_backup.get():
            backup_root = os.path.join(folder, "_backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(backup_root, exist_ok=True)
            self.log(f"Backing up originals to: {backup_root}")

        try:
            if self.run_bat.get(): 
                rename_core.run_bat_fixer(folder, self.log, is_dry, backup_root, manifest)
                
            if self.run_csv.get(): 
                rename_core.run_csv_organizer(folder, script_dir, self.log, is_dry, backup_root, manifest)
                
            if self.run_stadium.get(): 
                rename_core.run_stadium_fixer(folder, self.log, is_dry, backup_root, manifest)
                
            if self.run_face.get(): 
                rename_core.run_face_recovery(folder, self.log, is_dry, backup_root, manifest)
            
            log_filename = "rename_dryrun.log" if is_dry else "rename.log"
            log_path = os.path.join(folder, log_filename)
                
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("CRICKET 07 FILE RENAMER LOG\n")
                f.write(f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Target Directory: {folder}\n")
                f.write(f"Mode: {'DRY RUN' if is_dry else 'LIVE OPERATION'}\n")
                f.write(f"Total Files Processed: {len(manifest)}\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in manifest:
                    status = "[DRY-RUN]" if entry.get("dry_run") else "[MOVED/RENAMED]"
                    f.write(f"{status}\n")
                    f.write(f"  Source: {entry['src']}\n")
                    f.write(f"  Target: {entry['dest']}\n")
                    f.write("-" * 50 + "\n")

            self.log(f"\nLog written to: {log_path} ({len(manifest)} entries)")
            self.log("\n=== ALL TASKS COMPLETE ===")
            
        except Exception as e:
            self.log(f"\n[CRITICAL ERROR] Operation stopped: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_start.config(state="normal"))
            self.root.after(0, lambda: messagebox.showinfo("Complete", "Processing has finished. Check the log for details."))

if __name__ == "__main__":
    root = tk.Tk()
    app = CricketRecovererApp(root)
    root.mainloop()