import sys
import json
import os
import re
from datetime import datetime
import collections
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
                             QSizePolicy, QGridLayout) # Added QGridLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

CONFIG_FILE = "config.json"
LOG_FILE = "organizer.log"
TRAY_ICON_FILE = "tray_icon.png"

class SettingsDialog(QDialog):
    def __init__(self, app_logic, parent=None):
        super().__init__(parent)
        self.app_logic = app_logic
        self.setWindowTitle("Obsidian Note Organizer - Settings")

        # Set dialog size based on screen height
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.setFixedWidth(1200) # Increased width to show full paths
        self.setFixedHeight(screen_geometry.height() - 100) # Use most of the screen height, leaving some margin

        self.init_ui()
        self.load_settings_to_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Main Notes File ---
        notes_file_group = QGroupBox("Main Notes File")
        notes_file_layout = QHBoxLayout()
        notes_file_layout.addWidget(QLabel("Main Notes File (.md):"))
        self.notes_file_entry = QLineEdit(self.app_logic.last_notes_file)
        notes_file_layout.addWidget(self.notes_file_entry)
        browse_notes_button = QPushButton("Browse...")
        browse_notes_button.clicked.connect(self.browse_notes_file)
        notes_file_layout.addWidget(browse_notes_button)
        notes_file_group.setLayout(notes_file_layout)
        main_layout.addWidget(notes_file_group)

        # --- Mappings Management ---
        mappings_group = QGroupBox("Header to File Mappings")
        mappings_layout = QVBoxLayout()

        # Input fields for new/editing mappings
        input_layout = QGridLayout()
        input_layout.addWidget(QLabel("Header:"), 0, 0)
        self.header_entry = QLineEdit()
        input_layout.addWidget(self.header_entry, 0, 1)

        self.add_mapping_button = QPushButton("Add/Update Mapping")
        self.add_mapping_button.clicked.connect(self.add_or_update_mapping)
        input_layout.addWidget(self.add_mapping_button, 0, 2, 2, 1, Qt.AlignVCenter) # Span 2 rows

        input_layout.addWidget(QLabel("Target File Path:"), 1, 0)
        self.target_file_entry = QLineEdit()
        input_layout.addWidget(self.target_file_entry, 1, 1)
        
        browse_target_button = QPushButton("Browse...")
        browse_target_button.clicked.connect(self.browse_target_file)
        # Add browse target button next to target_file_entry, ensure add_mapping_button is to its right
        target_file_layout_h = QHBoxLayout()
        target_file_layout_h.addWidget(self.target_file_entry)
        target_file_layout_h.addWidget(browse_target_button)
        input_layout.addLayout(target_file_layout_h, 1,1)


        mappings_layout.addLayout(input_layout)

        # Mappings Table
        self.mappings_table = QTableWidget()
        self.mappings_table.setColumnCount(2)
        self.mappings_table.setHorizontalHeaderLabels(["Header", "Target File"])
        # Make columns resizable by user
        self.mappings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.mappings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        # Set initial column widths
        self.mappings_table.setColumnWidth(0, 200)
        self.mappings_table.setColumnWidth(1, 800)
        self.mappings_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mappings_table.setSelectionMode(QTableWidget.SingleSelection)
        self.mappings_table.itemSelectionChanged.connect(self.on_mapping_select)
        self.mappings_table.verticalHeader().setDefaultSectionSize(25) # Adjust row height for compactness
        mappings_layout.addWidget(self.mappings_table)

        # Buttons for table operations
        table_buttons_layout = QHBoxLayout()
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.setEnabled(False)
        self.move_up_button.clicked.connect(self.move_mapping_up)
        table_buttons_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.setEnabled(False)
        self.move_down_button.clicked.connect(self.move_mapping_down)
        table_buttons_layout.addWidget(self.move_down_button)
        
        table_buttons_layout.addStretch()
        
        self.remove_mapping_button = QPushButton("Remove Selected Mapping")
        self.remove_mapping_button.setEnabled(False)
        self.remove_mapping_button.clicked.connect(self.remove_mapping)
        table_buttons_layout.addWidget(self.remove_mapping_button)
        
        mappings_layout.addLayout(table_buttons_layout)
        
        mappings_group.setLayout(mappings_layout)
        main_layout.addWidget(mappings_group)

        # Dialog buttons (Save/Close)
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addStretch()
        # No explicit save button, save on close (accept)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept) # Accept will trigger saving
        dialog_button_layout.addWidget(close_button)
        main_layout.addLayout(dialog_button_layout)

    def load_settings_to_ui(self):
        self.notes_file_entry.setText(self.app_logic.last_notes_file)
        self.populate_mappings_list()

    def browse_notes_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Main Notes File", "", "Markdown files (*.md);;All files (*.*)"
        )
        if filepath:
            self.notes_file_entry.setText(filepath)
            # self.app_logic.last_notes_file = filepath # Will be saved on dialog close

    def browse_target_file(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Select or Create Target File", "", "Markdown files (*.md);;All files (*.*)"
        )
        if filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.target_file_entry.setText(filepath)

    def populate_mappings_list(self):
        self.mappings_table.setRowCount(0) # Clear table
        for i, mapping in enumerate(self.app_logic.mappings):
            self.mappings_table.insertRow(i)
            self.mappings_table.setItem(i, 0, QTableWidgetItem(mapping["header"]))
            self.mappings_table.setItem(i, 1, QTableWidgetItem(mapping["target_file"]))
        self.mappings_table.clearSelection()
        self.remove_mapping_button.setEnabled(False)


    def add_or_update_mapping(self):
        header = self.header_entry.text().strip()
        target_file = self.target_file_entry.text().strip()

        if not header:
            QMessageBox.warning(self, "Input Error", "Header cannot be empty.")
            return
        if not target_file:
            QMessageBox.warning(self, "Input Error", "Target file path cannot be empty.")
            return

        found_idx = -1
        for i, m in enumerate(self.app_logic.mappings):
            if m["header"] == header:
                found_idx = i
                break
        
        if found_idx != -1:
            reply = QMessageBox.question(self, "Confirm Update",
                                         f"Header '{header}' already exists. Update target file to '{target_file}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.app_logic.mappings[found_idx]["target_file"] = target_file
            else:
                return # User cancelled
        else:
            self.app_logic.mappings.append({"header": header, "target_file": target_file})

        # self.app_logic.save_config() # Save will happen on dialog close
        self.populate_mappings_list()
        self.header_entry.clear()
        self.target_file_entry.clear()
        QMessageBox.information(self, "Success", "Mapping added/updated successfully.")


    def on_mapping_select(self):
        selected_rows = self.mappings_table.selectionModel().selectedRows()
        if selected_rows:
            row_index = selected_rows[0].row()
            header = self.mappings_table.item(row_index, 0).text()
            target_file = self.mappings_table.item(row_index, 1).text()
            self.header_entry.setText(header)
            self.target_file_entry.setText(target_file)
            self.remove_mapping_button.setEnabled(True)
            
            # Enable/disable move buttons based on position
            total_rows = self.mappings_table.rowCount()
            self.move_up_button.setEnabled(row_index > 0)
            self.move_down_button.setEnabled(row_index < total_rows - 1)
        else:
            self.header_entry.clear()
            self.target_file_entry.clear()
            self.remove_mapping_button.setEnabled(False)
            self.move_up_button.setEnabled(False)
            self.move_down_button.setEnabled(False)

    def move_mapping_up(self):
        selected_rows = self.mappings_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row_index = selected_rows[0].row()
        if row_index <= 0:
            return
        
        # Swap the mappings in the data
        self.app_logic.mappings[row_index], self.app_logic.mappings[row_index - 1] = \
            self.app_logic.mappings[row_index - 1], self.app_logic.mappings[row_index]
        
        # Refresh the table
        self.populate_mappings_list()
        
        # Select the moved row
        self.mappings_table.selectRow(row_index - 1)

    def move_mapping_down(self):
        selected_rows = self.mappings_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row_index = selected_rows[0].row()
        if row_index >= len(self.app_logic.mappings) - 1:
            return
        
        # Swap the mappings in the data
        self.app_logic.mappings[row_index], self.app_logic.mappings[row_index + 1] = \
            self.app_logic.mappings[row_index + 1], self.app_logic.mappings[row_index]
        
        # Refresh the table
        self.populate_mappings_list()
        
        # Select the moved row
        self.mappings_table.selectRow(row_index + 1)

    def remove_mapping(self):
        selected_rows = self.mappings_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "No mapping selected to remove.")
            return

        row_index = selected_rows[0].row()
        header_to_remove = self.mappings_table.item(row_index, 0).text()

        reply = QMessageBox.question(self, "Confirm Removal",
                                     f"Are you sure you want to remove the mapping for header '{header_to_remove}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app_logic.mappings = [m for m in self.app_logic.mappings if m["header"] != header_to_remove]
            # self.app_logic.save_config() # Save on dialog close
            self.populate_mappings_list()
            self.header_entry.clear()
            self.target_file_entry.clear()
            self.remove_mapping_button.setEnabled(False)
            QMessageBox.information(self, "Success", "Mapping removed.")

    def accept(self): # Called when "Close" is clicked or dialog is closed
        self.app_logic.last_notes_file = self.notes_file_entry.text()
        self.app_logic.save_config()
        super().accept()

    def reject(self): # Called on Escape or if a Cancel button existed
        # Config is not saved if dialog is rejected
        super().reject()


class NoteOrganizerAppLogic:
    def __init__(self):
        self.q_app = QApplication.instance() # Get existing instance or None
        if not self.q_app:
             self.q_app = QApplication(sys.argv)
        self.q_app.setQuitOnLastWindowClosed(False) # Important for tray icon

        self.settings_dialog_instance = None
        self.tray_icon = None
        
        config_data = self.load_config()
        self.mappings = config_data.get("mappings", [])
        self.last_notes_file = config_data.get("last_notes_file", "")
        # No notes_file_path_var directly, UI will handle its own display

    def show_settings_window(self):
        if self.settings_dialog_instance is None or not self.settings_dialog_instance.isVisible():
            self.settings_dialog_instance = SettingsDialog(self)
            self.settings_dialog_instance.show()
            self.settings_dialog_instance.activateWindow() # Bring to front
            self.settings_dialog_instance.raise_()
        else:
            self.settings_dialog_instance.activateWindow()
            self.settings_dialog_instance.raise_()


    def run_organization_from_tray(self):
        self.log_action("TRAY_CLICK", "Organize triggered from tray", "N/A", "N/A")
        # Ensure config is current before organizing (already loaded in __init__, settings dialog saves on close)
        self.organize_notes()

    def on_quit(self):
        self.log_action("APP_QUIT", "Application quitting. Attempting to save config...", "System", "System")
        # If settings window is open and visible, grab the latest notes file path from it
        if self.settings_dialog_instance and self.settings_dialog_instance.isVisible():
            current_notes_file_in_dialog = self.settings_dialog_instance.notes_file_entry.text()
            if current_notes_file_in_dialog: # Only update if there's something in the field
                 self.last_notes_file = current_notes_file_in_dialog
        
        self.save_config() # Save configuration before quitting
        self.q_app.quit()

    def start_tray_app(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Systray", "I couldn't detect any system tray on this system.")
            self.log_action("ERROR", "System tray not available.", "System", "System")
            sys.exit(1)

        icon_path = TRAY_ICON_FILE
        if not os.path.exists(icon_path):
            QMessageBox.critical(None, "Tray Icon Error", f"Icon file '{icon_path}' not found. Exiting.")
            self.log_action("ERROR", f"Icon file {icon_path} not found.", "System", "System")
            sys.exit(1)
        
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.q_app)
        self.tray_icon.setToolTip("Obsidian Note Organizer")

        menu = QMenu()
        
        organize_action = QAction("Organize Notes", self.q_app)
        organize_action.triggered.connect(self.run_organization_from_tray)
        menu.addAction(organize_action)
        
        settings_action = QAction("Settings", self.q_app)
        settings_action.triggered.connect(self.show_settings_window)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self.q_app)
        quit_action.triggered.connect(self.on_quit)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        self.log_action("APP_START", "Application started in tray mode.", "System", "System")
        sys.exit(self.q_app.exec_())

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger: # Left click
            self.run_organization_from_tray()

    def load_config(self):
        default_config = {"mappings": [], "last_notes_file": ""}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    if not isinstance(config_data, dict):
                        self._show_config_error_message(f"{CONFIG_FILE} has an invalid format. Resetting.")
                        return default_config
                    if "mappings" not in config_data or not isinstance(config_data["mappings"], list):
                        config_data["mappings"] = []
                    if "last_notes_file" not in config_data or not isinstance(config_data["last_notes_file"], str):
                        config_data["last_notes_file"] = ""
                    return config_data
            except json.JSONDecodeError:
                self._show_config_error_message(f"Could not decode {CONFIG_FILE}. Using default configuration.")
                return default_config
            except Exception as e:
                self._show_config_error_message(f"Could not load {CONFIG_FILE}: {e}. Using default configuration.")
                return default_config
        return default_config

    def _show_config_error_message(self, message):
        # This might be called before QApplication is fully set up for dialogs if config load fails early
        print(f"CONFIG ERROR: {message}") # Fallback to console
        if QApplication.instance(): # Check if app instance exists for QMessageBox
             QMessageBox.critical(None, "Config Error", message)


    def save_config(self):
        config_data = {
            "mappings": self.mappings,
            "last_notes_file": self.last_notes_file # Updated by SettingsDialog on accept
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(None, "Config Save Error", f"Could not save configuration to {CONFIG_FILE}: {e}")
    
    def log_action(self, header, note_snippet, source_file, target_file):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | HEADER: {header} | NOTE_SNIPPET: {note_snippet[:30].replace(os.linesep, ' ')}... | MOVED_FROM: {os.path.basename(source_file)} | MOVED_TO: {target_file}{os.linesep}"
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Avoid showing QMessageBox here as it could be frequent or from background tasks
            print(f"Logging Error: Failed to write to log file {LOG_FILE}: {e}")


    def organize_notes(self):
        # self.save_config() # Config is saved by settings dialog on close, or loaded fresh
        
        # Ensure latest config is used if settings window wasn't opened / saved yet
        # Or, if called when settings window is not open, current state of self.mappings/last_notes_file is used.
        # This is fine as __init__ loads it, and settings dialog updates it then saves.
        current_main_notes_file = self.last_notes_file

        if not current_main_notes_file or not os.path.exists(current_main_notes_file):
            QMessageBox.critical(None, "File Error", "Main notes file path is invalid or file does not exist.")
            return

        if not self.mappings:
            if self.tray_icon:
                self.tray_icon.showMessage("Note Organizer", "No header-to-file mappings defined. Nothing to organize.", QSystemTrayIcon.Information, 3000)
            else: # Fallback if tray icon isn't initialized for some reason
                QMessageBox.information(None, "No Mappings", "No header-to-file mappings defined. Nothing to organize.")
            return
        
        try:
            with open(current_main_notes_file, "r", encoding="utf-8") as f:
                all_lines_from_file = f.readlines()
        except Exception as e:
            QMessageBox.critical(None, "File Read Error", f"Could not read main notes file: {e}")
            return

        remaining_lines_for_main_file = []
        notes_to_move_by_target = collections.defaultdict(list)
        notes_moved_count = 0

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        configured_headers_map = {}
        for m in self.mappings:
            header = m['header']
            # Since we're storing individual mappings, header should be a string
            configured_headers_map[header.lower()] = m['target_file']

        idx = 0
        while idx < len(all_lines_from_file):
            current_line_text = all_lines_from_file[idx].rstrip('\r\n')
            is_date_line = date_pattern.match(current_line_text)
            actual_header_str = ""
            num_header_lines_for_current_segment = 0
            first_line_of_segment = all_lines_from_file[idx]

            if is_date_line:
                if idx + 1 < len(all_lines_from_file):
                    actual_header_str = all_lines_from_file[idx+1].strip()
                    num_header_lines_for_current_segment = 2
                else:
                    remaining_lines_for_main_file.append(first_line_of_segment)
                    idx += 1
                    continue
            else:
                actual_header_str = current_line_text
                num_header_lines_for_current_segment = 1

            if actual_header_str.lower() in configured_headers_map:
                target_file = configured_headers_map[actual_header_str.lower()]
                current_note_lines_accumulator = []
                current_note_lines_accumulator.append(first_line_of_segment)
                if is_date_line:
                    current_note_lines_accumulator.append(all_lines_from_file[idx+1])

                content_scan_idx = idx + num_header_lines_for_current_segment
                while content_scan_idx < len(all_lines_from_file):
                    line_being_scanned = all_lines_from_file[content_scan_idx]
                    line_being_scanned_stripped = line_being_scanned.strip()
                    if not line_being_scanned_stripped:
                        idx = content_scan_idx + 1
                        break
                    scan_is_date = date_pattern.match(line_being_scanned_stripped)
                    scan_actual_header = ""
                    if scan_is_date:
                        if content_scan_idx + 1 < len(all_lines_from_file):
                            scan_actual_header = all_lines_from_file[content_scan_idx+1].strip()
                    else:
                        scan_actual_header = line_being_scanned_stripped
                    if scan_actual_header.lower() in configured_headers_map: # Use .lower() here too
                        idx = content_scan_idx
                        break
                    else:
                        current_note_lines_accumulator.append(line_being_scanned)
                        content_scan_idx += 1
                        if content_scan_idx == len(all_lines_from_file):
                            idx = content_scan_idx
                            break
                else:
                    idx = content_scan_idx
                
                note_content_lines = current_note_lines_accumulator[num_header_lines_for_current_segment:]
                actual_note_content_for_file = "".join(note_content_lines).strip()
                new_timestamp_header = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (auto)"
                formatted_note_for_target = new_timestamp_header
                if actual_note_content_for_file:
                    formatted_note_for_target += os.linesep + actual_note_content_for_file
                notes_to_move_by_target[target_file].append(formatted_note_for_target)
                log_snippet_content = "".join(note_content_lines)
                self.log_action(actual_header_str, log_snippet_content, current_main_notes_file, target_file)
                notes_moved_count += 1
            else:
                remaining_lines_for_main_file.append(first_line_of_segment)
                idx += 1
        
        updated_main_content = "".join(remaining_lines_for_main_file)
        try:
            backup_file_path = current_main_notes_file + ".bak"
            if os.path.exists(backup_file_path):
                 os.remove(backup_file_path)
            if os.path.exists(current_main_notes_file):
                os.rename(current_main_notes_file, backup_file_path)
            with open(current_main_notes_file, "w", encoding="utf-8") as f:
                f.write(updated_main_content)
        except Exception as e:
            QMessageBox.critical(None, "File Update Error", f"Could not update main notes file: {e}")
            if os.path.exists(backup_file_path) and not os.path.exists(current_main_notes_file):
                try:
                    os.rename(backup_file_path, current_main_notes_file)
                    if self.tray_icon:
                        self.tray_icon.showMessage("Note Organizer", "Attempted to restore original file from backup.", QSystemTrayIcon.Information, 3000)
                    else:
                        QMessageBox.information(None, "Restore", "Attempted to restore original file from backup.")
                except Exception as restore_error:
                    QMessageBox.critical(None, "Restore Error", f"Could not restore original file: {restore_error}")
            return

        for target_file, notes_list in notes_to_move_by_target.items():
            if not notes_list:
                continue
            target_dir = os.path.dirname(target_file)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            existing_content = ""
            if os.path.exists(target_file):
                try:
                    with open(target_file, "r", encoding="utf-8") as tf_read:
                        existing_content = tf_read.read()
                except Exception as e:
                    err_msg = f"Could not read existing target file {target_file}: {e}"
                    if self.tray_icon:
                        self.tray_icon.showMessage("Target Read Error", err_msg, QSystemTrayIcon.Warning, 5000)
                    else:
                        QMessageBox.warning(None, "Target Read Error", err_msg)
                    self.log_action("ERROR_TARGET_READ", err_msg, current_main_notes_file, target_file)
                    continue
            new_notes_block = (os.linesep + os.linesep).join(notes_list)
            final_content = new_notes_block
            if existing_content.strip():
                final_content += os.linesep + os.linesep + existing_content.strip()
            else:
                 final_content = new_notes_block.strip()
            try:
                with open(target_file, "w", encoding="utf-8") as tf_write:
                    tf_write.write(final_content + os.linesep)
            except Exception as e:
                err_msg = f"Could not write to target file {target_file}: {e}"
                if self.tray_icon:
                    self.tray_icon.showMessage("Target Write Error", err_msg, QSystemTrayIcon.Warning, 5000)
                else:
                    QMessageBox.warning(None, "Target Write Error", err_msg)
                self.log_action("ERROR_TARGET_WRITE", err_msg, current_main_notes_file, target_file)

        if notes_moved_count > 0:
            msg = (f"{notes_moved_count} note(s) moved.\n"
                   f"Original file backed up to: {current_main_notes_file + '.bak'}\n"
                   f"Please check {LOG_FILE} for details.")
            if self.tray_icon:
                self.tray_icon.showMessage("Organization Complete", msg, QSystemTrayIcon.Information, 5000)
            else:
                QMessageBox.information(None, "Organization Complete", msg)
        else:
            msg = "No notes matched the defined mappings for moving."
            if self.tray_icon:
                self.tray_icon.showMessage("Organization Complete", msg, QSystemTrayIcon.Information, 3000)
            else:
                QMessageBox.information(None, "Organization Complete", msg)


def main():
    # QApplication instance is managed by NoteOrganizerAppLogic
    app_logic = NoteOrganizerAppLogic()
    app_logic.start_tray_app()


if __name__ == "__main__":
    # It's good practice to ensure QT_QPA_PLATFORM is set if issues arise,
    # but often not needed. The example mouse_modes app uses it.
    os.environ["QT_QPA_PLATFORM"] = "xcb" # Ensure this is set before QApplication is created
    main()