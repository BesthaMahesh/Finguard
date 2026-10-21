import os
import sys
import uvicorn
import secrets

# Enable immediate output flushing for cloud logging services like Render
os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

if __name__ == "__main__":
    # Ensure strong cryptographic SECRET_KEY in production cloud environments (e.g. Render)
    current_secret = os.environ.get("SECRET_KEY", "")
    insecure_keys = [
        "finguard-enterprise-autonomous-risk-intelligence-secure-jwt-key",
        "finguard-secret-key-for-development-change-in-production",
        "secret", "changeme", "password"
    ]
    if not current_secret or current_secret in insecure_keys or len(current_secret) < 32:
        ephemeral_secret = secrets.token_urlsafe(48)
        os.environ["SECRET_KEY"] = ephemeral_secret
        print("[FinGuard] Notice: Auto-generated ephemeral 48-byte SECRET_KEY for cloud runtime.", flush=True)

    port_str = os.environ.get("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"[FinGuard] Warning: Invalid PORT '{port_str}', defaulting to 8000", flush=True)
        port = 8000

    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[FinGuard] Starting Uvicorn on {host}:{port}...", flush=True)
    uvicorn.run("backend.main:app", host=host, port=port, log_level="info")

