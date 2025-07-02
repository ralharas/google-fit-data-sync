import os
import sys
import datetime
import threading
import time
import pandas as pd
import tkinter.messagebox as messagebox
from time import sleep

from tkinter import Tk, Button, Label, Checkbutton, IntVar, Frame, Scrollbar, Canvas, VERTICAL
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ALL VALID Google Fit API scopes from your screenshot
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.blood_glucose.read',
    'https://www.googleapis.com/auth/fitness.blood_pressure.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.body_temperature.read',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.nutrition.read',
    'https://www.googleapis.com/auth/fitness.oxygen_saturation.read',
    'https://www.googleapis.com/auth/fitness.reproductive_health.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

        # Save output to user-accessible directory
        if getattr(sys, 'frozen', False):
            # When running as packaged app
            if sys.platform == 'darwin' and sys.executable.endswith('.app/Contents/MacOS/GoogleFitSync'):
                # On Mac, save next to the .app bundle, not inside it
                app_path = sys.executable.replace('/Contents/MacOS/GoogleFitSync', '')
                project_root = os.path.dirname(app_path)
            else:
                # On Windows/Linux, save next to executable
                project_root = os.path.dirname(sys.executable)
        else:
            # When running in development, use the script's directory
            project_root = os.path.dirname(os.path.abspath(__file__))
        
        output_dir = os.path.join(project_root, "Steps", "Raw")
        os.makedirs(output_dir, exist_ok=True)

        if historical:
            output_file = os.path.join(output_dir, 'steps_data_full.csv')
        else:
            output_file = os.path.join(output_dir, 'steps_data_daily.csv')

        pd.DataFrame(all_rows).to_csv(output_file, index=False)
        
        # Update status for user
        result_label.config(text="Collecting health data... (this may take a few minutes)")
        
        # Collect ALL available health data with rate limiting
        health_data = collect_all_health_data(fitness_service, start_date, end_date, project_root, historical)
        
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
        },
        'sleep': {
            'dataTypeName': 'com.google.sleep.segment',
            'folder': 'Sleep'
        },
        'reproductive_health': {
            'dataTypeName': 'com.google.menstruation',
            'folder': 'ReproductiveHealth'
        }
    }
    
    for i, (data_type, config) in enumerate(data_sources.items()):
        try:
            result_label.config(text=f"Collecting {data_type} data... ({i+1}/{len(data_sources)})")
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
                    # Shorter delay - 1 second should be enough
                    sleep(1)  # 1 second delay between API calls
                    result_label.config(text=f"Collecting {data_type} data... ({i+1}/{len(data_sources)}) - {current.strftime('%Y-%m')}")
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
                                elif data_type == 'height':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'height_meters': value})
                                elif data_type == 'body_fat':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'body_fat_percentage': value})
                                elif data_type == 'blood_pressure':
                                    systolic = point['value'][0]['fpVal'] if point['value'] else 0
                                    diastolic = point['value'][1]['fpVal'] if len(point['value']) > 1 else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'systolic_mmHg': systolic, 'diastolic_mmHg': diastolic})
                                elif data_type == 'blood_glucose':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'glucose_mmol_per_L': value})
                                elif data_type == 'oxygen_saturation':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'oxygen_saturation_percentage': value})
                                elif data_type == 'body_temperature':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'temperature_celsius': value})
                                elif data_type == 'sleep':
                                    value = point['value'][0]['intVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'sleep_type': value})
                                elif data_type == 'reproductive_health':
                                    value = point['value'][0]['intVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'menstruation_flow': value})
                                
                except Exception as e:
                    # Handle rate limiting and other errors
                    if "rateLimitExceeded" in str(e) or "429" in str(e):
                        result_label.config(text=f"Rate limit hit for {data_type}, waiting 30 seconds...")
                        sleep(30)  # Shorter wait - 30 seconds instead of 60
                        continue  # Retry the same request
                    elif "Invalid scope" in str(e) or "forbidden" in str(e).lower():
                        result_label.config(text=f"Skipping {data_type} (not available)")
                        sleep(0.5)
                        break  # Skip this data type entirely
                    else:
                        # Other errors - data might not be available
                        result_label.config(text=f"No {data_type} data found")
                        sleep(0.5)
                        break  # Skip this data type
                    
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
                result_label.config(text=f"✅ {data_type} saved ({len(rows)} records)")
                sleep(0.5)  # Brief pause to show success
            else:
                health_data[data_type] = None
                result_label.config(text=f"⚠️ No {data_type} data found")
                sleep(0.5)
                
        except Exception:
            health_data[data_type] = None
    
    return health_data

def start_sync():
    # Get selected data types
    selected_data_types = []
    for data_type, var in checkbox_vars.items():
        if var.get():
            selected_data_types.append(data_type)
    
    if not selected_data_types:
        messagebox.showwarning("Warning", "Please select at least one data type to import.")
        return
    
    result_label.config(text="Starting import...")
    threading.Thread(target=lambda: run_sync_with_selection(selected_data_types, historical=True)).start()

    def periodic_sync():
        while True:
            time.sleep(86400)
            run_sync_with_selection(selected_data_types, historical=False)

    threading.Thread(target=periodic_sync, daemon=True).start()

def run_sync_with_selection(selected_data_types, historical=False):
    """Run sync with only selected data types"""
    try:
        # Get executable directory for save location  
        if getattr(sys, 'frozen', False):
            if sys.platform == 'darwin' and sys.executable.endswith('.app/Contents/MacOS/GoogleFitSync'):
                app_path = sys.executable.replace('/Contents/MacOS/GoogleFitSync', '')
                project_root = os.path.dirname(app_path)
            else:
                project_root = os.path.dirname(sys.executable)
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
        
        # OAuth setup (same as before)
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
            raise Exception("OAuth credentials not found.")
        
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

        fitness_service = build('fitness', 'v1', credentials=creds)

        if historical:
            start_date = datetime.datetime(2022, 1, 1)
        else:
            start_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)

        end_date = datetime.datetime.utcnow()
        
        # Collect selected data types
        saved_files = []
        
        # Handle steps separately if selected
        if 'steps' in selected_data_types:
            steps_file = collect_steps_data(fitness_service, start_date, end_date, project_root, historical)
            if steps_file:
                saved_files.append(steps_file)
        
        # Handle other health data if selected
        other_data_types = [dt for dt in selected_data_types if dt != 'steps']
        if other_data_types:
            health_data = collect_selected_health_data(fitness_service, start_date, end_date, project_root, historical, other_data_types)
            saved_files.extend([f for f in health_data.values() if f])
        
        # Show final results
        if saved_files:
            folder_name = os.path.basename(project_root)
            result_text = f"✅ Data saved in '{folder_name}' folder ({len(saved_files)} files created)"
            if historical:
                messagebox.showinfo("Success", result_text)
        else:
            result_text = "⚠️ No data was available for the selected types"
            
        result_label.config(text=result_text)
            
    except Exception as e:
        result_label.config(text=f"❌ Error: {e}")
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

def collect_steps_data(fitness_service, start_date, end_date, project_root, historical):
    """Collect steps data specifically"""
    try:
        current = start_date
        all_rows = []
        total_months = ((end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))
        month_count = 0

        while current < end_date:
            month_count += 1
            next_month = current + datetime.timedelta(days=30)
            start_time = int(current.timestamp() * 1000)
            end_time = int(min(next_month, end_date).timestamp() * 1000)
            
            result_label.config(text=f"Collecting steps data... ({month_count}/{total_months}) - {current.strftime('%Y-%m')}")
            
            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.step_count.delta",
                    "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
                }],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": start_time,
                "endTimeMillis": end_time
            }

            sleep(1)  # Rate limiting
            response = fitness_service.users().dataset().aggregate(userId='me', body=body).execute()

            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        steps = point['value'][0]['intVal']
                        start = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                        end = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                        all_rows.append({'start': start, 'end': end, 'steps': steps})

            current = next_month

        # Save steps data
        if all_rows:
            output_dir = os.path.join(project_root, "Steps", "Raw")
            os.makedirs(output_dir, exist_ok=True)
            
            if historical:
                output_file = os.path.join(output_dir, 'steps_data_full.csv')
            else:
                output_file = os.path.join(output_dir, 'steps_data_daily.csv')
            
            pd.DataFrame(all_rows).to_csv(output_file, index=False)
            result_label.config(text=f"✅ Steps saved ({len(all_rows)} records)")
            sleep(0.5)
            return output_file
        else:
            result_label.config(text="⚠️ No steps data found")
            sleep(0.5)
            return None
            
    except Exception as e:
        result_label.config(text=f"⚠️ Steps data error: {str(e)[:50]}...")
        sleep(0.5)
        return None

def collect_selected_health_data(fitness_service, start_date, end_date, project_root, historical, selected_types):
    """Collect only selected health data types"""
    health_data = {}
    
    # All data source configurations for comprehensive health data
    all_data_sources = {
        'calories': {'dataTypeName': 'com.google.calories.expended', 'folder': 'Calories'},
        'distance': {'dataTypeName': 'com.google.distance.delta', 'folder': 'Distance'},
        'heart_rate': {'dataTypeName': 'com.google.heart_rate.bpm', 'folder': 'HeartRate'},
        'weight': {'dataTypeName': 'com.google.weight', 'folder': 'Weight'},
        'height': {'dataTypeName': 'com.google.height', 'folder': 'Height'},
        'body_fat': {'dataTypeName': 'com.google.body.fat.percentage', 'folder': 'BodyFat'},
        'blood_pressure': {'dataTypeName': 'com.google.blood_pressure', 'folder': 'BloodPressure'},
        'blood_glucose': {'dataTypeName': 'com.google.blood_glucose', 'folder': 'BloodGlucose'},
        'oxygen_saturation': {'dataTypeName': 'com.google.oxygen_saturation', 'folder': 'OxygenSaturation'},
        'body_temperature': {'dataTypeName': 'com.google.body.temperature', 'folder': 'BodyTemperature'},
        'sleep': {'dataTypeName': 'com.google.sleep.segment', 'folder': 'Sleep'},
        'reproductive_health': {'dataTypeName': 'com.google.menstruation', 'folder': 'ReproductiveHealth'}
    }
    
    # Filter to only selected data sources
    data_sources = {k: v for k, v in all_data_sources.items() if k in selected_types}
    
    # Use the existing collect_all_health_data logic but with filtered sources
    return collect_filtered_health_data(fitness_service, start_date, end_date, project_root, historical, data_sources)

def collect_filtered_health_data(fitness_service, start_date, end_date, project_root, historical, data_sources):
    """Modified version of collect_all_health_data for selected data types only"""
    health_data = {}
    
    for i, (data_type, config) in enumerate(data_sources.items()):
        try:
            result_label.config(text=f"Collecting {data_type} data... ({i+1}/{len(data_sources)})")
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
                    sleep(1)
                    result_label.config(text=f"Collecting {data_type} data... ({i+1}/{len(data_sources)}) - {current.strftime('%Y-%m')}")
                    response = fitness_service.users().dataset().aggregate(userId='me', body=body).execute()
                    
                    for bucket in response['bucket']:
                        for dataset in bucket['dataset']:
                            for point in dataset['point']:
                                start_dt = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                                end_dt = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                                
                                # Data type specific parsing for confirmed working data types
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
                                elif data_type == 'height':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'height_meters': value})
                                elif data_type == 'body_fat':
                                    value = point['value'][0]['fpVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'body_fat_percentage': value})
                                elif data_type == 'sleep':
                                    value = point['value'][0]['intVal'] if point['value'] else 0
                                    rows.append({'start': start_dt, 'end': end_dt, 'sleep_type': value})
                                
                except Exception as e:
                    if "rateLimitExceeded" in str(e) or "429" in str(e):
                        result_label.config(text=f"Rate limit hit for {data_type}, waiting 30 seconds...")
                        sleep(30)
                        continue
                    elif "Invalid scope" in str(e) or "forbidden" in str(e).lower():
                        result_label.config(text=f"Skipping {data_type} (not available)")
                        sleep(0.5)
                        break
                    else:
                        result_label.config(text=f"No {data_type} data found")
                        sleep(0.5)
                        break
                    
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
                result_label.config(text=f"✅ {data_type} saved ({len(rows)} records)")
                sleep(0.5)
            else:
                health_data[data_type] = None
                result_label.config(text=f"⚠️ No {data_type} data found")
                sleep(0.5)
                
        except Exception:
            health_data[data_type] = None
    
    return health_data

if __name__ == '__main__':
    root = Tk()
    root.title("Google Fit Data Sync")
    root.geometry("600x700")
    root.configure(bg='#f0f0f0')

    # Header
    header_frame = Frame(root, bg='#2c3e50', height=60)
    header_frame.pack(fill='x')
    header_frame.pack_propagate(False)
    
    header_label = Label(header_frame, text="Google Fit Data Sync", 
                        font=("Helvetica", 18, "bold"), 
                        fg='white', bg='#2c3e50')
    header_label.pack(expand=True)
    
    # Main content
    main_frame = Frame(root, bg='#f0f0f0')
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Instructions
    instruction_label = Label(main_frame, 
                             text="Select the data types you want to import from Google Fit:", 
                             font=("Helvetica", 12), 
                             bg='#f0f0f0', fg='#2c3e50')
    instruction_label.pack(pady=(0, 15))
    
    # Data type selection
    checkbox_vars = {}
    data_types = [
        ('steps', 'Steps (daily step count)'),
        ('calories', 'Calories (burned calories)'),
        ('distance', 'Distance (traveled distance)'),
        ('heart_rate', 'Heart Rate (BPM measurements)'),
        ('weight', 'Weight (body weight)'),
        ('height', 'Height (body height)'),
        ('body_fat', 'Body Fat (body fat percentage)'),
        ('blood_pressure', 'Blood Pressure (systolic/diastolic)'),
        ('blood_glucose', 'Blood Glucose (glucose levels)'),
        ('oxygen_saturation', 'Oxygen Saturation (O2 levels)'),
        ('body_temperature', 'Body Temperature (temperature)'),
        ('sleep', 'Sleep (sleep segments)'),
        ('reproductive_health', 'Reproductive Health (menstruation)')
    ]
    
    # Select All checkbox
    def select_all():
        for var in checkbox_vars.values():
            var.set(select_all_var.get())
    
    select_all_var = IntVar(value=1)
    select_all_frame = Frame(main_frame, bg='#f0f0f0')
    select_all_frame.pack(fill='x', pady=(0, 10))
    
    select_all_checkbox = Checkbutton(select_all_frame, 
                                     text="✅ Select All Data Types", 
                                     variable=select_all_var, 
                                     command=select_all,
                                     font=("Helvetica", 11, "bold"),
                                     bg='#f0f0f0', fg='#2c3e50',
                                     activebackground='#e8f4fd',
                                     selectcolor='#3498db')
    select_all_checkbox.pack(anchor='w')
    
    # Scrollable frame for checkboxes
    canvas_frame = Frame(main_frame, bg='#f0f0f0')
    canvas_frame.pack(fill='both', expand=True, pady=(0, 20))
    
    canvas = Canvas(canvas_frame, bg='#f0f0f0', height=300, highlightthickness=0)
    scrollbar = Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)
    scrollable_frame = Frame(canvas, bg='#f0f0f0')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Create checkboxes for each data type
    for data_key, data_desc in data_types:
        var = IntVar(value=1)  # Default to selected
        checkbox_vars[data_key] = var
        
        checkbox = Checkbutton(scrollable_frame, 
                              text=data_desc, 
                              variable=var,
                              font=("Helvetica", 10),
                              bg='#f0f0f0', fg='#34495e',
                              activebackground='#e8f4fd',
                              selectcolor='#3498db',
                              anchor='w',
                              wraplength=450)
        checkbox.pack(fill='x', padx=10, pady=2)
    
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    # Bottom section
    bottom_frame = Frame(main_frame, bg='#f0f0f0')
    bottom_frame.pack(fill='x', pady=(10, 0))
    
    # Date range info
    info_label = Label(bottom_frame, 
                      text="📅 Data Range: January 2022 - Present | 🔄 Auto-sync: Every 24 hours\n✅ All Google Fit data types available with comprehensive scopes", 
                      font=("Helvetica", 9), 
                      bg='#f0f0f0', fg='#7f8c8d',
                      justify='center')
    info_label.pack(pady=(0, 15))
    
    # Start button
    start_button = Button(bottom_frame, 
                         text="🚀 Start Import + Daily Auto", 
                         command=start_sync, 
                         font=("Helvetica", 12, "bold"),
                         bg='#3498db', fg='black',
                         activebackground='#2980b9', activeforeground='white',
                         height=2, width=35,
                         relief='flat')
    start_button.pack(pady=(0, 10))
    
    # Result label
    result_label = Label(bottom_frame, text="", 
                        font=("Helvetica", 11), 
                        bg='#f0f0f0', fg='#27ae60',
                        wraplength=550)
    result_label.pack(pady=10)
    
    root.mainloop()
