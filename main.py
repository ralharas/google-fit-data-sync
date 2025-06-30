import os
import sys
import datetime
import threading
import time
import pandas as pd
import tkinter.messagebox as messagebox

from tkinter import Tk, Button, Label
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read']

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

        # Save output to project root directory
        if getattr(sys, 'frozen', False):
            # When running as packaged app, save to a fixed project location
            project_root = "/Users/rawad/documents/projects/dataAutomationProject"
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

        if historical:
            result_label.config(text=f"✅ Full history saved!")
            messagebox.showinfo("Success", f"ALL steps data saved to:\n{output_file}")
        else:
            result_label.config(text=f"✅ Daily sync done!")
            # Note: GUI-only mode, no console output

    except Exception as e:
        result_label.config(text=f"❌ Error: {e}")
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

def start_sync():
    threading.Thread(target=lambda: run_sync(historical=True)).start()

    def periodic_sync():
        while True:
            time.sleep(86400)
            run_sync(historical=False)

    threading.Thread(target=periodic_sync, daemon=True).start()

if __name__ == '__main__':
    root = Tk()
    root.title("Google Fit Full Sync")
    root.geometry("400x200")

    Label(root, text="Connect & Sync ALL Google Fit Data", font=("Helvetica", 14)).pack(pady=20)
    Button(root, text="Start Full Import + Daily Auto", command=start_sync, height=2, width=30).pack()
    result_label = Label(root, text="", font=("Helvetica", 12))
    result_label.pack(pady=20)

    root.mainloop()
