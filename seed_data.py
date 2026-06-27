import sqlite3
import os
from datetime import datetime

DB_PATH = "data/restaurant_tracker.db"
os.makedirs("data", exist_ok=True)

def seed_everything():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Wipe tables clean to prevent schema collision
    tables = ["financials", "employees", "attendance", "salary_payouts", "menu", "rota", "daily_budget"]
    for t in tables: 
        c.execute(f"DROP TABLE IF EXISTS {t}")
    
    # Re-initialize fresh tables matching updated app.py parameters
    c.execute('''CREATE TABLE financials 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, category TEXT, 
                  item_name TEXT, quantity INTEGER, base_amount REAL, tax_amount REAL, net_amount REAL, 
                  status TEXT, original_order_id INTEGER)''')
    c.execute('''CREATE TABLE employees 
                 (name TEXT PRIMARY KEY, hourly_rate REAL, ot_multiplier REAL, standard_hours REAL)''')
    c.execute('''CREATE TABLE attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, date TEXT, clock_in TEXT, clock_out TEXT, reg_hours REAL, ot_hours REAL, total_hours REAL, is_late TEXT)''')
    c.execute('''CREATE TABLE salary_payouts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, employee_name TEXT, hours_covered REAL, amount_paid REAL, system_calculated REAL)''')
    c.execute('''CREATE TABLE menu (id INTEGER PRIMARY KEY AUTOINCREMENT, course_type TEXT, item_name TEXT, price REAL)''')
    c.execute('''CREATE TABLE rota (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, date TEXT, start_time TEXT, allocated_hours REAL)''')
    c.execute('''CREATE TABLE daily_budget (date TEXT PRIMARY KEY, wage_budget REAL)''')

    print("🧹 Database wiped. Instantiating fresh datasets for all tabs...")

    # --- 1. SEED LIVE MENU & BUDGET MANAGERS ---
    menu_items = [
        ("Starters", "Calamari Strips", 7.50),
        ("Starters", "Sticky BBQ Wings", 6.50),
        ("Chef Specials", "Pan-Seared Sea Bass", 22.00),
        ("Burgers", "Classic Cheese Burger", 13.50),
        ("Burgers", "Buttermilk Chicken Burger", 14.00),
        ("Sizzlers", "Sizzling Steak Fajitas", 18.50),
        ("Wagyu X", "A5 Grade Wagyu Sirloin 8oz", 65.00),
        ("Premium Cuts", "Tomahawk Ribeye 32oz", 75.00),
        ("Salads", "Grilled Chicken Caesar", 12.00),
        ("Sides", "Truffle Parmesan Fries", 4.50),
        ("Sides", "Sweet Potato Fries", 4.00),
        ("Mocktails", "Virgin Mojito", 5.50),
        ("Cold drinks", "Coca Cola 330ml", 3.00),
        ("Gourmet drinks", "Smoked Saffron Iced Chai", 6.50),
        ("Desserts", "Chocolate Lava Fondant", 7.00)
    ]
    c.executemany("INSERT INTO menu (course_type, item_name, price) VALUES (?, ?, ?)", menu_items)
    
    employees = [
        ("Alice Smith", 11.44, 1.5, 8.0),
        ("Bob Jones", 12.50, 1.5, 8.0),
        ("Charlie Green", 14.00, 1.5, 8.0)
    ]
    c.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", employees)

    # --- 2. SEED ACTIVE WORKFLOW DATA (TODAY) ---
    today_str = datetime.today().strftime("%Y-%m-%d")
    c.execute("INSERT OR REPLACE INTO daily_budget VALUES (?, 250.00)", (today_str,))
    
    rota_shifts = [
        ("Alice Smith", today_str, "16:00", 8.0),
        ("Bob Jones", today_str, "17:00", 8.0),
        ("Charlie Green", today_str, "12:00", 6.0)
    ]
    c.executemany("INSERT INTO rota (employee_name, date, start_time, allocated_hours) VALUES (?, ?, ?, ?)", rota_shifts)

    attendance_today = [
        ("Charlie Green", today_str, "12:00:00", "18:00:00", 6.0, 0.0, 6.0, "No"),
        ("Alice Smith", today_str, "16:02:00", None, None, None, None, "No"),
        ("Bob Jones", today_str, "17:45:22", None, None, None, None, "Yes")
    ]
    c.executemany("INSERT INTO attendance (employee_name, date, clock_in, clock_out, reg_hours, ot_hours, total_hours, is_late) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", attendance_today)

    c.execute("INSERT INTO salary_payouts (date, employee_name, hours_covered, amount_paid, system_calculated) VALUES (?, 'Charlie Green', 6.0, 84.00, 84.00)", (today_str,))
    
    today_till_entries = [
        (today_str, "Sale", "Wagyu X", "A5 Grade Wagyu Sirloin 8oz", 2, 130.00, 26.00, 104.00, "None", None),
        (today_str, "Sale", "Premium Cuts", "Tomahawk Ribeye 32oz", 1, 75.00, 15.00, 60.00, "None", None),
        (today_str, "Sale", "Sides", "Truffle Parmesan Fries", 4, 18.00, 3.60, 14.40, "None", None),
        (today_str, "Salary Paid", "Labor Cost", None, 1, -84.00, 0.0, -84.00, "Standard", None)
    ]
    c.executemany("INSERT INTO financials (date, type, category, item_name, quantity, base_amount, tax_amount, net_amount, status, original_order_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", today_till_entries)

    # --- 3. SEED 5-MONTH HISTORICAL SIMULATION ---
    months_simulation_data = [
        ("2026-02", "Classic Cheese Burger", 110, "Calamari Strips", 12, 3500.00, 450.00),
        ("2026-03", "Pan-Seared Sea Bass", 95, "Smoked Saffron Iced Chai", 18, 4200.00, 500.00),
        ("2026-04", "Tomahawk Ribeye 32oz", 45, "Chocolate Lava Fondant", 14, 5100.00, 480.00),
        ("2026-05", "A5 Grade Wagyu Sirloin 8oz", 60, "Classic Cheese Burger", 22, 6800.00, 520.00),
        ("2026-06", "Tomahawk Ribeye 32oz", 80, "Truffle Parmesan Fries", 30, 7900.00, 600.00)
    ]

    for prefix, top_item, top_q, worst_item, worst_q, gross, labor in months_simulation_data:
        for day in range(1, 29):
            # FIXED HERE: Use INSERT OR REPLACE to avoid day-clashing conflicts
            c.execute("INSERT OR REPLACE INTO daily_budget VALUES (?, 250.00)", (f"{prefix}-{day:02d}",))
            
        c.execute("""INSERT INTO financials (date, type, category, item_name, quantity, base_amount, tax_amount, net_amount, status, original_order_id) 
                     VALUES (?, 'Sale', 'Main', ?, ?, ?, ?, ?, 'None', NULL)""",
                  (f"{prefix}-10", top_item, top_q, gross*0.6, (gross*0.6)*0.2, (gross*0.6)*0.8))
        
        last_order_id = c.lastrowid
        
        c.execute("""INSERT INTO financials (date, type, category, item_name, quantity, base_amount, tax_amount, net_amount, status, original_order_id) 
                     VALUES (?, 'Sale', 'Sides', ?, ?, ?, ?, ?, 'None', NULL)""",
                  (f"{prefix}-15", worst_item, worst_q, gross*0.4, (gross*0.4)*0.2, (gross*0.4)*0.8))

        c.execute("""INSERT INTO financials (date, type, category, item_name, quantity, base_amount, tax_amount, net_amount, status, original_order_id) 
                     VALUES (?, 'Customer Complaint (Replacement)', 'Main', ?, 1, -5.00, 0, -5.00, 'None', ?)""",
                  (f"{prefix}-12", top_item, last_order_id))

        c.execute("INSERT INTO financials (date, type, category, base_amount, tax_amount, net_amount, status, original_order_id) VALUES (?, 'Expense', 'Fixed Operations', ?, 0, ?, 'Standard', NULL)",
                  (f"{prefix}-01", -800.00, -800.00))

        c.execute("INSERT INTO financials (date, type, category, base_amount, tax_amount, net_amount, status, original_order_id) VALUES (?, 'Salary Paid', 'Labor Cost', ?, 0, ?, 'Standard', NULL)",
                  (f"{prefix}-25", -labor, -labor))
        
        c.execute("""INSERT INTO salary_payouts (date, employee_name, hours_covered, amount_paid, system_calculated) 
                     VALUES (?, 'Alice Smith', 40.0, ?, ?)""",
                  (f"{prefix}-25", labor, labor))

    conn.commit()
    conn.close()
    print("🚀 SUCCESS! Master data injected. All real-time tabs and historical analytics are now full.")

if __name__ == "__main__":
    seed_everything()