# 🍳 Restaurant Command Center & Wage Auditor

A lightweight, secure, and fully containerized Python web application built using **Streamlit** and **SQLite**. Designed specifically for day-to-day restaurant management, this tool tracks daily sales, itemized expenses, employee shift attendance (with automatic overtime calculations), and provides a secure admin dashboard to audit payroll and manually adjust hours.

---

## ✨ Features

* **🇬🇧 Localized Currency:** Fully configured to Great British Pounds (`£`).
* **⏰ Shift Attendance Punch Clock:** Quick interface for staff to clock in and clock out. Handles overnight restaurant shifts seamlessly with smart lateness logging.
* **➕ Admin Manual Override (Password Protected):** Secure panel allowing managers to manually inject regular/overtime hours for past dates with instant verification notifications.
* **💷 Automated Salary Calculator & Auditor:** Automatically queries employee time logs for any specific date, calculates suggested earnings based on custom hourly/overtime rates, and highlights whether the *Actual Paid Amount* matches or underpays/overpays the staff.
* **📊 Itemized Multi-Month Profit & Loss Ledger:** Date-wise tracking of operational costs (inventory, utilities, rent, and **Interior Decoration**) and gross restaurant revenue across an itemized **5-month historical framework** (February 2026 – June 2026).
* **🚨 Smart Waste/Complaint Mapping:** Log a `Customer Complaint (Replacement)` to automatically track stock waste hits (estimated at a 30% raw food value cost penalty) dynamically linked back to an original order ticket ID.
* **📥 Data Export Center:** One-click CSV downloads for your entire itemized monthly financial ledger and employee cumulative timesheets.
* **💾 Persistent Docker Storage:** Mounts a volume to your local machine, ensuring database history is safe even if the container is destroyed or updated.

---

## 🔒 Security Architecture (First-Time Setup)

To replace unsecure hardcoded administrative overrides, the application utilizes an encrypted database credential framework:
* **Salt-Hashed Encryption:** Passwords are never stored in plain text. The application uses a cryptographically secure, random 16-byte unique salt combined with **PBKDF2 SHA-256** stretching over 100,000 iterations.
* **First-Launch Initialization:** If the system boots and detects an uninitialized credentials ledger, it hijacks the user interface to force the creation of a custom master administrative password, writing the unique salt-hash directly into the SQLite database state.

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

🛡️ Database Verification Testing (Inject Mock Data)
To populate your charts instantly with a fully functional 5-month historical mockup dataset (February 2026 – June 2026) complete with complex linked entries, roster lines, and pre-configured menus, run the following tool string sequence in your terminal:

docker cp seed_data.py tracker_instance:/app/seed_data.py
docker exec -it tracker_instance python seed_data.py

Note: Refreshing your browser page will instantly load the historical audit pipelines.

🍏 Native macOS Desktop Bundle Deployment
The repository includes compilation configuration pipelines to package the interactive Streamlit EPOS platform into a native standalone macOS desktop application (.app bundle). This compiles all underlying Python runtimes, C-libraries, and framework components into a single executable layer.

🛠️ Production Compilation Pipeline
Install Local Dependencies
Ensure your local macOS host environment contains the base application framework dependencies and pyinstaller system modules:

python3 -m pip install streamlit pandas pyinstaller --break-system-packages
Generate the Isolated Application Spec Bundle
Execute the pyinstaller compiler from the root project directory. The pipeline explicitly passes the --collect-all flag to force the compiler to recursively sweep and collect all dynamic web assets, Javascript dependencies, and frontend CSS styles bundled with Streamlit:

pyinstaller --name="RestaurantHub" --onedir --windowed --collect-all streamlit mac_run.py
Inject Operational Architecture Assets
Modern versions of PyInstaller isolate standard library references and execution scripts inside a protected subdirectory named _internal/ to preserve top-level folder health.

To allow the executable binary to resolve core system schemas at runtime, manually copy the application layout script and database directory directly into the internal dependency tree:

Source Files: app.py and the data/ directory (holding your restaurant_tracker.db file).

Target Compilation Directory: dist/RestaurantHub/_internal/

🎯 Booting the Application
Once your assets are injected into the internal tree, navigate back to the primary distribution directory (dist/RestaurantHub/) and launch the platform:

./dist/RestaurantHub/RestaurantHub
Desktop Application Execution: Alternatively, you can double-click the RestaurantHub executable binary file directly inside your macOS Finder layout. The background engine will instantly wake up, mount your local SQLite state, and automatically forward your desktop session to a live dashboard pipeline inside a standalone web container instance.*

💡 Recommended Daily Workflow
Roster Configurations: When first setting up, input your employees inside the Employee Roster Setup area along with their exact regular hourly wages.

Build Your Menus: Use the Menu & Budgets tab to index your custom dishes, price tags, and daily target wage caps.

Publish the Rota: Before the operational week starts, log scheduled shift assignments, dates, and times.

POS Order Taking: Leave the application loaded on a countertop tablet or terminal. Staff clock in/out directly on screen, and your tills process itemized customer orders, discounts, voids, or complaint metrics seamlessly.

Close the Books: Settle payroll transactions through the Payroll Auditor tab, and monitor your total tax liabilities, waste margins, and net performance directly inside Performance Analytics with immediate CSV print capabilities.