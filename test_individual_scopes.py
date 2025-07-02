
from google_auth_oauthlib.flow import InstalledAppFlow
import json

individual_scopes = [
    ['https://www.googleapis.com/auth/fitness.activity.read'],
    ['https://www.googleapis.com/auth/fitness.body.read'],
    ['https://www.googleapis.com/auth/fitness.location.read'],
    ['https://www.googleapis.com/auth/fitness.sleep.read']
]

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

for i, scopes in enumerate(individual_scopes, 1):
    scope_name = scopes[0].split('.')[-1]
    print(f"\n🧪 Test {i}: Testing {scope_name}")
    print(f"   Scope: {scopes[0]}")
    
    try:
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        print(f"   ✅ Flow created successfully for {scope_name}")
    except Exception as e:
        print(f"   ❌ Error with {scope_name}: {e}")

print(f"\n🔬 Testing all scopes together:")
all_scopes = [scope[0] for scope in individual_scopes]
print("Scopes being tested:")
for scope in all_scopes:
    print(f"  - {scope}")

try:
    flow = InstalledAppFlow.from_client_config(client_config, all_scopes)
    print("✅ All scopes flow created successfully")
    print("🌐 Try this authorization URL manually:")
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(auth_url)
except Exception as e:
    print(f"❌ Error with combined scopes: {e}")

