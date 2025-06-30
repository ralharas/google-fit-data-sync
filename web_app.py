#!/usr/bin/env python3
"""
Web-based Google Fit Sync - Works on any platform
Run this and access via web browser at http://localhost:5000
"""

import os
import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read']

def get_google_fit_data(historical=False):
    """Fetch Google Fit data"""
    client_secret_file = 'client_secret.json'
    token_file = os.path.expanduser('~/.google_fit_token.json')
    
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        else:
            return None  # Need to authorize first

    fitness_service = build('fitness', 'v1', credentials=creds)

    if historical:
        start_date = datetime.datetime(2022, 1, 1)
    else:
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=7)

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
                    start_dt = datetime.datetime.fromtimestamp(int(point['startTimeNanos']) / 1e9)
                    end_dt = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1e9)
                    all_rows.append({'start': start_dt, 'end': end_dt, 'steps': steps})

        current = next_month

    # Save to CSV
    output_dir = os.path.join(os.getcwd(), "Steps", "Raw")
    os.makedirs(output_dir, exist_ok=True)
    
    if historical:
        output_file = os.path.join(output_dir, 'steps_data_full.csv')
    else:
        output_file = os.path.join(output_dir, 'steps_data_recent.csv')

    pd.DataFrame(all_rows).to_csv(output_file, index=False)
    return output_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    from flask import session
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    from flask import session
    
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        state=session['state'],
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    flow.fetch_token(authorization_response=request.url)
    
    # Save credentials
    token_file = os.path.expanduser('~/.google_fit_token.json')
    with open(token_file, 'w') as token:
        token.write(flow.credentials.to_json())
    
    flash('✅ Successfully authorized with Google Fit!')
    return redirect(url_for('index'))

@app.route('/sync', methods=['POST'])
def sync():
    sync_type = request.form.get('sync_type')
    historical = (sync_type == 'historical')
    
    try:
        output_file = get_google_fit_data(historical=historical)
        if output_file:
            flash(f'✅ Sync completed! Data saved to {output_file}')
            return send_file(output_file, as_attachment=True)
        else:
            flash('❌ Please authorize with Google first')
            return redirect(url_for('authorize'))
    except Exception as e:
        flash(f'❌ Error: {str(e)}')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create templates directory and basic HTML
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Google Fit Sync</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        button { padding: 15px 30px; margin: 10px; font-size: 16px; }
        .success { color: green; } .error { color: red; }
    </style>
</head>
<body>
    <h1>🏃‍♂️ Google Fit Data Sync</h1>
    
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <p class="{% if '✅' in message %}success{% else %}error{% endif %}">{{ message }}</p>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <h3>Step 1: Authorize Google Fit Access</h3>
    <a href="/authorize"><button>🔐 Authorize with Google</button></a>
    
    <h3>Step 2: Sync Your Data</h3>
    <form method="post" action="/sync">
        <button type="submit" name="sync_type" value="recent">📅 Sync Recent (7 days)</button>
        <button type="submit" name="sync_type" value="historical">📊 Full Historical Sync</button>
    </form>
    
    <p><em>Files will be automatically downloaded when sync completes.</em></p>
</body>
</html>'''
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)
    
    print("🌐 Starting Google Fit Sync Web App...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🖥️  This works on Windows, Mac, Linux - any device with a web browser!")
    
    app.run(debug=True, port=5000)

