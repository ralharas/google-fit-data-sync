import os
import sys
import datetime
import threading
import time
import pandas as pd
import tkinter.messagebox as messagebox
import platform

from tkinter import Tk, Button, Label, Checkbutton, IntVar, Frame, Canvas, Scrollbar, VERTICAL, RIGHT, Y, LEFT, BOTH
from tkinter import ttk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Valid Google Fit API scopes
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.nutrition.read'
]

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_executable_dir():
    """Get directory where executable is located (for data storage)"""
    if getattr(sys, 'frozen', False):
        # When running as packaged app, use executable directory
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # When running in development, use script directory
        return os.path.dirname(os.path.abspath(__file__))

def run_sync(historical=False):
    try:
        # OAuth configuration from environment variables or config file
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        # If not in environment, try to load from config file
        if not client_id or not client_secret:
            config_file = resource_path("oauth_config.json")
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                client_id = config.get("client_id")
                client_secret = config.get("client_secret")
        
        if not client_id or not client_secret:
            raise Exception("OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables or provide oauth_config.json file.")
        
        client_config = {
            "installed": {
                "client_id": client_id,
                "project_id": "dataautomation-464320", 
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }
        
        # For token.json, we need to save it to a writable location
        # Use the user's home directory for persistent storage
        home_dir = os.path.expanduser("~")
        token_file = os.path.join(home_dir, '.google_fit_token.json')

        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                # Try multiple ports to avoid conflicts
                for port in [8080, 8081, 8082, 8083, 0]:  # 0 = any available port
                    try:
                        creds = flow.run_local_server(port=port)
                        break
                    except OSError as e:
                        if port == 0:  # Last attempt with any port
                            raise e
                        continue
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        fitness_service = build('fitness', 'v1', credentials=creds)

        if historical:
            start_date = datetime.datetime(2022, 1, 1)
        else:
            start_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        end_date = datetime.datetime.utcnow()
        current = start_date
        all_rows = []

        while current < end_date:
            next_month = current + datetime.timedelta(days=30)
            start_time = int(current.timestamp() * 1000)
            end_time = int(min(next_month, end_date).timestamp() * 1000)

            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.step_count.delta",
                    "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
                }],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": start_time,
                "endTimeMillis": end_time
            }

            response = fitness_service.users().dataset().aggregate(userId='me', body=body).execute()

            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        steps = point['value'][0]['intVal']
                        start = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                        end = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                        all_rows.append({'start': start, 'end': end, 'steps': steps})

            current = next_month

        # Save output to executable directory
        project_root = get_executable_dir()
        
        output_dir = os.path.join(project_root, "Steps", "Raw")
        os.makedirs(output_dir, exist_ok=True)

        if historical:
            output_file = os.path.join(output_dir, 'steps_data_full.csv')
        else:
            output_file = os.path.join(output_dir, 'steps_data_daily.csv')

        pd.DataFrame(all_rows).to_csv(output_file, index=False)
        
        # Additional health data collection (commented out for simplicity)
        
        if historical:
            result_label.config(text=f"✅ Full history saved!")
            message = f"Steps data saved to: {output_file}"
            messagebox.showinfo("Success", message)
        else:
            result_label.config(text=f"✅ Daily sync done!")
            # Note: GUI-only mode, no console output

    except Exception as e:
        result_label.config(text=f"❌ Error: {e}")
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

def collect_all_health_data(fitness_service, start_date, end_date, project_root, historical):
    """Collect heart rate, weight, calories, and distance data"""
    health_data = {}
    
    # Data source configurations for comprehensive health data
    data_sources = {
        'calories': {
            'dataTypeName': 'com.google.calories.expended',
            'folder': 'Calories'
        },
        'distance': {
            'dataTypeName': 'com.google.distance.delta',
            'folder': 'Distance'
        },
        'heart_rate': {
            'dataTypeName': 'com.google.heart_rate.bpm',
            'folder': 'HeartRate'
        },
        'weight': {
            'dataTypeName': 'com.google.weight',
            'folder': 'Weight'
        },
        'height': {
            'dataTypeName': 'com.google.height',
            'folder': 'Height'
        },
        'body_fat': {
            'dataTypeName': 'com.google.body.fat.percentage',
            'folder': 'BodyFat'
        },
        'blood_pressure': {
            'dataTypeName': 'com.google.blood_pressure',
            'folder': 'BloodPressure'
        },
        'blood_glucose': {
            'dataTypeName': 'com.google.blood_glucose',
            'folder': 'BloodGlucose'
        },
        'oxygen_saturation': {
            'dataTypeName': 'com.google.oxygen_saturation',
            'folder': 'OxygenSaturation'
        },
        'body_temperature': {
            'dataTypeName': 'com.google.body.temperature',
            'folder': 'BodyTemperature'
        }
    }
    
    for data_type, config in data_sources.items():
        try:
            rows = []
            current = start_date
            
            while current < end_date:
                next_month = current + datetime.timedelta(days=30)
                start_time = int(current.timestamp() * 1000)
                end_time = int(min(next_month, end_date).timestamp() * 1000)
                
                body = {
                    "aggregateBy": [{
                        "dataTypeName": config['dataTypeName']
                    }],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_time,
                    "endTimeMillis": end_time
                }
                
                try:
                    response = fitness_service.users().dataset().aggregate(userId='me', body=body).execute()
                    
                    for bucket in response['bucket']:
                        for dataset in bucket['dataset']:
                            for point in dataset['point']:
                                start_dt = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                                end_dt = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                                
                                if data_type == 'heart_rate':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'heart_rate_bpm': value})
                                elif data_type == 'weight':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'weight_kg': value})
                                elif data_type == 'calories':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'calories': value})
                                elif data_type == 'distance':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'distance_meters': value})
                                
                except Exception:
                    # Data might not be available
                    pass
                    
                current = next_month
            
            # Save data if we have any
            if rows:
                output_dir = os.path.join(project_root, config['folder'], "Raw")
                os.makedirs(output_dir, exist_ok=True)
                
                if historical:
                    output_file = os.path.join(output_dir, f'{data_type}_data_full.csv')
                else:
                    output_file = os.path.join(output_dir, f'{data_type}_data_daily.csv')
                
                pd.DataFrame(rows).to_csv(output_file, index=False)
                health_data[data_type] = output_file
            else:
                health_data[data_type] = None
                
        except Exception:
            health_data[data_type] = None
    
    return health_data

def run_comprehensive_sync(selected_data_types, historical=False):
    """Run sync for selected data types with comprehensive data collection"""
    try:
        # OAuth configuration from environment variables or config file
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        # If not in environment, try to load from config file
        if not client_id or not client_secret:
            config_file = resource_path("oauth_config.json")
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                client_id = config.get("client_id")
                client_secret = config.get("client_secret")
        
        if not client_id or not client_secret:
            raise Exception("OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables or provide oauth_config.json file.")
        
        client_config = {
            "installed": {
                "client_id": client_id,
                "project_id": "dataautomation-464320", 
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }
        
        # For token.json, we need to save it to a writable location
        home_dir = os.path.expanduser("~")
        token_file = os.path.join(home_dir, '.google_fit_token.json')

        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                # Try multiple ports to avoid conflicts
                for port in [8080, 8081, 8082, 8083, 0]:  # 0 = any available port
                    try:
                        creds = flow.run_local_server(port=port)
                        break
                    except OSError as e:
                        if port == 0:  # Last attempt with any port
                            raise e
                        continue
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        fitness_service = build('fitness', 'v1', credentials=creds)

        if historical:
            start_date = datetime.datetime(2022, 1, 1)
        else:
            start_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        end_date = datetime.datetime.utcnow()
        
        # Get project root directory (where executable is located)
        project_root = get_executable_dir()
        
        collected_data = {}
        
        # Collect selected data types
        for data_type in selected_data_types:
            try:
                if data_type == 'steps':
                    collected_data[data_type] = collect_steps_data(fitness_service, start_date, end_date, project_root, historical)
                elif data_type in ['calories', 'distance', 'heart_rate', 'weight', 'height', 'body_fat', 'blood_pressure', 'blood_glucose', 'oxygen_saturation', 'body_temperature']:
                    health_data = collect_all_health_data(fitness_service, start_date, end_date, project_root, historical)
                    if data_type in health_data:
                        collected_data[data_type] = health_data[data_type]
            except Exception as e:
                collected_data[data_type] = f"Error: {str(e)}"
        
        # Update result label with summary
        successful_imports = [k for k, v in collected_data.items() if v and 'Error' not in str(v)]
        failed_imports = [k for k, v in collected_data.items() if not v or 'Error' in str(v)]
        
        # Cross-platform status messages
        if platform.system() == "Windows":
            success_icon = "[OK]"
            warning_icon = "[WARN]"
            error_icon = "[ERROR]"
        else:
            success_icon = "✅"
            warning_icon = "⚠️"
            error_icon = "❌"
        
        if successful_imports:
            result_text = f"{success_icon} Successfully imported: {', '.join(successful_imports)}"
            if failed_imports:
                result_text += f"\n{warning_icon} Failed: {', '.join(failed_imports)}"
        else:
            result_text = f"{error_icon} No data could be imported"
        
        result_label.config(text=result_text)
        
        if historical:
            messagebox.showinfo("Import Complete", result_text)
            
    except Exception as e:
        # Cross-platform error message
        if platform.system() == "Windows":
            error_text = f"[ERROR] Error: {e}"
        else:
            error_text = f"❌ Error: {e}"
        
        result_label.config(text=error_text)
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

def collect_steps_data(fitness_service, start_date, end_date, project_root, historical):
    """Collect steps data specifically"""
    current = start_date
    all_rows = []

    while current < end_date:
        next_month = current + datetime.timedelta(days=30)
        start_time = int(current.timestamp() * 1000)
        end_time = int(min(next_month, end_date).timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        response = fitness_service.users().dataset().aggregate(userId='me', body=body).execute()

        for bucket in response['bucket']:
            for dataset in bucket['dataset']:
                for point in dataset['point']:
                    steps = point['value'][0]['intVal']
                    start = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                    end = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                    all_rows.append({'start': start, 'end': end, 'steps': steps})

        current = next_month

    # Save output to executable directory
    output_dir = os.path.join(project_root, "Steps", "Raw")
    os.makedirs(output_dir, exist_ok=True)

    if historical:
        output_file = os.path.join(output_dir, 'steps_data_full.csv')
    else:
        output_file = os.path.join(output_dir, 'steps_data_daily.csv')

    # Create DataFrame with proper date formatting
    df = pd.DataFrame(all_rows)
    if not df.empty:
        # Format dates nicely
        df['date'] = pd.to_datetime(df['start']).dt.date
        df = df.groupby('date')['steps'].sum().reset_index()
        df.to_csv(output_file, index=False)
    
    return output_file

def start_sync():
    # Get selected data types
    selected_data_types = []
    for data_type, var in checkbox_vars.items():
        if var.get():
            selected_data_types.append(data_type.lower().replace(' ', '_'))
    
    if not selected_data_types:
        messagebox.showwarning("Warning", "Please select at least one data type to import.")
        return
    
    # Cross-platform loading message
    if platform.system() == "Windows":
        loading_text = "[LOADING] Starting import..."
    else:
        loading_text = "🔄 Starting import..."
    
    result_label.config(text=loading_text)
    threading.Thread(target=lambda: run_comprehensive_sync(selected_data_types, historical=True)).start()

    def periodic_sync():
        while True:
            time.sleep(86400)
            run_comprehensive_sync(selected_data_types, historical=False)

    threading.Thread(target=periodic_sync, daemon=True).start()

def get_system_font():
    """Get appropriate font family based on operating system"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "SF Pro Display"
    else:  # Linux and others
        return "Ubuntu"

def get_emoji_font():
    """Get emoji-compatible font based on operating system"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI Emoji"
    elif system == "Darwin":  # macOS
        return "Apple Color Emoji"
    else:  # Linux
        return "Noto Color Emoji"

if __name__ == '__main__':
    root = Tk()
    root.title("Google Fit Data Sync")
    
    # Cross-platform window sizing and positioning
    window_width = 600
    window_height = 650
    
    # Center window on screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.configure(bg='#f0f0f0')
    root.resizable(True, True)
    root.minsize(500, 500)
    
    # Get system-appropriate fonts
    system_font = get_system_font()
    
    # Header
    header_frame = Frame(root, bg='#2c3e50', height=70)
    header_frame.pack(fill='x')
    header_frame.pack_propagate(False)
    
    # Use different approaches for emoji display based on OS
    if platform.system() == "Windows":
        header_text = "Google Fit Data Sync"
    else:
        header_text = "🏃‍♂️ Google Fit Data Sync"
    
    header_label = Label(header_frame, text=header_text, 
                        font=(system_font, 18, "bold"), 
                        fg='white', bg='#2c3e50')
    header_label.pack(expand=True)
    
    # Main content frame
    main_frame = Frame(root, bg='#f0f0f0')
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Step 1: Authentication Section
    auth_frame = Frame(main_frame, bg='#f0f0f0')
    auth_frame.pack(fill='x', pady=(0, 20))
    
    auth_label = Label(auth_frame, 
                      text="Step 1: Connect to Google Fit", 
                      font=(system_font, 14, "bold"), 
                      bg='#f0f0f0', fg='#2c3e50')
    auth_label.pack(pady=(0, 10))
    
    def do_auth():
        """Perform actual Google OAuth authentication"""
        try:
            auth_status.config(text="Connecting...", fg='#f39c12')
            auth_button.config(state='disabled')
            
            # OAuth configuration
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                config_file = resource_path("oauth_config.json")
                if os.path.exists(config_file):
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    client_id = config.get("client_id")
                    client_secret = config.get("client_secret")
            
            if not client_id or not client_secret:
                raise Exception("OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables or provide oauth_config.json file.")
            
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "project_id": "dataautomation-464320",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": client_secret,
                    "redirect_uris": ["http://localhost"]
                }
            }
            
            home_dir = os.path.expanduser("~")
            token_file = os.path.join(home_dir, '.google_fit_token.json')
            
            creds = None
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    for port in [8080, 8081, 8082, 8083, 0]:
                        try:
                            creds = flow.run_local_server(port=port)
                            break
                        except OSError as e:
                            if port == 0:
                                raise e
                            continue
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Test the connection
            fitness_service = build('fitness', 'v1', credentials=creds)
            
            # Success!
            auth_status.config(text="✅ Connected to Google Fit!" if platform.system() != "Windows" else "Connected to Google Fit!", fg='#27ae60')
            auth_button.config(text="✅ Connected" if platform.system() != "Windows" else "Connected", state='normal', bg='#27ae60')
            data_frame.pack(fill='both', expand=True, pady=(20, 0))
            
        except Exception as e:
            auth_status.config(text=f"Error: {str(e)[:50]}...", fg='#e74c3c')
            auth_button.config(state='normal')
            messagebox.showerror("Authentication Error", f"Failed to connect to Google Fit:\n{e}")
    
    auth_button = Button(auth_frame, 
                        text="🔐 Authorize with Google" if platform.system() != "Windows" else "Authorize with Google", 
                        command=lambda: threading.Thread(target=do_auth).start(),
                        font=(system_font, 11, "bold"),
                        bg='#27ae60', fg='white',
                        activebackground='#229954',
                        cursor='hand2',
                        padx=20, pady=8)
    auth_button.pack()
    
    auth_status = Label(auth_frame, text="Not connected", 
                       font=(system_font, 10), 
                       bg='#f0f0f0', fg='#e74c3c')
    auth_status.pack(pady=(5, 0))
    
    # Step 2: Data Selection Section (Initially Hidden)
    data_frame = Frame(main_frame, bg='#f0f0f0')
    
    data_label = Label(data_frame, 
                      text="Step 2: Select Data Types to Import", 
                      font=(system_font, 14, "bold"), 
                      bg='#f0f0f0', fg='#2c3e50')
    data_label.pack(pady=(0, 15))
    
    # Checkbox for each data type (matching available scopes)
    checkbox_vars = {}
    data_types = ['Steps', 'Calories', 'Distance', 'Heart Rate', 'Weight', 'Height']
    
    # Select All Checkbox
    def select_all():
        for var in checkbox_vars.values():
            var.set(select_all_var.get())
    
    select_all_var = IntVar(value=1)  # Default to selected
    select_all_frame = Frame(data_frame, bg='#f0f0f0')
    select_all_frame.pack(fill='x', pady=(0, 10))
    
    # Cross-platform checkbox text
    if platform.system() == "Windows":
        select_all_text = "Select All Data Types"
    else:
        select_all_text = "✅ Select All Data Types"
    
    select_all_checkbox = Checkbutton(select_all_frame, 
                                     text=select_all_text, 
                                     variable=select_all_var, 
                                     command=select_all,
                                     font=(system_font, 11, "bold"),
                                     bg='#f0f0f0', fg='#2c3e50',
                                     activebackground='#e8f4fd',
                                     selectcolor='#3498db')
    select_all_checkbox.pack(anchor='w')
    
    # Scrollable frame for checkboxes
    checkbox_container = Frame(data_frame, bg='#f0f0f0')
    checkbox_container.pack(fill='both', expand=True, pady=(0, 10))
    
    canvas = Canvas(checkbox_container, bg='#f0f0f0', height=180, highlightthickness=0)
    scrollbar = Scrollbar(checkbox_container, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas, bg='#f0f0f0')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Create checkboxes in a grid layout
    for i, data_type in enumerate(data_types):
        var = IntVar(value=1)  # Default to selected
        checkbox_vars[data_type] = var
        
        # Cross-platform emoji and icon handling
        if platform.system() == "Windows":
            icon_map = {
                'Steps': '[S]', 'Calories': '[C]', 'Distance': '[D]', 'Heart Rate': '[H]',
                'Weight': '[W]', 'Height': '[Ht]', 'Body Fat': '[BF]', 'Blood Pressure': '[BP]',
                'Blood Glucose': '[BG]', 'Oxygen Saturation': '[O2]', 'Body Temperature': '[T]'
            }
            checkbox_text = f"{icon_map.get(data_type, '[*]')} {data_type}"
        else:
            emoji_map = {
                'Steps': '👟', 'Calories': '🔥', 'Distance': '📏', 'Heart Rate': '❤️',
                'Weight': '⚖️', 'Height': '📐', 'Body Fat': '💪', 'Blood Pressure': '🩸',
                'Blood Glucose': '🍯', 'Oxygen Saturation': '💨', 'Body Temperature': '🌡️'
            }
            checkbox_text = f"{emoji_map.get(data_type, '📊')} {data_type}"
        
        checkbox = Checkbutton(scrollable_frame, 
                              text=checkbox_text, 
                              variable=var,
                              font=(system_font, 10),
                              bg='#f0f0f0', fg='#34495e',
                              activebackground='#e8f4fd',
                              selectcolor='#3498db',
                              anchor='w')
        checkbox.grid(row=i//2, column=i%2, sticky='ew', padx=15, pady=3)
        
        # Configure grid weights for responsive layout
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
    
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    # Button frame
    button_frame = Frame(data_frame, bg='#f0f0f0')
    button_frame.pack(fill='x', pady=20)
    
    # Cross-platform button styling
    if platform.system() == "Windows":
        button_text = "Start Full Import + Daily Auto"
        button_style = {'relief': 'raised', 'bd': 2}
    else:
        button_text = "🚀 Start Full Import + Daily Auto"
        button_style = {'relief': 'flat', 'bd': 0}
    
    start_button = Button(button_frame, 
                         text=button_text, 
                         command=start_sync, 
                         font=(system_font, 12, "bold"),
                         bg='#3498db', fg='white',
                         activebackground='#2980b9',
                         cursor='hand2',
                         padx=30, pady=12,
                         **button_style)
    start_button.pack()
    
    # Result label
    result_label = Label(data_frame, text="", 
                        font=(system_font, 11), 
                        bg='#f0f0f0', fg='#27ae60',
                        wraplength=550,
                        justify='center')
    result_label.pack(pady=15)
    
    root.mainloop()
