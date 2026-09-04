import sys
import os
import traceback

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import app
except Exception as e:
    tb = traceback.format_exc()
    print("FATAL ERROR LOADING FLASK APP:", tb, file=sys.stderr)

    # Fallback WSGI application to show the exact traceback in the browser
    def app(environ, start_response):
        status = "200 OK"
        headers = [("Content-type", "text/html; charset=utf-8")]
        start_response(status, headers)
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Serverless Diagnostic Log</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; background: #0b0f19; color: #e2e8f0; padding: 2rem; }}
        h1 {{ color: #f43f5e; font-size: 1.5rem; }}
        pre {{ background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; color: #f87171; overflow-x: auto; font-size: 13px; line-height: 1.6; }}
        .meta {{ color: #94a3b8; font-size: 13px; margin-top: 1rem; }}
    </style>
</head>
<body>
    <h1>Function Startup Exception</h1>
    <p class="meta">The serverless container encountered an error during initialization:</p>
    <pre>{tb}</pre>
    <div class="meta">
        <p><strong>CWD:</strong> {os.getcwd()}</p>
        <p><strong>Root Dir:</strong> {root_dir}</p>
        <p><strong>Files in Root:</strong> {os.listdir(root_dir) if os.path.exists(root_dir) else 'N/A'}</p>
        <p><strong>Sys Path:</strong> {sys.path}</p>
    </div>
</body>
</html>"""
        return [html.encode("utf-8")]
