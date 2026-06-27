import os
import sys
import streamlit.web.cli as stcli

if __name__ == '__main__':
    # Find the folder where this specific executable is running
    base_path = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_path, "app.py")
    
    # Force the execution parameters to use the absolute path to app.py
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false"]
    sys.exit(stcli.main())
