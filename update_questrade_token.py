import os
import json
import urllib.request
import urllib.parse
import base64

def get_new_questrade_token(current_refresh_token):
    """Exchange current refresh token for a new one."""
    url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={current_refresh_token}"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Length", "0")
    
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    print(f"✅ Got new Questrade token. API server: {data['api_server']}")
    return data['refresh_token']

def update_github_secret(token, secret_name, repo, gh_token):
    """Update a GitHub Actions secret using the GitHub API."""
    
    # Step 1: Get repo public key for encryption
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {gh_token}")
    req.add_header("Accept", "application/vnd.github+json")
    
    with urllib.request.urlopen(req) as response:
        key_data = json.loads(response.read().decode())
    
    key_id = key_data["key_id"]
    public_key = key_data["key"]
    
    # Step 2: Encrypt the secret using libsodium
    try:
        from base64 import b64decode, b64encode
        from nacl.public import PublicKey, SealedBox
        
        public_key_bytes = b64decode(public_key)
        sealed_box = SealedBox(PublicKey(public_key_bytes))
        encrypted = sealed_box.encrypt(token.encode())
        encrypted_value = b64encode(encrypted).decode()
    except ImportError:
        print("ERROR: PyNaCl not installed. Run: pip install PyNaCl")
        raise

    # Step 3: Update the secret
    url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    payload = json.dumps({
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }).encode()
    
    req = urllib.request.Request(url, data=payload, method="PUT")
    req.add_header("Authorization", f"Bearer {gh_token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    
    with urllib.request.urlopen(req) as response:
        print(f"✅ GitHub secret '{secret_name}' updated successfully!")

if __name__ == "__main__":
    # Read from environment
    current_token = os.environ.get("QUESTRADE_REFRESH_TOKEN", "")
    gh_token = os.environ.get("GH_PUSH_TOKEN", "")
    repo = "snapscenes4-hue/workflows"
    
    if not current_token:
        print("ERROR: QUESTRADE_REFRESH_TOKEN not set")
        raise SystemExit(1)
    
    if not gh_token:
        print("ERROR: GH_PUSH_TOKEN not set")
        raise SystemExit(1)
    
    print("🔄 Rotating Questrade refresh token...")
    new_token = get_new_questrade_token(current_token)
    
    print("🔐 Updating GitHub secret...")
    update_github_secret(new_token, "QUESTRADE_REFRESH_TOKEN", repo, gh_token)
    
    print("✅ Token rotation complete! New token saved to GitHub secrets.")
