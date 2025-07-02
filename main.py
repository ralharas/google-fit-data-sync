import os
import sys
import datetime
import threading
import time
import pandas as pd
import tkinter.messagebox as messagebox
import platform

from tkinter import Tk, Button, Label, Checkbutton, IntVar, Frame
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ✅ FULL Google Fit SCOPES
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.nutrition.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

# ✅ Data types to fetch
DATA_SOURCES = {
    'steps': {'dataTypeName': 'com.google.step_count.delta', 'folder': 'Steps'},
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
    'nutrition': {'dataTypeName': 'com.google.nutrition', 'folder': 'Nutrition'},
    'hydration': {'dataTypeName': 'com.google.hydration', 'folder': 'Hydration'},
    'activity_segment': {'dataTypeName': 'com.google.activity.segment', 'folder': 'ActivitySegment'},
    'elevation': {'dataTypeName': 'com.google.elevation.gain', 'folder': 'Elevation'},
    'cycling_wheel_revolution': {'dataTypeName': 'com.google.cycling.wheel_revolution.cumulative', 'folder': 'CyclingWheelRevolution'}
}


def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def run_sync(selected_data_types, historical=False):
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            config_file = resource_path("oauth_config.json")
            if os.path.exists(config_file):
                import json
                with open(config_file) as f:
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
                creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        service = build('fitness', 'v1', credentials=creds)

        if historical:
            start_date = datetime.datetime(2022, 1, 1)
        else:
            start_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        end_date = datetime.datetime.utcnow()

        root_dir = get_executable_dir()
        imported = []

        for key in selected_data_types:
            conf = DATA_SOURCES[key]
            rows = []
            current = start_date
            while current < end_date:
                next_month = current + datetime.timedelta(days=30)
                body = {
                    "aggregateBy": [{"dataTypeName": conf['dataTypeName']}],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": int(current.timestamp() * 1000),
                    "endTimeMillis": int(min(next_month, end_date).timestamp() * 1000)
                }
                resp = service.users().dataset().aggregate(userId='me', body=body).execute()
                for bucket in resp.get('bucket', []):
                    for dataset in bucket['dataset']:
                        for point in dataset['point']:
                            start = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                            end = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                            value = point['value'][0]
                            if 'intVal' in value:
                                val = value['intVal']
                            elif 'fpVal' in value:
                                val = value['fpVal']
                            else:
                                val = str(value)
                            rows.append({'start': start, 'end': end, 'value': val})
                current = next_month

            if rows:
                outdir = os.path.join(root_dir, conf['folder'], 'Raw')
                os.makedirs(outdir, exist_ok=True)
                fname = f"{key}_data_{'full' if historical else 'daily'}.csv"
                pd.DataFrame(rows).to_csv(os.path.join(outdir, fname), index=False)
                imported.append(key)

        if imported:
            result_label.config(text=f"✅ Imported: {', '.join(imported)}")
        else:
            result_label.config(text="⚠️ No data found")

    except Exception as e:
        result_label.config(text=f"❌ Error: {e}")
        messagebox.showerror("Error", str(e))


def start_sync():
    selected = [k for k, var in checkbox_vars.items() if var.get()]
    if not selected:
        messagebox.showwarning("Nothing selected", "Select at least one data type.")
        return
    result_label.config(text="🔄 Importing...")
    threading.Thread(target=lambda: run_sync(selected, historical=True)).start()


if __name__ == "__main__":
    root = Tk()
    root.title("Google Fit Full Data Import")

    checkbox_vars = {}
    for k in DATA_SOURCES:
        checkbox_vars[k] = IntVar(value=1)

    Label(root, text="Select Google Fit Data Types:").pack(pady=10)
    for k in DATA_SOURCES:
        Checkbutton(root, text=k, variable=checkbox_vars[k]).pack(anchor="w")

    Button(root, text="Run Full Import", command=start_sync).pack(pady=15)
    result_label = Label(root, text="")
    result_label.pack(pady=10)

    root.mainloop()
