import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font
import json
import os
import re
from datetime import datetime
import collections

CONFIG_FILE = "config.json"
LOG_FILE = "organizer.log"

class NoteOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Note Organizer")
        self.root.geometry("1200x1500") # Increased height

        config_data = self.load_config()
        self.mappings = config_data.get("mappings", [])
        self.last_notes_file = config_data.get("last_notes_file", "")

        # --- Main Notes File ---
        tk.Label(root, text="Main Notes File (.md):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.notes_file_path_var = tk.StringVar(value=self.last_notes_file)
        self.notes_file_entry = tk.Entry(root, textvariable=self.notes_file_path_var, width=60)
        self.notes_file_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = tk.Button(root, text="Browse...", command=self.browse_notes_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Mappings Management ---
        mappings_frame = tk.LabelFrame(root, text="Header to File Mappings")
        mappings_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ewns")

        tk.Label(mappings_frame, text="Header:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.header_entry_var = tk.StringVar()
        self.header_entry = tk.Entry(mappings_frame, textvariable=self.header_entry_var, width=30)
        self.header_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Move Add/Update button next to header input
        self.add_mapping_button = tk.Button(mappings_frame, text="Add/Update Mapping", command=self.add_or_update_mapping)
        self.add_mapping_button.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(mappings_frame, text="Target File Path:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.target_file_entry_var = tk.StringVar()
        self.target_file_entry = tk.Entry(mappings_frame, textvariable=self.target_file_entry_var, width=50)
        self.target_file_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.browse_target_button = tk.Button(mappings_frame, text="Browse...", command=self.browse_target_file)
        self.browse_target_button.grid(row=1, column=2, padx=5, pady=2)

        # --- Mappings List ---
        self.mappings_list_frame = tk.Frame(mappings_frame, height=100)
        self.mappings_list_frame.grid(row=2, column=0, columnspan=3, sticky="ewns", padx=5, pady=2)
        
        columns = ("Header", "Target File")
        self.mappings_tree = ttk.Treeview(self.mappings_list_frame, columns=columns, show="headings", selectmode="browse")
        self.mappings_tree.heading("Header", text="Header")
        self.mappings_tree.heading("Target File", text="Target File")
        self.mappings_tree.column("Header", width=250)
        self.mappings_tree.column("Target File", width=400)
        
        self.mappings_tree_scrollbar = ttk.Scrollbar(self.mappings_list_frame, orient="vertical", command=self.mappings_tree.yview)
        self.mappings_tree.configure(yscrollcommand=self.mappings_tree_scrollbar.set)
        
        self.mappings_tree.pack(side="left", fill="both", expand=True, pady=2)
        self.mappings_tree.configure(height=28)
        self.mappings_tree_scrollbar.pack(side="right", fill="y")

        # Style for Treeview to prevent text cutoff - balanced row height
        style = ttk.Style()
        # Using a balanced row height - compact but readable
        style.configure("Treeview", rowheight=35)
        # If further issues, consider styling "Treeview.Heading" and "Treeview.Item" explicitly
        # e.g., style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), padding=(0,5,0,5))
        #      style.configure("Treeview.Item", padding=(0,2,0,2))

        self.mappings_tree.bind("<<TreeviewSelect>>", self.on_mapping_select)

        self.remove_mapping_button = tk.Button(mappings_frame, text="Remove Selected Mapping", command=self.remove_mapping, state=tk.DISABLED)
        self.remove_mapping_button.grid(row=3, column=0, columnspan=3, padx=5, pady=2)
        
        self.populate_mappings_list()

        # --- Actions ---
        actions_frame = tk.Frame(root)
        actions_frame.grid(row=2, column=0, columnspan=3, pady=5)
        self.organize_button = tk.Button(actions_frame, text="Organize Notes", command=self.organize_notes, bg="lightblue", font=("Arial", 12))
        self.organize_button.pack(pady=5)

        # Configure grid column weights
        root.grid_columnconfigure(1, weight=1)
        mappings_frame.grid_columnconfigure(1, weight=1)

        # Handle app close
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)


    def on_app_close(self):
        self.save_config()
        self.root.destroy()

    def browse_notes_file(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if filepath:
            self.notes_file_path_var.set(filepath)
            self.last_notes_file = filepath
            self.save_config()

    def browse_target_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            title="Select or Create Target File"
        )
        if filepath:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.target_file_entry_var.set(filepath)

    def load_config(self):
        default_config = {"mappings": [], "last_notes_file": ""}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    # Ensure basic structure for robustness
                    if not isinstance(config_data, dict):
                        messagebox.showerror("Config Error", f"{CONFIG_FILE} has an invalid format. Resetting.")
                        return default_config
                    if "mappings" not in config_data or not isinstance(config_data["mappings"], list):
                        config_data["mappings"] = []
                    if "last_notes_file" not in config_data or not isinstance(config_data["last_notes_file"], str):
                        config_data["last_notes_file"] = ""
                    return config_data
            except json.JSONDecodeError:
                messagebox.showerror("Config Error", f"Could not decode {CONFIG_FILE}. Using default configuration.")
                return default_config
            except Exception as e:
                messagebox.showerror("Config Error", f"Could not load {CONFIG_FILE}: {e}. Using default configuration.")
                return default_config
        return default_config

    def save_config(self):
        # Ensure self.last_notes_file is updated from the StringVar before saving
        current_notes_file = self.notes_file_path_var.get()
        if current_notes_file: # Only update if there's something in the field
            self.last_notes_file = current_notes_file
            
        config_data = {
            "mappings": self.mappings,
            "last_notes_file": self.last_notes_file
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Config Error", f"Could not save configuration to {CONFIG_FILE}: {e}")

    def populate_mappings_list(self):
        for item in self.mappings_tree.get_children():
            self.mappings_tree.delete(item)
        for i, mapping in enumerate(self.mappings):
            self.mappings_tree.insert("", "end", iid=str(i), values=(mapping["header"], mapping["target_file"]))

    def add_or_update_mapping(self):
        header = self.header_entry_var.get().strip()
        target_file = self.target_file_entry_var.get().strip()

        if not header:
            messagebox.showwarning("Input Error", "Header cannot be empty.")
            return
        if not target_file:
            messagebox.showwarning("Input Error", "Target file path cannot be empty.")
            return

        # Check if header already exists, if so, update
        found = False
        for mapping in self.mappings:
            if mapping["header"] == header:
                if messagebox.askyesno("Confirm Update", f"Header '{header}' already exists. Update target file to '{target_file}'?"):
                    mapping["target_file"] = target_file
                    found = True
                else:
                    return # User cancelled update
                break
        
        if not found:
            self.mappings.append({"header": header, "target_file": target_file})

        self.save_config()
        self.populate_mappings_list()
        self.header_entry_var.set("")
        self.target_file_entry_var.set("")
        messagebox.showinfo("Success", "Mapping added/updated successfully.")

    def on_mapping_select(self, event):
        selected_items = self.mappings_tree.selection()
        if selected_items:
            selected_iid = selected_items[0]
            item = self.mappings_tree.item(selected_iid)
            values = item['values']
            if values:
                self.header_entry_var.set(values[0])
                self.target_file_entry_var.set(values[1])
                self.remove_mapping_button.config(state=tk.NORMAL)
        else:
            self.header_entry_var.set("")
            self.target_file_entry_var.set("")
            self.remove_mapping_button.config(state=tk.DISABLED)


    def remove_mapping(self):
        selected_items = self.mappings_tree.selection()
        if not selected_items:
            messagebox.showwarning("Selection Error", "No mapping selected to remove.")
            return

        selected_iid = selected_items[0]
        item = self.mappings_tree.item(selected_iid)
        header_to_remove = item['values'][0]

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove the mapping for header '{header_to_remove}'?"):
            self.mappings = [m for m in self.mappings if m["header"] != header_to_remove]
            self.save_config()
            self.populate_mappings_list()
            self.header_entry_var.set("")
            self.target_file_entry_var.set("")
            self.remove_mapping_button.config(state=tk.DISABLED)
            messagebox.showinfo("Success", "Mapping removed.")
    
    def log_action(self, header, note_snippet, source_file, target_file):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | HEADER: {header} | NOTE_SNIPPET: {note_snippet[:30].replace(os.linesep, ' ')}... | MOVED_FROM: {os.path.basename(source_file)} | MOVED_TO: {target_file}{os.linesep}"
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            messagebox.showerror("Logging Error", f"Failed to write to log file {LOG_FILE}: {e}")

    def organize_notes(self):
        # Save current config (especially the notes file path) before organizing
        self.save_config()
        
        main_notes_file = self.notes_file_path_var.get()
        if not main_notes_file or not os.path.exists(main_notes_file):
            messagebox.showerror("File Error", "Main notes file path is invalid or file does not exist.")
            return

        if not self.mappings:
            messagebox.showinfo("No Mappings", "No header-to-file mappings defined. Nothing to organize.")
            return

        try:
            with open(main_notes_file, "r", encoding="utf-8") as f:
                all_lines_from_file = f.readlines() # Read all lines with their original endings
        except Exception as e:
            messagebox.showerror("File Read Error", f"Could not read main notes file: {e}")
            return

        remaining_lines_for_main_file = []
        notes_to_move_by_target = collections.defaultdict(list)
        notes_moved_count = 0

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        configured_headers_map = {m['header'].lower(): m['target_file'] for m in self.mappings}

        idx = 0
        while idx < len(all_lines_from_file):
            current_line_text = all_lines_from_file[idx].rstrip('\r\n') # Strip newlines for matching
            
            is_date_line = date_pattern.match(current_line_text)
            actual_header_str = ""
            num_header_lines_for_current_segment = 0 # Lines that form the header itself (1 or 2)
            
            first_line_of_segment = all_lines_from_file[idx] # Keep original line ending

            if is_date_line:
                if idx + 1 < len(all_lines_from_file):
                    actual_header_str = all_lines_from_file[idx+1].strip()
                    num_header_lines_for_current_segment = 2
                else: # Date line at EOF, not a valid header for us
                    remaining_lines_for_main_file.append(first_line_of_segment)
                    idx += 1
                    continue
            else:
                actual_header_str = current_line_text
                num_header_lines_for_current_segment = 1

            if actual_header_str.lower() in configured_headers_map:
                target_file = configured_headers_map[actual_header_str.lower()]
                current_note_lines_accumulator = []

                # Add header lines to accumulator
                current_note_lines_accumulator.append(first_line_of_segment) # date or header line
                if is_date_line:
                    current_note_lines_accumulator.append(all_lines_from_file[idx+1]) # actual header line

                # Start accumulating content lines for this specific note
                content_scan_idx = idx + num_header_lines_for_current_segment
                
                while content_scan_idx < len(all_lines_from_file):
                    line_being_scanned = all_lines_from_file[content_scan_idx]
                    line_being_scanned_stripped = line_being_scanned.strip()

                    if not line_being_scanned_stripped: # Empty line, this note ends
                        idx = content_scan_idx + 1 # Next outer loop iteration starts after this empty line
                        break
                    
                    # Check if this line_being_scanned starts a *new* mapped note
                    # This check determines the end of the current note if a new one starts immediately
                    scan_is_date = date_pattern.match(line_being_scanned_stripped)
                    scan_actual_header = ""
                    if scan_is_date:
                        if content_scan_idx + 1 < len(all_lines_from_file):
                            scan_actual_header = all_lines_from_file[content_scan_idx+1].strip()
                    else:
                        scan_actual_header = line_being_scanned_stripped
                    
                    if scan_actual_header in configured_headers_map: # New mapped note starts
                        idx = content_scan_idx # Next outer loop will process this new header
                        break
                    else: # Regular content line for the current note
                        current_note_lines_accumulator.append(line_being_scanned)
                        content_scan_idx += 1
                        if content_scan_idx == len(all_lines_from_file): # Reached EOF
                            idx = content_scan_idx
                            break
                else: # Inner loop finished without break (scanned till EOF or next header was not mapped)
                    idx = content_scan_idx

                # Extract content, excluding original header lines
                note_content_lines = current_note_lines_accumulator[num_header_lines_for_current_segment:]
                actual_note_content_for_file = "".join(note_content_lines).strip() # Join and strip leading/trailing whitespace from content block
                
                # Create new timestamp header
                new_timestamp_header = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (auto)"
                
                # Prepare the block to be written to the target file
                formatted_note_for_target = new_timestamp_header
                if actual_note_content_for_file: # Add content only if it's not empty
                    formatted_note_for_target += os.linesep + actual_note_content_for_file
                
                notes_to_move_by_target[target_file].append(formatted_note_for_target)
                
                # Log with original header and a snippet of the *content* part for clarity
                log_snippet_content = "".join(note_content_lines)
                self.log_action(actual_header_str, log_snippet_content, main_notes_file, target_file)
                notes_moved_count += 1
            else: # Line does not start a mapped note
                remaining_lines_for_main_file.append(first_line_of_segment)
                idx += 1
        
        # --- Update Main Notes File ---
        updated_main_content = "".join(remaining_lines_for_main_file) # Join lines keeping original endings

        try:
            backup_file_path = main_notes_file + ".bak"
            if os.path.exists(backup_file_path):
                 os.remove(backup_file_path)
            if os.path.exists(main_notes_file): # Only rename if it exists
                os.rename(main_notes_file, backup_file_path)
            
            with open(main_notes_file, "w", encoding="utf-8") as f:
                f.write(updated_main_content)
        except Exception as e:
            messagebox.showerror("File Update Error", f"Could not update main notes file: {e}")
            # Attempt to restore from backup if rename succeeded but write failed
            if os.path.exists(backup_file_path) and not os.path.exists(main_notes_file):
                try:
                    os.rename(backup_file_path, main_notes_file)
                    messagebox.showinfo("Restore", "Attempted to restore original file from backup.")
                except Exception as restore_error: # Renamed 're' to 'restore_error'
                    messagebox.showerror("Restore Error", f"Could not restore original file: {restore_error}")
            return # Stop processing if main file update fails

        # --- Write Moved Notes to Target Files (Prepending) ---
        for target_file, notes_list in notes_to_move_by_target.items():
            if not notes_list:
                continue

            # Ensure target directory exists
            target_dir = os.path.dirname(target_file)
            if target_dir and not os.path.exists(target_dir): # Check if target_dir is not empty (for files in root)
                os.makedirs(target_dir, exist_ok=True)

            existing_content = ""
            if os.path.exists(target_file):
                try:
                    with open(target_file, "r", encoding="utf-8") as tf_read:
                        existing_content = tf_read.read()
                except Exception as e:
                    messagebox.showerror("Target Read Error", f"Could not read existing target file {target_file}: {e}")
                    continue # Skip this target if cannot read

            # Join new notes with double newlines
            new_notes_block = (os.linesep + os.linesep).join(notes_list)

            final_content = new_notes_block
            if existing_content.strip(): # Add existing content only if it's not just whitespace
                final_content += os.linesep + os.linesep + existing_content.strip()
            else: # If existing content is empty or whitespace, just use new notes (strip to avoid leading newlines)
                 final_content = new_notes_block.strip()


            try:
                with open(target_file, "w", encoding="utf-8") as tf_write:
                    tf_write.write(final_content + os.linesep) # Add a trailing newline
            except Exception as e:
                messagebox.showerror("Target Write Error", f"Could not write to target file {target_file}: {e}")

        if notes_moved_count > 0:
            messagebox.showinfo("Organization Complete",
                                f"{notes_moved_count} note(s) moved.\n"
                                f"Original file backed up to: {main_notes_file + '.bak'}\n"
                                f"Please check {LOG_FILE} for details.")
        else:
            messagebox.showinfo("Organization Complete", "No notes matched the defined mappings for moving.")

def main():
    root = tk.Tk()
    app = NoteOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()