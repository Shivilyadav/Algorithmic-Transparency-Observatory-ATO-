"""
Award-grade minimal server for the Algorithmic Transparency Observatory (ATO).
Runs with Python stdlib only and serves both API + frontend.
"""
import json
import os
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer

import ato_db
import mock_models

PORT = 8080


class ATOHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, relative_path, content_type):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.normpath(os.path.join(base_dir, relative_path))
        if not os.path.exists(full_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        with open(full_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            return self._serve_file("../frontend/index.html", "text/html")
        if path.startswith("/css/"):
            return self._serve_file(f"../frontend{path}", "text/css")
        if path.startswith("/js/"):
            return self._serve_file(f"../frontend{path}", "application/javascript")

        try:
            if path == "/api/health":
                return self._send_json({"status": "System Online", "version": "2.0.0"})
            if path == "/api/dashboard/metrics":
                return self._send_json(mock_models.get_real_time_metrics())
            if path == "/api/bias/analytics":
                return self._send_json(mock_models.get_bias_metrics())
            if path == "/api/decisions/recent":
                return self._send_json(mock_models.get_recent_decisions_for_dropdown())
            if path.startswith("/api/xai/explain/"):
                return self._send_json(mock_models.get_xai_explanation(path.rsplit("/", 1)[-1]))
            if path == "/api/compliance/logs":
                return self._send_json({"logs": mock_models.get_compliance_logs()})
            if path == "/api/database/raw":
                return self._send_json(mock_models.get_raw_database_logs())
            if path == "/api/agents/architectures":
                return self._send_json({"architectures": mock_models.get_agent_architectures()})

            # Research-paper aligned new modules
            if path == "/api/research/abstract":
                return self._send_json(mock_models.get_research_abstract())
            if path == "/api/flowchart/stages":
                return self._send_json(mock_models.get_flowchart_stages())
            if path == "/api/data-collection/status":
                return self._send_json(mock_models.get_sector_collection_status())
            if path == "/api/fairness/snapshot":
                return self._send_json(mock_models.get_fairness_snapshot())
            if path == "/api/governance/compliance":
                return self._send_json(mock_models.get_governance_compliance_snapshot())
            if path == "/api/evaluation/report":
                return self._send_json(mock_models.get_evaluation_report())
            if path == "/api/reports/transparency":
                return self._send_json(mock_models.get_transparency_report())
            if path == "/api/compliance/report":
                return self._send_json(mock_models.get_transparency_report())

            return self._send_json({"error": "Not found", "path": path}, 404)
        except Exception as exc:
            return self._send_json({"error": str(exc)}, 500)

    def do_POST(self):
        path = self.path.split("?")[0]
        
        if path == "/api/log_decision":
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return self._send_json({"error": "Empty payload"}, 400)
            
            try:
                body = self.rfile.read(content_length).decode('utf-8')
                payload = json.loads(body)
                
                # Dynamic import to avoid circular dependency if not in root
                import ato_sdk
                
                required_keys = ['model_name', 'sector', 'demographic_group', 'demographic_tag', 'outcome', 'score', 'features', 'feature_importance']
                for key in required_keys:
                    if key not in payload:
                        return self._send_json({"error": f"Missing required parameter: {key}"}, 400)
                
                dec_id = ato_sdk.log_decision(
                    model_name=payload['model_name'],
                    sector=payload['sector'],
                    demographic_group=payload['demographic_group'],
                    demographic_tag=payload['demographic_tag'],
                    outcome=payload['outcome'],
                    score=payload['score'],
                    features=payload['features'],
                    feature_importance=payload['feature_importance'],
                    logic_steps=payload.get('logic_steps', []),
                    has_alert=payload.get('has_alert', 0),
                    alert_reason=payload.get('alert_reason', "")
                )
                
                if dec_id:
                    return self._send_json({"status": "success", "decision_id": dec_id}, 201)
                else:
                    return self._send_json({"error": "Failed to log decision to database"}, 500)
                    
            except json.JSONDecodeError:
                return self._send_json({"error": "Invalid JSON mapping"}, 400)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)
                
        return self._send_json({"error": "Not found", "path": path}, 404)


if __name__ == "__main__":
    ato_db.init_db()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ThreadingTCPServer.allow_reuse_address = True
    with ThreadingTCPServer(("0.0.0.0", PORT), ATOHandler) as server:
        print(f"ATO minimal server running at http://localhost:{PORT}")
        print("Serving UI + core API + advanced research endpoints")
        server.serve_forever()
