"""
Warehouse Management System
Copyright (c) 2026 Mark Benjamin H. Acob - All Rights Reserved

Proprietary Software - Internal Use Only
This software is proprietary and confidential.
Unauthorized copying, modification, or distribution is prohibited.

A comprehensive warehouse management system with QR code generation,
item staging, and shelf management capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import uuid
import qrcode
from datetime import datetime

FILE = "warehouse.xlsx"

# Predefined shelves
SHELVES = [
    "Area A",
    "Area B",
    "Area C",
    "Rack 1 - Bay 1",
    "Rack 1 - Bay 2",
    "Rack 1 - Bay 3",
    "Rack 2 - Bay 1",
    "Rack 2 - Bay 2",
    "Rack 2 - Bay 3",
]

# ========== INITIALIZATION ==========

def initialize_file():
    if not os.path.exists(FILE):
        df_items = pd.DataFrame(columns=["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"])
        df_shelves = pd.DataFrame({
            "Shelf": SHELVES,
            "Status": ["AVAILABLE"] * len(SHELVES),
            "Date_Full": [None] * len(SHELVES)
        })
        df_pullouts = pd.DataFrame(columns=["Hostname", "Shelf", "Remarks", "Pull Reason", "Date"])
        with pd.ExcelWriter(FILE, engine='openpyxl') as writer:
            df_items.to_excel(writer, sheet_name="items", index=False)
            df_shelves.to_excel(writer, sheet_name="shelves", index=False)
            df_pullouts.to_excel(writer, sheet_name="pullouts", index=False)
    else:
        with pd.ExcelFile(FILE) as xls:
            sheets = xls.sheet_names
        df_items = pd.DataFrame(columns=["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"])
        df_shelves = pd.DataFrame({
            "Shelf": SHELVES,
            "Status": ["AVAILABLE"] * len(SHELVES),
            "Date_Full": [None] * len(SHELVES)
        })
        df_pullouts = pd.DataFrame(columns=["Hostname", "Shelf", "Remarks", "Pull Reason", "Date"])
        with pd.ExcelWriter(FILE, engine='openpyxl', mode='a') as writer:
            if "items" not in sheets:
                df_items.to_excel(writer, sheet_name="items", index=False)
            if "shelves" not in sheets:
                df_shelves.to_excel(writer, sheet_name="shelves", index=False)
            if "pullouts" not in sheets:
                df_pullouts.to_excel(writer, sheet_name="pullouts", index=False)

# ========== STAGING LIST ==========
staged_items = []  # List to hold items before committing to warehouse
selected_staged_index = None  # Track selected staged item

# ========== LOAD / SAVE FUNCTIONS ==========

def load_items():
    try:
        return pd.read_excel(FILE, sheet_name="items")
    except:
        initialize_file()
        return pd.read_excel(FILE, sheet_name="items")

def load_shelves():
    try:
        return pd.read_excel(FILE, sheet_name="shelves")
    except:
        initialize_file()
        return pd.read_excel(FILE, sheet_name="shelves")

def load_pullouts():
    try:
        return pd.read_excel(FILE, sheet_name="pullouts")
    except:
        initialize_file()
        return pd.read_excel(FILE, sheet_name="pullouts")

def show_pullouts():
    tree_warehouse.pack_forget()
    tree_available.pack_forget()
    tree_pullouts.delete(*tree_pullouts.get_children())
    tree_pullouts.pack(fill="both", expand=True)

    df_pullouts = load_pullouts()

    for _, row in df_pullouts.iterrows():
        tree_pullouts.insert("", "end", values=(
            row.get("Hostname", ""),
            row.get("Shelf", ""),
            row.get("Remarks", ""),
            row.get("Pull Reason", ""),
            row.get("Date", "")
        ))

def filter_pullouts():
    shelf_filter = pull_shelf_var.get()
    remarks_filter = pull_remarks_var.get()

    if not shelf_filter and not remarks_filter:
        messagebox.showinfo("Info", "Please select at least one filter")
        return

    df_items = load_items()

    if shelf_filter:
        df_items = df_items[df_items["Shelf"] == shelf_filter]
    if remarks_filter:
        df_items = df_items[df_items["Remarks"] == remarks_filter]

    tree_available.pack_forget()
    tree_pullouts.pack_forget()
    tree_warehouse.delete(*tree_warehouse.get_children())
    tree_warehouse.pack(fill="both", expand=True)

    for _, row in df_items.iterrows():
        tree_warehouse.insert("", "end", values=(
            row.get("QR", ""),
            row.get("Hostname", ""),
            row.get("Serial Number", ""),
            row.get("Checked By", ""),
            row.get("Shelf", ""),
            row.get("Remarks", ""),
            row.get("Date", "")
        ))

    search_label.config(text=f"Filtered: {len(df_items)} item(s) "
                             f"{'| Shelf: ' + shelf_filter if shelf_filter else ''} "
                             f"{'| Remarks: ' + remarks_filter if remarks_filter else ''}")

def clear_pull_filters():
    pull_shelf_var.set("")
    pull_remarks_var.set("")
    search_entry.delete(0, tk.END)
    search_label.config(text="")
    show_warehouse()

def save_all(df_items, df_shelves, df_pullouts=None):
    if df_pullouts is None:
        df_pullouts = load_pullouts()
    with pd.ExcelWriter(FILE, engine='openpyxl') as writer:
        df_items.to_excel(writer, sheet_name="items", index=False)
        df_shelves.to_excel(writer, sheet_name="shelves", index=False)
        df_pullouts.to_excel(writer, sheet_name="pullouts", index=False)

def update_full_shelves_display():
    df_shelves = load_shelves()
    full_shelves = df_shelves[df_shelves["Status"] == "FULL"]["Shelf"].tolist()

    if full_shelves:
        text = "FULL Shelves:\n" + "\n".join(full_shelves)
    else:
        text = "FULL Shelves: None"

    full_label.config(text=text)

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
    selected_staged_index = index  # ← STORE selection

    item = staged_items[index]

    hostname_entry.delete(0, tk.END)
    hostname_entry.insert(0, item["Hostname"])
    serial_entry.delete(0, tk.END)
    serial_entry.insert(0, item.get("Serial Number", ""))
    checked_by_entry.delete(0, tk.END)
    checked_by_entry.insert(0, item.get("Checked By", ""))
    shelf_var.set(item["Shelf"])
    remarks_var.set(item["Remarks"])

# ========== CORE FUNCTIONS ==========
def remove_from_staging():
    global selected_staged_index

    # If a specific staged item is selected, remove just that one
    if selected_staged_index is not None:
        index = selected_staged_index

        if index >= len(staged_items):
            messagebox.showerror("Error", "Invalid staged selection")
            selected_staged_index = None
            return

        removed = staged_items.pop(index)
        messagebox.showinfo("Removed", f"'{removed['Hostname']}' removed from staging")

        selected_staged_index = None

        # Clear input fields
        hostname_entry.delete(0, tk.END)
        serial_entry.delete(0, tk.END)
        checked_by_entry.delete(0, tk.END)
        shelf_var.set("")
        remarks_var.set("")

        update_staged_display()
        return

    # If nothing is selected, ask to clear all staged items
    if not staged_items:
        messagebox.showinfo("Info", "No staged items to clear")
        return

    confirm = messagebox.askyesno("Confirm", f"Clear all {len(staged_items)} staged item(s)?")
    if not confirm:
        return

    staged_items.clear()
    selected_staged_index = None

    hostname_entry.delete(0, tk.END)
    shelf_var.set("")
    remarks_var.set("")

    messagebox.showinfo("Cleared", "All staged items cleared")
    update_staged_display()

def put_item():
    hostname = hostname_entry.get().strip()
    serial = serial_entry.get().strip()
    checked_by = checked_by_entry.get().strip()
    shelf = shelf_var.get()
    remarks = remarks_var.get()

    if not hostname or not shelf:
        messagebox.showerror("Error", "Fill all fields")
        return

    df_items = load_items()
    df_shelves = load_shelves()

    # Check if hostname already exists in warehouse
    if hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", "Hostname already exists in warehouse")
        return
    
    # Check if hostname already staged
    if any(item['Hostname'] == hostname for item in staged_items):
        messagebox.showerror("Error", "Hostname already staged")
        return

    # Check if shelf is FULL
    status = df_shelves[df_shelves["Shelf"] == shelf]["Status"].values
    if len(status) > 0 and status[0] == "FULL":
        messagebox.showerror("Error", "Shelf is marked FULL")
        return

    # Add to staging instead of directly saving
    new_item = {
        "Hostname": hostname,
        "Serial Number": serial,
        "Checked By": checked_by,
        "Shelf": shelf,
        "Remarks": remarks,
    }
    
    staged_items.append(new_item)
    messagebox.showinfo("Staged", f"'{hostname}' added to staging queue")
    
    # Clear input fields
    hostname_entry.delete(0, tk.END)
    serial_entry.delete(0, tk.END)
    checked_by_entry.delete(0, tk.END)
    remarks_var.set("")
    shelf_var.set("")
    
    update_staged_display()

def put_warehouse():
    if not staged_items:
        messagebox.showerror("Error", "No staged items to put")
        return
    
    confirm = messagebox.askyesno("Confirm", f"Put {len(staged_items)} item(s) to warehouse?")
    if not confirm:
        return

    try:
        df_items = load_items()
        df_shelves = load_shelves()

        # Ensure new columns exist in loaded dataframe
        for col in ["Serial Number", "Checked By"]:
            if col not in df_items.columns:
                df_items[col] = ""

        QR_FOLDER = "qr_codes"
        if not os.path.exists(QR_FOLDER):
            os.makedirs(QR_FOLDER)

        for item in staged_items:
            qr_code = str(uuid.uuid4())
            qr_img = qrcode.make(qr_code)
            safe_hostname = item['Hostname'].replace(" ", "_")
            qr_path = os.path.join(QR_FOLDER, f"{safe_hostname}.png")
            qr_img.save(qr_path)
            
            new_row = {
                "QR": qr_code,
                "Hostname": item['Hostname'],
                "Serial Number": item.get('Serial Number', ''),
                "Checked By": item.get('Checked By', ''),
                "Shelf": item['Shelf'],
                "Remarks": item['Remarks'],
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)

        save_all(df_items, df_shelves)
        
        count = len(staged_items)
        staged_items.clear()
        
        messagebox.showinfo("Success", f"{count} item(s) added to warehouse")
        
        update_staged_display()
        refresh_all()

    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save to Excel:\n{str(e)}\n\n"
                                          "Common causes:\n"
                                          "• Excel file is open → close it\n"
                                          "• Wrong folder (check working directory)")
        print("DEBUG ERROR:", e)
     
def update_item():
    global selected_staged_index

    new_hostname = hostname_entry.get().strip()

    if not new_hostname:
        messagebox.showerror("Error", "Hostname cannot be empty")
        return

    selected = tree_warehouse.selection()

    # ===== PRIORITY: STAGED ITEM UPDATE =====
    if selected_staged_index is not None:
        index = selected_staged_index

        if index >= len(staged_items):
            messagebox.showerror("Error", "Invalid staged selection")
            selected_staged_index = None
            return

        # Prevent duplicate in staging
        if any(i != index and item['Hostname'] == new_hostname for i, item in enumerate(staged_items)):
            messagebox.showerror("Error", "Hostname already exists in staging")
            return

        # Update staged item
        staged_items[index]["Hostname"] = new_hostname
        staged_items[index]["Serial Number"] = serial_entry.get().strip()
        staged_items[index]["Checked By"] = checked_by_entry.get().strip()
        staged_items[index]["Shelf"] = shelf_var.get()
        staged_items[index]["Remarks"] = remarks_var.get()

        messagebox.showinfo("Updated", "Staged item updated")

        update_staged_display()
        selected_staged_index = None
        return

    # ===== WAREHOUSE UPDATE =====
    if not selected:
        messagebox.showerror("Error", "Select item to update")
        return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])

    current_hostname = df_items.at[index, "Hostname"]

    if new_hostname != current_hostname and new_hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", "Hostname already exists and has a QR assigned")
        return

    df_items.at[index, "Hostname"] = new_hostname
    df_items.at[index, "Serial Number"] = serial_entry.get().strip()
    df_items.at[index, "Checked By"] = checked_by_entry.get().strip()
    df_items.at[index, "Shelf"] = shelf_var.get()
    df_items.at[index, "Remarks"] = remarks_var.get()

    save_all(df_items, df_shelves)

    messagebox.showinfo("Updated", "Record updated")
    refresh_all()


def delete_item():
    selected = tree_warehouse.selection()
    if not selected:
        messagebox.showerror("Error", "Select item")
        return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])

    # Reconstruct QR path from hostname
    hostname = df_items.at[index, "Hostname"]
    safe_hostname = hostname.replace(" ", "_")
    qr_path = os.path.join("qr_codes", f"{safe_hostname}.png")

    # Delete the QR image file
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except Exception as e:
            messagebox.showwarning("Warning", f"QR file not deleted: {e}")

    # Now delete from dataframe
    df_items = df_items.drop(index).reset_index(drop=True)

    save_all(df_items, df_shelves)

    messagebox.showinfo("Deleted", "Record and QR code deleted")
    refresh_all()

def add_shelf():
    new_shelf = remove_shelf_var.get().strip()

    if not new_shelf:
        messagebox.showerror("Error", "Enter shelf name")
        return

    df_shelves = load_shelves()

    # Prevent duplicate
    if new_shelf in df_shelves["Shelf"].values:
        messagebox.showerror("Error", "Shelf already exists")
        return

    # Add shelf
    new_row = {
        "Shelf": new_shelf,
        "Status": "AVAILABLE"
    }

    df_shelves = pd.concat([df_shelves, pd.DataFrame([new_row])], ignore_index=True)
    
    # Sort shelves alphabetically
    df_shelves = df_shelves.sort_values("Shelf", ignore_index=True)

    df_items = load_items()
    save_all(df_items, df_shelves)

    messagebox.showinfo("Success", f"Shelf '{new_shelf}' added")

    remove_shelf_var.set("")
    update_shelf_dropdown()

def set_shelf_status(new_status):
    shelf = shelf_control_var.get()

    if not shelf:
        messagebox.showerror("Error", "Select a shelf from Shelf Control")
        return

    df_items = load_items()
    df_shelves = load_shelves()

    idx = df_shelves[df_shelves["Shelf"] == shelf].index

    if len(idx) == 0:
        return

    df_shelves.at[idx[0], "Status"] = new_status
    
    # Add date when marking as FULL
    if new_status == "FULL":
        df_shelves.at[idx[0], "Date_Full"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        df_shelves.at[idx[0], "Date_Full"] = None

    save_all(df_items, df_shelves)

    status_label.config(text=f"{shelf} → {new_status}")
    refresh_all()

def reset_ui():
    # Clear input fields
    hostname_entry.delete(0, tk.END)
    serial_entry.delete(0, tk.END)
    checked_by_entry.delete(0, tk.END)
    shelf_var.set("")
    remarks_var.set("")

    # Clear Treeview selection
    for selected_item in tree_warehouse.selection():
        tree_warehouse.selection_remove(selected_item)

    # Clear status labels
    status_label.config(text="")
    search_label.config(text="")

    # Refresh Treeview to show all items
    show_warehouse()

def reset_shelf_control():
    shelf_control_var.set("")
    status_label.config(text="")

def reset_shelf_addition():
    remove_shelf_var.set("")
    status_label.config(text="")

def reset_pull_out():
    pull_item_entry.delete(0, tk.END)
    pull_reason_entry.delete(0, tk.END)
    search_label.config(text="")
    show_warehouse()

    # Clear Treeview selection
    for selected_item in tree_warehouse.selection():
        tree_warehouse.selection_remove(selected_item)

    # Clear status labels
    status_label.config(text="")
    search_label.config(text="")

    # Refresh Treeview to show all items
    show_warehouse()


# ========== DISPLAY FUNCTIONS ==========

def show_warehouse():
    update_full_shelves_display()
    tree_warehouse.delete(*tree_warehouse.get_children())
    tree_available.pack_forget()
    tree_pullouts.pack_forget()
    tree_warehouse.pack(fill="both", expand=True)
    
    df_items = load_items()
    
    if "Date" not in df_items.columns:
        df_items["Date"] = ""
    
    for _, row in df_items.iterrows():
        tree_warehouse.insert("", "end", values=(
            row.get("QR", ""),
            row.get("Hostname", ""),
            row.get("Serial Number", ""),
            row.get("Checked By", ""),
            row.get("Shelf", ""),
            row.get("Remarks", ""),
            row.get("Date", "")
        ))

def show_available():
    tree_warehouse.pack_forget()
    tree_pullouts.pack_forget()          # ← add this line
    tree_available.delete(*tree_available.get_children())
    tree_available.pack(fill="both", expand=True)
    
    df_shelves = load_shelves()
    available = df_shelves.sort_values("Shelf")
    
    for _, row in available.iterrows():
        shelf_name = row["Shelf"]
        status = row["Status"]
        date_full = row.get("Date_Full", "")
        
        tree_available.insert("", "end", values=(shelf_name, status, date_full if pd.notna(date_full) else ""))

def refresh_all():
    show_warehouse()
    update_shelf_dropdown()

def update_shelf_dropdown():
    df_shelves = load_shelves()
    shelf_list = sorted(df_shelves["Shelf"].tolist())
    shelf_dropdown["values"] = shelf_list
    shelf_control_dropdown["values"] = shelf_list
    remove_shelf_dropdown["values"] = shelf_list
    pull_shelf_dropdown["values"] = shelf_list

def select_item(event):
    selected = tree_warehouse.selection()
    if selected:
        values = tree_warehouse.item(selected[0], "values")
        hostname_entry.delete(0, tk.END)
        hostname_entry.insert(0, values[1])
        serial_entry.delete(0, tk.END)
        serial_entry.insert(0, values[2])
        checked_by_entry.delete(0, tk.END)
        checked_by_entry.insert(0, values[3])
        shelf_var.set(values[4])
        remarks_var.set(values[5])

        # Auto-fill pull out segment
        pull_item_entry.delete(0, tk.END)
        pull_item_entry.insert(0, values[1])

def search_item():
    keyword = search_entry.get().strip().lower()
    df_items = load_items()

    if not keyword:
        show_warehouse()
        search_label.config(text="")
        return

    filtered = df_items[df_items["Hostname"].str.lower().str.contains(keyword, na=False)]

    tree_available.pack_forget()
    tree_pullouts.pack_forget()
    tree_warehouse.pack(fill="both", expand=True)
    tree_warehouse.delete(*tree_warehouse.get_children())
    for _, row in filtered.iterrows():
        tree_warehouse.insert("", "end", values=(
            row.get("QR", ""),
            row.get("Hostname", ""),
            row.get("Serial Number", ""),
            row.get("Checked By", ""),
            row.get("Shelf", ""),
            row.get("Remarks", ""),
            row.get("Date", "")
        ))

    search_label.config(text=f"Search: {len(filtered)} result(s)")

def search_shelf():
    shelf_name = pull_shelf_var.get().strip()
    df_items = load_items()

    if not shelf_name:
        show_warehouse()
        search_label.config(text="")
        return

    filtered = df_items[df_items["Shelf"] == shelf_name]

    tree_available.pack_forget()
    tree_pullouts.pack_forget()
    tree_warehouse.pack(fill="both", expand=True)
    tree_warehouse.delete(*tree_warehouse.get_children())
    for _, row in filtered.iterrows():
        tree_warehouse.insert("", "end", values=(
            row.get("QR", ""),
            row.get("Hostname", ""),
            row.get("Serial Number", ""),
            row.get("Checked By", ""),
            row.get("Shelf", ""),
            row.get("Remarks", ""),
            row.get("Date", "")
        ))

    search_label.config(text=f"Shelf '{shelf_name}': {len(filtered)} item(s)")

def remove_shelf():
    shelf_name = remove_shelf_var.get().strip()

    if not shelf_name:
        messagebox.showerror("Error", "Select a shelf to remove")
        return

    df_items = load_items()
    df_shelves = load_shelves()

    # Check if shelf has any items
    items_in_shelf = df_items[df_items["Shelf"] == shelf_name]
    if len(items_in_shelf) > 0:
        messagebox.showerror("Error", f"Cannot remove shelf '{shelf_name}' - it has {len(items_in_shelf)} item(s)")
        return

    # Check if shelf exists
    if shelf_name not in df_shelves["Shelf"].values:
        messagebox.showerror("Error", f"Shelf '{shelf_name}' does not exist")
        return

    # Remove shelf
    df_shelves = df_shelves[df_shelves["Shelf"] != shelf_name]
    
    # Reset index and sort alphabetically
    df_shelves = df_shelves.reset_index(drop=True)
    df_shelves = df_shelves.sort_values("Shelf", ignore_index=True)
    
    save_all(df_items, df_shelves)

    messagebox.showinfo("Success", f"Shelf '{shelf_name}' removed")
    remove_shelf_var.set("")
    update_shelf_dropdown()

def pull_item():
    hostname = pull_item_entry.get().strip()
    reason = pull_reason_entry.get().strip()

    if not hostname:
        messagebox.showerror("Error", "No item selected for pull out")
        return

    if not reason:
        messagebox.showerror("Error", "Please enter a pull reason")
        return

    df_items = load_items()
    df_shelves = load_shelves()
    df_pullouts = load_pullouts()

    # Check item exists in warehouse
    match = df_items[df_items["Hostname"] == hostname]
    if match.empty:
        messagebox.showerror("Error", f"'{hostname}' not found in warehouse")
        return

    confirm = messagebox.askyesno("Confirm Pull Out", f"Pull out '{hostname}' from warehouse?\nReason: {reason}")
    if not confirm:
        return

    # Get item details before removing
    item_row = match.iloc[0]
    shelf = str(item_row.get("Shelf", ""))
    remarks = str(item_row.get("Remarks", ""))

    # Delete QR file
    safe_hostname = hostname.replace(" ", "_")
    qr_path = os.path.join("qr_codes", f"{safe_hostname}.png")
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except Exception as e:
            messagebox.showwarning("Warning", f"QR file not deleted: {e}")

    # Remove from items
    df_items = df_items[df_items["Hostname"] != hostname].reset_index(drop=True)

    # Log to pullouts
    new_pullout = {
        "Hostname": hostname,
        "Serial Number": str(item_row.get("Serial Number", "")),
        "Checked By": str(item_row.get("Checked By", "")),
        "Shelf": shelf,
        "Remarks": remarks,
        "Pull Reason": reason,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    df_pullouts = pd.concat([df_pullouts, pd.DataFrame([new_pullout])], ignore_index=True)

    save_all(df_items, df_shelves, df_pullouts)

    messagebox.showinfo("Success", f"'{hostname}' pulled out successfully")

    # Clear pull fields
    pull_item_entry.delete(0, tk.END)
    pull_reason_entry.delete(0, tk.END)

    refresh_all()


def undo_pull(event):
    item_id = tree_pullouts.identify_row(event.y)
    if not item_id:
        return

    values = tree_pullouts.item(item_id, "values")
    if not values:
        return

    hostname = values[0]
    shelf = values[1]
    remarks = values[2]

    confirm = messagebox.askyesno(
        "Undo Pull",
        f"Restore '{hostname}' back to the warehouse?\n\nShelf: {shelf}\nRemarks: {remarks}"
    )
    if not confirm:
        return

    df_items = load_items()
    df_shelves = load_shelves()
    df_pullouts = load_pullouts()

    if hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", f"'{hostname}' already exists in warehouse")
        return

    # Get full record from pullouts sheet
    match = df_pullouts[df_pullouts["Hostname"] == hostname]
    if match.empty:
        messagebox.showerror("Error", f"'{hostname}' not found in pull history")
        return

    pull_row = match.iloc[0]
    serial = str(pull_row.get("Serial Number", ""))
    checked_by = str(pull_row.get("Checked By", ""))

    # Regenerate QR code
    try:
        QR_FOLDER = "qr_codes"
        if not os.path.exists(QR_FOLDER):
            os.makedirs(QR_FOLDER)
        qr_code = str(uuid.uuid4())
        qr_img = qrcode.make(qr_code)
        safe_hostname = hostname.replace(" ", "_")
        qr_path = os.path.join(QR_FOLDER, f"{safe_hostname}.png")
        qr_img.save(qr_path)
    except Exception as e:
        messagebox.showwarning("Warning", f"QR code not regenerated: {e}")
        qr_code = ""

    # Ensure new columns exist
    for col in ["Serial Number", "Checked By"]:
        if col not in df_items.columns:
            df_items[col] = ""

    # Restore directly to warehouse
    new_row = {
        "QR": qr_code,
        "Hostname": hostname,
        "Serial Number": serial,
        "Checked By": checked_by,
        "Shelf": shelf,
        "Remarks": remarks,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)

    # Remove from pullouts
    df_pullouts = df_pullouts[df_pullouts["Hostname"] != hostname].reset_index(drop=True)

    save_all(df_items, df_shelves, df_pullouts)

    messagebox.showinfo("Restored", f"'{hostname}' has been restored to the warehouse")
    show_pullouts()

def unstage_from_warehouse(event):
    item_id = tree_warehouse.identify_row(event.y)
    if not item_id:
        return

    values = tree_warehouse.item(item_id, "values")
    if not values:
        return

    hostname = values[1]
    serial = values[2]
    checked_by = values[3]
    shelf = values[4]
    remarks = values[5]

    confirm = messagebox.askyesno(
        "Move to Staging",
        f"Move '{hostname}' back to staging?\n\nShelf: {shelf}\nRemarks: {remarks}"
    )
    if not confirm:
        return

    if any(item['Hostname'] == hostname for item in staged_items):
        messagebox.showerror("Error", f"'{hostname}' is already in staging")
        return

    df_items = load_items()
    df_shelves = load_shelves()

    safe_hostname = hostname.replace(" ", "_")
    qr_path = os.path.join("qr_codes", f"{safe_hostname}.png")
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except Exception as e:
            messagebox.showwarning("Warning", f"QR file not deleted: {e}")

    df_items = df_items[df_items["Hostname"] != hostname].reset_index(drop=True)
    save_all(df_items, df_shelves)

    staged_items.append({
        "Hostname": hostname,
        "Serial Number": serial,
        "Checked By": checked_by,
        "Shelf": shelf,
        "Remarks": remarks
    })

    update_staged_display()
    show_warehouse()
    update_shelf_dropdown()

    messagebox.showinfo("Moved", f"'{hostname}' moved back to staging")

# ========== UI SETUP ==========

root = tk.Tk()
root.title("Warehouse System")
root.geometry("1200x700")

# ===== MAIN CONTAINER =====
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# ===== ROW 1: ITEM MANAGEMENT | SHELF CONTROLS | VIEW =====
row1_frame = tk.Frame(main_frame)
row1_frame.pack(fill="x")

# --- Item Management ---
input_frame = tk.LabelFrame(row1_frame, text="Item Management", padx=10, pady=5)
input_frame.pack(side="left", fill="both", padx=5)

tk.Label(input_frame, text="Hostname").grid(row=0, column=0, sticky="w")
hostname_entry = tk.Entry(input_frame, width=22)
hostname_entry.grid(row=0, column=1, pady=3)

tk.Label(input_frame, text="Serial Number").grid(row=1, column=0, sticky="w")
serial_entry = tk.Entry(input_frame, width=22)
serial_entry.grid(row=1, column=1, pady=3)

tk.Label(input_frame, text="Checked By").grid(row=2, column=0, sticky="w")
checked_by_entry = tk.Entry(input_frame, width=22)
checked_by_entry.grid(row=2, column=1, pady=3)

tk.Label(input_frame, text="Shelf").grid(row=3, column=0, sticky="w")

shelf_var = tk.StringVar()
shelf_dropdown = ttk.Combobox(input_frame, textvariable=shelf_var, width=19)
shelf_dropdown.grid(row=3, column=1, pady=3)

tk.Label(input_frame, text="Remarks").grid(row=4, column=0, sticky="w")
remarks_var = tk.StringVar()
ttk.Combobox(
    input_frame,
    textvariable=remarks_var,
    values=["No Issue", "Minimal", "Defective"],
    width=19
).grid(row=4, column=1, pady=3)

crud_frame = tk.Frame(input_frame)
crud_frame.grid(row=5, column=0, columnspan=2, pady=5)


tk.Button(crud_frame, text="PUT", command=put_item, width=8).grid(row=0, column=0, padx=3)
tk.Button(crud_frame, text="UPDATE", command=update_item, width=8).grid(row=0, column=1, padx=3)
tk.Button(crud_frame, text="↻", command=reset_ui, width=3).grid(row=0, column=2, padx=3)

tk.Label(input_frame, text="Staged Items (Click to Edit)", fg="green", font=("Arial", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w")
staged_listbox = tk.Listbox(input_frame, height=4, width=32)
staged_listbox.grid(row=7, column=0, columnspan=2, sticky="we", pady=3)
staged_listbox.bind("<<ListboxSelect>>", select_staged_item)

staging_btn_frame = tk.Frame(input_frame)
staging_btn_frame.grid(row=8, column=0, columnspan=2, pady=3)

tk.Button(staging_btn_frame, text="CLEAR ITEMS", command=remove_from_staging, width=13).pack(side="left", padx=2)
tk.Button(staging_btn_frame, text="PUT WAREHOUSE", command=put_warehouse, width=13).pack(side="left", padx=2)

# --- Shelf Controls (stacked vertically in the middle) ---
shelf_mid_frame = tk.Frame(row1_frame)
shelf_mid_frame.pack(side="left", fill="both", expand=True, padx=5)

# Shelf Control & Management (two sub-sections)
shelf_control = tk.LabelFrame(shelf_mid_frame, text="Shelf Control & Management", padx=10, pady=5)
shelf_control.pack(fill="x")

# -- Status Control --
status_control_frame = tk.LabelFrame(shelf_control, text="Status Control", padx=8, pady=5)
status_control_frame.pack(fill="x", pady=(0, 5))

shelf_control_var = tk.StringVar()
shelf_control_dropdown = ttk.Combobox(status_control_frame, textvariable=shelf_control_var, width=22, state="readonly")
shelf_control_dropdown.pack(side="left", padx=5)
tk.Button(status_control_frame, text="SET FULL", command=lambda: set_shelf_status("FULL"), width=10).pack(side="left", padx=3)
tk.Button(status_control_frame, text="SET AVAILABLE", command=lambda: set_shelf_status("AVAILABLE"), width=12).pack(side="left", padx=3)
tk.Button(status_control_frame, text="↻", command=reset_shelf_control, width=3).pack(side="left", padx=3)



# -- Add / Remove --
add_remove_frame = tk.LabelFrame(shelf_control, text="Add / Remove", padx=8, pady=5)
add_remove_frame.pack(fill="x")

remove_shelf_var = tk.StringVar()
remove_shelf_dropdown = ttk.Combobox(add_remove_frame, textvariable=remove_shelf_var, width=22)
remove_shelf_dropdown.pack(side="left", padx=5)
tk.Button(add_remove_frame, text="ADD", command=add_shelf).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="REMOVE", command=remove_shelf).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="↻", command=reset_shelf_addition, width=3).pack(side="left", padx=3)

# --- View ---
view_frame = tk.LabelFrame(row1_frame, text="View", padx=10, pady=5)
view_frame.pack(side="right", fill="both", padx=5)

tk.Button(view_frame, text="Show Warehouse", command=show_warehouse, width=15).pack(anchor="w", pady=3)
tk.Button(view_frame, text="Shelf Status", command=show_available, width=15).pack(anchor="w", pady=3)
tk.Button(view_frame, text="Pull History", command=show_pullouts, width=15).pack(anchor="w", pady=3)

# ===== ROW 2: WAREHOUSE SEARCH/FILTER/PULL =====
pullout_frame = tk.LabelFrame(main_frame, text="Warehouse", padx=10, pady=8)
pullout_frame.pack(fill="x", pady=5)


# ── Search & Filter ──
search_filter_frame = tk.LabelFrame(pullout_frame, text="Search & Filter", padx=8, pady=5)
search_filter_frame.pack(fill="x", pady=(0, 5))

tk.Label(search_filter_frame, text="Search:").pack(side="left", padx=(5, 2))
search_entry = tk.Entry(search_filter_frame, width=20)
search_entry.pack(side="left", padx=(0, 2))
tk.Button(search_filter_frame, text="🔍", command=search_item, width=2).pack(side="left", padx=(0, 15))

tk.Label(search_filter_frame, text="Shelf:").pack(side="left", padx=(5, 2))
pull_shelf_var = tk.StringVar()
pull_shelf_dropdown = ttk.Combobox(search_filter_frame, textvariable=pull_shelf_var, width=16, state="readonly")
pull_shelf_dropdown.pack(side="left", padx=(0, 15))

tk.Label(search_filter_frame, text="Remarks:").pack(side="left", padx=(5, 2))
pull_remarks_var = tk.StringVar()
ttk.Combobox(
    search_filter_frame,
    textvariable=pull_remarks_var,
    values=["No Issue", "Minimal", "Defective"],
    width=16,
    state="readonly"
).pack(side="left", padx=(0, 15))

tk.Button(search_filter_frame, text="FILTER", command=filter_pullouts, width=8).pack(side="left", padx=3)
tk.Button(search_filter_frame, text="↻", command=clear_pull_filters, width=3).pack(side="left", padx=3)

# ── Pull Out ──
pull_action_frame = tk.LabelFrame(pullout_frame, text="Pull Out", padx=8, pady=5)
pull_action_frame.pack(fill="x")

tk.Label(pull_action_frame, text="Selected Item:").pack(side="left", padx=(5, 2))
pull_item_entry = tk.Entry(pull_action_frame, width=20)
pull_item_entry.pack(side="left", padx=(0, 15))

tk.Label(pull_action_frame, text="Pull Reason:").pack(side="left", padx=(5, 2))
pull_reason_entry = tk.Entry(pull_action_frame, width=30)
pull_reason_entry.pack(side="left", padx=(0, 15))

tk.Button(pull_action_frame, text="WAREHOUSE PULL", command=pull_item, width=16).pack(side="left", padx=3)
tk.Button(pull_action_frame, text="↻", command=reset_pull_out, width=3).pack(side="left", padx=3)

# ===== STATUS =====
status_frame = tk.Frame(main_frame)
status_frame.pack(fill="x")

full_label = tk.Label(status_frame, text="FULL Shelves: None", fg="red")
full_label.pack(side="left", padx=10)

search_label = tk.Label(status_frame, text="", fg="blue")
search_label.pack(side="left", padx=10)

status_label = tk.Label(status_frame, text="", fg="green")
status_label.pack(side="left", padx=10)

# ===== TABLE =====
table_frame = tk.Frame(main_frame)
table_frame.pack(fill="both", expand=True, pady=5)

# Warehouse history table view

tree_warehouse = ttk.Treeview(
    table_frame,
    columns=("Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7"),
    show='headings'
)
tree_warehouse.heading("Col1", text="QR")
tree_warehouse.heading("Col2", text="Hostname")
tree_warehouse.heading("Col3", text="Serial Number")
tree_warehouse.heading("Col4", text="Checked By")
tree_warehouse.heading("Col5", text="Shelf")
tree_warehouse.heading("Col6", text="Remarks")
tree_warehouse.heading("Col7", text="Date")
tree_warehouse.column("Col1", width=200)
tree_warehouse.column("Col2", width=150)
tree_warehouse.column("Col3", width=130)
tree_warehouse.column("Col4", width=120)
tree_warehouse.column("Col5", width=130)
tree_warehouse.column("Col6", width=100)
tree_warehouse.column("Col7", width=150)
tree_warehouse.bind("<<TreeviewSelect>>", select_item)
tree_warehouse.bind("<Double-1>", unstage_from_warehouse)

tree_available = ttk.Treeview(
    table_frame,
    columns=("Col1", "Col2", "Col3"),
    show='headings'
)
tree_available.heading("Col1", text="Shelf")
tree_available.heading("Col2", text="Status")
tree_available.heading("Col3", text="Date_Full")
tree_available.column("Col1", width=250)
tree_available.column("Col2", width=150)
tree_available.column("Col3", width=200)

# Pullouts history table view

tree_pullouts = ttk.Treeview(
    table_frame,
    columns=("Col1", "Col2", "Col3", "Col4", "Col5"),
    show='headings'
)
tree_pullouts.heading("Col1", text="Hostname")
tree_pullouts.heading("Col2", text="Shelf")
tree_pullouts.heading("Col3", text="Remarks")
tree_pullouts.heading("Col4", text="Pull Reason")
tree_pullouts.heading("Col5", text="Date")
tree_pullouts.bind("<Double-1>", undo_pull)
tree_pullouts.column("Col1", width=180)
tree_pullouts.column("Col2", width=150)
tree_pullouts.column("Col3", width=100)
tree_pullouts.column("Col4", width=250)
tree_pullouts.column("Col5", width=160)

# ===== INIT =====
update_shelf_dropdown()
update_staged_display()
show_warehouse()

root.mainloop()
