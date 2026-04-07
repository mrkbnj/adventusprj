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
        df_items = pd.DataFrame(columns=["QR", "Hostname", "Shelf", "Remarks", "Date"])
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
        df_items = pd.DataFrame(columns=["QR", "Hostname", "Shelf", "Remarks", "Date"])
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

    # Switch to warehouse view
    tree_available.pack_forget()
    tree_pullouts.pack_forget()
    tree_warehouse.delete(*tree_warehouse.get_children())
    tree_warehouse.pack(fill="both", expand=True)

    for _, row in df_items.iterrows():
        tree_warehouse.insert("", "end", values=(
            row.get("QR", ""),
            row.get("Hostname", ""),
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
        "Shelf": shelf,
        "Remarks": remarks,
    }
    
    staged_items.append(new_item)
    messagebox.showinfo("Staged", f"'{hostname}' added to staging queue")
    
    # Clear input fields
    hostname_entry.delete(0, tk.END)
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
        QR_FOLDER = "qr_codes"
        
        if not os.path.exists(QR_FOLDER):
            os.makedirs(QR_FOLDER)

        # Add all staged items
        for item in staged_items:
            qr_code = str(uuid.uuid4())
            qr_img = qrcode.make(qr_code)
            safe_hostname = item['Hostname'].replace(" ", "_")
            qr_path = os.path.join(QR_FOLDER, f"{safe_hostname}.png")
            qr_img.save(qr_path)
            
            new_row = {
                "QR": qr_code,
                "Hostname": item['Hostname'],
                "Shelf": item['Shelf'],
                "Remarks": item['Remarks'],
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)

        # ← This is where the actual save happens
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
        print("DEBUG ERROR:", e)  # ← shows full traceback in console
     
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
    new_shelf = shelf_entry.get().strip()

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

    shelf_entry.delete(0, tk.END)
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
    shelf_var.set("")  # Reset shelf selection
    remarks_var.set("")  # Reset remarks

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
    tree_warehouse.pack(fill="both", expand=True)
    
    df_items = load_items()
    
    # Ensure Date column exists
    if "Date" not in df_items.columns:
        df_items["Date"] = ""
    
    for _, row in df_items.iterrows():
        tree_warehouse.insert("", "end", values=(row.get("QR", ""), row.get("Hostname", ""), row.get("Shelf", ""), row.get("Remarks", ""), row.get("Date", "")))

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
        shelf_var.set(values[2])
        remarks_var.set(values[3])

        # Auto-fill pull out segment
        pull_item_entry.delete(0, tk.END)
        pull_item_entry.insert(0, values[1])

def search_item():
    keyword = search_entry.get().strip().lower()
    df_items = load_items()

    if not keyword:
        show_warehouse()
        search_label.config(text="")  # Clear search label
        return

    # Filter items whose hostname contains the keyword
    filtered = df_items[df_items["Hostname"].str.lower().str.contains(keyword, na=False)]

    tree_available.pack_forget()
    tree_pullouts.pack_forget()          # ← add this line
    tree_warehouse.pack(fill="both", expand=True)
    tree_warehouse.delete(*tree_warehouse.get_children())
    for _, row in filtered.iterrows():
        tree_warehouse.insert("", "end", values=(row.get("QR", ""), row.get("Hostname", ""), row.get("Shelf", ""), row.get("Remarks", ""), row.get("Date", "")))

    search_label.config(text=f"Search: {len(filtered)} result(s)")

def search_shelf():
    shelf_name = shelf_search_entry.get().strip()
    df_items = load_items()

    if not shelf_name:
        show_warehouse()
        search_label.config(text="")
        return

    # Filter items by shelf
    filtered = df_items[df_items["Shelf"] == shelf_name]

    tree_available.pack_forget()
    tree_warehouse.pack(fill="both", expand=True)
    tree_warehouse.delete(*tree_warehouse.get_children())
    for _, row in filtered.iterrows():
        tree_warehouse.insert("", "end", values=(row.get("QR", ""), row.get("Hostname", ""), row.get("Shelf", ""), row.get("Remarks", ""), row.get("Date", "")))

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
    shelf = item_row["Shelf"]
    remarks = item_row["Remarks"]

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

# ========== UI SETUP ==========

root = tk.Tk()
root.title("Warehouse System")
root.geometry("1100x650")

# ===== MAIN CONTAINER =====
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# ===== TOP SECTION (2 COLUMNS) =====
top_frame = tk.Frame(main_frame)
top_frame.pack(fill="x")

# ================= LEFT: INPUT PANEL =================
input_frame = tk.LabelFrame(top_frame, text="Item Management", padx=10, pady=10)
input_frame.pack(side="left", fill="both", expand=True, padx=5)

tk.Label(input_frame, text="Hostname").grid(row=0, column=0, sticky="w")
hostname_entry = tk.Entry(input_frame, width=25)
hostname_entry.grid(row=0, column=1, pady=5)

tk.Label(input_frame, text="Shelf").grid(row=1, column=0, sticky="w")
shelf_var = tk.StringVar()
shelf_dropdown = ttk.Combobox(input_frame, textvariable=shelf_var, width=22)
shelf_dropdown.grid(row=1, column=1, pady=5)

tk.Label(input_frame, text="Remarks").grid(row=2, column=0, sticky="w")
remarks_var = tk.StringVar()
ttk.Combobox(
    input_frame,
    textvariable=remarks_var,
    values=["No Issue", "Minimal", "Defective"],
    width=22
).grid(row=2, column=1, pady=5)

# CRUD Buttons
crud_frame = tk.Frame(input_frame)
crud_frame.grid(row=3, column=0, columnspan=2, pady=10)

tk.Button(crud_frame, text="PUT", command=put_item, width=10).grid(row=0, column=0, padx=3)
tk.Button(crud_frame, text="UPDATE", command=update_item, width=10).grid(row=0, column=2, padx=3)
tk.Button(crud_frame, text="↻", command=reset_ui, width=3).grid(row=0, column=4, padx=3)

# Staged Items Indicator
tk.Label(input_frame, text="Staged Items (Click to Edit)", fg="green", font=("Arial", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky="w")

staged_listbox = tk.Listbox(input_frame, height=6)
staged_listbox.grid(row=5, column=0, columnspan=2, sticky="we", pady=5)
staged_listbox.bind("<<ListboxSelect>>", select_staged_item)

tk.Button(input_frame, text="CLEAR ITEMS", command=remove_from_staging, width=20).grid(row=6, column=0, columnspan=2, pady=5)
tk.Button(input_frame, text="PUT WAREHOUSE", command=put_warehouse, width=20).grid(row=7, column=0, columnspan=2, pady=5)

# ================= RIGHT: SEARCH PANEL =================
search_frame = tk.LabelFrame(top_frame, text="Search", padx=10, pady=10)
search_frame.pack(side="right", fill="both", expand=True, padx=5)

tk.Label(search_frame, text="Hostname").grid(row=0, column=0, sticky="w")
search_entry = tk.Entry(search_frame, width=20)
search_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Button(search_frame, text="🔍", command=search_item, width=2)\
    .grid(row=0, column=2, padx=2)

tk.Label(search_frame, text="Shelf").grid(row=1, column=0, sticky="w")
shelf_search_entry = tk.Entry(search_frame, width=20)
shelf_search_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Button(search_frame, text="🔍", command=search_shelf, width=2)\
    .grid(row=1, column=2, padx=2)

# ===== VIEW SECTION =====
view_frame = tk.LabelFrame(top_frame, text="View", padx=10, pady=10)
view_frame.pack(side="right", fill="both", expand=False, padx=5)

tk.Button(view_frame, text="Show Warehouse", command=show_warehouse, width=15)\
    .pack(side="left", padx=5)

tk.Button(view_frame, text="Shelf Status", command=show_available, width=15)\
    .pack(side="left", padx=5)

# ===== MIDDLE SECTION =====
middle_frame = tk.Frame(main_frame)
middle_frame.pack(fill="x", pady=10)

# Shelf Control
shelf_control = tk.LabelFrame(middle_frame, text="Shelf Control", padx=10, pady=10)
shelf_control.pack(side="left", fill="x", expand=True, padx=5)

tk.Label(shelf_control, text="Select Shelf").pack(side="left", padx=5)
shelf_control_var = tk.StringVar()
shelf_control_dropdown = ttk.Combobox(shelf_control, textvariable=shelf_control_var, width=25, state="readonly")
shelf_control_dropdown.pack(side="left", padx=5)

tk.Button(shelf_control, text="SET FULL",
          command=lambda: set_shelf_status("FULL"), width=12)\
    .pack(side="left", padx=5)

tk.Button(shelf_control, text="SET AVAILABLE",
          command=lambda: set_shelf_status("AVAILABLE"), width=12)\
    .pack(side="left", padx=5)

tk.Button(view_frame, text="Pull History", command=show_pullouts, width=15)\
    .pack(side="left", padx=5)

# Add Shelf
add_frame = tk.LabelFrame(middle_frame, text="Add/Remove Shelf", padx=10, pady=10)
add_frame.pack(side="left", fill="x", expand=True, padx=5)

tk.Label(add_frame, text="New Shelf").pack(side="left")
shelf_entry = tk.Entry(add_frame, width=15)
shelf_entry.pack(side="left", padx=5)

tk.Button(add_frame, text="Add", command=add_shelf).pack(side="left", padx=2)

tk.Label(add_frame, text="Remove").pack(side="left", padx=(10, 0))
remove_shelf_var = tk.StringVar()
remove_shelf_dropdown = ttk.Combobox(add_frame, textvariable=remove_shelf_var, width=15, state="readonly")
remove_shelf_dropdown.pack(side="left", padx=5)

tk.Button(add_frame, text="Remove", command=remove_shelf).pack(side="left", padx=2)

# ===== PULL OUT SECTION =====
pullout_frame = tk.LabelFrame(main_frame, text="Pull Out", padx=10, pady=10)
pullout_frame.pack(fill="x", pady=5)

# Row 0 - Selected Item and Pull Reason
tk.Label(pullout_frame, text="Selected Item:").grid(row=0, column=0, sticky="w", padx=5)
pull_item_entry = tk.Entry(pullout_frame, width=25)
pull_item_entry.grid(row=0, column=1, padx=5, pady=3)

tk.Label(pullout_frame, text="Pull Reason:").grid(row=0, column=2, sticky="w", padx=5)
pull_reason_entry = tk.Entry(pullout_frame, width=25)
pull_reason_entry.grid(row=0, column=3, padx=5, pady=3)

# Row 1 - Filters
tk.Label(pullout_frame, text="Filter Shelf:").grid(row=1, column=0, sticky="w", padx=5)
pull_shelf_var = tk.StringVar()
pull_shelf_dropdown = ttk.Combobox(pullout_frame, textvariable=pull_shelf_var, width=22, state="readonly")
pull_shelf_dropdown.grid(row=1, column=1, padx=5, pady=3)

tk.Label(pullout_frame, text="Filter Remarks:").grid(row=1, column=2, sticky="w", padx=5)
pull_remarks_var = tk.StringVar()
ttk.Combobox(
    pullout_frame,
    textvariable=pull_remarks_var,
    values=["No Issue", "Minimal", "Defective"],
    width=22,
    state="readonly"
).grid(row=1, column=3, padx=5, pady=3)

# Row 2 - Buttons
btn_frame = tk.Frame(pullout_frame)
btn_frame.grid(row=2, column=0, columnspan=4, pady=8)

tk.Button(btn_frame, text="WAREHOUSE PULL", command=pull_item, width=18).pack(side="left", padx=5)
tk.Button(btn_frame, text="FILTER", command=filter_pullouts, width=10).pack(side="left", padx=5)
tk.Button(btn_frame, text="↻", command=clear_pull_filters, width=3).pack(side="left", padx=5)

# ===== WAREHOUSING SECTION =====
# warehousing_frame = tk.LabelFrame(main_frame, text="Warehousing", padx=10, pady=10)
# warehousing_frame.pack(fill="x", pady=10)

#PENDING FUNCTION
# tk.Button(warehousing_frame, text="PULL ITEM", command=pull_item, width=20).pack(side="left", padx=10, pady=5)

#tk.Button(warehousing_frame, text="DELETE ITEM", command=delete_item, width=20).pack(side="left", padx=10, pady=5)



# ===== STATUS SECTION =====
status_frame = tk.Frame(main_frame)
status_frame.pack(fill="x")

full_label = tk.Label(status_frame, text="FULL Shelves: None", fg="red")
full_label.pack(anchor="w")

search_label = tk.Label(status_frame, text="", fg="blue")
search_label.pack(anchor="w")

status_label = tk.Label(status_frame, text="", fg="green")
status_label.pack(anchor="w")

# ===== TABLE =====
table_frame = tk.Frame(main_frame)
table_frame.pack(fill="both", expand=True, pady=10)

# Warehouse Table
tree_warehouse = ttk.Treeview(
    table_frame,
    columns=("Col1", "Col2", "Col3", "Col4", "Col5"),
    show='headings'
)
tree_warehouse.heading("Col1", text="QR")
tree_warehouse.heading("Col2", text="Hostname")
tree_warehouse.heading("Col3", text="Shelf")
tree_warehouse.heading("Col4", text="Remarks")
tree_warehouse.heading("Col5", text="Date")
tree_warehouse.bind("<<TreeviewSelect>>", select_item)

# Available Shelves Table
tree_available = ttk.Treeview(
    table_frame,
    columns=("Col1", "Col2", "Col3"),
    show='headings'
)
tree_available.heading("Col1", text="Shelf")
tree_available.heading("Col2", text="Status")
tree_available.heading("Col3", text="Date_Full")

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

# ===== INIT =====
update_shelf_dropdown()
update_staged_display()
show_warehouse()

root.mainloop()
