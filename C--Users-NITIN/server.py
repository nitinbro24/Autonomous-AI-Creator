import json
import os
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess
import threading

BASE_DIR = r".claude\projects\C--Users-NITIN\memory"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/agent/init':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                persona = data.get('persona')
                if not persona or 'name' not in persona or 'domain' not in persona:
                    self.send_error(400, "Invalid persona")
                    return
                # Generate agentId
                agent_id = str(uuid.uuid4())
                # Create agent directory
                agent_dir = os.path.join(BASE_DIR, agent_id)
                os.makedirs(agent_dir, exist_ok=True)
                # Write persona.json
                persona_file = os.path.join(agent_dir, 'persona.json')
                with open(persona_file, 'w') as f:
                    json.dump(persona, f)
                # Initialize posts.json
                posts_file = os.path.join(agent_dir, 'posts.json')
                with open(posts_file, 'w') as f:
                    json.dump([], f)
                # Start the agent script in the background
                agent_script = os.path.join(r".claude\projects\C--Users-NITIN", 'agent.py')
                # We pass the agent_dir as an argument
                subprocess.Popen(['python', agent_script, '--agentDir', agent_dir],
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                # Return agentId
                response_data = {
                    "agentId": agent_id
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/agent/feed':
            query_params = parse_qs(parsed_path.query)
            agent_id_list = query_params.get('agentId')
            if not agent_id_list or len(agent_id_list) == 0:
                self.send_error(400, "Missing agentId")
                return
            agent_id = agent_id_list[0]
            # Construct the path to the posts.json file
            posts_file = os.path.join(BASE_DIR, agent_id, "posts.json")
            try:
                with open(posts_file, 'r') as f:
                    posts = json.load(f)
            except FileNotFoundError:
                posts = []
            except json.JSONDecodeError:
                posts = []

            # Sort posts by createdAt descending
            try:
                posts.sort(key=lambda x: x['createdAt'], reverse=True)
            except:
                # If there's an error in sorting, just use the list as is
                pass

            response_data = {
                "posts": posts
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

if __name__ == '__main__':
    port = 5000
    server_address = ('', port)
    httpd = HTTPServer(server_address, Handler)
    print(f"Server running on port {port}")
    httpd.serve_forever()