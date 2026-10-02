import json
import os
import re
import http.server
import socketserver
import requests

PORT = 3456
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are an expert LangGraph 0.2+ system architect.
Given a user requirement for a workflow or flowchart, return ONLY a valid, parseable JSON object matching this schema strictly without markdown fencing:
{
  "title": "Title of the Workflow",
  "stateName": "AgentStateName",
  "stateSchema": "class AgentStateName(TypedDict):\\n    messages: Annotated[list[BaseMessage], add_messages]\\n    ...",
  "nodes": [
    {
      "id": "node_id_slug",
      "type": "start" | "agent" | "conditional" | "subgraph" | "end",
      "label": "Short Title",
      "desc": "Role description",
      "color": "#38bdf8",
      "icon": "bot",
      "stateKeys": ["key1", "key2"],
      "interrupt": "interrupt_before" or null,
      "condition": "def check_condition(state)" or null
    }
  ],
  "edges": [
    {
      "from": "source_node_id",
      "to": "target_node_id",
      "label": "condition or action",
      "type": "fixed" | "conditional"
    }
  ],
  "pythonCode": "from langgraph.graph import StateGraph, START, END\\n..."
}
Make sure:
1. Exactly one 'start' node (type 'start') and at least one 'end' node (type 'end').
2. Node icons should be common Lucide icons (e.g. 'play', 'bot', 'cpu', 'shield-check', 'split', 'flag', 'user-check', 'database', 'terminal').
3. The graph must be logically coherent and reflect advanced LangGraph concepts.
"""

class LangGraphHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
                prompt = data.get("prompt", "")
                user_key = data.get("apiKey") or GROQ_API_KEY
                
                headers = {
                    "Authorization": f"Bearer {user_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                groq_payload = {
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Generate a complete LangGraph 0.2 workflow specification for: {prompt}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                }
                
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=groq_payload,
                    timeout=30
                )
                
                if res.status_code != 200:
                    raise Exception(f"Groq API error {res.status_code}: {res.text}")
                
                raw_content = res.json()["choices"][0]["message"]["content"]
                
                # Clean any markdown tags
                cleaned = re.sub(r"^```json\s*", "", raw_content.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                
                # Validate JSON parse
                parsed_json = json.loads(cleaned)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(parsed_json).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LangGraphHandler) as httpd:
        print(f"LangGraph Server running on http://localhost:{PORT}")
        httpd.serve_forever()
