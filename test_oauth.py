

from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

print("🔍 Testing OAuth with these exact scopes:")
for i, scope in enumerate(SCOPES, 1):
    print(f"  {i}. {scope}")

with open('oauth_config.json', 'r') as f:
    config = json.load(f)

client_config = {
    "installed": {
        "client_id": config["client_id"],
        "project_id": "dataautomation-464320",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config["client_secret"],
        "redirect_uris": ["http://localhost"]
    }
}

print(f"\n🔑 Using Client ID: {config['client_id'][:20]}...")
print(f"🔒 Using Client Secret: {config['client_secret'][:15]}...")

try:
    print("\n🚀 Starting OAuth flow...")
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    print("\n✅ OAuth successful!")
    print("📋 Token info:")
    token_info = json.loads(creds.to_json())
    print(f"  - Valid: {creds.valid}")
    print(f"  - Scopes: {token_info.get('scopes', 'Not found')}")
    from googleapiclient.discovery import build
    fitness_service = build('fitness', 'v1', credentials=creds)
    print("\n✅ Google Fit service built successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

