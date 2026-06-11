import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar
import os

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin"  # Change this to your preferred secure password
DB_PATH = "data/restaurant_tracker.db"
os.makedirs("data", exist_ok=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS financials 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, type TEXT, category TEXT, amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS employees 
                 (name TEXT PRIMARY KEY, hourly_rate REAL, ot_multiplier REAL, standard_hours REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, date TEXT, clock_in TEXT, clock_out TEXT, reg_hours REAL, ot_hours REAL, total_hours REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS salary_payouts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, employee_name TEXT, hours_covered REAL, amount_paid REAL, system_calculated REAL)''')
    conn.commit()
    conn.close()

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
st.set_page_config(page_title="Restaurant Management Hub", layout="wide")
st.title("🍳 Restaurant Command Center & Wage Auditor")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⏰ Daily Punch Clock", 
    "💷 Daily Salary Payouts", 
    "🧾 Log Sales & Expenses", 
    "📈 Monthly Profit & Loss",
    "👥 Employee Roster Setup"
])

# --- TAB 5: EMPLOYEE ROSTER SETUP ---
with tab5:
    st.header("Manage Staff Profiles & Wage Rules")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Add/Update Employee")
        e_name = st.text_input("Full Name", placeholder="e.g. John Doe").strip()
        e_rate = st.number_input("Standard Hourly Rate (£/hr)", min_value=0.0, value=11.44, step=0.5)
        e_std = st.number_input("Standard Shift Length (Hours before OT starts)", min_value=1.0, value=8.0, step=0.5)
        e_ot = st.number_input("Overtime Multiplier (e.g. 1.5 for Time-and-a-half)", min_value=1.0, value=1.5, step=0.1)
        
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
                
    with col2:
        st.subheader("Current Active Profiles")
        df_emp = run_query("SELECT name as 'Employee Name', hourly_rate as 'Base Rate (£/hr)', standard_hours as 'Regular Shift Max (Hrs)', ot_multiplier as 'OT Rate' FROM employees")
        st.dataframe(df_emp, use_container_width=True)

# --- TAB 1: DAILY PUNCH CLOCK ---
with tab1:
    st.header("Shift Attendance Punch Clock")
    col1, col2 = st.columns(2)
    
    emp_profiles = run_query("SELECT name FROM employees")['name'].tolist()
    
    with col1:
        st.subheader("Staff Live Punch Clock")
        if not emp_profiles:
            st.warning("⚠️ Please add employees in the 'Employee Roster Setup' tab first before clocking in.")
        else:
            p_name = st.selectbox("Select Employee", emp_profiles, key="punch_name")
            p_action = st.radio("Punch Type", ["Clock In", "Clock Out"])
            
            if st.button("Submit Time Punch"):
                today_str = datetime.today().strftime("%Y-%m-%d")
                now_str = datetime.now().strftime("%H:%M:%S")
                
                if p_action == "Clock In":
                    check = run_query("SELECT * FROM attendance WHERE employee_name=? AND clock_out IS NULL", (p_name,))
                    if not check.empty:
                        st.warning(f"⚠️ {p_name} is already clocked in!")
                    else:
                        execute_db("INSERT INTO attendance (employee_name, date, clock_in) VALUES (?, ?, ?)", (p_name, today_str, now_str))
                        st.success(f"✅ {p_name} clocked IN at {now_str}")
                        st.rerun()
                        
                elif p_action == "Clock Out":
                    active = run_query("SELECT id, clock_in FROM attendance WHERE employee_name=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1", (p_name,))
                    if active.empty:
                        st.error(f"❌ No active clock-in found for {p_name}.")
                    else:
                        row_id = int(active.iloc[0]['id'])
                        in_time_str = active.iloc[0]['clock_in']
                        
                        fmt = "%H:%M:%S"
                        t_in = datetime.strptime(in_time_str, fmt)
                        t_out = datetime.strptime(now_str, fmt)
                        if t_out < t_in: t_out += timedelta(days=1)
                        
                        total_hours = (t_out - t_in).total_seconds() / 3600.0
                        
                        rules = run_query("SELECT standard_hours FROM employees WHERE name=?", (p_name,))
                        std_limit = float(rules.iloc[0]['standard_hours']) if not rules.empty else 8.0
                        
                        if total_hours > std_limit:
                            reg_h = std_limit
                            ot_h = total_hours - std_limit
                        else:
                            reg_h = total_hours
                            ot_h = 0.0
                            
                        execute_db("""UPDATE attendance SET clock_out=?, reg_hours=?, ot_hours=?, total_hours=? 
                                      WHERE id=?""", (now_str, round(reg_h, 2), round(ot_h, 2), round(total_hours, 2), row_id))
                        st.success(f"🏁 {p_name} clocked OUT at {now_str}. Regular: {reg_h:.2f} hrs, Overtime: {ot_h:.2f} hrs.")
                        st.rerun()

        st.write("---")
        
        # --- ADMIN OVERRIDE SECTION ---
        st.subheader("🔑 Admin Manual Hours Entry")
        admin_pass = st.text_input("Enter Admin Password", type="password")
        
        if admin_pass == ADMIN_PASSWORD:
            st.success("Access Granted: Admin Mode Active")
            
            # Show persisting success/error status message if it exists in session memory
            if "admin_message" in st.session_state:
                st.info(st.session_state["admin_message"])
                # Clear it so it won't permanently stick around if they change tabs later
                del st.session_state["admin_message"]
                
            if not emp_profiles:
                st.info("No employee configurations available.")
            else:
                m_name = st.selectbox("Add Hours For", emp_profiles, key="admin_name")
                m_date = st.date_input("Date of Shift", datetime.today(), key="admin_date")
                m_reg = st.number_input("Regular Hours Worked", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
                m_ot = st.number_input("Overtime Hours Worked", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
                m_total = m_reg + m_ot
                
                if st.button("Apply Manual Shift Logs", type="primary"):
                    date_str = m_date.strftime("%Y-%m-%d")
                    
                    try:
                        # Database operation validation check
                        execute_db("""INSERT INTO attendance (employee_name, date, clock_in, clock_out, reg_hours, ot_hours, total_hours) 
                                      VALUES (?, ?, 'MANUAL', 'MANUAL', ?, ?, ?)""", 
                                   (m_name, date_str, round(m_reg, 2), round(m_ot, 2), round(m_total, 2)))
                        
                        # Store structural message into state session
                        st.session_state["admin_message"] = f"💾 SUCCESS: Saved manual entry for {m_name} on {date_str}. Total logged: {m_total:.2f} Hours ({m_reg:.2f} Regular, {m_ot:.2f} Overtime)."
                    except Exception as e:
                        st.session_state["admin_message"] = f"❌ FAILED to write logs to database. Error details: {str(e)}"
                    
                    st.rerun()
        elif admin_pass != "":
            st.error("Incorrect Password. Access Denied.")

    with col2:
        st.subheader("Currently Working Shifts")
        active_shifts = run_query("SELECT employee_name as 'Employee', date as 'Date Started', clock_in as 'Clocked In At' FROM attendance WHERE clock_out IS NULL")
        st.dataframe(active_shifts, use_container_width=True)

# --- TAB 2: DAILY SALARY PAYOUTS ---
with tab2:
    st.header("Daily Wage Automated Calculator & Disbursement")
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("Calculate & Record Payroll")
        if not emp_profiles:
            st.info("Add employees to record salary payouts.")
        else:
            pay_name = st.selectbox("Pay To Employee", emp_profiles, key="pay_name_sb")
            pay_date = st.date_input("Target Work Date to Pay", datetime.today())
            pay_date_str = pay_date.strftime("%Y-%m-%d")
            
            prof = run_query("SELECT hourly_rate, ot_multiplier FROM employees WHERE name=?", (pay_name,))
            shifts = run_query("SELECT SUM(reg_hours) as reg, SUM(ot_hours) as ot, SUM(total_hours) as tot FROM attendance WHERE employee_name=? AND date=? AND clock_out IS NOT NULL", (pay_name, pay_date_str))
            
            base_rate = float(prof.iloc[0]['hourly_rate']) if not prof.empty else 0.0
            ot_mult = float(prof.iloc[0]['ot_multiplier']) if not prof.empty else 1.0
            
            tracked_reg = float(shifts.iloc[0]['reg']) if not shifts.empty and shifts.iloc[0]['reg'] is not None else 0.0
            tracked_ot = float(shifts.iloc[0]['ot']) if not shifts.empty and shifts.iloc[0]['ot'] is not None else 0.0
            tracked_total = tracked_reg + tracked_ot
            
            system_earnings = (tracked_reg * base_rate) + (tracked_ot * (base_rate * ot_mult))
            
            st.info(f"""
            **Time Clock Data for {pay_name} on {pay_date_str}:**
            * Regular Hours: {tracked_reg:.2f} hrs (@ £{base_rate:.2f}/hr)
            * Overtime Hours: {tracked_ot:.2f} hrs (@ £{base_rate * ot_mult:.2f}/hr)
            * **Suggested System Earnings: £{system_earnings:.2f}**
            """)
            
            pay_amount = st.number_input("Actual Amount Paid Out (£)", min_value=0.0, value=round(system_earnings, 2), step=5.0)
            
            if st.button("Log & Settle Payout"):
                execute_db("INSERT INTO salary_payouts (date, employee_name, hours_covered, amount_paid, system_calculated) VALUES (?, ?, ?, ?, ?)",
                           (pay_date_str, pay_name, tracked_total, pay_amount, system_earnings))
                execute_db("INSERT INTO financials (date, type, category, amount) VALUES (?, 'Salary Paid', ?, ?)",
                           (pay_date_str, f"Wages to {pay_name}", pay_amount))
                st.success(f"Logged payment of £{pay_amount:.2f} to {pay_name} for date {pay_date_str}")
                st.rerun()

    with col2:
        st.subheader("Wage Verification Audit Trail")
        df_payouts = run_query("SELECT date as 'Date', employee_name as 'Employee', hours_covered as 'Hours', system_calculated as 'Expected (£)', amount_paid as 'Paid Out (£)' FROM salary_payouts ORDER BY id DESC")
        
        if df_payouts.empty:
            st.info("No recorded payouts yet.")
        else:
            audit_records = []
            for idx, row in df_payouts.iterrows():
                diff = row['Paid Out (£)'] - row['Expected (£)']
                if abs(diff) < 0.05:
                    status = "✅ Match"
                elif diff > 0:
                    status = f"⚠️ Overpaid (£{abs(diff):.2f})"
                else:
                    status = f"🚨 Underpaid (£{abs(diff):.2f})"
                
                audit_records.append({
                    "Date": row['Date'],
                    "Employee": row['Employee'],
                    "Hours": row['Hours'],
                    "Expected": f"£{row['Expected (£)']:,.2f}",
                    "Paid Out": f"£{row['Paid Out (£)']:,.2f}",
                    "Status": status
                })
            st.dataframe(pd.DataFrame(audit_records), use_container_width=True)

# --- TAB 3: LOG SALES & EXPENSES ---
with tab3:
    st.header("Restaurant Ledger Entry")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Log Item")
        f_date = st.date_input("Date", datetime.today(), key="ledger_date")
        f_type = st.selectbox("Category Group", ["Sale", "Expense"])
        f_cat = st.selectbox("Description Item", [
            "Food/Ingredient Inventory", "Beverage Supplies", "Kitchen Equipment", 
            "Rent & Lease", "Electricity & Gas", "Water Utility", "Marketing",
            "Front-of-House Till Cash Sale", "Online Delivery Platform Income", "Catering Service Drop"
        ] if f_type == "Expense" else ["Front-of-House Till Cash Sale", "Online Delivery Platform Income", "Catering Service Drop"])
        
        f_amount = st.number_input("Total Transaction Value (£)", min_value=0.0, step=10.0)
        
        if st.button("Save Transaction Record"):
            if f_amount > 0:
                execute_db("INSERT INTO financials (date, type, category, amount) VALUES (?, ?, ?, ?)",
                           (f_date.strftime("%Y-%m-%d"), f_type, f_cat, f_amount))
                st.success(f"Logged £{f_amount} under {f_type}")
                st.rerun()

    with col2:
        st.subheader("Last 10 General Ledger Rows")
        df_ledg = run_query("SELECT date as 'Date', type as 'Type', category as 'Item Description', amount as 'Amount (£)' FROM financials ORDER BY id DESC LIMIT 10")
        st.dataframe(df_ledg, use_container_width=True)

# --- TAB 4: MONTHLY PROFIT & LOSS ---
with tab4:
    st.header("Monthly Profitability Analytics & Export Center")
    
    years = [2026, 2027, 2025]
    months = list(calendar.month_name)[1:]
    
    c1, c2 = st.columns(2)
    with c1:
        sel_month_name = st.selectbox("Select Target Month", months, index=datetime.today().month - 1)
    with c2:
        sel_year = st.selectbox("Select Target Year", years, index=0)
        
    sel_month_num = months.index(sel_month_name) + 1
    month_prefix = f"{sel_year}-{sel_month_num:02d}"
    
    df_m_fin = run_query("SELECT date as 'Date', type as 'Ledger Type', category as 'Line Item Description', amount as 'Amount (£)' FROM financials WHERE date LIKE ? ORDER BY date ASC", (f"{month_prefix}%",))
    
    st.subheader(f"Financial Status Breakdown for {sel_month_name} {sel_year}")
    
    if df_m_fin.empty:
        st.info("No financial ledger entries found for this specific month.")
    else:
        m_sales = df_m_fin[df_m_fin['Ledger Type'] == 'Sale']['Amount (£)'].sum()
        m_expenses = df_m_fin[df_m_fin['Ledger Type'] == 'Expense']['Amount (£)'].sum()
        m_salaries = df_m_fin[df_m_fin['Ledger Type'] == 'Salary Paid']['Amount (£)'].sum()
        m_profit = m_sales - (m_expenses + m_salaries)
        
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Gross Restaurant Sales", f"£{m_sales:,.2f}")
        mc2.metric("Operational Expenses", f"£{m_expenses:,.2f}")
        mc3.metric("Total Payroll Settled", f"£{m_salaries:,.2f}")
        
        if m_profit >= 0:
            mc4.metric("Net Restaurant Profit", f"£{m_profit:,.2f}", delta=f"£{m_profit:,.2f} Net Surplus")
        else:
            mc4.metric("Net Restaurant Profit", f"£{m_profit:,.2f}", delta=f"£{m_profit:,.2f} Deficit", delta_color="inverse")
            
        st.write("#### Date-Wise Itemized Category Breakdown Ledger")
        st.dataframe(df_m_fin, use_container_width=True)
        
        csv_fin = df_m_fin.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Monthly Ledger as CSV",
            data=csv_fin,
            file_name=f"Financial_Ledger_{month_prefix}.csv",
            mime="text/csv"
        )

    st.write("---")
    st.subheader(f"Total Working Hours & Overtime Log: {sel_month_name} {sel_year}")
    
    df_m_att = run_query("""
        SELECT employee_name as 'Staff Member', 
               COUNT(id) as 'Total Shifts Formed', 
               SUM(reg_hours) as 'Regular Hours Worked', 
               SUM(ot_hours) as 'Overtime Hours Logged', 
               SUM(total_hours) as 'Total Accumulated Hours' 
        FROM attendance 
        WHERE date LIKE ? AND clock_out IS NOT NULL 
        GROUP BY employee_name
    """, (f"{month_prefix}%",))
    
    if not df_m_att.empty:
        st.dataframe(df_m_att, use_container_width=True)
        
        csv_att = df_m_att.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Monthly Hours Report as CSV",
            data=csv_att,
            file_name=f"Employee_Hours_{month_prefix}.csv",
            mime="text/csv"
        )
    else:
        st.info("No clocked employee shift records found finalized for this month.")