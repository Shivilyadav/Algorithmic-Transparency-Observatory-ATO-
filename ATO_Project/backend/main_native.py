import json
import http.server
import socketserver
import mock_models
import os

PORT = 8000

class ATOResponseHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_GET(self):
        try:
            # Serve the frontend files if requested from the root
            if self.path == '/' or self.path == '/index.html':
                self.serve_static_file('../frontend/index.html', 'text/html')
                return
            elif self.path.startswith('/css/') or self.path.startswith('/js/'):
                content_type = 'text/css' if '.css' in self.path else 'application/javascript'
                self.serve_static_file('../frontend' + self.path, content_type)
                return

            # Handle API routes
            response_data = None
            
            if self.path == '/api/health':
                response_data = {"status": "System Online", "version": "1.0.0"}
            elif self.path == '/api/dashboard/metrics':
                response_data = mock_models.get_real_time_metrics()
            elif self.path == '/api/bias/analytics':
                response_data = mock_models.get_bias_metrics()
            elif self.path == '/api/decisions/recent':
                response_data = mock_models.get_recent_decisions_for_dropdown()
            elif self.path.startswith('/api/xai/explain/'):
                decision_id = self.path.split('/')[-1]
                response_data = mock_models.get_xai_explanation(decision_id)
            elif self.path == '/api/compliance/logs':
                response_data = {"logs": mock_models.get_compliance_logs()}
            elif self.path == '/api/agents/architectures':
                response_data = {"architectures": mock_models.get_agent_architectures()}
            elif self.path == '/api/database/raw':
                response_data = mock_models.get_raw_database_logs()

            if response_data is not None:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))
        except Exception as e:
            print(f"[CRITICAL ERROR] : {e}")
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            except:
                pass

    def serve_static_file(self, file_path, content_type):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.normpath(os.path.join(base_dir, file_path))
            
            if not os.path.exists(full_path):
                print(f"[ERROR] : Static file not found: {full_path}")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found")
                return

            with open(full_path, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            print(f"[ERROR] : Failed to serve {file_path}: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Server Error: {e}".encode())



if __name__ == "__main__":
    Handler = ATOResponseHandler
    # Change working directory so SimpleHTTPRequestHandler finds files correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    socketserver.TCPServer.allow_reuse_address = True
    # Explicitly bind to 0.0.0.0 and use Threading for concurrent UI/API requests
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"ATO API Server running on http://localhost:{PORT}")
        httpd.serve_forever()
