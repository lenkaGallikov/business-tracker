import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar
import os

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin"
DB_PATH = "data/restaurant_tracker.db"
os.makedirs("data", exist_ok=True)

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS financials 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, category TEXT, 
                      item_name TEXT, quantity INTEGER, base_amount REAL, tax_amount REAL, net_amount REAL, 
                      status TEXT, original_order_id INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS employees 
                     (name TEXT PRIMARY KEY, hourly_rate REAL, ot_multiplier REAL, standard_hours REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, date TEXT, clock_in TEXT, clock_out TEXT, 
                      reg_hours REAL, ot_hours REAL, total_hours REAL, is_late TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS salary_payouts 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, employee_name TEXT, hours_covered REAL, amount_paid REAL, system_calculated REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS menu 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, course_type TEXT, item_name TEXT, price REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rota 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, date TEXT, start_time TEXT, allocated_hours REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS daily_budget 
                     (date TEXT PRIMARY KEY, wage_budget REAL)''')
        conn.commit()

init_db()

def run_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="EPOS Restaurant Hub", layout="wide")
st.title("🍳 Restaurant EPOS Engine, Rota Planner & Analytics")

if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

def check_admin_access():
    if not st.session_state["admin_authenticated"]:
        st.subheader("🔒 Admin Access Required")
        entered_password = st.text_input("Enter Master Admin Password", type="password", key=f"global_admin_pwd_{st.session_state.get('current_tab', 'default')}")
        if st.button("Unlock Management Tabs", key=f"global_admin_btn_{st.session_state.get('current_tab', 'default')}"):
            if entered_password == ADMIN_PASSWORD:
                st.session_state["admin_authenticated"] = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Incorrect Password. Access Denied.")
        return False
    return True

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧾 Log Sales & Ops (Public Floor Till)",
    "⏰ Clock, Rota & Staff Setup", 
    "📊 Menu & Budgets", 
    "💷 Payroll Auditor", 
    "📈 Performance Analytics"
])

MENU_CATEGORIES = [
    "Starters", "Chef Specials", "Burgers", "Sizzlers", "Wagyu X", "Premium Cuts", "Salads", "Sides", 
    "Mocktails", "Cold drinks", "Gourmet drinks", "Desserts"
]

# --- TAB 1: LOG SALES & OPERATIONS ---
with tab1:
    st.session_state["current_tab"] = "sales"
    st.header("Restaurant Order Processing & EPOS Tills")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Register Ticket Item")
        op_group = st.selectbox("Transaction Group Type", ["Sale", "Expense", "Void", "Customer Complaint (Replacement)"])
        tax_rate = st.number_input("Tax Rate / VAT Percentage (%)", min_value=0.0, value=20.0, step=1.0) / 100.0
        
        if op_group in ["Sale", "Void", "Customer Complaint (Replacement)"]:
            orig_id = None
            if op_group == "Customer Complaint (Replacement)":
                orig_id = st.number_input("Original Order Ticket ID to Link", min_value=1, step=1, help="Enter the ID from your sales history ledger to map this loss.")
                
            sel_course = st.selectbox("Course Catalog Group", MENU_CATEGORIES)
            menu_df = run_query("SELECT item_name, price FROM menu WHERE course_type=?", (sel_course,))
            
            if menu_df.empty:
                st.error(f"⚠️ No items found under '{sel_course}'. Please log into the '📊 Menu & Budgets' tab to add your products first.")
            else:
                sel_item = st.selectbox("Menu Item Select", menu_df['item_name'].tolist())
                item_unit_price = float(menu_df[menu_df['item_name'] == sel_item]['price'].values[0])
                qty = st.number_input("Quantity Ordered/Replaced", min_value=1, value=1, step=1)
                
                discount_type = st.selectbox("Apply Order Discount", ["None", "Student (10%)", "BlueLight (20%)", "Custom Custom Amount"])
                disc_pct = 0.0
                if discount_type == "Student (10%)": disc_pct = 0.10
                elif discount_type == "BlueLight (20%)": disc_pct = 0.20
                
                custom_disc = 0.0
                if discount_type == "Custom Custom Amount":
                    custom_disc = st.number_input("Custom Discount Value (£)", min_value=0.0, value=0.0)
                
                base_calc = (item_unit_price * qty) * (1.0 - disc_pct) - custom_disc
                base_calc = max(0.0, base_calc)
                
                if op_group == "Void": 
                    base_calc = 0.0  
                elif op_group == "Customer Complaint (Replacement)": 
                    base_calc = -(item_unit_price * qty * 0.30) 
                
                calculated_tax = base_calc * tax_rate if op_group == "Sale" else 0.0
                final_net = base_calc - calculated_tax if op_group == "Sale" else base_calc
                
                st.warning(f"Estimated Impact Level: Gross Impact: £{base_calc:.2f} | Tax: £{calculated_tax:.2f} | Net: £{final_net:.2f}")
                
                if st.button("Post Ticket Entry"):
                    t_date = st.date_input("Execution Date", datetime.today(), key="exec_date_btn")
                    execute_db("""INSERT INTO financials (date, type, category, item_name, quantity, base_amount, tax_amount, net_amount, status, original_order_id) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (t_date.strftime("%Y-%m-%d"), op_group, sel_course, sel_item, qty, base_calc, calculated_tax, final_net, discount_type, orig_id))
                    st.success("Ticket Entry posted successfully.")
                    st.rerun()
        else:
            # UPDATED: Added "Interior Decoration" directly to the options array list here
            exp_cat = st.selectbox("Operating Expense Description", [
                "Food/Ingredient Inventory", 
                "Beverage Supplies", 
                "Kitchen Equipment", 
                "Rent & Lease", 
                "Electricity & Gas", 
                "Water Utility",
                "Interior Decoration"
            ])
            exp_amt = st.number_input("Value Amount Paid Out (£)", min_value=0.0)
            if st.button("Log Operational Expense"):
                t_date = st.date_input("Execution Date", datetime.today(), key="exp_date_btn")
                execute_db("INSERT INTO financials (date, type, category, base_amount, tax_amount, net_amount, status, original_order_id) VALUES (?, 'Expense', ?, ?, 0, ?, 'Standard', NULL)",
                           (t_date.strftime("%Y-%m-%d"), exp_cat, -exp_amt, -exp_amt))
                st.success("Expense logged.")
                st.rerun()

    with col2:
        st.subheader("Live Operational Entry Stream (Today)")
        st.caption("Tip: Use the leftmost 'id' column number as your Original Order ID reference.")
        st.dataframe(run_query("SELECT id, date as Date, type as Type, category as Category, item_name as Item, base_amount as 'Cost/Rev (£)' FROM financials ORDER BY id DESC LIMIT 15"), use_container_width=True)

# --- TAB 2: CLOCK, ROTA & STAFF SETUP ---
with tab2:
    st.session_state["current_tab"] = "clock"
    if check_admin_access():
        st.header("Weekly Rota & Attendance Desk")
        st.subheader("👥 Employee Master Roster Profiles")
        col_emp1, col_emp2 = st.columns([1, 2])
        with col_emp1:
            st.write("**Add / Update Staff Member**")
            e_name = st.text_input("Full Name (Unique)", placeholder="e.g. John Doe").strip()
            e_rate = st.number_input("Standard Hourly Rate (£/hr)", min_value=0.0, value=11.44, step=0.5)
            e_std = st.number_input("Standard Shift Length Max (Hours)", min_value=1.0, value=8.0, step=0.5)
            e_ot = st.number_input("Overtime Multiplier", min_value=1.0, value=1.5, step=0.1)
            
            if st.button("Save Staff Profile"):
                if e_name:
                    execute_db("""INSERT INTO employees (name, hourly_rate, ot_multiplier, standard_hours) 
                                  VALUES (?, ?, ?, ?) 
                                  ON CONFLICT(name) DO UPDATE SET 
                                  hourly_rate=excluded.hourly_rate, 
                                  ot_multiplier=excluded.ot_multiplier, 
                                  standard_hours=excluded.standard_hours""", 
                               (e_name, e_rate, e_ot, e_std))
                    st.success(f"Profile saved for {e_name}!")
                    st.rerun()
                else:
                    st.error("Please enter a name.")
        with col_emp2:
            st.write("**Active Roster Records**")
            df_emp = run_query("SELECT name as 'Employee Name', hourly_rate as 'Base Rate (£/hr)', standard_hours as 'Regular Shift Max (Hrs)', ot_multiplier as 'OT Rate' FROM employees")
            st.dataframe(df_emp, use_container_width=True)
            
        st.write("---")
        col1, col2 = st.columns([1.2, 2])
        emp_profiles = run_query("SELECT name FROM employees")['name'].tolist()
        
        with col1:
            st.subheader("📅 Schedule a Staff Shift (Rota)")
            if not emp_profiles:
                st.info("ℹ️ Create an employee profile above first to enable scheduling selections.")
            else:
                r_name = st.selectbox("Staff Member", emp_profiles, key="rota_name")
                r_date = st.date_input("Shift Date", datetime.today(), key="rota_date")
                r_start = st.time_input("Scheduled Start Time", datetime.strptime("17:00", "%H:%M").time())
                r_hours = st.number_input("Allocated Hours", min_value=0.5, max_value=16.0, value=8.0, step=0.5)
                if st.button("Publish to Rota"):
                    execute_db("INSERT INTO rota (employee_name, date, start_time, allocated_hours) VALUES (?, ?, ?, ?)",
                               (r_name, r_date.strftime("%Y-%m-%d"), r_start.strftime("%H:%M"), r_hours))
                    st.success(f"Shift published for {r_name} on {r_date}")
            
            st.write("---")
            st.subheader("⏱️ Live Punch Clock")
            if not emp_profiles:
                st.info("ℹ️ Attendance tools unlock once employee roster lines exist.")
            else:
                p_name = st.selectbox("Employee Select", emp_profiles, key="punch_name")
                p_action = st.radio("Punch", ["Clock In", "Clock Out"])
                if st.button("Submit Time Punch"):
                    t_str = datetime.today().strftime("%Y-%m-%d")
                    n_str = datetime.now().strftime("%H:%M:%S")
                    if p_action == "Clock In":
                        sched = run_query("SELECT start_time FROM rota WHERE employee_name=? AND date=?", (p_name, t_str))
                        is_late = "No"
                        if not sched.empty:
                            sched_time = datetime.strptime(f"{t_str} {sched.iloc[0]['start_time']}:00", "%Y-%m-%d %H:%M:%S")
                            if datetime.now() > sched_time + timedelta(minutes=15): is_late = "Yes"
                        execute_db("INSERT INTO attendance (employee_name, date, clock_in, is_late) VALUES (?, ?, ?, ?)", (p_name, t_str, n_str, is_late))
                        st.success(f"Clocked IN. Lateness flagged: {is_late}")
                    else:
                        active = run_query("SELECT id, clock_in FROM attendance WHERE employee_name=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1", (p_name,))
                        if active.empty: st.error("No active shift setup found for this user.")
                        else:
                            t_in = datetime.strptime(active.iloc[0]['clock_in'], "%H:%M:%S")
                            t_out = datetime.strptime(n_str, "%H:%M:%S")
                            tot_h = max(0.1, (t_out - t_in).total_seconds() / 3600.0)
                            execute_db("UPDATE attendance SET clock_out=?, reg_hours=?, ot_hours=0, total_hours=? WHERE id=?", (n_str, round(tot_h, 2), round(tot_h, 2), int(active.iloc[0]['id'])))
                            st.success(f"Clocked OUT. Total hours: {tot_h:.2f}")
                            st.rerun()

        with col2:
            st.subheader("📋 Current Weekly Rota Blueprint")
            st.dataframe(run_query("SELECT date as Date, employee_name as Staff, start_time as 'Start Time', allocated_hours as 'Allocated Hrs' FROM rota ORDER BY date DESC"), use_container_width=True)
            st.subheader("🟢 Active Floor Shifts & Lateness Log")
            st.dataframe(run_query("SELECT date as Date, employee_name as Staff, clock_in as 'In', clock_out as 'Out', total_hours as 'Hours', is_late as 'Late?' FROM attendance ORDER BY id DESC LIMIT 10"), use_container_width=True)

# --- TAB 3: MENU & BUDGETS (ADMIN) ---
with tab3:
    st.session_state["current_tab"] = "menu"
    if check_admin_access():
        st.header("Global Configuration: Menus & Daily Wage Budgets")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🍴 Live Menu Management System")
            m_course = st.selectbox("Category Classification", MENU_CATEGORIES, key="menu_cat_mgr")
            m_name = st.text_input("New Item Title Name").strip()
            m_price = st.number_input("Base Selling Value Price (£)", min_value=0.0, value=5.0)
            
            if st.button("Save New Menu Item"):
                if m_name:
                    execute_db("INSERT INTO menu (course_type, item_name, price) VALUES (?, ?, ?)", (m_course, m_name, m_price))
                    st.success(f"Added {m_name} to menu.")
                    st.rerun()
                    
            st.write("---")
            st.caption("Active Menu Listings (Select to Delete)")
            all_menu = run_query("SELECT id, course_type as Category, item_name as Name, price as 'Price (£)' FROM menu ORDER BY course_type ASC")
            if not all_menu.empty:
                st.dataframe(all_menu, use_container_width=True)
                del_id = st.number_input("Enter Menu ID number to erase", min_value=1, step=1)
                if st.button("Delete Selected Menu Item", type="secondary"):
                    execute_db("DELETE FROM menu WHERE id=?", (del_id,))
                    st.success("Item removed from system index.")
                    st.rerun()

        with col2:
            st.subheader("💰 Daily Wage Cap Controls & Labor Budgets")
            b_date = st.date_input("Target Allocation Date", datetime.today())
            b_budget = st.number_input("Target Daily Wage Cap Allowance (£)", min_value=0.0, value=200.0)
            if st.button("Save Wage Budget Limit"):
                execute_db("INSERT INTO daily_budget (date, wage_budget) VALUES (?, ?) ON CONFLICT(date) DO UPDATE SET wage_budget=excluded.wage_budget",
                           (b_date.strftime("%Y-%m-%d"), b_budget))
                st.success(f"Budget for {b_date} updated.")
                
            st.write("---")
            st.subheader("Daily Budget Financial Performance Tracker")
            b_logs = run_query("SELECT date as Date, wage_budget as 'Budget Limit (£)' FROM daily_budget ORDER BY date DESC LIMIT 10")
            st.dataframe(b_logs, use_container_width=True)

# --- TAB 4: PAYROLL AUDITOR (ADMIN) ---
with tab4:
    st.session_state["current_tab"] = "payroll"
    if check_admin_access():
        st.header("Automated Salary Calculator & Wage Disbursement")
        col1, col2 = st.columns([1, 1.5])
        emp_profiles = run_query("SELECT name FROM employees")['name'].tolist()
        
        with col1:
            st.subheader("Process Shift Payroll")
            if not emp_profiles:
                st.info("⚠️ Please add staff profiles in the 'Clock & Rota' setup area first.")
            else:
                pay_name = st.selectbox("Staff Target Member", emp_profiles, key="payout_sb")
                pay_date = st.date_input("Work Date Target to Settle", datetime.today())
                p_date_str = pay_date.strftime("%Y-%m-%d")
                
                prof = run_query("SELECT hourly_rate, ot_multiplier FROM employees WHERE name=?", (pay_name,))
                shifts = run_query("SELECT SUM(reg_hours) as reg, is_late FROM attendance WHERE employee_name=? AND date=?", (pay_name, p_date_str))
                
                base_rate = float(prof.iloc[0]['hourly_rate']) if not prof.empty else 0.0
                tracked_reg = float(shifts.iloc[0]['reg']) if not shifts.empty and shifts.iloc[0]['reg'] is not None else 0.0
                is_late_flag = shifts.iloc[0]['is_late'] if not shifts.empty else "No"
                
                system_earnings = tracked_reg * base_rate
                
                st.info(f"""
                **Payroll Analysis for {pay_name} on {p_date_str}:**
                * Total Hours Logged: {tracked_reg:.2f} Hours
                * Marked Late Today?: **{is_late_flag}**
                * **Suggested System Earnings: £{system_earnings:.2f}**
                """)
                
                pay_amount = st.number_input("Actual Amount Disbursed Out (£)", min_value=0.0, value=round(system_earnings, 2))
                if st.button("Log & Settle Payout"):
                    execute_db("INSERT INTO salary_payouts (date, employee_name, hours_covered, amount_paid, system_calculated) VALUES (?, ?, ?, ?, ?)",
                               (p_date_str, pay_name, tracked_reg, pay_amount, system_earnings))
                    execute_db("INSERT INTO financials (date, type, category, base_amount, tax_amount, net_amount, status, original_order_id) VALUES (?, 'Salary Paid', 'Labor Cost', ?, 0, ?, 'Standard', NULL)",
                               (p_date_str, -pay_amount, -pay_amount))
                    st.success("Payroll transaction cleared.")
                    st.rerun()

        with col2:
            st.subheader("Payroll Audits & Historic Records")
            st.dataframe(run_query("SELECT date as Date, employee_name as Staff, hours_covered as Hours, system_calculated as 'Expected (£)', amount_paid as 'Paid (£)' FROM salary_payouts ORDER BY id DESC"), use_container_width=True)

# --- TAB 5: PERFORMANCE ANALYTICS (ADMIN) ---
with tab5:
    st.session_state["current_tab"] = "analytics"
    if check_admin_access():
        st.header("Executive Restaurant Profit Analytics & Product Audits")
        
        years = [2026, 2027, 2025]
        months = list(calendar.month_name)[1:]
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1: sel_m = st.selectbox("Primary Analysis Month", months, index=datetime.today().month - 1)
        with col_sel2: sel_y = st.selectbox("Primary Analysis Year", years, index=0)
        
        m_num = months.index(sel_m) + 1
        m_prefix = f"{sel_y}-{m_num:02d}"
        
        f_df = run_query("SELECT * FROM financials WHERE date LIKE ?", (f"{m_prefix}%",))
        
        st.subheader(f"📊 Business Dashboard: Overview for {sel_m} {sel_y}")
        if f_df.empty:
            st.info("No sales or expense metrics found for this period.")
        else:
            gross_sales = f_df[f_df['type'] == 'Sale']['base_amount'].sum()
            collected_tax = f_df[f_df['type'] == 'Sale']['tax_amount'].sum()
            
            ops_expenses = abs(f_df[f_df['type'] == 'Expense']['base_amount'].sum())
            complaints_cost = abs(f_df[f_df['type'] == 'Customer Complaint (Replacement)']['base_amount'].sum())
            labor_paid = abs(f_df[f_df['type'] == 'Salary Paid']['base_amount'].sum())
            
            total_profit = gross_sales - collected_tax - ops_expenses - complaints_cost - labor_paid
            
            budget_df = run_query("SELECT SUM(wage_budget) as allowed FROM daily_budget WHERE date LIKE ?", (f"{m_prefix}%",))
            allowed_wage_budget = float(budget_df.iloc[0]['allowed']) if not budget_df.empty and budget_df.iloc[0]['allowed'] is not None else 0.0
            remaining_wage_budget = max(0.0, allowed_wage_budget - labor_paid)
            
            final_adjusted_profit = total_profit + remaining_wage_budget

            # Metrics
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric("Gross Revenue (Total Sale)", f"£{gross_sales:,.2f}")
            c_m2.metric("Collected VAT Tax", f"£{collected_tax:,.2f}")
            c_m3.metric("Labor & Ops Costs", f"£{(ops_expenses + labor_paid + complaints_cost):,.2f}")
            c_m4.metric("Adjusted Net Profit", f"£{final_adjusted_profit:,.2f}", delta=f"£{remaining_wage_budget:.2f} Unspent Labor Savings Included")
            
            # Complaints Audit Section
            st.write("---")
            st.subheader("🚨 Month-End Customer Complaint Cost Audit")
            complaints_df = f_df[f_df['type'] == 'Customer Complaint (Replacement)']
            if not complaints_df.empty:
                st.dataframe(complaints_df[['date', 'original_order_id', 'item_name', 'quantity', 'base_amount']].rename(
                    columns={'date':'Date', 'original_order_id':'Original Ticket ID', 'item_name':'Item Name', 'quantity':'Qty', 'base_amount':'Wasted Cost Hit (£)'}
                ), use_container_width=True)
            else:
                st.info("Excellent! No food replacement complaints recorded this month.")

            st.write("---")
            st.subheader("📦 Product Sales Volume Count Report")
            v_df = f_df[f_df['type'] == 'Sale'].groupby(['category', 'item_name'])['quantity'].sum().reset_index()
            v_df.columns = ['Product Group', 'Item Name', 'Units Sold Count']
            st.dataframe(v_df.sort_values(by='Units Sold Count', ascending=False), use_container_width=True)

        st.write("---")
        st.subheader("📈 Multi-Month Performance Comparison Engines")
        
        comp_m = st.multiselect("Select Target Months to Compare Side-by-Side", months, default=["February", "March", "April", "May", "June"])
        if comp_m:
            comp_data = []
            for cm in comp_m:
                cm_num = months.index(cm) + 1
                cm_pref = f"{sel_y}-{cm_num:02d}"
                cm_df = run_query("SELECT item_name, quantity, type FROM financials WHERE date LIKE ?", (f"{cm_pref}%",))
                
                if not cm_df.empty:
                    sales_cm = cm_df[cm_df['type'] == 'Sale']
                    if not sales_cm.empty:
                        top_performer = sales_cm.groupby('item_name')['quantity'].sum().idxmax()
                        top_units = sales_cm.groupby('item_name')['quantity'].sum().max()
                        worst_performer = sales_cm.groupby('item_name')['quantity'].sum().idxmin()
                        worst_units = sales_cm.groupby('item_name')['quantity'].sum().min()
                        
                        comp_data.append({
                            "Month Evaluated": cm,
                            "Top Selling Menu Item": top_performer,
                            "Top Units Volume": int(top_units),
                            "Lowest Selling Menu Item": worst_performer,
                            "Lowest Units Volume": int(worst_units)
                        })
            if comp_data:
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True)