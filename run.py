import os
import sys
import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"[FinGuard] Warning: Invalid PORT '{port_str}', defaulting to 8000", flush=True)
        port = 8000

    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[FinGuard] Successfully bound and listening on {host}:{port}", flush=True)
    uvicorn.run("backend.main:app", host=host, port=port, log_level="info")
