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
LOG_FILE = "activity_log.xlsx"
QR_FOLDER = "qr_codes"
QR_LABELS_FOLDER = "qr_labels"

SHELVES = [
    "Area A", "Area B", "Area C",
    "Rack 1 - Bay 1", "Rack 1 - Bay 2", "Rack 1 - Bay 3",
    "Rack 2 - Bay 1", "Rack 2 - Bay 2", "Rack 2 - Bay 3",
]

staged_items = []
selected_staged_index = None
current_user = ""
session_start = ""

# ========== INITIALIZATION ==========

def initialize_file():
    sheets_to_create = {}
    if not os.path.exists(FILE):
        sheets_to_create = {"items": None, "shelves": None, "pullouts": None}
        mode = 'w'
    else:
        with pd.ExcelFile(FILE) as xls:
            existing = xls.sheet_names
        sheets_to_create = {s: None for s in ["items", "shelves", "pullouts"] if s not in existing}
        mode = 'a'

    if not sheets_to_create:
        return

    default_dfs = {
        "items": pd.DataFrame(columns=["QR", "Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Date"]),
        "shelves": pd.DataFrame({"Shelf": SHELVES, "Status": ["AVAILABLE"] * len(SHELVES), "Date_Full": [None] * len(SHELVES)}),
        "pullouts": pd.DataFrame(columns=["Hostname", "Serial Number", "Checked By", "Shelf", "Remarks", "Pull Reason", "Date"]),
    }
    with pd.ExcelWriter(FILE, engine='openpyxl', mode=mode) as writer:
        for sheet in sheets_to_create:
            default_dfs[sheet].to_excel(writer, sheet_name=sheet, index=False)

def initialize_log():
    if not os.path.exists(LOG_FILE):
        with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
            pd.DataFrame(columns=["Timestamp", "User", "Action", "Details"]).to_excel(writer, sheet_name="logs", index=False)

# ========== LOAD / SAVE FUNCTIONS ==========

def _load_sheet(file, sheet, init_fn):
    try:
        return pd.read_excel(file, sheet_name=sheet)
    except Exception:
        init_fn()
        return pd.read_excel(file, sheet_name=sheet)

def load_items():    return _load_sheet(FILE, "items", initialize_file)
def load_shelves():  return _load_sheet(FILE, "shelves", initialize_file)
def load_pullouts(): return _load_sheet(FILE, "pullouts", initialize_file)
def load_logs():     return _load_sheet(LOG_FILE, "logs", initialize_log)

def save_all(df_items, df_shelves, df_pullouts=None):
    if df_pullouts is None:
        df_pullouts = load_pullouts()
    with pd.ExcelWriter(FILE, engine='openpyxl') as writer:
        df_items.to_excel(writer, sheet_name="items", index=False)
        df_shelves.to_excel(writer, sheet_name="shelves", index=False)
        df_pullouts.to_excel(writer, sheet_name="pullouts", index=False)

def save_log(action, details=""):
    initialize_log()
    df_log = load_logs()
    new_row = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": current_user, "Action": action, "Details": details}
    df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)
    with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
        df_log.to_excel(writer, sheet_name="logs", index=False)

# ========== QR HELPERS ==========

def qr_path_for(hostname):
    return os.path.join(QR_FOLDER, f"{hostname.replace(' ', '_')}.png")

def generate_qr(hostname, data):
    os.makedirs(QR_FOLDER, exist_ok=True)
    qr_img = qrcode.make(data)
    qr_img.save(qr_path_for(hostname))

def delete_qr(hostname):
    path = qr_path_for(hostname)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            messagebox.showwarning("Warning", f"QR file not deleted: {e}")

# ========== STAGING ==========

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

# ========== INPUT FIELD HELPERS ==========

def _fill_input_fields(hostname="", serial="", checked_by="", shelf="", remarks=""):
    hostname_entry.delete(0, tk.END); hostname_entry.insert(0, hostname)
    serial_entry.delete(0, tk.END);   serial_entry.insert(0, serial)
    checked_by_entry.delete(0, tk.END); checked_by_entry.insert(0, checked_by)
    shelf_var.set(shelf)
    remarks_var.set(remarks)

def _clear_input_fields():
    _fill_input_fields()

# ========== CORE FUNCTIONS ==========

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

    status = df_shelves[df_shelves["Shelf"] == shelf]["Status"].values
    if len(status) > 0 and status[0] == "FULL":
        messagebox.showerror("Error", "Shelf is marked FULL"); return

    staged_items.append({
        "Hostname": hostname,
        "Serial Number": serial_entry.get().strip(),
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
            ))
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
            pdf_path = generate_qr_pdf(staged_items)
            pdf_msg = f"\nQR labels saved to:\n{pdf_path}"
        except Exception as pdf_err:
            pdf_msg = f"\nPDF generation failed: {pdf_err}"

        count = len(staged_items)
        for item in staged_items:
            save_log("PUT WAREHOUSE", f"Hostname: {item['Hostname']} | Shelf: {item['Shelf']}")

        staged_items.clear()
        messagebox.showinfo("Success", f"{count} item(s) added to warehouse{pdf_msg}")
        update_staged_display()
        refresh_all()

    except Exception as e:
        messagebox.showerror("Save Error",
            f"Failed to save to Excel:\n{str(e)}\n\n"
            "Common causes:\n• Excel file is open → close it\n• Wrong folder (check working directory)")

def update_item():
    global selected_staged_index
    new_hostname = hostname_entry.get().strip()
    if not new_hostname:
        messagebox.showerror("Error", "Hostname cannot be empty"); return

    # Update staged item
    if selected_staged_index is not None:
        index = selected_staged_index
        if index >= len(staged_items):
            messagebox.showerror("Error", "Invalid staged selection")
            selected_staged_index = None
            return
        if any(i != index and item['Hostname'] == new_hostname for i, item in enumerate(staged_items)):
            messagebox.showerror("Error", "Hostname already exists in staging"); return
        staged_items[index].update({
            "Hostname": new_hostname,
            "Serial Number": serial_entry.get().strip(),
            "Checked By": checked_by_entry.get().strip(),
            "Shelf": shelf_var.get(),
            "Remarks": remarks_var.get(),
        })
        messagebox.showinfo("Updated", "Staged item updated")
        update_staged_display()
        selected_staged_index = None
        return

    # Update warehouse item
    selected = tree_warehouse.selection()
    if not selected:
        messagebox.showerror("Error", "Select item to update"); return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])

    if new_hostname != df_items.at[index, "Hostname"] and new_hostname in df_items["Hostname"].values:
        messagebox.showerror("Error", "Hostname already exists and has a QR assigned"); return

    df_items.at[index, "Hostname"] = new_hostname
    df_items.at[index, "Serial Number"] = serial_entry.get().strip()
    df_items.at[index, "Checked By"] = checked_by_entry.get().strip()
    df_items.at[index, "Shelf"] = shelf_var.get()
    df_items.at[index, "Remarks"] = remarks_var.get()
    save_all(df_items, df_shelves)
    save_log("UPDATE ITEM", f"Hostname: {new_hostname} | Shelf: {shelf_var.get()}")
    messagebox.showinfo("Updated", "Record updated")
    refresh_all()

def delete_item():
    selected = tree_warehouse.selection()
    if not selected:
        messagebox.showerror("Error", "Select item"); return

    df_items = load_items()
    df_shelves = load_shelves()
    index = tree_warehouse.index(selected[0])
    hostname = df_items.at[index, "Hostname"]

    delete_qr(hostname)
    df_items = df_items.drop(index).reset_index(drop=True)
    save_all(df_items, df_shelves)
    save_log("DELETE ITEM", f"Hostname: {hostname}")
    messagebox.showinfo("Deleted", "Record and QR code deleted")
    refresh_all()

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

    delete_qr(hostname)
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
    save_log("WAREHOUSE PULL", f"Hostname: {hostname} | Shelf: {shelf} | Reason: {reason}")
    messagebox.showinfo("Success", f"'{hostname}' pulled out successfully")
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
        generate_qr(hostname, qr_code)
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
    save_log("UNDO PULL", f"Hostname: {hostname} | Shelf: {shelf}")
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
    delete_qr(hostname)
    df_items = df_items[df_items["Hostname"] != hostname].reset_index(drop=True)
    save_all(df_items, df_shelves)
    staged_items.append({"Hostname": hostname, "Serial Number": serial, "Checked By": checked_by, "Shelf": shelf, "Remarks": remarks})
    save_log("UNSTAGE", f"Hostname: {hostname} | Shelf: {shelf}")
    messagebox.showinfo("Moved", f"'{hostname}' moved back to staging")
    update_staged_display()
    refresh_all()

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
    update_shelf_dropdown()

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
    update_shelf_dropdown()

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
    status_label.config(text=f"{shelf} → {new_status}")
    refresh_all()

# ========== DISPLAY FUNCTIONS ==========

def _show_tree(tree):
    for t in (tree_warehouse, tree_available, tree_pullouts):
        if t is not tree:
            t.pack_forget()
    tree.pack(fill="both", expand=True)

def show_warehouse():
    update_full_shelves_display()
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
        show_warehouse(); search_label.config(text=""); return
    filtered = load_items()[lambda df: df["Hostname"].str.lower().str.contains(keyword, na=False)]
    _populate_warehouse_tree(filtered)
    search_label.config(text=f"Search: {len(filtered)} result(s)")

def filter_pullouts():
    shelf_filter = pull_shelf_var.get()
    remarks_filter = pull_remarks_var.get()
    if not shelf_filter and not remarks_filter:
        messagebox.showinfo("Info", "Please select at least one filter"); return

    df = load_items()
    if shelf_filter:   df = df[df["Shelf"] == shelf_filter]
    if remarks_filter: df = df[df["Remarks"] == remarks_filter]

    _populate_warehouse_tree(df)
    search_label.config(text=f"Filtered: {len(df)} item(s)"
        + (f" | Shelf: {shelf_filter}" if shelf_filter else "")
        + (f" | Remarks: {remarks_filter}" if remarks_filter else ""))

def update_full_shelves_display():
    df_shelves = load_shelves()
    full_shelves = df_shelves[df_shelves["Status"] == "FULL"]["Shelf"].tolist()
    full_label.config(text="FULL Shelves:\n" + "\n".join(full_shelves) if full_shelves else "FULL Shelves: None")

def refresh_all():
    show_warehouse()
    update_shelf_dropdown()

def update_shelf_dropdown():
    shelf_list = sorted(load_shelves()["Shelf"].tolist())
    for dropdown in (shelf_dropdown, shelf_control_dropdown, remove_shelf_dropdown, pull_shelf_dropdown):
        dropdown["values"] = shelf_list

def select_item(event):
    selected = tree_warehouse.selection()
    if selected:
        values = tree_warehouse.item(selected[0], "values")
        _fill_input_fields(values[1], values[2], values[3], values[4], values[5])
        pull_item_entry.delete(0, tk.END)
        pull_item_entry.insert(0, values[1])

# ========== RESET FUNCTIONS ==========

def reset_ui():
    _clear_input_fields()
    for s in tree_warehouse.selection(): tree_warehouse.selection_remove(s)
    status_label.config(text="")
    search_label.config(text="")
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
    for s in tree_warehouse.selection(): tree_warehouse.selection_remove(s)
    status_label.config(text="")
    search_label.config(text="")
    show_warehouse()

def clear_pull_filters():
    pull_shelf_var.set("")
    pull_remarks_var.set("")
    search_entry.delete(0, tk.END)
    search_label.config(text="")
    show_warehouse()

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
            pdf.add_page()
            col = row = 0
            x, y = MARGIN_X, MARGIN_Y

        pdf.set_draw_color(150, 150, 150)
        pdf.rect(x, y, LABEL_W, LABEL_H)

        path = qr_path_for(item['Hostname'])
        if os.path.exists(path):
            qr_size = 20
            pdf.image(path, x=x + (LABEL_W - qr_size) / 2, y=y + 3, w=qr_size, h=qr_size)

        label_x, value_x, text_y, line_h = x + 2, x + 19, y + 26, 4.8
        fields = [
            ("Hostname:", str(item.get("Hostname", ""))),
            ("Serial No:", str(item.get("Serial Number", ""))),
            ("Checked By:", str(item.get("Checked By", ""))),
            ("Shelf:", str(item.get("Shelf", ""))),
            ("Remarks:", str(item.get("Remarks", ""))),
            ("Date:", datetime.now().strftime("%Y-%m-%d")),
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

    os.makedirs(QR_LABELS_FOLDER, exist_ok=True)
    pdf_path = os.path.join(QR_LABELS_FOLDER, f"qr_labels_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf")
    pdf.output(pdf_path)
    return pdf_path

# ========== DIALOGS ==========

def open_label_manager():
    manager = tk.Toplevel(root)
    manager.title("QR Label Manager")
    manager.geometry("520x350")
    manager.resizable(False, False)

    tk.Label(manager, text="QR Label Files", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))

    table_frame_m = tk.Frame(manager)
    table_frame_m.pack(fill="both", expand=True, padx=10, pady=5)

    tree_labels = ttk.Treeview(table_frame_m, columns=("File", "Date", "Size"), show="headings", height=12)
    for col, text, width in [("File", "Filename", 260), ("Date", "Created", 150), ("Size", "Size", 70)]:
        tree_labels.heading(col, text=text)
        tree_labels.column(col, width=width)
    tree_labels.pack(fill="both", expand=True)

    def load_label_files():
        tree_labels.delete(*tree_labels.get_children())
        if not os.path.exists(QR_LABELS_FOLDER):
            return
        now = datetime.now()
        for f in sorted([f for f in os.listdir(QR_LABELS_FOLDER) if f.endswith(".pdf")], reverse=True):
            full_path = os.path.join(QR_LABELS_FOLDER, f)
            size_kb = round(os.path.getsize(full_path) / 1024, 1)
            try:
                file_dt = datetime.strptime(f.replace("qr_labels_", "").replace(".pdf", ""), "%Y-%m-%d_%H-%M-%S")
                delta = now - file_dt
                age = "Today" if delta.days == 0 else ("1 day ago" if delta.days == 1 else f"{delta.days} days ago")
                date_str = f"{file_dt.strftime('%Y-%m-%d %H:%M')}  ({age})"
            except Exception:
                date_str = "Unknown"
            tree_labels.insert("", "end", values=(f, date_str, f"{size_kb} kb"))

    def open_selected():
        selected = tree_labels.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a file to open", parent=manager); return
        full_path = os.path.join(QR_LABELS_FOLDER, tree_labels.item(selected[0], "values")[0])
        if os.path.exists(full_path):
            os.startfile(full_path)
        else:
            messagebox.showerror("Error", "File not found", parent=manager)

    def clear_selected():
        selected = tree_labels.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a file to clear", parent=manager); return
        filename = tree_labels.item(selected[0], "values")[0]
        if not messagebox.askyesno("Confirm Clear", f"Delete '{filename}'?", parent=manager):
            return
        try:
            os.remove(os.path.join(QR_LABELS_FOLDER, filename))
            load_label_files()
            messagebox.showinfo("Cleared", f"'{filename}' deleted", parent=manager)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}", parent=manager)

    btn_frame_m = tk.Frame(manager)
    btn_frame_m.pack(pady=8)
    tk.Button(btn_frame_m, text="OPEN",    command=open_selected,  width=12).pack(side="left", padx=5)
    tk.Button(btn_frame_m, text="CLEAR",   command=clear_selected,  width=12).pack(side="left", padx=5)
    tk.Button(btn_frame_m, text="REFRESH", command=load_label_files, width=12).pack(side="left", padx=5)
    load_label_files()

def open_activity_log():
    log_win = tk.Toplevel(root)
    log_win.title("Activity Log")
    log_win.geometry("700x450")

    filter_frame = tk.Frame(log_win)
    filter_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(filter_frame, text="Filter User:").pack(side="left", padx=5)
    filter_user_var = tk.StringVar()
    tk.Entry(filter_frame, textvariable=filter_user_var, width=15).pack(side="left", padx=5)

    tk.Label(filter_frame, text="Filter Action:").pack(side="left", padx=5)
    filter_action_var = tk.StringVar()
    ttk.Combobox(filter_frame, textvariable=filter_action_var, state="readonly", width=15,
        values=["", "LOGIN", "PUT WAREHOUSE", "WAREHOUSE PULL", "UPDATE ITEM", "DELETE ITEM", "UNDO PULL", "UNSTAGE", "SHELF STATUS"]
    ).pack(side="left", padx=5)

    table_frame_l = tk.Frame(log_win)
    table_frame_l.pack(fill="both", expand=True, padx=10, pady=5)
    scrollbar = ttk.Scrollbar(table_frame_l)
    scrollbar.pack(side="right", fill="y")

    tree_log = ttk.Treeview(table_frame_l, columns=("Timestamp", "User", "Action", "Details"),
        show="headings", yscrollcommand=scrollbar.set)
    for col, width in [("Timestamp", 140), ("User", 100), ("Action", 120), ("Details", 300)]:
        tree_log.heading(col, text=col)
        tree_log.column(col, width=width)
    tree_log.pack(fill="both", expand=True)
    scrollbar.config(command=tree_log.yview)

    count_label = tk.Label(log_win, text="", fg="blue")
    count_label.pack(anchor="w", padx=10)

    def load_log_data():
        tree_log.delete(*tree_log.get_children())
        df_log = load_logs()
        user_f = filter_user_var.get().strip().lower()
        action_f = filter_action_var.get().strip()
        if user_f:   df_log = df_log[df_log["User"].str.lower().str.contains(user_f, na=False)]
        if action_f: df_log = df_log[df_log["Action"] == action_f]
        df_log = df_log.iloc[::-1].reset_index(drop=True)
        for _, row in df_log.iterrows():
            tree_log.insert("", "end", values=tuple(row.get(c, "") for c in ["Timestamp", "User", "Action", "Details"]))
        count_label.config(text=f"{len(df_log)} record(s)")

    def reset_filters():
        filter_user_var.set(""); filter_action_var.set(""); load_log_data()

    tk.Button(filter_frame, text="FILTER", command=load_log_data, width=8).pack(side="left", padx=5)
    tk.Button(filter_frame, text="↻",      command=reset_filters,  width=3).pack(side="left", padx=3)
    load_log_data()

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
root.title("Warehouse System")
root.geometry("1200x700")
root.eval('tk::PlaceWindow . center')

# User bar
user_bar = tk.Frame(root, bg="#2c3e50", height=28)
user_bar.pack(fill="x")
tk.Label(user_bar, text=f"👤  {current_user}", bg="#2c3e50", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=4)
tk.Label(user_bar, text=f"Session started: {session_start}", bg="#2c3e50", fg="#95a5a6", font=("Arial", 8)).pack(side="left", padx=5, pady=4)
clock_label = tk.Label(user_bar, text="", bg="#2c3e50", fg="#95a5a6", font=("Arial", 8))
clock_label.pack(side="right", padx=10, pady=4)

def update_clock():
    clock_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.after(1000, update_clock)
update_clock()

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Row 1
row1_frame = tk.Frame(main_frame)
row1_frame.pack(fill="x")

# Item Management
input_frame = tk.LabelFrame(row1_frame, text="Item Management", padx=10, pady=5)
input_frame.pack(side="left", fill="both", padx=5)

for row_i, (label, attr) in enumerate([("Hostname", "hostname_entry"), ("Serial Number", "serial_entry"), ("Checked By", "checked_by_entry")]):
    tk.Label(input_frame, text=label).grid(row=row_i, column=0, sticky="w")
locals()  # just to ensure entries are created below
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
tk.Button(crud_frame, text="PUT",    command=put_item,   width=8).grid(row=0, column=0, padx=3)
tk.Button(crud_frame, text="UPDATE", command=update_item, width=8).grid(row=0, column=1, padx=3)
tk.Button(crud_frame, text="↻",      command=reset_ui,    width=3).grid(row=0, column=2, padx=3)

tk.Label(input_frame, text="Staged Items (Click to Edit)", fg="green", font=("Arial", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w")
staged_listbox = tk.Listbox(input_frame, height=4, width=32)
staged_listbox.grid(row=7, column=0, columnspan=2, sticky="we", pady=3)
staged_listbox.bind("<<ListboxSelect>>", select_staged_item)

staging_btn_frame = tk.Frame(input_frame)
staging_btn_frame.grid(row=8, column=0, columnspan=2, pady=3)
tk.Button(staging_btn_frame, text="CLEAR ITEMS",    command=remove_from_staging, width=13).pack(side="left", padx=2)
tk.Button(staging_btn_frame, text="PUT WAREHOUSE",  command=put_warehouse,       width=13).pack(side="left", padx=2)

# Shelf Controls
shelf_mid_frame = tk.Frame(row1_frame)
shelf_mid_frame.pack(side="left", fill="both", expand=True, padx=5)
shelf_control = tk.LabelFrame(shelf_mid_frame, text="Shelf Control & Management", padx=10, pady=5)
shelf_control.pack(fill="x")

status_control_frame = tk.LabelFrame(shelf_control, text="Status Control", padx=8, pady=5)
status_control_frame.pack(fill="x", pady=(0, 5))
shelf_control_var = tk.StringVar()
shelf_control_dropdown = ttk.Combobox(status_control_frame, textvariable=shelf_control_var, width=22, state="readonly")
shelf_control_dropdown.pack(side="left", padx=5)
tk.Button(status_control_frame, text="SET FULL",      command=lambda: set_shelf_status("FULL"),      width=10).pack(side="left", padx=3)
tk.Button(status_control_frame, text="SET AVAILABLE", command=lambda: set_shelf_status("AVAILABLE"), width=12).pack(side="left", padx=3)
tk.Button(status_control_frame, text="↻",             command=reset_shelf_control,                   width=3).pack(side="left", padx=3)

add_remove_frame = tk.LabelFrame(shelf_control, text="Add / Remove", padx=8, pady=5)
add_remove_frame.pack(fill="x")
remove_shelf_var = tk.StringVar()
remove_shelf_dropdown = ttk.Combobox(add_remove_frame, textvariable=remove_shelf_var, width=22)
remove_shelf_dropdown.pack(side="left", padx=5)
tk.Button(add_remove_frame, text="ADD",    command=add_shelf,          ).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="REMOVE", command=remove_shelf,        ).pack(side="left", padx=3)
tk.Button(add_remove_frame, text="↻",      command=reset_shelf_addition, width=3).pack(side="left", padx=3)

# View
view_frame = tk.LabelFrame(row1_frame, text="View", padx=10, pady=5)
view_frame.pack(side="right", fill="both", padx=5)
for text, cmd in [
    ("Show Warehouse", show_warehouse),
    ("Shelf Status",   show_available),
    ("Pull History",   show_pullouts),
    ("QR Label Manager", open_label_manager),
    ("Activity Log",   open_activity_log),
]:
    tk.Button(view_frame, text=text, command=cmd, width=15).pack(anchor="w", pady=3)

# Row 2: Warehouse search/filter/pull
pullout_frame = tk.LabelFrame(main_frame, text="Warehouse", padx=10, pady=8)
pullout_frame.pack(fill="x", pady=5)

search_filter_frame = tk.LabelFrame(pullout_frame, text="Search & Filter", padx=8, pady=5)
search_filter_frame.pack(fill="x", pady=(0, 5))

tk.Label(search_filter_frame, text="Search:").pack(side="left", padx=(5, 2))
search_entry = tk.Entry(search_filter_frame, width=20); search_entry.pack(side="left", padx=(0, 2))
tk.Button(search_filter_frame, text="🔍", command=search_item, width=2).pack(side="left", padx=(0, 15))

tk.Label(search_filter_frame, text="Shelf:").pack(side="left", padx=(5, 2))
pull_shelf_var = tk.StringVar()
pull_shelf_dropdown = ttk.Combobox(search_filter_frame, textvariable=pull_shelf_var, width=16, state="readonly")
pull_shelf_dropdown.pack(side="left", padx=(0, 15))

tk.Label(search_filter_frame, text="Remarks:").pack(side="left", padx=(5, 2))
pull_remarks_var = tk.StringVar()
ttk.Combobox(search_filter_frame, textvariable=pull_remarks_var, values=["No Issue", "Minimal", "Defective"], width=16, state="readonly").pack(side="left", padx=(0, 15))
tk.Button(search_filter_frame, text="FILTER", command=filter_pullouts,  width=8).pack(side="left", padx=3)
tk.Button(search_filter_frame, text="↻",      command=clear_pull_filters, width=3).pack(side="left", padx=3)

pull_action_frame = tk.LabelFrame(pullout_frame, text="Pull Out", padx=8, pady=5)
pull_action_frame.pack(fill="x")
tk.Label(pull_action_frame, text="Selected Item:").pack(side="left", padx=(5, 2))
pull_item_entry = tk.Entry(pull_action_frame, width=20); pull_item_entry.pack(side="left", padx=(0, 15))
tk.Label(pull_action_frame, text="Pull Reason:").pack(side="left", padx=(5, 2))
pull_reason_entry = tk.Entry(pull_action_frame, width=30); pull_reason_entry.pack(side="left", padx=(0, 15))
tk.Button(pull_action_frame, text="WAREHOUSE PULL", command=pull_item,    width=16).pack(side="left", padx=3)
tk.Button(pull_action_frame, text="↻",              command=reset_pull_out, width=3).pack(side="left", padx=3)

# Status
status_frame = tk.Frame(main_frame)
status_frame.pack(fill="x")
full_label   = tk.Label(status_frame, text="FULL Shelves: None", fg="red");   full_label.pack(side="left", padx=10)
search_label = tk.Label(status_frame, text="", fg="blue");                    search_label.pack(side="left", padx=10)
status_label = tk.Label(status_frame, text="", fg="green");                   status_label.pack(side="left", padx=10)

# Tables
table_frame = tk.Frame(main_frame)
table_frame.pack(fill="both", expand=True, pady=5)

tree_warehouse = ttk.Treeview(table_frame, columns=("Col1","Col2","Col3","Col4","Col5","Col6","Col7"), show='headings')
for col, text, width in zip(
    ("Col1","Col2","Col3","Col4","Col5","Col6","Col7"),
    ("QR","Hostname","Serial Number","Checked By","Shelf","Remarks","Date"),
    (200,150,130,120,130,100,150)
):
    tree_warehouse.heading(col, text=text)
    tree_warehouse.column(col, width=width)
tree_warehouse.bind("<<TreeviewSelect>>", select_item)
tree_warehouse.bind("<Double-1>", unstage_from_warehouse)

tree_available = ttk.Treeview(table_frame, columns=("Col1","Col2","Col3"), show='headings')
for col, text, width in zip(("Col1","Col2","Col3"), ("Shelf","Status","Date_Full"), (250,150,200)):
    tree_available.heading(col, text=text)
    tree_available.column(col, width=width)

tree_pullouts = ttk.Treeview(table_frame, columns=("Col1","Col2","Col3","Col4","Col5"), show='headings')
for col, text, width in zip(("Col1","Col2","Col3","Col4","Col5"), ("Hostname","Shelf","Remarks","Pull Reason","Date"), (180,150,100,250,160)):
    tree_pullouts.heading(col, text=text)
    tree_pullouts.column(col, width=width)
tree_pullouts.bind("<Double-1>", undo_pull)

# Init
update_shelf_dropdown()
update_staged_display()
show_warehouse()

root.mainloop()
