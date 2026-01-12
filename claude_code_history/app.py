#!/usr/bin/env python3
"""
Claude Code History Viewer
A simple web app to view conversation history from Claude Code.
"""

import json
import os
import socket
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import html

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def get_projects():
    """Get list of all Claude Code projects."""
    projects = []
    if CLAUDE_PROJECTS_DIR.exists():
        for item in CLAUDE_PROJECTS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Convert folder name back to readable path
                readable_name = item.name.replace('-', '/')
                if readable_name.startswith('/'):
                    readable_name = readable_name[1:]
                projects.append({
                    'folder': item.name,
                    'name': readable_name,
                    'path': str(item)
                })
    return sorted(projects, key=lambda x: x['name'])


def get_conversations(project_folder):
    """Get list of conversations for a project."""
    project_path = CLAUDE_PROJECTS_DIR / project_folder
    conversations = []

    if project_path.exists():
        for jsonl_file in project_path.glob("*.jsonl"):
            # Skip agent files for main conversation list
            if jsonl_file.name.startswith('agent-'):
                continue

            # Get first message to determine conversation start
            summary = None
            first_user_msg = None
            timestamp = None

            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if data.get('type') == 'summary':
                                summary = data.get('summary', '')
                            elif data.get('type') == 'user' and not first_user_msg:
                                msg = data.get('message', {})
                                content = msg.get('content', '')
                                if isinstance(content, str):
                                    first_user_msg = content[:100]
                                timestamp = data.get('timestamp', '')
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

            conversations.append({
                'file': jsonl_file.name,
                'session_id': jsonl_file.stem,
                'summary': summary or first_user_msg or 'No content',
                'timestamp': timestamp or ''
            })

    # Sort by timestamp descending
    return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)


def parse_message_content(content):
    """Parse message content which can be string or list of content blocks."""
    if isinstance(content, str):
        return html.escape(content)

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                block_type = block.get('type', '')
                if block_type == 'text':
                    parts.append(html.escape(block.get('text', '')))
                elif block_type == 'thinking':
                    thinking = block.get('thinking', '')
                    if thinking:
                        escaped = html.escape(thinking)
                        parts.append(f'<details class="thinking"><summary>💭 Thinking...</summary><pre>{escaped}</pre></details>')
                elif block_type == 'tool_use':
                    tool_name = block.get('name', 'Unknown Tool')
                    tool_input = json.dumps(block.get('input', {}), indent=2)
                    parts.append(f'<div class="tool-use"><strong>🔧 {html.escape(tool_name)}</strong><pre>{html.escape(tool_input)}</pre></div>')
                elif block_type == 'tool_result':
                    result = block.get('content', '')
                    if isinstance(result, str):
                        parts.append(f'<div class="tool-result"><pre>{html.escape(result[:500])}{"..." if len(result) > 500 else ""}</pre></div>')
        return '\n'.join(parts)

    return str(content)


def get_conversation_messages(project_folder, session_id):
    """Get all messages from a conversation."""
    jsonl_path = CLAUDE_PROJECTS_DIR / project_folder / f"{session_id}.jsonl"
    messages = []

    if jsonl_path.exists():
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    msg_type = data.get('type', '')

                    if msg_type == 'user':
                        msg = data.get('message', {})
                        content = msg.get('content', '')
                        messages.append({
                            'role': 'user',
                            'content': parse_message_content(content),
                            'timestamp': data.get('timestamp', '')
                        })
                    elif msg_type == 'assistant':
                        msg = data.get('message', {})
                        content = msg.get('content', [])
                        messages.append({
                            'role': 'assistant',
                            'content': parse_message_content(content),
                            'timestamp': data.get('timestamp', ''),
                            'model': msg.get('model', '')
                        })
                except json.JSONDecodeError:
                    continue

    return messages


class HistoryHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for the history viewer."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            self.send_html(self.render_home())
        elif path == '/api/projects':
            self.send_json(get_projects())
        elif path == '/api/conversations':
            project = params.get('project', [''])[0]
            self.send_json(get_conversations(project))
        elif path == '/api/messages':
            project = params.get('project', [''])[0]
            session = params.get('session', [''])[0]
            self.send_json(get_conversation_messages(project, session))
        elif path == '/project':
            project = params.get('name', [''])[0]
            self.send_html(self.render_project(project))
        elif path == '/conversation':
            project = params.get('project', [''])[0]
            session = params.get('session', [''])[0]
            self.send_html(self.render_conversation(project, session))
        else:
            self.send_error(404)

    def send_html(self, content):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def render_home(self):
        projects = get_projects()
        project_list = ''.join([
            f'<a href="/project?name={p["folder"]}" class="project-card">'
            f'<div class="project-name">{html.escape(p["name"])}</div>'
            f'</a>'
            for p in projects
        ])

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Code History Viewer</title>
    {self.get_styles()}
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Claude Code History Viewer</h1>
            <p class="subtitle">View your conversation history from Claude Code</p>
        </header>
        <main>
            <h2>Projects</h2>
            <div class="project-grid">
                {project_list if project_list else '<p>No projects found</p>'}
            </div>
        </main>
    </div>
</body>
</html>'''

    def render_project(self, project_folder):
        conversations = get_conversations(project_folder)
        readable_name = project_folder.replace('-', '/')[1:] if project_folder.startswith('-') else project_folder.replace('-', '/')

        conv_list = ''.join([
            f'<a href="/conversation?project={project_folder}&session={c["session_id"]}" class="conversation-card">'
            f'<div class="conv-summary">{html.escape(c["summary"][:80])}{"..." if len(c["summary"]) > 80 else ""}</div>'
            f'<div class="conv-time">{c["timestamp"][:10] if c["timestamp"] else "Unknown date"}</div>'
            f'</a>'
            for c in conversations
        ])

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(readable_name)} - Claude Code History</title>
    {self.get_styles()}
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-link">← Back to Projects</a>
            <h1>📁 {html.escape(readable_name)}</h1>
        </header>
        <main>
            <h2>Conversations ({len(conversations)})</h2>
            <div class="conversation-list">
                {conv_list if conv_list else '<p>No conversations found</p>'}
            </div>
        </main>
    </div>
</body>
</html>'''

    def render_conversation(self, project_folder, session_id):
        messages = get_conversation_messages(project_folder, session_id)
        readable_name = project_folder.replace('-', '/')[1:] if project_folder.startswith('-') else project_folder.replace('-', '/')

        msg_parts = []
        for m in messages:
            role_icon = "👤 User" if m["role"] == "user" else "🤖 Claude"
            timestamp = m.get("timestamp", "")[:19].replace("T", " ")
            model_html = f'<span class="model">{m.get("model", "")}</span>' if m.get("model") else ""
            msg_parts.append(
                f'<div class="message {m["role"]}">'
                f'<div class="message-header">'
                f'<span class="role">{role_icon}</span>'
                f'<span class="time">{timestamp}</span>'
                f'{model_html}'
                f'</div>'
                f'<div class="message-content">{m["content"]}</div>'
                f'</div>'
            )
        msg_html = ''.join(msg_parts)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation - Claude Code History</title>
    {self.get_styles()}
</head>
<body>
    <div class="container">
        <header>
            <a href="/project?name={project_folder}" class="back-link">← Back to {html.escape(readable_name)}</a>
            <h1>💬 Conversation</h1>
            <p class="subtitle">Session: {session_id}</p>
        </header>
        <main class="messages-container">
            {msg_html if msg_html else '<p>No messages found</p>'}
        </main>
    </div>
</body>
</html>'''

    def get_styles(self):
        return '''<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    min-height: 100vh;
    color: #e0e0e0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    padding: 40px 20px;
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    color: #888;
    font-size: 1.1em;
}

.back-link {
    display: inline-block;
    color: #667eea;
    text-decoration: none;
    margin-bottom: 20px;
    font-size: 0.9em;
}

.back-link:hover {
    text-decoration: underline;
}

h2 {
    margin-bottom: 20px;
    color: #ccc;
}

.project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.project-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s ease;
}

.project-card:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
    border-color: #667eea;
}

.project-name {
    font-size: 1.1em;
    font-family: monospace;
    word-break: break-all;
}

.conversation-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.conversation-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px 20px;
    text-decoration: none;
    color: inherit;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
}

.conversation-card:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #667eea;
}

.conv-summary {
    flex: 1;
}

.conv-time {
    color: #888;
    font-size: 0.9em;
    margin-left: 20px;
}

.messages-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.message {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.message.user {
    border-left: 4px solid #4CAF50;
}

.message.assistant {
    border-left: 4px solid #667eea;
}

.message-header {
    display: flex;
    gap: 15px;
    margin-bottom: 15px;
    font-size: 0.9em;
    color: #888;
}

.role {
    font-weight: bold;
    color: #ccc;
}

.model {
    background: rgba(102, 126, 234, 0.2);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.85em;
}

.message-content {
    white-space: pre-wrap;
    word-wrap: break-word;
    line-height: 1.6;
}

.thinking {
    background: rgba(255, 193, 7, 0.1);
    border: 1px solid rgba(255, 193, 7, 0.3);
    border-radius: 8px;
    margin: 10px 0;
    padding: 10px;
}

.thinking summary {
    cursor: pointer;
    color: #ffc107;
}

.thinking pre {
    margin-top: 10px;
    overflow-x: auto;
    font-size: 0.85em;
    color: #ccc;
}

.tool-use {
    background: rgba(76, 175, 80, 0.1);
    border: 1px solid rgba(76, 175, 80, 0.3);
    border-radius: 8px;
    margin: 10px 0;
    padding: 10px;
}

.tool-use pre {
    margin-top: 10px;
    overflow-x: auto;
    font-size: 0.85em;
}

.tool-result {
    background: rgba(158, 158, 158, 0.1);
    border: 1px solid rgba(158, 158, 158, 0.3);
    border-radius: 8px;
    margin: 10px 0;
    padding: 10px;
}

.tool-result pre {
    overflow-x: auto;
    font-size: 0.85em;
    max-height: 200px;
    overflow-y: auto;
}

pre {
    background: rgba(0, 0, 0, 0.2);
    padding: 10px;
    border-radius: 6px;
}
</style>'''


def is_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False


def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    return None


def main():
    parser = argparse.ArgumentParser(
        description='claude-code-history - View conversation history from Claude Code'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to run the server on (default: 8000)'
    )
    args = parser.parse_args()
    
    requested_port = args.port
    
    # Check if the requested port is available
    if is_port_available(requested_port):
        port = requested_port
    else:
        # If requested port is not available, try to find an available one
        print(f"⚠️  Port {requested_port} is in use, trying to find an available port...")
        port = find_available_port(requested_port)
        if port is None:
            print(f"❌ Error: Could not find an available port starting from {requested_port}.")
            return
        if port != requested_port:
            print(f"⚠️  Using port {port} instead of {requested_port}")
    
    server = HTTPServer(('localhost', port), HistoryHandler)
    print(f"🚀 Claude Code History Viewer running at http://localhost:{port}")
    print(f"📁 Reading from: {CLAUDE_PROJECTS_DIR}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()

