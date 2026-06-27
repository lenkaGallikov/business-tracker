# 🍳 Restaurant Command Center & Wage Auditor

A lightweight, secure, and fully containerized Python web application built using **Streamlit** and **SQLite**. Designed specifically for day-to-day restaurant management, this tool tracks daily sales, itemized expenses, employee shift attendance (with automatic overtime calculations), and provides a secure admin dashboard to audit payroll and manually adjust hours.

---

## ✨ Features

* **🇬🇧 Localized Currency:** Fully configured to Great British Pounds (`£`).
* **⏰ Shift Attendance Punch Clock:** Quick interface for staff to clock in and clock out. Handles overnight restaurant shifts seamlessly.
* **➕ Admin Manual Override (Password Protected):** Secure panel allowing managers to manually inject regular/overtime hours for past dates with instant verification notifications.
* **💷 Automated Salary Calculator & Auditor:** Automatically queries employee time logs for any specific date, calculates suggested earnings based on custom hourly/overtime rates, and highlights whether the *Actual Paid Amount* matches or underpays/overpays the staff.
* **📊 Itemized Monthly Profit & Loss Ledger:** Date-wise tracking of operational costs (inventory, utilities, rent) and gross restaurant revenue.
* **📥 Data Export Center:** One-click CSV downloads for your entire itemized monthly financial ledger and employee cumulative timesheets.
* **💾 Persistent Docker Storage:** Mounts a volume to your local machine, ensuring database history is safe even if the container is destroyed or updated.

---

## 🛠️ Project Structure

Ensure your project directory contains the following files:

```text
business-tracker/
├── app.py                 # Core Streamlit application logic
├── Dockerfile             # Container blueprint
├── requirements.txt       # Python package dependencies
├── Makefile               # Automation commands for Mac Terminal
└── data/                  # Auto-generated directory containing your database
    └── restaurant_tracker.db

🚀 Getting Started on Mac
Prerequisites
Download and install Docker Desktop for Mac.

Open Docker Desktop and ensure the engine is fully running in the background.

Setup & Launch in 1 Command
Open the Terminal app on your Mac, navigate to your project folder, and simply run:
make

The Makefile will automatically stop any older instances, wipe the old configuration profile, compile your updated application source code, and deploy the isolated container.

Once complete, open your web browser and go to:
👉 http://localhost:8501

📝 Automation Commands (Makefile Shortcuts)
Instead of typing multi-line Docker scripts, you can use these simple terminal shortcuts:

make — Complete pipeline execution: stops, cleans, rebuilds, and relaunches the app.

make run — Launches the container immediately without executing a fresh image build.

make stop — Gracefully terminates the running container app instance.

make clean — Wipes the container profile cache to prevent configuration conflicts.

🔒 Configuration Notes
Default Admin Password: The default password to log manual hours is admin.

Changing the Password: To secure your application, open app.py in a text editor and update the variable at the very top of the file:
ADMIN_PASSWORD = "your-custom-secure-password"

🛡️ Database Verification Testing (Inject Mock Data)
To populate your charts instantly with a fully functional month of simulated restaurant transactions (June 2026), run the following tool string sequence in your terminal:

Bash
docker cp seed_data.py tracker_instance:/app/seed_data.py
docker exec -it tracker_instance python seed_data.py
Note: Refreshing your browser will immediately reflect pre-configured menus, lateness violations, and complex discount ticket actions.

💡 Recommended Daily Workflow
Roster Configurations: When first setting up, input your employees inside the Employee Roster Setup area along with their exact regular hourly wages.

Build Your Menus: Use the Menu & Budgets tab to index your custom dishes, price tags, and daily target wage caps.

Publish the Rota: Before the operational week starts, log scheduled shift assignments, dates, and times.

POS Order Taking: Leave the application loaded on a countertop tablet or terminal. Staff clock in/out directly on screen, and your tills process itemized customer orders, discounts, voids, or complaint metrics seamlessly.

Close the Books: Settle payroll transactions through the Payroll Auditor tab, and monitor your total tax liabilities, waste margins, and net performance directly inside Performance Analytics with immediate CSV print capabilities.




## 🍏 Native macOS Desktop Bundle Deployment

The repository includes compilation configuration pipelines to package the interactive Streamlit EPOS platform into a native standalone macOS desktop application (`.app` bundle). This compiles all underlying Python runtimes, C-libraries, and framework components into a single executable layer.

### 🛠️ Production Compilation Pipeline

1. **Install Local Dependencies**
   Ensure your local macOS host environment contains the base application framework dependencies and `pyinstaller` system modules:
   ```bash
   python3 -m pip install streamlit pandas pyinstaller --break-system-packages


Generate the Isolated Application Spec Bundle
Execute the pyinstaller compiler from the root project directory. The pipeline explicitly passes the --collect-all flag to force the compiler to recursively sweep and collect all dynamic web assets, Javascript dependencies, and frontend CSS styles bundled with Streamlit:

Bash
pyinstaller --name="RestaurantHub" --onedir --windowed --collect-all streamlit mac_run.py

Inject Operational Architecture Assets
Modern versions of PyInstaller isolate standard library references and execution scripts inside a protected subdirectory named _internal/ to preserve top-level folder health.

To allow the executable binary to resolve core system schemas at runtime, manually copy the application layout script and database directory directly into the internal dependency tree:

Source Files: app.py and the data/ directory (holding your restaurant_tracker.db file).

Target Compilation Directory: dist/RestaurantHub/_internal/

### 🎯 Booting the Application
Once your assets are injected into the internal tree, navigate back to the primary distribution directory (dist/RestaurantHub/) and launch the platform:

Bash
./dist/RestaurantHub/RestaurantHub
Desktop Application Execution: Alternatively, you can double-click the RestaurantHub executable binary file directly inside your macOS Finder layout. The background engine will instantly wake up, mount your local SQLite state, and automatically forward your desktop session to a live dashboard pipeline inside a standalone web container instance.
