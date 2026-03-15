"""
ATO Pure-Stdlib HTTP API Server
Serves all endpoints required by the frontend dashboard.
No third-party dependencies - works on any Python 3.x installation.
"""
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import ato_db
import mock_models

PORT = 8080


class ATOHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Quiet logging
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # CORS headers so the frontend (opened via file://) can talk to us
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]  # Strip query params

        # --- Health ---
        if path == "/api/health":
            self.send_json({"status": "System Online", "version": "1.0.0"})

        # --- Dashboard Metrics ---
        elif path == "/api/dashboard/metrics":
            try:
                data = mock_models.get_real_time_metrics()
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- Bias Analytics ---
        elif path == "/api/bias/analytics":
            try:
                data = mock_models.get_bias_metrics()
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- Recent Decisions (for XAI dropdown) ---
        elif path == "/api/decisions/recent":
            try:
                data = mock_models.get_recent_decisions_for_dropdown()
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- XAI Explain ---
        elif path.startswith("/api/xai/explain/"):
            decision_id = path[len("/api/xai/explain/"):]
            try:
                data = mock_models.get_xai_explanation(decision_id)
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- Compliance Logs ---
        elif path == "/api/compliance/logs":
            try:
                logs = mock_models.get_compliance_logs()
                self.send_json({"logs": logs})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- Raw Database Logs ---
        elif path == "/api/database/raw":
            try:
                data = mock_models.get_raw_database_logs()
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        # --- Agent Architectures ---
        elif path == "/api/agents/architectures":
            try:
                data = mock_models.get_agent_architectures()
                self.send_json({"architectures": data})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        else:
            self.send_json({"error": "Not found", "path": path}, 404)


def main():
    print("Initializing ATO Database...", flush=True)
    ato_db.init_db()
    print(f"ATO API Server starting on http://localhost:{PORT}", flush=True)
    print("Endpoints: /api/health | /api/dashboard/metrics | /api/bias/analytics", flush=True)
    print("           /api/decisions/recent | /api/xai/explain/<id>", flush=True)
    print("           /api/compliance/logs | /api/database/raw | /api/agents/architectures", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    server = HTTPServer(("", PORT), ATOHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
