# Warehouse System

A comprehensive Python-based warehouse management system with QR code generation, item staging, and shelf management.

## Features

- **Item Management** - Add, update, delete, and search warehouse items
- **Staging System** - Stage items before committing to warehouse (batch operations)
- **QR Code Generation** - Automatic QR code generation for each item
- **Shelf Control** - Manage shelf availability and status tracking
- **Search Functionality** - Search by hostname or shelf location
- **Data Persistence** - Excel-based database (warehouse.xlsx)

## Requirements

- Python 3.7+
- pandas
- openpyxl
- qrcode
- Pillow

## Installation

```bash
pip install pandas openpyxl qrcode[pil]
```

## Usage

```bash
python warehouse_system.py
```

## How It Works

1. **PUT** - Stage items for warehousing
2. **Manage Staging** - Review/remove staged items before committing
3. **PUT WAREHOUSE** - Commit all staged items at once to the database
4. **PULL** - Remove items from warehouse
5. **UPDATE** - Modify item details (hostname, shelf, remarks)
6. **DELETE** - Delete items and associated QR codes

## Data Storage

- `warehouse.xlsx` - Contains items and shelves data with two sheets:
  - `items` - Individual items with QR codes, hostname, shelf, remarks, date
  - `shelves` - Available shelves with status (AVAILABLE/FULL)
- `qr_codes/` - Generated QR code images organized by hostname

## Key Features Explained

### Staging System
- Items are not immediately added to warehouse
- Stage multiple items and review before final commit
- Prevents duplicate hostnames in both warehouse and staging queue
- Manage staged items (remove specific items or clear all)

### Duplicate Prevention
- Blocks adding items with hostnames that already exist in warehouse
- Prevents duplicate staging of same hostname
- Prevents updating items to duplicate hostnames

### Shelf Management
- Add/remove custom shelves
- Mark shelves as FULL to prevent new item assignments
- Track when shelves were marked as FULL

## License

This project is licensed under a Proprietary License with Internal Use Grant.
All code is the copyright property of Mark Benjamin H. Acob.
See [LICENSE](LICENSE) file for full terms.

**Authorized internal use only** - redistribution and public redistribution are prohibited.

## Author

Mark Benjamin H. Acob - Adventus System
