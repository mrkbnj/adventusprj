"""
Warehouse Management System
Copyright (c) 2026 Mark Benjamin H. Acob - All Rights Reserved

Proprietary Software - Internal Use Only
This software is proprietary and confidential.
Unauthorized copying, modification, or distribution is prohibited.

A comprehensive warehouse management system with QR code generation,
item staging, and shelf management capabilities.
Warehouse 1: General IT Equipment
Warehouse 2: Computer Peripherals (Monitor, Keyboard, Mouse, Headset)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import uuid
import qrcode
import re
from datetime import datetime

FILE = "warehouse.xlsx"
LOG_FILE = "activity_log.xlsx"
QR_FOLDER = "qr_codes"
QR_FOLDER_W1 = os.path.join(QR_FOLDER, "warehouse_1")
QR_FOLDER_W2 = os.path.join(QR_FOLDER, "warehouse_2")
QR_LABELS_FOLDER = "qr_labels"
QR_LABELS_FOLDER_W1 = os.path.join(QR_LABELS_FOLDER, "warehouse_1")
QR_LABELS_FOLDER_W2 = os.path.join(QR_LABELS_FOLDER, "warehouse_2")

SHELVES_W1= [
    "Area A", "Area B", "Area C",
    "Rack 1 - Bay 1", "Rack 1 - Bay 2", "Rack 1 - Bay 3",
    "Rack 2 - Bay 1", "Rack 2 - Bay 2", "Rack 2 - Bay 3",
]

SHELVES_W2= [
    "Area A", "Area B", "Area C",
    "Rack 1 - Bay 1", "Rack 1 - Bay 2", "Rack 1 - Bay 3",
    "Rack 2 - Bay 1", "Rack 2 - Bay 2", "Rack 2 - Bay 3",
]

EQUIPMENT_TYPES = ["Monitor", "Keyboard", "Mouse", "Headset"]

staged_items = []
selected_staged_index = None
staged_sets = []
selected_set_index = None
current_user = ""
session_start = ""

# ========== INITIALIZATION ==========

def initialize_file():
    sheets_to_create = {}
    if not os.path.exists(FILE):
        sheets_to_create = {"items": None, "shelves": None, "pullouts": None,
                            "items_w2": None, "pullouts_w2": None}
        mode = 'w'
    else:
        with pd.ExcelFile(FILE) as xls:
            existing = xls.sheet_names
        needed = ["items", "shelves", "pullouts", "items_w2", "shelves_w2", "pullouts_w2"]
        sheets_to_create = {s: None for s in needed if s not in existing}
        mode = 'a'

    if not sheets_to_create:
        return

    default_dfs = {
        # W1 Sheets
        "items": pd.DataFrame(columns=["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]),
        "shelves": pd.DataFrame({"Shelf": SHELVES_W1, "Status": ["AVAILABLE"] * len(SHELVES_W1), "Date_Full": [None] * len(SHELVES_W1)}),
        "pullouts": pd.DataFrame(columns=["Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Pull Reason", "Date"]),
        
        # W2 Sheets
        "items_w2": pd.DataFrame(columns=["QR", "Set ID", "Equipment Type", "Brand/Model", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]),
        "shelves_w2": pd.DataFrame({"Shelf": SHELVES_W2, "Status": ["AVAILABLE"] * len(SHELVES_W2), "Date_Full": [None] * len(SHELVES_W2)}),
        "pullouts_w2": pd.DataFrame(columns=["Set ID", "Equipment Type", "Brand/Model", "Serial Number", "Checked By", "Shelf", "Remarks", "Pull Reason", "Date"]),
    }
    with pd.ExcelWriter(FILE, engine='openpyxl', mode=mode) as writer:
        for sheet in sheets_to_create:
            default_dfs[sheet].to_excel(writer, sheet_name=sheet, index=False)

def initialize_log():
    if not os.path.exists(LOG_FILE):
        with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
            pd.DataFrame(columns=["Timestamp", "User", "Action", "Details"]).to_excel(writer, sheet_name="logs", index=False)

# ========== LOAD / SAVE ==========

def _load_sheet(file, sheet, init_fn):
    try:
        return pd.read_excel(file, sheet_name=sheet)
    except Exception:
        init_fn()
        return pd.read_excel(file, sheet_name=sheet)

def load_items():       return _load_sheet(FILE, "items", initialize_file)
def load_shelves():     return _load_sheet(FILE, "shelves", initialize_file) # W1 Only
def load_shelves_w2():  return _load_sheet(FILE, "shelves_w2", initialize_file) # W2 Only
def load_pullouts():    return _load_sheet(FILE, "pullouts", initialize_file)
def load_items_w2():    return _load_sheet(FILE, "items_w2", initialize_file)
def load_pullouts_w2(): return _load_sheet(FILE, "pullouts_w2", initialize_file)
def load_logs():        return _load_sheet(LOG_FILE, "logs", initialize_log)

def save_warehouse_1(df_items, df_shelves, df_pullouts=None):
    """Strictly saves Warehouse 1 sheets while preserving Warehouse 2."""
    if df_pullouts is None: df_pullouts = load_pullouts()
    df_items_w2 = load_items_w2()
    df_shelves_w2 = load_shelves_w2()
    df_po2 = load_pullouts_w2()
    
    with pd.ExcelWriter(FILE, engine='openpyxl') as writer:
        df_items.to_excel(writer, sheet_name="items", index=False)
        df_shelves.to_excel(writer, sheet_name="shelves", index=False)
        df_pullouts.to_excel(writer, sheet_name="pullouts", index=False)
        df_items_w2.to_excel(writer, sheet_name="items_w2", index=False)
        df_shelves_w2.to_excel(writer, sheet_name="shelves_w2", index=False)
        df_po2.to_excel(writer, sheet_name="pullouts_w2", index=False)

def save_warehouse_2(df_items_w2, df_shelves_w2, df_pullouts_w2=None):
    """Strictly saves Warehouse 2 sheets while preserving Warehouse 1."""
    if df_pullouts_w2 is None: df_pullouts_w2 = load_pullouts_w2()
    df_items_w1 = load_items()
    df_shelves_w1 = load_shelves()
    df_po1 = load_pullouts()
    
    with pd.ExcelWriter(FILE, engine='openpyxl') as writer:
        df_items_w1.to_excel(writer, sheet_name="items", index=False)
        df_shelves_w1.to_excel(writer, sheet_name="shelves", index=False)
        df_po1.to_excel(writer, sheet_name="pullouts", index=False)
        df_items_w2.to_excel(writer, sheet_name="items_w2", index=False)
        df_shelves_w2.to_excel(writer, sheet_name="shelves_w2", index=False)
        df_pullouts_w2.to_excel(writer, sheet_name="pullouts_w2", index=False)

def save_all(df_items, df_shelves, df_pullouts=None):
    """Alias for save_warehouse_1 — saves W1 sheets while preserving W2."""
    save_warehouse_1(df_items, df_shelves, df_pullouts)

def save_all_w2(df_items_w2, df_pullouts_w2=None):
    """Alias for save_warehouse_2 — saves W2 sheets while preserving W1."""
    df_shelves_w2 = load_shelves_w2()
    save_warehouse_2(df_items_w2, df_shelves_w2, df_pullouts_w2)

def save_log(action, details=""):
    initialize_log()
    df_log = load_logs()
    new_row = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": current_user, "Action": action, "Details": details}
    df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)
    with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
        df_log.to_excel(writer, sheet_name="logs", index=False)

# ========== QR HELPERS ==========

def qr_path_for(hostname, warehouse=1):
    folder = QR_FOLDER_W1 if warehouse == 1 else QR_FOLDER_W2
    return os.path.join(folder, f"{hostname.replace(' ', '_')}.png")

def generate_qr(hostname, data, warehouse=1):
    folder = QR_FOLDER_W1 if warehouse == 1 else QR_FOLDER_W2
    os.makedirs(folder, exist_ok=True)
    qr_img = qrcode.make(data)
    qr_img.save(qr_path_for(hostname, warehouse))

def delete_qr(hostname, warehouse=1):
    path = qr_path_for(hostname, warehouse)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            messagebox.showwarning("Warning", f"QR file not deleted: {e}")

def next_set_id():
    df = load_items_w2()
    # Also include staged sets
    existing_ids = set(df["Set ID"].dropna().tolist()) if "Set ID" in df.columns else set()
    for s in staged_sets:
        existing_ids.add(s["set_id"])
    n = 1
    while True:
        sid = f"SET-{n:03d}"
        if sid not in existing_ids:
            return sid
        n += 1

# ========== W1 STAGING ==========

def update_staged_display():
    staged_listbox.delete(0, tk.END)
    if not staged_items:
        staged_listbox.insert(tk.END, "No staged items")
        return
    for item in staged_items:
        staged_listbox.insert(tk.END, f"{item['Hostname']} → {item['Shelf']} → {item['Remarks']}")

def select_staged_item(event):
    global selected_staged_index
    selection = staged_listbox.curselection()
    if not selection:
        return
    index = selection[0]
    selected_staged_index = index
    item = staged_items[index]
    _fill_input_fields(item["Hostname"], item.get("Serial Number", ""), item.get("Checked By", ""), item["Shelf"], item["Remarks"])

# ========== W1 INPUT HELPERS ==========

def _fill_input_fields(hostname="", serial="", checked_by="", shelf="", remarks=""):
    hostname_entry.delete(0, tk.END); hostname_entry.insert(0, hostname)
    serial_entry.delete(0, tk.END);   serial_entry.insert(0, serial)
    checked_by_entry.delete(0, tk.END); checked_by_entry.insert(0, checked_by)
    shelf_var.set(shelf)
    remarks_var.set(remarks)

def _clear_input_fields():
    _fill_input_fields()

# ========== W1 CORE ==========

def remove_from_staging():
    global selected_staged_index
    if selected_staged_index is not None:
        index = selected_staged_index
        if index >= len(staged_items):
            messagebox.showerror("Error", "Invalid staged selection")
            selected_staged_index = None
            return
        removed = staged_items.pop(index)
        selected_staged_index = None
        _clear_input_fields()
        messagebox.showinfo("Removed", f"'{removed['Hostname']}' removed from staging")
    else:
        if not staged_items:
            messagebox.showinfo("Info", "No staged items to clear")
            return
        if not messagebox.askyesno("Confirm", f"Clear all {len(staged_items)} staged item(s)?"):
            return
        staged_items.clear()
        selected_staged_index = None
        _clear_input_fields()
        messagebox.showinfo("Cleared", "All staged items cleared")
    update_staged_display()

def put_item():
    hostname = hostname_entry.get().strip()
    shelf = shelf_var.get()
    serial = serial_entry.get().strip()

    if not hostname:
        messagebox.showerror("Error", "Please enter a Hostname"); return
    if not shelf:
        messagebox.showerror("Error", "Please select a Shelf"); return

    df_items = load_items()
    df_shelves = load_shelves()

    if hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", "Hostname already exists in warehouse"); return
    if any(item['Hostname'] == hostname for item in staged_items):
        messagebox.showerror("Error", "Hostname already staged"); return

    if serial:
        if serial in df_items["Serial Number"].astype(str).values:
            match = df_items[df_items["Serial Number"].astype(str) == serial].iloc[0]
            messagebox.showerror("Error",
                f"Serial Number '{serial}' is already assigned to:\n"
                f"Hostname: {match['Hostname']} | Shelf: {match['Shelf']}"); return
        if any(item.get('Serial Number') == serial for item in staged_items):
            match = next(item for item in staged_items if item.get('Serial Number') == serial)
            messagebox.showerror("Error",
                f"Serial Number '{serial}' is already staged under:\n"
                f"Hostname: {match['Hostname']} | Shelf: {match['Shelf']}"); return

    status = df_shelves[df_shelves["Shelf"] == shelf]["Status"].values
    if len(status) > 0 and status[0] == "FULL":
        messagebox.showerror("Error", "Shelf is marked FULL"); return

    staged_items.append({
        "Hostname": hostname,
        "Serial Number": serial,
        "Checked By": checked_by_entry.get().strip(),
        "Shelf": shelf,
        "Remarks": remarks_var.get(),
    })
    _clear_input_fields()
    messagebox.showinfo("Staged", f"'{hostname}' added to staging queue")
    update_staged_display()

def put_warehouse():
    if not staged_items:
        messagebox.showerror("Error", "No staged items to put"); return
    if not messagebox.askyesno("Confirm", f"Put {len(staged_items)} item(s) to warehouse?"):
        return

    try:
        df_items = load_items()
        df_shelves = load_shelves()
        for col in ["Serial Number", "Checked By"]:
            if col not in df_items.columns:
                df_items[col] = ""

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in staged_items:
            qr_code = str(uuid.uuid4())
            generate_qr(item['Hostname'], (
                f"Hostname: {item['Hostname']}\n"
                f"Serial Number: {item.get('Serial Number', '')}\n"
                f"Checked By: {item.get('Checked By', '')}\n"
                f"Shelf: {item['Shelf']}\n"
                f"Remarks: {item['Remarks']}\n"
                f"Date: {now_str}"
            ), warehouse=1)
            df_items = pd.concat([df_items, pd.DataFrame([{
                "QR": qr_code,
                "Hostname": item['Hostname'],
                "Serial Number": item.get('Serial Number', ''),
                "Checked By": item.get('Checked By', ''),
                "Shelf": item['Shelf'],
                "Remarks": item['Remarks'],
                "Date": now_str
            }])], ignore_index=True)

        save_all(df_items, df_shelves)

        try:
            pdf_path = generate_qr_pdf([{**item, '_warehouse': 1} for item in staged_items])
            pdf_msg = f"\nQR labels saved to:\n{pdf_path}"
        except Exception as pdf_err:
            pdf_msg = f"\nPDF generation failed: {pdf_err}"

        count = len(staged_items)
        for item in staged_items:
            save_log("PUT WAREHOUSE", f"[W1] Hostname: {item['Hostname']} | Shelf: {item['Shelf']}")

        staged_items.clear()
        messagebox.showinfo("Success", f"{count} item(s) added to Warehouse 1{pdf_msg}")
        update_staged_display()
        w1_refresh_all()

    except Exception as e:
        messagebox.showerror("Save Error",
            f"Failed to save to Excel:\n{str(e)}\n\n"
            "Common causes:\n• Excel file is open → close it\n• Wrong folder")
        
def get_global_inventory():
    # Load W1 Data
    df_w1 = load_items()
    df_w1["Warehouse"] = "W1 - General IT"
    df_w1["Item Name"] = df_w1["Hostname"] # Standardize naming for the view
    
    # Load W2 Data
    df_w2 = load_items_w2()
    df_w2["Warehouse"] = "W2 - Peripherals"
    # Combine Set ID and Equipment type so it reads clearly in a global list
    df_w2["Item Name"] = df_w2["Set ID"] + " (" + df_w2["Equipment Type"] + ")" 
    
    # Align columns you want to display in the global viewer
    cols_to_keep = ["Warehouse", "Item Name", "Serial Number", "Shelf", "Checked By", "Date"]
    
    # Handle missing columns gracefully before merging
    for df in [df_w1, df_w2]:
        for col in cols_to_keep:
            if col not in df.columns:
                df[col] = ""

    # Merge them together vertically
    df_global = pd.concat([df_w1[cols_to_keep], df_w2[cols_to_keep]], ignore_index=True)
    return df_global

def search_global_inventory(keyword=""):
    df_all = get_global_inventory()
    
    if keyword:
        keyword = keyword.lower()
        # Search across Item Name, Serial, and Shelf
        mask = (
            df_all["Item Name"].str.lower().str.contains(keyword, na=False) |
            df_all["Serial Number"].str.lower().str.contains(keyword, na=False) |
            df_all["Shelf"].str.lower().str.contains(keyword, na=False)
        )
        df_all = df_all[mask]
        
    # Clear your global TreeView
    tree_global_view.delete(*tree_global_view.get_children())
    
    # Populate TreeView
    for _, row in df_all.iterrows():
        tree_global_view.insert("", "end", values=(
            row["Warehouse"], 
            row["Item Name"], 
            row["Serial Number"], 
            row["Shelf"], 
            row["Checked By"]
        ))

def update_item():
    global selected_staged_index
    new_hostname = hostname_entry.get().strip()
    new_serial = serial_entry.get().strip()

    if not new_hostname:
        messagebox.showerror("Error", "Hostname cannot be empty"); return

    if selected_staged_index is not None:
        index = selected_staged_index
        if index >= len(staged_items):
            messagebox.showerror("Error", "Invalid staged selection")
            selected_staged_index = None
            return
        if any(i != index and item['Hostname'] == new_hostname for i, item in enumerate(staged_items)):
            messagebox.showerror("Error", "Hostname already exists in staging"); return
        if new_serial:
            if any(i != index and item.get('Serial Number') == new_serial for i, item in enumerate(staged_items)):
                match = next(item for i, item in enumerate(staged_items) if i != index and item.get('Serial Number') == new_serial)
                messagebox.showerror("Error",
                    f"Serial Number '{new_serial}' is already staged under:\n"
                    f"Hostname: {match['Hostname']}"); return
            df_items = load_items()
            if new_serial in df_items["Serial Number"].astype(str).values:
                match = df_items[df_items["Serial Number"].astype(str) == new_serial].iloc[0]
                messagebox.showerror("Error",
                    f"Serial Number '{new_serial}' is already in warehouse:\n"
                    f"Hostname: {match['Hostname']} | Shelf: {match['Shelf']}"); return
        staged_items[index].update({
            "Hostname": new_hostname,
            "Serial Number": new_serial,
            "Checked By": checked_by_entry.get().strip(),
            "Shelf": shelf_var.get(),
            "Remarks": remarks_var.get(),
        })
        messagebox.showinfo("Updated", "Staged item updated")
        update_staged_display()
        selected_staged_index = None
        return

    selected = tree_warehouse.selection()
    if not selected:
        messagebox.showerror("Error", "Select item to update"); return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])
    old_serial = df_items.at[index, "Serial Number"]

    if new_hostname != df_items.at[index, "Hostname"] and new_hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", "Hostname already exists and has a QR assigned"); return

    if new_serial and new_serial != str(old_serial):
        dup = df_items[df_items["Serial Number"].astype(str) == new_serial]
        dup = dup[dup.index != index]
        if not dup.empty:
            match = dup.iloc[0]
            messagebox.showerror("Error",
                f"Serial Number '{new_serial}' is already assigned to:\n"
                f"Hostname: {match['Hostname']} | Shelf: {match['Shelf']}"); return

    df_items.at[index, "Hostname"] = new_hostname
    df_items.at[index, "Serial Number"] = new_serial
    df_items.at[index, "Checked By"] = checked_by_entry.get().strip()
    df_items.at[index, "Shelf"] = shelf_var.get()
    df_items.at[index, "Remarks"] = remarks_var.get()
    save_all(df_items, df_shelves)
    save_log("UPDATE ITEM", f"[W1] Hostname: {new_hostname} | Shelf: {shelf_var.get()}")
    messagebox.showinfo("Updated", "Record updated")
    w1_refresh_all()

def delete_item():
    selected = tree_warehouse.selection()
    if not selected:
        messagebox.showerror("Error", "Select item"); return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])
    hostname = df_items.at[index, "Hostname"]

    delete_qr(hostname, warehouse=1)
    df_items = df_items.drop(index).reset_index(drop=True)
    save_all(df_items, df_shelves)
    save_log("DELETE ITEM", f"[W1] Hostname: {hostname}")
    messagebox.showinfo("Deleted", "Record and QR code deleted")
    w1_refresh_all()

def pull_item():
    hostname = pull_item_entry.get().strip()
    reason = pull_reason_entry.get().strip()
    if not hostname:
        messagebox.showerror("Error", "No item selected for pull out"); return
    if not reason:
        messagebox.showerror("Error", "Please enter a pull reason"); return

    df_items = load_items()
    df_shelves = load_shelves()
    df_pullouts = load_pullouts()

    match = df_items[df_items["Hostname"] == hostname]
    if match.empty:
        messagebox.showerror("Error", f"'{hostname}' not found in warehouse"); return
    if not messagebox.askyesno("Confirm Pull Out", f"Pull out '{hostname}' from warehouse?\nReason: {reason}"):
        return

    item_row = match.iloc[0]
    shelf = str(item_row.get("Shelf", ""))

    delete_qr(hostname, warehouse=1)
    df_items = df_items[df_items["Hostname"] != hostname].reset_index(drop=True)
    df_pullouts = pd.concat([df_pullouts, pd.DataFrame([{
        "Hostname": hostname,
        "Serial Number": str(item_row.get("Serial Number", "")),
        "Checked By": str(item_row.get("Checked By", "")),
        "Shelf": shelf,
        "Remarks": str(item_row.get("Remarks", "")),
        "Pull Reason": reason,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])], ignore_index=True)

    save_all(df_items, df_shelves, df_pullouts)
    save_log("WAREHOUSE PULL", f"[W1] Hostname: {hostname} | Shelf: {shelf} | Reason: {reason}")
    messagebox.showinfo("Success", f"'{hostname}' pulled out successfully")
    pull_item_entry.delete(0, tk.END)
    pull_reason_entry.delete(0, tk.END)
    w1_refresh_all()

def undo_pull(event):
    item_id = tree_pullouts.identify_row(event.y)
    if not item_id:
        return
    values = tree_pullouts.item(item_id, "values")
    if not values:
        return

    hostname, shelf, remarks = values[0], values[1], values[2]
    if not messagebox.askyesno("Undo Pull", f"Restore '{hostname}' back to the warehouse?\n\nShelf: {shelf}\nRemarks: {remarks}"):
        return

    df_items = load_items()
    df_shelves = load_shelves()
    df_pullouts = load_pullouts()

    if hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", f"'{hostname}' already exists in warehouse"); return

    match = df_pullouts[df_pullouts["Hostname"] == hostname]
    if match.empty:
        messagebox.showerror("Error", f"'{hostname}' not found in pull history"); return

    pull_row = match.iloc[0]
    qr_code = ""
    try:
        qr_code = str(uuid.uuid4())
        generate_qr(hostname, qr_code, warehouse=1)
    except Exception as e:
        messagebox.showwarning("Warning", f"QR code not regenerated: {e}")

    for col in ["Serial Number", "Checked By"]:
        if col not in df_items.columns:
            df_items[col] = ""

    df_items = pd.concat([df_items, pd.DataFrame([{
        "QR": qr_code,
        "Hostname": hostname,
        "Serial Number": str(pull_row.get("Serial Number", "")),
        "Checked By": str(pull_row.get("Checked By", "")),
        "Shelf": shelf,
        "Remarks": remarks,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])], ignore_index=True)

    df_pullouts = df_pullouts[df_pullouts["Hostname"] != hostname].reset_index(drop=True)
    save_all(df_items, df_shelves, df_pullouts)
    save_log("UNDO PULL", f"[W1] Hostname: {hostname} | Shelf: {shelf}")
    messagebox.showinfo("Restored", f"'{hostname}' has been restored to the warehouse")
    show_pullouts()

def unstage_from_warehouse(event):
    item_id = tree_warehouse.identify_row(event.y)
    if not item_id:
        return
    values = tree_warehouse.item(item_id, "values")
    if not values:
        return

    hostname, serial, checked_by, shelf, remarks = values[1], values[2], values[3], values[4], values[5]
    if not messagebox.askyesno("Move to Staging", f"Move '{hostname}' back to staging?\n\nShelf: {shelf}\nRemarks: {remarks}"):
        return
    if any(item['Hostname'] == hostname for item in staged_items):
        messagebox.showerror("Error", f"'{hostname}' is already in staging"); return

    df_items = load_items()
    df_shelves = load_shelves()
    delete_qr(hostname, warehouse=1)
    df_items = df_items[df_items["Hostname"] != hostname].reset_index(drop=True)
    save_all(df_items, df_shelves)
    staged_items.append({"Hostname": hostname, "Serial Number": serial, "Checked By": checked_by, "Shelf": shelf, "Remarks": remarks})
    save_log("UNSTAGE", f"[W1] Hostname: {hostname} | Shelf: {shelf}")
    messagebox.showinfo("Moved", f"'{hostname}' moved back to staging")
    update_staged_display()
    w1_refresh_all()

# ========== W1 SHELF MANAGEMENT ==========

def add_shelf():
    new_shelf = remove_shelf_var.get().strip()
    if not new_shelf:
        messagebox.showerror("Error", "Enter shelf name"); return
    df_shelves = load_shelves()
    if new_shelf in df_shelves["Shelf"].values:
        messagebox.showerror("Error", "Shelf already exists"); return
    df_shelves = pd.concat([df_shelves, pd.DataFrame([{"Shelf": new_shelf, "Status": "AVAILABLE"}])], ignore_index=True)
    df_shelves = df_shelves.sort_values("Shelf", ignore_index=True)
    save_all(load_items(), df_shelves)
    messagebox.showinfo("Success", f"Shelf '{new_shelf}' added")
    remove_shelf_var.set("")
    update_all_shelf_dropdowns()

def remove_shelf():
    shelf_name = remove_shelf_var.get().strip()
    if not shelf_name:
        messagebox.showerror("Error", "Select a shelf to remove"); return
    df_items = load_items()
    df_shelves = load_shelves()
    items_in_shelf = df_items[df_items["Shelf"] == shelf_name]
    if not items_in_shelf.empty:
        messagebox.showerror("Error", f"Cannot remove shelf '{shelf_name}' - it has {len(items_in_shelf)} item(s)"); return
    if shelf_name not in df_shelves["Shelf"].values:
        messagebox.showerror("Error", f"Shelf '{shelf_name}' does not exist"); return
    df_shelves = df_shelves[df_shelves["Shelf"] != shelf_name].sort_values("Shelf", ignore_index=True)
    save_all(df_items, df_shelves)
    messagebox.showinfo("Success", f"Shelf '{shelf_name}' removed")
    remove_shelf_var.set("")
    update_all_shelf_dropdowns()

def set_shelf_status(new_status):
    shelf = shelf_control_var.get()
    if not shelf:
        messagebox.showerror("Error", "Select a shelf from Shelf Control"); return
    df_items = load_items()
    df_shelves = load_shelves()
    idx = df_shelves[df_shelves["Shelf"] == shelf].index
    if len(idx) == 0:
        return
    df_shelves.at[idx[0], "Status"] = new_status
    df_shelves.at[idx[0], "Date_Full"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "FULL" else None
    save_all(df_items, df_shelves)
    save_log("SHELF STATUS", f"Shelf: {shelf} → {new_status}")
    w1_status_label.config(text=f"{shelf} → {new_status}")
    w1_refresh_all()

# ========== W1 DISPLAY ==========

def _show_tree(tree):
    for t in (tree_warehouse, tree_available, tree_pullouts, tree_qr):
        if t is not tree:
            t.pack_forget()
    tree.pack(fill="both", expand=True)

def show_qr_codes():
    _show_tree(tree_qr)
    tree_qr.delete(*tree_qr.get_children())
    df_items = load_items()
    for _, row in df_items.iterrows():
        hostname = row.get("Hostname", "")
        qr_str = row.get("QR", "")
        file_status = "Exists" if os.path.exists(qr_path_for(hostname, warehouse=1)) else "Missing"
        tree_qr.insert("", "end", values=(hostname, qr_str, file_status))

def show_warehouse():
    w1_update_full_shelves_display()
    _show_tree(tree_warehouse)
    tree_warehouse.delete(*tree_warehouse.get_children())
    df_items = load_items()
    if "Date" not in df_items.columns:
        df_items["Date"] = ""
    for _, row in df_items.iterrows():
        tree_warehouse.insert("", "end", values=tuple(row.get(c, "") for c in ["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]))

def show_available():
    _show_tree(tree_available)
    tree_available.delete(*tree_available.get_children())
    for _, row in load_shelves().sort_values("Shelf").iterrows():
        date_full = row.get("Date_Full", "")
        tree_available.insert("", "end", values=(row["Shelf"], row["Status"], date_full if pd.notna(date_full) else ""))

def show_pullouts():
    _show_tree(tree_pullouts)
    tree_pullouts.delete(*tree_pullouts.get_children())
    for _, row in load_pullouts().iterrows():
        tree_pullouts.insert("", "end", values=tuple(row.get(c, "") for c in ["Hostname", "Shelf", "Remarks", "Pull Reason", "Date"]))

def _populate_warehouse_tree(df):
    _show_tree(tree_warehouse)
    tree_warehouse.delete(*tree_warehouse.get_children())
    for _, row in df.iterrows():
        tree_warehouse.insert("", "end", values=tuple(row.get(c, "") for c in ["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]))

def search_item():
    keyword = search_entry.get().strip().lower()
    if not keyword:
        show_warehouse(); w1_search_label.config(text=""); return
    filtered = load_items()[lambda df: df["Hostname"].str.lower().str.contains(keyword, na=False)]
    _populate_warehouse_tree(filtered)
    w1_search_label.config(text=f"Search: {len(filtered)} result(s)")

def filter_pullouts():
    shelf_filter = pull_shelf_var.get()
    remarks_filter = pull_remarks_var.get()
    if not shelf_filter and not remarks_filter:
        messagebox.showinfo("Info", "Please select at least one filter"); return
    df = load_items()
    if shelf_filter:   df = df[df["Shelf"] == shelf_filter]
    if remarks_filter: df = df[df["Remarks"] == remarks_filter]
    _populate_warehouse_tree(df)
    w1_search_label.config(text=f"Filtered: {len(df)} item(s)"
        + (f" | Shelf: {shelf_filter}" if shelf_filter else "")
        + (f" | Remarks: {remarks_filter}" if remarks_filter else ""))

def filter_pull_history():
    reason = pull_reason_filter_entry.get().strip().lower()
    if not reason:
        show_pullouts(); return
    _show_tree(tree_pullouts)
    tree_pullouts.delete(*tree_pullouts.get_children())
    df = load_pullouts()
    filtered = df[df["Pull Reason"].str.lower().str.contains(reason, na=False)]
    for _, row in filtered.iterrows():
        tree_pullouts.insert("", "end", values=tuple(row.get(c, "") for c in ["Hostname", "Shelf", "Remarks", "Pull Reason", "Date"]))
    w1_search_label.config(text=f"Pull History Filtered: {len(filtered)} result(s)")

def w1_update_full_shelves_display():
    df_shelves = load_shelves()
    full_shelves = df_shelves[df_shelves["Status"] == "FULL"]["Shelf"].tolist()
    w1_full_label.config(text="FULL Shelves:\n" + "\n".join(full_shelves) if full_shelves else "FULL Shelves: None")

def w1_refresh_all():
    show_warehouse()
    update_all_shelf_dropdowns()

def update_all_shelf_dropdowns():
    # Load separate lists
    w1_shelf_list = sorted(load_shelves()["Shelf"].tolist())
    w2_shelf_list = sorted(load_shelves_w2()["Shelf"].tolist())

    # Update W1 specific dropdowns
    for dropdown in (shelf_dropdown, shelf_control_dropdown, remove_shelf_dropdown, pull_shelf_dropdown):
        try:
            dropdown["values"] = w1_shelf_list
        except NameError:
            pass # Ignore if UI isn't initialized yet

    # Update W2 specific dropdowns
    for dropdown in (w2_shelf_control_dropdown, w2_remove_shelf_dropdown): 
        try:
            dropdown["values"] = w2_shelf_list
        except NameError:
            pass

def select_item(event):
    selected = tree_warehouse.selection()
    if selected:
        values = tree_warehouse.item(selected[0], "values")
        _fill_input_fields(values[1], values[2], values[3], values[4], values[5])
        pull_item_entry.delete(0, tk.END)
        pull_item_entry.insert(0, values[1])

# ========== W1 RESET ==========

def reset_ui():
    _clear_input_fields()
    for s in tree_warehouse.selection(): tree_warehouse.selection_remove(s)
    w1_status_label.config(text="")
    w1_search_label.config(text="")
    show_warehouse()

def reset_shelf_control():
    shelf_control_var.set("")
    w1_status_label.config(text="")

def reset_shelf_addition():
    remove_shelf_var.set("")
    w1_status_label.config(text="")

def reset_pull_out():
    pull_item_entry.delete(0, tk.END)
    pull_reason_entry.delete(0, tk.END)
    for s in tree_warehouse.selection(): tree_warehouse.selection_remove(s)
    w1_status_label.config(text="")
    w1_search_label.config(text="")
    show_warehouse()

def clear_pull_filters():
    pull_shelf_var.set("")
    pull_remarks_var.set("")
    search_entry.delete(0, tk.END)
    pull_reason_filter_entry.delete(0, tk.END)
    w1_search_label.config(text="")
    show_warehouse()

# ========== W2 STAGING ==========

def update_w2_staged_display():
    w2_staged_listbox.delete(0, tk.END)
    if not staged_sets:
        w2_staged_listbox.insert(tk.END, "No staged sets")
        return
    for s in staged_sets:
        types = ", ".join(i["Equipment Type"] for i in s["items"])
        w2_staged_listbox.insert(tk.END, f"{s['set_id']} → {types}")

def w2_build_set():
    """Open a dialog to build a new equipment set."""
    selected_types = []
    for eq_type, var in w2_equip_vars.items():
        if var.get():
            selected_types.append(eq_type)

    if not selected_types:
        messagebox.showerror("Error", "Please select at least one equipment type"); return

    set_id = next_set_id()

    build_win = tk.Toplevel(root)
    build_win.title(f"Build {set_id}")
    build_win.resizable(False, False)
    build_win.transient(root)

    tk.Label(build_win, text=f"Fill in details for {set_id}", font=("Arial", 10, "bold")).pack(pady=(10, 5))

    shelf_list = sorted(load_shelves_w2()["Shelf"].tolist())

    # Build a form row per equipment type
    form_frame = tk.Frame(build_win, padx=10, pady=5)
    form_frame.pack()

    headers = ["Equipment", "Brand / Model", "Serial Number", "Checked By", "Shelf", "Remarks"]
    for col, h in enumerate(headers):
        tk.Label(form_frame, text=h, font=("Arial", 8, "bold"), width=14, anchor="w").grid(row=0, column=col, padx=3, pady=2)

    rows = {}
    for r, eq_type in enumerate(selected_types, start=1):
        tk.Label(form_frame, text=eq_type, width=14, anchor="w").grid(row=r, column=0, padx=3, pady=3)
        brand_e = tk.Entry(form_frame, width=16); brand_e.grid(row=r, column=1, padx=3)
        serial_e = tk.Entry(form_frame, width=14); serial_e.grid(row=r, column=2, padx=3)
        checked_e = tk.Entry(form_frame, width=14); checked_e.grid(row=r, column=3, padx=3)
        shelf_v = tk.StringVar()
        shelf_cb = ttk.Combobox(form_frame, textvariable=shelf_v, values=shelf_list, width=16, state="readonly")
        shelf_cb.grid(row=r, column=4, padx=3)
        remarks_v = tk.StringVar()
        remarks_cb = ttk.Combobox(form_frame, textvariable=remarks_v, values=["No Issue", "Minimal", "Defective"], width=12, state="readonly")
        remarks_cb.grid(row=r, column=5, padx=3)
        rows[eq_type] = (brand_e, serial_e, checked_e, shelf_v, remarks_v)

    error_lbl = tk.Label(build_win, text="", fg="red", font=("Arial", 8))
    error_lbl.pack()

    def confirm_set():
        df_items_w2 = load_items_w2()
        existing_serials_w2 = df_items_w2["Serial Number"].astype(str).tolist() if "Serial Number" in df_items_w2.columns else []
        # Also collect serials already in staged_sets
        staged_serials = []
        for ss in staged_sets:
            for it in ss["items"]:
                if it.get("Serial Number"):
                    staged_serials.append(it["Serial Number"])

        items = []
        for eq_type, (brand_e, serial_e, checked_e, shelf_v, remarks_v) in rows.items():
            shelf = shelf_v.get().strip()
            if not shelf:
                error_lbl.config(text=f"Please select a shelf for {eq_type}"); return
            serial = serial_e.get().strip()
            if serial:
                if serial in existing_serials_w2:
                    error_lbl.config(text=f"Serial '{serial}' already exists in Warehouse 2"); return
                if serial in staged_serials:
                    error_lbl.config(text=f"Serial '{serial}' already staged in another set"); return
                # check within this set
                if serial in [i.get("Serial Number") for i in items]:
                    error_lbl.config(text=f"Duplicate serial '{serial}' within this set"); return
            items.append({
                "Equipment Type": eq_type,
                "Brand/Model": brand_e.get().strip(),
                "Serial Number": serial,
                "Checked By": checked_e.get().strip(),
                "Shelf": shelf,
                "Remarks": remarks_v.get(),
            })

        staged_sets.append({"set_id": set_id, "items": items})
        # Clear checkboxes
        for var in w2_equip_vars.values():
            var.set(False)
        build_win.destroy()
        update_w2_staged_display()
        messagebox.showinfo("Staged", f"{set_id} added to staging with {len(items)} item(s)")

    btn_f = tk.Frame(build_win)
    btn_f.pack(pady=8)
    tk.Button(btn_f, text="Add to Staging", command=confirm_set, width=16).pack(side="left", padx=5)
    tk.Button(btn_f, text="Cancel", command=build_win.destroy, width=10).pack(side="left", padx=5)

    build_win.update_idletasks()
    build_win.grab_set()
    build_win.focus_force()

def w2_remove_staged_set():
    global selected_set_index
    sel = w2_staged_listbox.curselection()
    if not sel:
        if not staged_sets:
            messagebox.showinfo("Info", "No staged sets to clear"); return
        if not messagebox.askyesno("Confirm", f"Clear all {len(staged_sets)} staged set(s)?"):
            return
        staged_sets.clear()
        selected_set_index = None
        update_w2_staged_display()
        messagebox.showinfo("Cleared", "All staged sets cleared")
        return
    index = sel[0]
    if index >= len(staged_sets):
        return
    removed = staged_sets.pop(index)
    selected_set_index = None
    update_w2_staged_display()
    messagebox.showinfo("Removed", f"{removed['set_id']} removed from staging")

def w2_put_warehouse():
    if not staged_sets:
        messagebox.showerror("Error", "No staged sets to put"); return

    total_items = sum(len(s["items"]) for s in staged_sets)
    if not messagebox.askyesno("Confirm",
        f"Put {len(staged_sets)} set(s) ({total_items} item(s)) to Warehouse 2?"):
        return

    try:
        df_w2 = load_items_w2()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_items = []

        for s in staged_sets:
            set_id = s["set_id"]
            for item in s["items"]:
                eq_type = item["Equipment Type"]
                qr_label = f"{set_id}-{eq_type}"
                qr_code = str(uuid.uuid4())
                generate_qr(qr_label, (
                    f"Set ID: {set_id}\n"
                    f"Equipment: {eq_type}\n"
                    f"Brand/Model: {item.get('Brand/Model', '')}\n"
                    f"Serial Number: {item.get('Serial Number', '')}\n"
                    f"Checked By: {item.get('Checked By', '')}\n"
                    f"Shelf: {item['Shelf']}\n"
                    f"Remarks: {item['Remarks']}\n"
                    f"Date: {now_str}"
                ), warehouse=2)
                df_w2 = pd.concat([df_w2, pd.DataFrame([{
                    "QR": qr_code,
                    "Set ID": set_id,
                    "Equipment Type": eq_type,
                    "Brand/Model": item.get("Brand/Model", ""),
                    "Serial Number": item.get("Serial Number", ""),
                    "Checked By": item.get("Checked By", ""),
                    "Shelf": item["Shelf"],
                    "Remarks": item["Remarks"],
                    "Date": now_str
                }])], ignore_index=True)
                pdf_items.append({
                    "Hostname":       qr_label,
                    "Set ID":         set_id,
                    "Equipment Type": eq_type,
                    "Brand/Model":    item.get("Brand/Model", ""),
                    "Serial Number":  item.get("Serial Number", ""),
                    "Checked By":     item.get("Checked By", ""),
                    "Shelf":          item["Shelf"],
                    "Remarks":        item["Remarks"],
                    "_warehouse":     2,
                })
            save_log("PUT WAREHOUSE", f"[W2] Set: {set_id} | Items: {len(s['items'])}")

        save_all_w2(df_w2)

        try:
            pdf_path = generate_qr_pdf(pdf_items)
            pdf_msg = f"\nQR labels saved to:\n{pdf_path}"
        except Exception as pdf_err:
            pdf_msg = f"\nPDF generation failed: {pdf_err}"

        count = len(staged_sets)
        staged_sets.clear()
        update_w2_staged_display()
        w2_refresh_all()
        messagebox.showinfo("Success", f"{count} set(s) added to Warehouse 2{pdf_msg}")

    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save:\n{str(e)}")

# ========== W2 DISPLAY ==========

def _show_w2_tree(tree):
    for t in (tree_w2_warehouse, tree_w2_available, tree_w2_pullouts, tree_w2_qr):
        if t is not tree:
            t.pack_forget()
    tree.pack(fill="both", expand=True)

def w2_show_warehouse():
    w2_update_full_shelves_display()
    _show_w2_tree(tree_w2_warehouse)
    tree_w2_warehouse.delete(*tree_w2_warehouse.get_children())
    df = load_items_w2()
    for _, row in df.iterrows():
        tree_w2_warehouse.insert("", "end", values=tuple(
            row.get(c, "") for c in ["QR", "Set ID", "Equipment Type", "Brand/Model", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]))

def w2_show_available():
    _show_w2_tree(tree_w2_available)
    tree_w2_available.delete(*tree_w2_available.get_children())
    for _, row in load_shelves_w2().sort_values("Shelf").iterrows():
        date_full = row.get("Date_Full", "")
        tree_w2_available.insert("", "end", values=(row["Shelf"], row["Status"], date_full if pd.notna(date_full) else ""))

def w2_show_pullouts():
    _show_w2_tree(tree_w2_pullouts)
    tree_w2_pullouts.delete(*tree_w2_pullouts.get_children())
    for _, row in load_pullouts_w2().iterrows():
        tree_w2_pullouts.insert("", "end", values=tuple(
            row.get(c, "") for c in ["Set ID", "Equipment Type", "Brand/Model", "Shelf", "Remarks", "Pull Reason", "Date"]))

def w2_show_qr_codes():
    _show_w2_tree(tree_w2_qr)
    tree_w2_qr.delete(*tree_w2_qr.get_children())
    df = load_items_w2()
    for _, row in df.iterrows():
        eq_type = row.get("Equipment Type", "")
        set_id = row.get("Set ID", "")
        qr_label = f"{set_id}-{eq_type}"
        qr_str = row.get("QR", "")
        file_status = "Exists" if os.path.exists(qr_path_for(qr_label, warehouse=2)) else "Missing"
        tree_w2_qr.insert("", "end", values=(set_id, eq_type, qr_str, file_status))

def w2_search_item():
    keyword = w2_search_entry.get().strip().lower()
    if not keyword:
        w2_show_warehouse(); w2_search_label.config(text=""); return
    df = load_items_w2()
    filtered = df[
        df["Equipment Type"].str.lower().str.contains(keyword, na=False) |
        df["Brand/Model"].str.lower().str.contains(keyword, na=False) |
        df["Set ID"].str.lower().str.contains(keyword, na=False)
    ]
    _show_w2_tree(tree_w2_warehouse)
    tree_w2_warehouse.delete(*tree_w2_warehouse.get_children())
    for _, row in filtered.iterrows():
        tree_w2_warehouse.insert("", "end", values=tuple(
            row.get(c, "") for c in ["QR", "Set ID", "Equipment Type", "Brand/Model", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]))
    w2_search_label.config(text=f"Search: {len(filtered)} result(s)")

def w2_filter_items():
    shelf_f = w2_pull_shelf_var.get()
    type_f  = w2_type_filter_var.get()
    if not shelf_f and not type_f:
        messagebox.showinfo("Info", "Please select at least one filter"); return
    df = load_items_w2()
    if shelf_f: df = df[df["Shelf"] == shelf_f]
    if type_f:  df = df[df["Equipment Type"] == type_f]
    _show_w2_tree(tree_w2_warehouse)
    tree_w2_warehouse.delete(*tree_w2_warehouse.get_children())
    for _, row in df.iterrows():
        tree_w2_warehouse.insert("", "end", values=tuple(
            row.get(c, "") for c in ["QR", "Set ID", "Equipment Type", "Brand/Model", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]))
    w2_search_label.config(text=f"Filtered: {len(df)} item(s)")

def w2_clear_filters():
    w2_pull_shelf_var.set("")
    w2_type_filter_var.set("")
    w2_search_entry.delete(0, tk.END)
    w2_search_label.config(text="")
    w2_show_warehouse()

def w2_update_full_shelves_display():
    df_shelves = load_shelves_w2()
    full_shelves = df_shelves[df_shelves["Status"] == "FULL"]["Shelf"].tolist()
    w2_full_label.config(text="FULL Shelves:\n" + "\n".join(full_shelves) if full_shelves else "FULL Shelves: None")

def w2_refresh_all():
    w2_show_warehouse()
    update_all_shelf_dropdowns()

# ========== W2 PULL OUT ==========

def w2_select_item(event):
    selected = tree_w2_warehouse.selection()
    if selected:
        values = tree_w2_warehouse.item(selected[0], "values")
        # values: QR, Set ID, Equipment Type, Brand/Model, Serial, Checked By, Shelf, Remarks, Date
        w2_pull_item_entry.delete(0, tk.END)
        w2_pull_item_entry.insert(0, f"{values[1]} - {values[2]}")  # SET-001 - Monitor

def w2_pull_item():
    selection_text = w2_pull_item_entry.get().strip()
    reason = w2_pull_reason_entry.get().strip()
    if not selection_text:
        messagebox.showerror("Error", "No item selected for pull out"); return
    if not reason:
        messagebox.showerror("Error", "Please enter a pull reason"); return

    # Parse "SET-001 - Monitor"
    try:
        set_id, eq_type = [x.strip() for x in selection_text.split(" - ", 1)]
    except ValueError:
        messagebox.showerror("Error", "Invalid selection format"); return

    df_w2 = load_items_w2()
    df_po2 = load_pullouts_w2()

    match = df_w2[(df_w2["Set ID"] == set_id) & (df_w2["Equipment Type"] == eq_type)]
    if match.empty:
        messagebox.showerror("Error", f"'{selection_text}' not found in Warehouse 2"); return

    if not messagebox.askyesno("Confirm Pull Out",
        f"Pull out {eq_type} from {set_id}?\nReason: {reason}"):
        return

    item_row = match.iloc[0]
    qr_label = f"{set_id}-{eq_type}"
    delete_qr(qr_label, warehouse=2)

    df_w2 = df_w2.drop(match.index).reset_index(drop=True)
    df_po2 = pd.concat([df_po2, pd.DataFrame([{
        "Set ID": set_id,
        "Equipment Type": eq_type,
        "Brand/Model": str(item_row.get("Brand/Model", "")),
        "Serial Number": str(item_row.get("Serial Number", "")),
        "Checked By": str(item_row.get("Checked By", "")),
        "Shelf": str(item_row.get("Shelf", "")),
        "Remarks": str(item_row.get("Remarks", "")),
        "Pull Reason": reason,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])], ignore_index=True)

    save_all_w2(df_w2, df_po2)
    save_log("WAREHOUSE PULL", f"[W2] Set: {set_id} | Item: {eq_type} | Reason: {reason}")
    messagebox.showinfo("Success", f"{eq_type} from {set_id} pulled out successfully")
    w2_pull_item_entry.delete(0, tk.END)
    w2_pull_reason_entry.delete(0, tk.END)
    w2_refresh_all()

def w2_undo_pull(event):
    item_id = tree_w2_pullouts.identify_row(event.y)
    if not item_id:
        return
    values = tree_w2_pullouts.item(item_id, "values")
    if not values:
        return
    set_id, eq_type, brand, shelf, remarks = values[0], values[1], values[2], values[3], values[4]
    if not messagebox.askyesno("Undo Pull",
        f"Restore {eq_type} ({set_id}) back to Warehouse 2?\nShelf: {shelf}"):
        return

    df_w2 = load_items_w2()
    df_po2 = load_pullouts_w2()

    match = df_po2[(df_po2["Set ID"] == set_id) & (df_po2["Equipment Type"] == eq_type)]
    if match.empty:
        messagebox.showerror("Error", "Record not found in pull history"); return

    pull_row = match.iloc[0]
    qr_label = f"{set_id}-{eq_type}"
    qr_code = str(uuid.uuid4())
    try:
        generate_qr(qr_label, qr_code, warehouse=2)
    except Exception as e:
        messagebox.showwarning("Warning", f"QR not regenerated: {e}")

    df_w2 = pd.concat([df_w2, pd.DataFrame([{
        "QR": qr_code,
        "Set ID": set_id,
        "Equipment Type": eq_type,
        "Brand/Model": str(pull_row.get("Brand/Model", "")),
        "Serial Number": str(pull_row.get("Serial Number", "")),
        "Checked By": str(pull_row.get("Checked By", "")),
        "Shelf": shelf,
        "Remarks": remarks,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])], ignore_index=True)

    df_po2 = df_po2.drop(match.index).reset_index(drop=True)
    save_all_w2(df_w2, df_po2)
    save_log("UNDO PULL", f"[W2] Set: {set_id} | Item: {eq_type} | Shelf: {shelf}")
    messagebox.showinfo("Restored", f"{eq_type} from {set_id} restored to Warehouse 2")
    w2_show_pullouts()

# ========== W2 SHELF MANAGEMENT ==========

def w2_set_shelf_status(new_status):
    shelf = w2_shelf_control_var.get()
    if not shelf:
        messagebox.showerror("Error", "Select a shelf"); return
    df_items_w2 = load_items_w2()
    df_shelves_w2 = load_shelves_w2()
    idx = df_shelves_w2[df_shelves_w2["Shelf"] == shelf].index
    if len(idx) == 0:
        return
    df_shelves_w2.at[idx[0], "Status"] = new_status
    df_shelves_w2.at[idx[0], "Date_Full"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "FULL" else None
    save_warehouse_2(df_items_w2, df_shelves_w2)
    save_log("SHELF STATUS", f"[W2] Shelf: {shelf} → {new_status}")
    w2_status_label.config(text=f"{shelf} → {new_status}")
    w2_refresh_all()

def w2_add_shelf():
    new_shelf = w2_remove_shelf_var.get().strip()
    if not new_shelf:
        messagebox.showerror("Error", "Enter shelf name"); return
    df_shelves_w2 = load_shelves_w2()
    if new_shelf in df_shelves_w2["Shelf"].values:
        messagebox.showerror("Error", "Shelf already exists in W2"); return
    df_shelves_w2 = pd.concat([df_shelves_w2, pd.DataFrame([{"Shelf": new_shelf, "Status": "AVAILABLE"}])], ignore_index=True)
    df_shelves_w2 = df_shelves_w2.sort_values("Shelf", ignore_index=True)
    save_warehouse_2(load_items_w2(), df_shelves_w2)
    messagebox.showinfo("Success", f"Shelf '{new_shelf}' added to Warehouse 2")
    w2_remove_shelf_var.set("")
    update_all_shelf_dropdowns()

def w2_remove_shelf():
    shelf_name = w2_remove_shelf_var.get().strip()
    if not shelf_name:
        messagebox.showerror("Error", "Select a shelf to remove"); return
    df_items_w2 = load_items_w2()
    df_shelves_w2 = load_shelves_w2()
    if not df_items_w2[df_items_w2["Shelf"] == shelf_name].empty:
        messagebox.showerror("Error", f"Cannot remove shelf '{shelf_name}' — it still has items"); return
    if shelf_name not in df_shelves_w2["Shelf"].values:
        messagebox.showerror("Error", f"Shelf '{shelf_name}' does not exist in W2"); return
    df_shelves_w2 = df_shelves_w2[df_shelves_w2["Shelf"] != shelf_name].sort_values("Shelf", ignore_index=True)
    save_warehouse_2(df_items_w2, df_shelves_w2)
    messagebox.showinfo("Success", f"Shelf '{shelf_name}' removed from Warehouse 2")
    w2_remove_shelf_var.set("")
    update_all_shelf_dropdowns()

def w2_reset_shelf_control():
    w2_shelf_control_var.set("")
    w2_status_label.config(text="")

def w2_reset_shelf_addition():
    w2_remove_shelf_var.set("")
    w2_status_label.config(text="")

def w2_reset_pull_out():
    w2_pull_item_entry.delete(0, tk.END)
    w2_pull_reason_entry.delete(0, tk.END)
    w2_status_label.config(text="")
    w2_search_label.config(text="")
    w2_show_warehouse()

# ========== QR LABEL PDF ==========

def generate_qr_pdf(items_batch):
    from fpdf import FPDF
    PAGE_W, LABEL_W, LABEL_H = 210, 54, 58
    MARGIN_X, MARGIN_Y, COLS, ROW_GAP = 12, 10, 3, 3
    GAP_X = (PAGE_W - (COLS * LABEL_W) - (2 * MARGIN_X)) / (COLS - 1)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    col = row = 0
    for item in items_batch:
        x = MARGIN_X + col * (LABEL_W + GAP_X)
        y = MARGIN_Y + row * (LABEL_H + ROW_GAP)
        if y + LABEL_H > 297 - MARGIN_Y:
            pdf.add_page(); col = row = 0; x, y = MARGIN_X, MARGIN_Y
        pdf.set_draw_color(150, 150, 150)
        pdf.rect(x, y, LABEL_W, LABEL_H)
        path = qr_path_for(item['Hostname'], warehouse=item.get('_warehouse', 1))
        if not os.path.exists(path):
            alt = qr_path_for(item['Hostname'], warehouse=2 if item.get('_warehouse', 1) == 1 else 1)
            if os.path.exists(alt):
                path = alt
        if os.path.exists(path):
            qr_size = 20
            pdf.image(path, x=x + (LABEL_W - qr_size) / 2, y=y + 3, w=qr_size, h=qr_size)
        label_x, value_x, text_y, line_h = x + 2, x + 19, y + 26, 4.8

        # W2 items have Set ID / Equipment Type; W1 items have Hostname
        if item.get('_warehouse', 1) == 2:
            fields = [
                ("Set ID:",      str(item.get("Set ID", item.get("Hostname", "")))),
                ("Type:",        str(item.get("Equipment Type", ""))),
                ("Brand/Model:", str(item.get("Brand/Model", ""))),
                ("Serial No:",   str(item.get("Serial Number", ""))),
                ("Shelf:",       str(item.get("Shelf", ""))),
                ("Remarks:",     str(item.get("Remarks", ""))),
                ("Date:",        datetime.now().strftime("%Y-%m-%d")),
            ]
        else:
            fields = [
                ("Hostname:",   str(item.get("Hostname", ""))),
                ("Serial No:",  str(item.get("Serial Number", ""))),
                ("Checked By:", str(item.get("Checked By", ""))),
                ("Shelf:",      str(item.get("Shelf", ""))),
                ("Remarks:",    str(item.get("Remarks", ""))),
                ("Date:",       datetime.now().strftime("%Y-%m-%d")),
            ]

        for label, value in fields:
            pdf.set_font("Helvetica", style="B", size=5.5)
            pdf.set_xy(label_x, text_y); pdf.cell(17, line_h, label, ln=0)
            pdf.set_font("Helvetica", size=5.5)
            pdf.set_xy(value_x, text_y); pdf.cell(LABEL_W - 21, line_h, value[:22], ln=0)
            text_y += line_h
        col += 1
        if col >= COLS:
            col = 0; row += 1
    date_str = datetime.now().strftime("%Y-%m-%d")
    if items_batch and items_batch[0].get('_warehouse', 1) == 2:
        output_folder = QR_LABELS_FOLDER_W2
        # W2: collect unique Set IDs
        set_ids = list(dict.fromkeys(item.get("Set ID", item.get("Hostname", "")) for item in items_batch))
        label_name = "_".join(set_ids[:3])
        if len(set_ids) > 3:
            label_name += f"_and_{len(set_ids)-3}_more"
    else:
        output_folder = QR_LABELS_FOLDER_W1
        # W1: collect unique hostnames
        hostnames = list(dict.fromkeys(item.get("Hostname", "") for item in items_batch))
        label_name = "_".join(hostnames[:3])
        if len(hostnames) > 3:
            label_name += f"_and_{len(hostnames)-3}_more"
    os.makedirs(output_folder, exist_ok=True)
    safe_name = label_name.replace(" ", "_").replace("/", "-")
    pdf_path = os.path.join(output_folder, f"{safe_name}_{date_str}.pdf")
    pdf.output(pdf_path)
    return pdf_path

# ========== DIALOGS ==========

def open_label_manager():
    manager = tk.Toplevel(root)
    manager.title("QR Label Manager")
    manager.geometry("640x420")
    manager.resizable(False, False)
    tk.Label(manager, text="QR Label Files", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
    table_frame_m = tk.Frame(manager)
    table_frame_m.pack(fill="both", expand=True, padx=10, pady=5)
    tree_labels = ttk.Treeview(table_frame_m, columns=("Warehouse", "File", "Date", "Size"), show="headings", height=14)
    for col, text, width in [("Warehouse", "Warehouse", 120), ("File", "Filename", 280), ("Date", "Created", 130), ("Size", "Size", 65)]:
        tree_labels.heading(col, text=text); tree_labels.column(col, width=width)
    tree_labels.pack(fill="both", expand=True)

    # store full path alongside each row so open/delete know where to look
    row_paths = {}

    def load_label_files():
        tree_labels.delete(*tree_labels.get_children())
        row_paths.clear()
        now = datetime.now()
        for warehouse_label, folder in [
            ("Warehouse 1", QR_LABELS_FOLDER_W1),
            ("Warehouse 2", QR_LABELS_FOLDER_W2),
        ]:
            if not os.path.exists(folder):
                continue
            for f in sorted([f for f in os.listdir(folder) if f.endswith(".pdf")], reverse=True):
                full_path = os.path.join(folder, f)
                size_kb = round(os.path.getsize(full_path) / 1024, 1)
                try:
                    # try to parse a date from the end of the filename
                    date_part = f.replace(".pdf", "")[-10:]  # last 10 chars = YYYY-MM-DD
                    file_dt = datetime.strptime(date_part, "%Y-%m-%d")
                    delta = now - file_dt
                    age = "Today" if delta.days == 0 else ("1 day ago" if delta.days == 1 else f"{delta.days} days ago")
                    date_str = f"{file_dt.strftime('%Y-%m-%d')}  ({age})"
                except Exception:
                    date_str = "Unknown"
                iid = tree_labels.insert("", "end", values=(warehouse_label, f, date_str, f"{size_kb} kb"))
                row_paths[iid] = full_path

    def open_selected():
        selected = tree_labels.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a file to open", parent=manager); return
        full_path = row_paths.get(selected[0])
        if full_path and os.path.exists(full_path):
            os.startfile(full_path)
        else:
            messagebox.showerror("Error", "File not found", parent=manager)

    def clear_selected():
        selected = tree_labels.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a file to clear", parent=manager); return
        full_path = row_paths.get(selected[0])
        filename = tree_labels.item(selected[0], "values")[1]
        if not messagebox.askyesno("Confirm Clear", f"Delete '{filename}'?", parent=manager): return
        try:
            os.remove(full_path)
            load_label_files()
            messagebox.showinfo("Cleared", f"'{filename}' deleted", parent=manager)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}", parent=manager)

    btn_frame_m = tk.Frame(manager)
    btn_frame_m.pack(pady=8)
    tk.Button(btn_frame_m, text="OPEN",    command=open_selected,   width=12).pack(side="left", padx=5)
    tk.Button(btn_frame_m, text="CLEAR",   command=clear_selected,  width=12).pack(side="left", padx=5)
    tk.Button(btn_frame_m, text="REFRESH", command=load_label_files, width=12).pack(side="left", padx=5)
    load_label_files()

def open_activity_log():
    log_win = tk.Toplevel(root)
    log_win.title("Activity Log")
    log_win.geometry("820x500")

    filter_frame = tk.Frame(log_win)
    filter_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(filter_frame, text="Filter Action:").pack(side="left", padx=(0, 2))
    filter_action_var = tk.StringVar()
    ttk.Combobox(filter_frame, textvariable=filter_action_var, state="readonly", width=15,
        values=["", "LOGIN", "LOGOUT", "PUT WAREHOUSE", "WAREHOUSE PULL", "UPDATE ITEM",
                "DELETE ITEM", "UNDO PULL", "UNSTAGE", "SHELF STATUS"]
    ).pack(side="left", padx=(0, 10))

    count_label = tk.Label(filter_frame, text="", fg="blue")
    count_label.pack(side="right", padx=10)

    content_frame = tk.Frame(log_win)
    content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    user_panel = tk.LabelFrame(content_frame, text="Users", padx=5, pady=5)
    user_panel.pack(side="left", fill="y", padx=(0, 8))

    user_scrollbar = ttk.Scrollbar(user_panel, orient="vertical")
    user_scrollbar.pack(side="right", fill="y")
    user_listbox = tk.Listbox(user_panel, width=18, yscrollcommand=user_scrollbar.set,
                               selectmode="single", exportselection=False, font=("Arial", 9))
    user_listbox.pack(side="left", fill="y")
    user_scrollbar.config(command=user_listbox.yview)

    btn_frame = tk.Frame(user_panel)
    btn_frame.pack(pady=(5, 0))
    tk.Button(btn_frame, text="FILTER", command=lambda: load_log_data(), width=8).pack(side="left", padx=2)
    tk.Button(btn_frame, text="↻",      command=lambda: reset_filters(), width=3).pack(side="left", padx=2)

    table_frame_l = tk.Frame(content_frame)
    table_frame_l.pack(side="left", fill="both", expand=True)
    scrollbar_y = ttk.Scrollbar(table_frame_l, orient="vertical")
    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x = ttk.Scrollbar(table_frame_l, orient="horizontal")
    scrollbar_x.pack(side="bottom", fill="x")
    tree_log = ttk.Treeview(table_frame_l,
                             columns=("Timestamp", "User", "Action", "Details"),
                             show="headings",
                             yscrollcommand=scrollbar_y.set,
                             xscrollcommand=scrollbar_x.set)
    for col, width in [("Timestamp", 140), ("User", 110), ("Action", 130), ("Details", 350)]:
        tree_log.heading(col, text=col); tree_log.column(col, width=width)
    tree_log.pack(fill="both", expand=True)
    scrollbar_y.config(command=tree_log.yview)
    scrollbar_x.config(command=tree_log.xview)

    def populate_user_listbox():
        try:
            df_log = load_logs()
            users = sorted(df_log["User"].dropna().unique().tolist())
        except Exception:
            users = []
        user_listbox.delete(0, tk.END)
        user_listbox.insert(tk.END, "(All Users)")
        for u in users:
            user_listbox.insert(tk.END, u)
        user_listbox.selection_set(0)

    def get_selected_user():
        sel = user_listbox.curselection()
        if not sel: return None
        val = user_listbox.get(sel[0])
        return None if val == "(All Users)" else val

    def load_log_data():
        tree_log.delete(*tree_log.get_children())
        df_log = load_logs()
        action_f = filter_action_var.get().strip()
        user_f = get_selected_user()
        if user_f:   df_log = df_log[df_log["User"] == user_f]
        if action_f: df_log = df_log[df_log["Action"] == action_f]
        df_log = df_log.iloc[::-1].reset_index(drop=True)
        for _, row in df_log.iterrows():
            tree_log.insert("", "end", values=tuple(
                row.get(c, "") for c in ["Timestamp", "User", "Action", "Details"]))
        count_label.config(text=f"{len(df_log)} record(s)")

    def reset_filters():
        filter_action_var.set("")
        user_listbox.selection_clear(0, tk.END)
        user_listbox.selection_set(0)
        load_log_data()

    user_listbox.bind("<<ListboxSelect>>", lambda e: load_log_data())
    populate_user_listbox()
    load_log_data()

# ========== SWITCH USER ==========

def switch_user():
    global current_user, session_start

    switch_win = tk.Toplevel(root)
    switch_win.title("Change User")
    switch_win.geometry("300x200")
    switch_win.resizable(False, False)
    switch_win.transient(root)

    tk.Label(switch_win, text="Enter new user name:", font=("Arial", 10)).pack(pady=(20, 5))
    name_var = tk.StringVar()
    name_entry = tk.Entry(switch_win, textvariable=name_var, width=25, font=("Arial", 10))
    name_entry.pack(pady=5)
    error_label = tk.Label(switch_win, text="", fg="red", font=("Arial", 8))
    error_label.pack()

    def validate_name(name):
        if not name:
            return "Please enter a name to continue"
        if not re.match(r'^[A-Za-z][A-Za-z ]*$', name):
            return "Name must contain letters and spaces only"
        if '  ' in name:
            return "Name cannot contain consecutive spaces"
        return None

    def on_key_release(event):
        val = name_var.get()
        cleaned = re.sub(r'[^A-Za-z ]', '', val)
        if cleaned != val:
            name_var.set(cleaned)
            name_entry.icursor(len(cleaned))
            error_label.config(text="Numbers and special characters are not allowed")
        else:
            error_label.config(text="")

    def apply_switch():
        global current_user, session_start
        new_name = name_var.get().strip()
        error = validate_name(new_name)
        if error:
            error_label.config(text=error); return
        save_log("LOGOUT", f"Session ended for '{current_user}'")
        current_user = new_name
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_label.config(text=f"👤  {current_user}")
        session_label.config(text=f"Session started: {session_start}")
        save_log("LOGIN", f"Session started by '{current_user}'")
        switch_win.destroy()
        messagebox.showinfo("User Changed", f"Successfully switched to: {current_user}")

    name_entry.bind("<KeyRelease>", on_key_release)
    tk.Button(switch_win, text="Switch", command=apply_switch, width=15).pack(pady=10)
    switch_win.bind("<Return>", lambda e: apply_switch())
    switch_win.update_idletasks()
    switch_win.grab_set()
    switch_win.focus_force()
    name_entry.focus_set()
    switch_win.wait_window()

# ========== LOGIN ==========

def show_login():
    global current_user, session_start
    login_win = tk.Tk()
    login_win.title("Warehouse System — Login")
    login_win.geometry("320x180")
    login_win.resizable(False, False)
    login_win.eval('tk::PlaceWindow . center')

    tk.Label(login_win, text="Warehouse System", font=("Arial", 13, "bold")).pack(pady=(20, 5))
    tk.Label(login_win, text="Who is using the system?", font=("Arial", 9)).pack()

    name_var = tk.StringVar()
    name_entry = tk.Entry(login_win, textvariable=name_var, width=25, font=("Arial", 10))
    name_entry.pack(pady=10)
    name_entry.focus()

    error_label = tk.Label(login_win, text="", fg="red", font=("Arial", 8))
    error_label.pack()

    def attempt_login():
        global current_user, session_start
        name = name_var.get().strip()
        if not name:
            error_label.config(text="Please enter your name to continue"); return
        if not re.match(r'^[A-Za-z][A-Za-z ]*$', name):
            error_label.config(text="Name must contain letters and spaces only"); return
        if '  ' in name:
            error_label.config(text="Name cannot contain consecutive spaces"); return
        current_user = name
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        login_win.quit()

    tk.Button(login_win, text="LOGIN", command=attempt_login, width=15).pack(pady=5)
    name_entry.bind("<Return>", lambda e: attempt_login())
    login_win.protocol("WM_DELETE_WINDOW", lambda: None)
    login_win.mainloop()
    login_win.destroy()
    initialize_log()
    save_log("LOGIN", f"Session started by '{current_user}'")

# ========== UI SETUP ==========

show_login()

root = tk.Tk()
root.title("Warehouse Management System")
root.geometry("1280x780")
root.eval('tk::PlaceWindow . center')

# ── User bar ──────────────────────────────────────────────
user_bar = tk.Frame(root, bg="#2c3e50", height=28)
user_bar.pack(fill="x")

clock_label = tk.Label(user_bar, text="", bg="#2c3e50", fg="#95a5a6", font=("Arial", 8))
clock_label.pack(side="right", padx=10, pady=4)

tk.Button(user_bar, text="Change User", command=switch_user,
          bg="#34495e", fg="white", bd=0, padx=10).pack(side="right", padx=10, pady=2)

user_label = tk.Label(user_bar, text=f"👤  {current_user}", bg="#2c3e50", fg="white", font=("Arial", 9, "bold"))
user_label.pack(side="left", padx=10, pady=4)

session_label = tk.Label(user_bar, text=f"Session started: {session_start}", bg="#2c3e50", fg="#95a5a6", font=("Arial", 8))
session_label.pack(side="left", padx=5, pady=4)

def update_clock():
    clock_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.after(1000, update_clock)
update_clock()

# ── Notebook (tabs) ───────────────────────────────────────
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=6, pady=6)

tab1 = tk.Frame(notebook)
tab2 = tk.Frame(notebook)
notebook.add(tab1, text="  Warehouse 1 — Laptops")
notebook.add(tab2, text="  Warehouse 2 — Computer Peripherals / Equipment")  

# ══════════════════════════════════════════════════════════
#  WAREHOUSE 1 TAB
# ══════════════════════════════════════════════════════════

w1_main = tk.Frame(tab1)
w1_main.pack(fill="both", expand=True, padx=8, pady=8)

w1_row1 = tk.Frame(w1_main)
w1_row1.pack(fill="x")

# Item Management
input_frame = tk.LabelFrame(w1_row1, text="Item Management", padx=10, pady=5)
input_frame.pack(side="left", fill="both", padx=5)

tk.Label(input_frame, text="Hostname").grid(row=0, column=0, sticky="w")
hostname_entry = tk.Entry(input_frame, width=22); hostname_entry.grid(row=0, column=1, pady=3)
tk.Label(input_frame, text="Serial Number").grid(row=1, column=0, sticky="w")
serial_entry = tk.Entry(input_frame, width=22); serial_entry.grid(row=1, column=1, pady=3)
tk.Label(input_frame, text="Checked By").grid(row=2, column=0, sticky="w")
checked_by_entry = tk.Entry(input_frame, width=22); checked_by_entry.grid(row=2, column=1, pady=3)

tk.Label(input_frame, text="Shelf").grid(row=3, column=0, sticky="w")
shelf_var = tk.StringVar()
shelf_dropdown = ttk.Combobox(input_frame, textvariable=shelf_var, width=19)
shelf_dropdown.grid(row=3, column=1, pady=3)

tk.Label(input_frame, text="Remarks").grid(row=4, column=0, sticky="w")
remarks_var = tk.StringVar()
ttk.Combobox(input_frame, textvariable=remarks_var, values=["No Issue", "Minimal", "Defective"], width=19).grid(row=4, column=1, pady=3)

crud_frame = tk.Frame(input_frame)
crud_frame.grid(row=5, column=0, columnspan=2, pady=5)
tk.Button(crud_frame, text="PUT",    command=put_item,    width=8).grid(row=0, column=0, padx=3)
tk.Button(crud_frame, text="UPDATE", command=update_item, width=8).grid(row=0, column=1, padx=3)
tk.Button(crud_frame, text="↻",      command=reset_ui,    width=3).grid(row=0, column=2, padx=3)

tk.Label(input_frame, text="Staged Items (Click to Edit)", fg="green", font=("Arial", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w")
staged_listbox = tk.Listbox(input_frame, height=4, width=32)
staged_listbox.grid(row=7, column=0, columnspan=2, sticky="we", pady=3)
staged_listbox.bind("<<ListboxSelect>>", select_staged_item)

staging_btn_frame = tk.Frame(input_frame)
staging_btn_frame.grid(row=8, column=0, columnspan=2, pady=3)
tk.Button(staging_btn_frame, text="CLEAR ITEMS",   command=remove_from_staging, width=13).pack(side="left", padx=2)
tk.Button(staging_btn_frame, text="PUT WAREHOUSE", command=put_warehouse,       width=13).pack(side="left", padx=2)

# Shelf Controls W1
shelf_mid_frame = tk.Frame(w1_row1)
shelf_mid_frame.pack(side="left", fill="both", expand=True, padx=5)
shelf_control_frame = tk.LabelFrame(shelf_mid_frame, text="Shelf Control & Management", padx=10, pady=5)
shelf_control_frame.pack(fill="x")

status_control_frame = tk.LabelFrame(shelf_control_frame, text="Status Control", padx=8, pady=5)
status_control_frame.pack(fill="x", pady=(0, 5))
shelf_control_var = tk.StringVar()
shelf_control_dropdown = ttk.Combobox(status_control_frame, textvariable=shelf_control_var, width=22, state="readonly")
shelf_control_dropdown.pack(side="left", padx=5)
tk.Button(status_control_frame, text="SET FULL",      command=lambda: set_shelf_status("FULL"),      width=10).pack(side="left", padx=3)
tk.Button(status_control_frame, text="SET AVAILABLE", command=lambda: set_shelf_status("AVAILABLE"), width=12).pack(side="left", padx=3)
tk.Button(status_control_frame, text="↻",             command=reset_shelf_control,                   width=3).pack(side="left", padx=3)

add_remove_frame = tk.LabelFrame(shelf_control_frame, text="Add / Remove", padx=8, pady=5)
add_remove_frame.pack(fill="x")
remove_shelf_var = tk.StringVar()
remove_shelf_dropdown = ttk.Combobox(add_remove_frame, textvariable=remove_shelf_var, width=22)
remove_shelf_dropdown.pack(side="left", padx=5)
tk.Button(add_remove_frame, text="ADD",    command=add_shelf,           ).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="REMOVE", command=remove_shelf,         ).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="↻",      command=reset_shelf_addition, width=3).pack(side="left", padx=3)

# View W1
view_frame = tk.LabelFrame(w1_row1, text="View", padx=10, pady=5)
view_frame.pack(side="right", fill="both", padx=5)
for text, cmd in [
    ("Show Warehouse",   show_warehouse),
    ("Shelf Status",     show_available),
    ("Pull History",     show_pullouts),
    ("Stored QR Codes",  show_qr_codes),
    ("QR Label Manager", open_label_manager),
    ("Activity Log",     open_activity_log),
]:
    tk.Button(view_frame, text=text, command=cmd, width=15).pack(anchor="w", pady=3)

# Search & Filter W1
w1_pullout_frame = tk.LabelFrame(w1_main, text="Warehouse", padx=10, pady=8)
w1_pullout_frame.pack(fill="x", pady=5)

w1_search_filter = tk.LabelFrame(w1_pullout_frame, text="Search & Filter", padx=8, pady=5)
w1_search_filter.pack(fill="x", pady=(0, 5))

tk.Label(w1_search_filter, text="Search:").pack(side="left", padx=(5, 2))
search_entry = tk.Entry(w1_search_filter, width=20); search_entry.pack(side="left", padx=(0, 2))
tk.Button(w1_search_filter, text="🔍", command=search_item, width=2).pack(side="left", padx=(0, 10))

tk.Label(w1_search_filter, text="Shelf:").pack(side="left", padx=(5, 2))
pull_shelf_var = tk.StringVar()
pull_shelf_dropdown = ttk.Combobox(w1_search_filter, textvariable=pull_shelf_var, width=16, state="readonly")
pull_shelf_dropdown.pack(side="left", padx=(0, 10))

tk.Label(w1_search_filter, text="Remarks:").pack(side="left", padx=(5, 2))
pull_remarks_var = tk.StringVar()
ttk.Combobox(w1_search_filter, textvariable=pull_remarks_var, values=["No Issue", "Minimal", "Defective"], width=14, state="readonly").pack(side="left", padx=(0, 5))
tk.Button(w1_search_filter, text="FILTER", command=filter_pullouts,   width=8).pack(side="left", padx=3)
tk.Button(w1_search_filter, text="↻",      command=clear_pull_filters, width=3).pack(side="left", padx=3)

tk.Label(w1_search_filter, text="|  Pull Reason:").pack(side="left", padx=(10, 2))
pull_reason_filter_entry = tk.Entry(w1_search_filter, width=15)
pull_reason_filter_entry.pack(side="left", padx=(0, 5))
tk.Button(w1_search_filter, text="FILTER PULLS", command=filter_pull_history, width=12).pack(side="left", padx=3)

w1_pull_action = tk.LabelFrame(w1_pullout_frame, text="Pull Out", padx=8, pady=5)
w1_pull_action.pack(fill="x")
tk.Label(w1_pull_action, text="Selected Item:").pack(side="left", padx=(5, 2))
pull_item_entry = tk.Entry(w1_pull_action, width=20); pull_item_entry.pack(side="left", padx=(0, 10))
tk.Label(w1_pull_action, text="Pull Reason:").pack(side="left", padx=(5, 2))
pull_reason_entry = tk.Entry(w1_pull_action, width=30); pull_reason_entry.pack(side="left", padx=(0, 10))
tk.Button(w1_pull_action, text="WAREHOUSE PULL", command=pull_item,     width=16).pack(side="left", padx=3)
tk.Button(w1_pull_action, text="↻",              command=reset_pull_out, width=3).pack(side="left", padx=3)

# Status bar W1
w1_status_bar = tk.Frame(w1_main)
w1_status_bar.pack(fill="x")
w1_full_label   = tk.Label(w1_status_bar, text="FULL Shelves: None", fg="red");  w1_full_label.pack(side="left", padx=10)
w1_search_label = tk.Label(w1_status_bar, text="", fg="blue");                   w1_search_label.pack(side="left", padx=10)
w1_status_label = tk.Label(w1_status_bar, text="", fg="green");                  w1_status_label.pack(side="left", padx=10)

# Tables W1
w1_table_frame = tk.Frame(w1_main)
w1_table_frame.pack(fill="both", expand=True, pady=5)

tree_warehouse = ttk.Treeview(w1_table_frame, columns=("C1","C2","C3","C4","C5","C6","C7"), show='headings')
for col, text, width in zip(("C1","C2","C3","C4","C5","C6","C7"),
    ("QR","Hostname","Serial Number","Checked By","Shelf","Remarks","Date"),
    (200,150,130,120,130,100,150)):
    tree_warehouse.heading(col, text=text); tree_warehouse.column(col, width=width)
tree_warehouse.bind("<<TreeviewSelect>>", select_item)
tree_warehouse.bind("<Double-1>", unstage_from_warehouse)

tree_available = ttk.Treeview(w1_table_frame, columns=("C1","C2","C3"), show='headings')
for col, text, width in zip(("C1","C2","C3"), ("Shelf","Status","Date_Full"), (250,150,200)):
    tree_available.heading(col, text=text); tree_available.column(col, width=width)

tree_pullouts = ttk.Treeview(w1_table_frame, columns=("C1","C2","C3","C4","C5"), show='headings')
for col, text, width in zip(("C1","C2","C3","C4","C5"),
    ("Hostname","Shelf","Remarks","Pull Reason","Date"), (180,150,100,250,160)):
    tree_pullouts.heading(col, text=text); tree_pullouts.column(col, width=width)
tree_pullouts.bind("<Double-1>", undo_pull)

tree_qr = ttk.Treeview(w1_table_frame, columns=("C1","C2","C3"), show='headings')
for col, text, width in zip(("C1","C2","C3"),
    ("Hostname","QR UUID String","File Status (PNG)"), (200,400,150)):
    tree_qr.heading(col, text=text); tree_qr.column(col, width=width)

# ══════════════════════════════════════════════════════════
#  WAREHOUSE 2 TAB
# ══════════════════════════════════════════════════════════

w2_main = tk.Frame(tab2)
w2_main.pack(fill="both", expand=True, padx=8, pady=8)

w2_row1 = tk.Frame(w2_main)
w2_row1.pack(fill="x")

# Equipment selection + staging panel
w2_input_frame = tk.LabelFrame(w2_row1, text="Set Staging", padx=10, pady=5)
w2_input_frame.pack(side="left", fill="both", padx=5)

tk.Label(w2_input_frame, text="Select Equipment:", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

w2_equip_vars = {}
for i, eq in enumerate(EQUIPMENT_TYPES):
    var = tk.BooleanVar()
    w2_equip_vars[eq] = var
    tk.Checkbutton(w2_input_frame, text=eq, variable=var, width=10, anchor="w").grid(
        row=1 + i // 2, column=i % 2, sticky="w", padx=4)

tk.Button(w2_input_frame, text="BUILD SET", command=w2_build_set,
          bg="#2980b9", fg="white", width=28).grid(row=3, column=0, columnspan=2, pady=(8, 4))

tk.Label(w2_input_frame, text="Staged Sets", fg="green", font=("Arial", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky="w")
w2_staged_listbox = tk.Listbox(w2_input_frame, height=5, width=34)
w2_staged_listbox.grid(row=5, column=0, columnspan=2, sticky="we", pady=3)

w2_stage_btns = tk.Frame(w2_input_frame)
w2_stage_btns.grid(row=6, column=0, columnspan=2, pady=3)
tk.Button(w2_stage_btns, text="CLEAR SETS",    command=w2_remove_staged_set, width=13).pack(side="left", padx=2)
tk.Button(w2_stage_btns, text="PUT WAREHOUSE", command=w2_put_warehouse,     width=13).pack(side="left", padx=2)

# Shelf Controls W2
w2_shelf_mid = tk.Frame(w2_row1)
w2_shelf_mid.pack(side="left", fill="both", expand=True, padx=5)
w2_shelf_ctrl_frame = tk.LabelFrame(w2_shelf_mid, text="Shelf Control & Management", padx=10, pady=5)
w2_shelf_ctrl_frame.pack(fill="x")

w2_status_ctrl = tk.LabelFrame(w2_shelf_ctrl_frame, text="Status Control", padx=8, pady=5)
w2_status_ctrl.pack(fill="x", pady=(0, 5))
w2_shelf_control_var = tk.StringVar()
w2_shelf_control_dropdown = ttk.Combobox(w2_status_ctrl, textvariable=w2_shelf_control_var, width=22, state="readonly")
w2_shelf_control_dropdown.pack(side="left", padx=5)
tk.Button(w2_status_ctrl, text="SET FULL",      command=lambda: w2_set_shelf_status("FULL"),      width=10).pack(side="left", padx=3)
tk.Button(w2_status_ctrl, text="SET AVAILABLE", command=lambda: w2_set_shelf_status("AVAILABLE"), width=12).pack(side="left", padx=3)
tk.Button(w2_status_ctrl, text="↻",             command=w2_reset_shelf_control,                   width=3).pack(side="left", padx=3)

w2_add_remove = tk.LabelFrame(w2_shelf_ctrl_frame, text="Add / Remove", padx=8, pady=5)
w2_add_remove.pack(fill="x")
w2_remove_shelf_var = tk.StringVar()
w2_remove_shelf_dropdown = ttk.Combobox(w2_add_remove, textvariable=w2_remove_shelf_var, width=22)
w2_remove_shelf_dropdown.pack(side="left", padx=5)
tk.Button(w2_add_remove, text="ADD",    command=w2_add_shelf,           ).pack(side="left", padx=3)
tk.Button(w2_add_remove, text="REMOVE", command=w2_remove_shelf,         ).pack(side="left", padx=3)
tk.Button(w2_add_remove, text="↻",      command=w2_reset_shelf_addition, width=3).pack(side="left", padx=3)

# View W2
w2_view_frame = tk.LabelFrame(w2_row1, text="View", padx=10, pady=5)
w2_view_frame.pack(side="right", fill="both", padx=5)
for text, cmd in [
    ("Show Warehouse",   w2_show_warehouse),
    ("Shelf Status",     w2_show_available),
    ("Pull History",     w2_show_pullouts),
    ("Stored QR Codes",  w2_show_qr_codes),
    ("QR Label Manager", open_label_manager),
    ("Activity Log",     open_activity_log),
]:
    tk.Button(w2_view_frame, text=text, command=cmd, width=15).pack(anchor="w", pady=3)

# Search & Filter W2
w2_pullout_frame = tk.LabelFrame(w2_main, text="Warehouse 2", padx=10, pady=8)
w2_pullout_frame.pack(fill="x", pady=5)

w2_search_filter = tk.LabelFrame(w2_pullout_frame, text="Search & Filter", padx=8, pady=5)
w2_search_filter.pack(fill="x", pady=(0, 5))

tk.Label(w2_search_filter, text="Search:").pack(side="left", padx=(5, 2))
w2_search_entry = tk.Entry(w2_search_filter, width=18); w2_search_entry.pack(side="left", padx=(0, 2))
tk.Button(w2_search_filter, text="🔍", command=w2_search_item, width=2).pack(side="left", padx=(0, 10))

tk.Label(w2_search_filter, text="Shelf:").pack(side="left", padx=(5, 2))
w2_pull_shelf_var = tk.StringVar()
ttk.Combobox(w2_search_filter, textvariable=w2_pull_shelf_var, width=16, state="readonly").pack(side="left", padx=(0, 10))

tk.Label(w2_search_filter, text="Type:").pack(side="left", padx=(5, 2))
w2_type_filter_var = tk.StringVar()
ttk.Combobox(w2_search_filter, textvariable=w2_type_filter_var,
             values=[""] + EQUIPMENT_TYPES, width=12, state="readonly").pack(side="left", padx=(0, 5))
tk.Button(w2_search_filter, text="FILTER", command=w2_filter_items,  width=8).pack(side="left", padx=3)
tk.Button(w2_search_filter, text="↻",      command=w2_clear_filters,  width=3).pack(side="left", padx=3)

w2_pull_action = tk.LabelFrame(w2_pullout_frame, text="Pull Out", padx=8, pady=5)
w2_pull_action.pack(fill="x")
tk.Label(w2_pull_action, text="Selected Item:").pack(side="left", padx=(5, 2))
w2_pull_item_entry = tk.Entry(w2_pull_action, width=24); w2_pull_item_entry.pack(side="left", padx=(0, 10))
tk.Label(w2_pull_action, text="Pull Reason:").pack(side="left", padx=(5, 2))
w2_pull_reason_entry = tk.Entry(w2_pull_action, width=30); w2_pull_reason_entry.pack(side="left", padx=(0, 10))
tk.Button(w2_pull_action, text="WAREHOUSE PULL", command=w2_pull_item,     width=16).pack(side="left", padx=3)
tk.Button(w2_pull_action, text="↻",              command=w2_reset_pull_out, width=3).pack(side="left", padx=3)

# Status bar W2
w2_status_bar = tk.Frame(w2_main)
w2_status_bar.pack(fill="x")
w2_full_label   = tk.Label(w2_status_bar, text="FULL Shelves: None", fg="red");  w2_full_label.pack(side="left", padx=10)
w2_search_label = tk.Label(w2_status_bar, text="", fg="blue");                   w2_search_label.pack(side="left", padx=10)
w2_status_label = tk.Label(w2_status_bar, text="", fg="green");                  w2_status_label.pack(side="left", padx=10)

# Tables W2
w2_table_frame = tk.Frame(w2_main)
w2_table_frame.pack(fill="both", expand=True, pady=5)

tree_w2_warehouse = ttk.Treeview(w2_table_frame,
    columns=("C1","C2","C3","C4","C5","C6","C7","C8","C9"), show='headings')
for col, text, width in zip(
    ("C1","C2","C3","C4","C5","C6","C7","C8","C9"),
    ("QR","Set ID","Equipment Type","Brand/Model","Serial Number","Checked By","Shelf","Remarks","Date"),
    (180,90,120,140,120,110,120,90,140)):
    tree_w2_warehouse.heading(col, text=text); tree_w2_warehouse.column(col, width=width)
tree_w2_warehouse.bind("<<TreeviewSelect>>", w2_select_item)

tree_w2_available = ttk.Treeview(w2_table_frame, columns=("C1","C2","C3"), show='headings')
for col, text, width in zip(("C1","C2","C3"), ("Shelf","Status","Date_Full"), (250,150,200)):
    tree_w2_available.heading(col, text=text); tree_w2_available.column(col, width=width)

tree_w2_pullouts = ttk.Treeview(w2_table_frame,
    columns=("C1","C2","C3","C4","C5","C6","C7"), show='headings')
for col, text, width in zip(
    ("C1","C2","C3","C4","C5","C6","C7"),
    ("Set ID","Equipment Type","Brand/Model","Shelf","Remarks","Pull Reason","Date"),
    (90,120,140,120,90,200,140)):
    tree_w2_pullouts.heading(col, text=text); tree_w2_pullouts.column(col, width=width)
tree_w2_pullouts.bind("<Double-1>", w2_undo_pull)

tree_w2_qr = ttk.Treeview(w2_table_frame, columns=("C1","C2","C3","C4"), show='headings')
for col, text, width in zip(("C1","C2","C3","C4"),
    ("Set ID","Equipment Type","QR UUID String","File Status (PNG)"), (100,120,380,130)):
    tree_w2_qr.heading(col, text=text); tree_w2_qr.column(col, width=width)

# ── Init ──────────────────────────────────────────────────
initialize_file()
update_all_shelf_dropdowns()
update_staged_display()
update_w2_staged_display()
show_warehouse()
w2_show_warehouse()

root.mainloop()