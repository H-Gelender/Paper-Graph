#!/usr/bin/env python
"""
web_app.py

FastAPI web application that provides a web interface for the MCP chatbot.
Features:
- WebSocket endpoint for real-time chat communication
- Integration with the existing MCP client
- Session management for chat history
- Static file serving for the frontend
"""

import asyncio
import json
import os
import sys
import uuid
from contextlib import AsyncExitStack
from typing import Dict, List, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Add the client directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client'))

# Import from existing MCP client
from config import SYSTEM_PROMPT, MODEL
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="MCP Chatbot Web Interface", version="1.0.0")

# Global variables for agent and tools
agent = None
tools = []
llm = None
exit_stack = None  # Keep the async exit stack alive

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_sessions: Dict[str, List[Dict[str, str]]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()

class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder for LangChain objects"""
    def default(self, o):
        if hasattr(o, "content"):
            return {"type": o.__class__.__name__, "content": o.content}
        return super().default(o)

def read_config_json():
    """Read MCP server configuration"""
    config_path = os.getenv("MCP_CONFIG_PATH")
    if not config_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "client", "mcp_config.json")
        print(f"⚠️  MCP_CONFIG_PATH not set. Using: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            print(f"✅ Loaded config file from: {config_path}")
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read config file at '{config_path}': {e}")
        return {}

async def initialize_agent():
    """Initialize the MCP agent with all tools"""
    global agent, tools, llm, exit_stack
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=MODEL,
        temperature=0,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    config = read_config_json()
    mcp_servers = config.get("mcpServers", {})
    
    if not mcp_servers:
        print("❌ No MCP servers found in configuration.")
        return False
    
    tools = []
    
    # Keep the exit stack alive for the lifetime of the application
    exit_stack = AsyncExitStack()
    
    try:
        for server_name, server_info in mcp_servers.items():
            print(f"🔗 Connecting to MCP Server: {server_name}...")
            
            server_params = StdioServerParameters(
                command=server_info["command"],
                args=server_info["args"]
            )
            
            try:
                read, write = await exit_stack.enter_async_context(stdio_client(server_params))
                session = await exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                server_tools = await load_mcp_tools(session)
                
                for tool in server_tools:
                    print(f"🔧 Loaded tool: {tool.name}")
                    tools.append(tool)
                
                print(f"✅ {len(server_tools)} tools loaded from {server_name}")
            except Exception as e:
                print(f"❌ Failed to connect to server {server_name}: {e}")
        
        if tools:
            agent = create_react_agent(llm, tools)
            print(f"🚀 Agent initialized with {len(tools)} tools")
            return True
        else:
            print("❌ No tools loaded from any server")
            return False
            
    except Exception as e:
        print(f"❌ Error during agent initialization: {e}")
        if exit_stack:
            await exit_stack.aclose()
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the agent when the app starts"""
    success = await initialize_agent()
    if not success:
        print("⚠️ Agent initialization failed. Some features may not work.")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down"""
    global exit_stack
    print("🛑 Shutting down MCP connections...")
    if exit_stack:
        try:
            await exit_stack.aclose()
            print("✅ MCP connections closed")
        except Exception as e:
            print(f"⚠️ Error closing MCP connections: {e}")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main chat interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Chatbot</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.5/dist/purify.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .chat-container {
                width: 90%;
                max-width: 800px;
                height: 90vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 1.2em;
                font-weight: 600;
            }
            
            .status {
                padding: 10px 20px;
                background: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
                font-size: 0.9em;
                color: #6c757d;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #dc3545;
                animation: pulse 2s infinite;
            }
            
            .status-dot.connected {
                background: #28a745;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            .messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .message {
                display: flex;
                gap: 10px;
                max-width: 80%;
                animation: slideIn 0.3s ease-out;
            }
            
            .message.user {
                align-self: flex-end;
                flex-direction: row-reverse;
            }
            
            .message.assistant {
                align-self: flex-start;
            }
            
            .message-content {
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                white-space: pre-wrap;
                line-height: 1.4;
            }
            
            /* Markdown styling for assistant messages */
            .message.assistant .message-content h1,
            .message.assistant .message-content h2,
            .message.assistant .message-content h3,
            .message.assistant .message-content h4,
            .message.assistant .message-content h5,
            .message.assistant .message-content h6 {
                margin: 16px 0 8px 0;
                font-weight: 600;
                color: #2d3748;
            }
            
            .message.assistant .message-content h1 { font-size: 1.5em; }
            .message.assistant .message-content h2 { font-size: 1.3em; }
            .message.assistant .message-content h3 { font-size: 1.2em; }
            .message.assistant .message-content h4 { font-size: 1.1em; }
            
            .message.assistant .message-content p {
                margin: 8px 0;
                line-height: 1.6;
            }
            
            .message.assistant .message-content ul,
            .message.assistant .message-content ol {
                margin: 8px 0;
                padding-left: 20px;
            }
            
            .message.assistant .message-content li {
                margin: 4px 0;
                line-height: 1.5;
            }
            
            .message.assistant .message-content code {
                background: #f6f8fa;
                border: 1px solid #e1e4e8;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.9em;
                color: #d73a49;
            }
            
            .message.assistant .message-content pre {
                background: #f6f8fa;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                padding: 12px;
                margin: 12px 0;
                overflow-x: auto;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.9em;
                line-height: 1.4;
            }
            
            .message.assistant .message-content pre code {
                background: none;
                border: none;
                padding: 0;
                color: #24292e;
            }
            
            .message.assistant .message-content blockquote {
                border-left: 4px solid #667eea;
                margin: 12px 0;
                padding: 8px 0 8px 16px;
                background: #f8f9ff;
                font-style: italic;
                color: #4a5568;
            }
            
            .message.assistant .message-content a {
                color: #667eea;
                text-decoration: none;
                border-bottom: 1px solid transparent;
                transition: border-color 0.2s;
            }
            
            .message.assistant .message-content a:hover {
                border-bottom-color: #667eea;
            }
            
            .message.assistant .message-content table {
                border-collapse: collapse;
                margin: 12px 0;
                width: 100%;
                font-size: 0.9em;
            }
            
            .message.assistant .message-content th,
            .message.assistant .message-content td {
                border: 1px solid #e1e4e8;
                padding: 6px 12px;
                text-align: left;
            }
            
            .message.assistant .message-content th {
                background: #f6f8fa;
                font-weight: 600;
            }
            
            .message.assistant .message-content strong {
                font-weight: 600;
                color: #2d3748;
            }
            
            .message.assistant .message-content em {
                font-style: italic;
                color: #4a5568;
            }
            
            .message.assistant .message-content hr {
                border: none;
                border-top: 2px solid #e1e4e8;
                margin: 20px 0;
            }
            
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .message.assistant .message-content {
                background: #f1f3f4;
                color: #333;
                border: 1px solid #e0e0e0;
            }
            
            .avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: 600;
                flex-shrink: 0;
            }
            
            .avatar.user {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .avatar.assistant {
                background: #f1f3f4;
                color: #333;
                border: 2px solid #e0e0e0;
            }
            
            .typing-indicator {
                display: none;
                align-items: center;
                gap: 10px;
                padding: 12px 16px;
                background: #f1f3f4;
                border-radius: 18px;
                border: 1px solid #e0e0e0;
                max-width: 100px;
            }
            
            .typing-dots {
                display: flex;
                gap: 4px;
            }
            
            .typing-dot {
                width: 6px;
                height: 6px;
                background: #999;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
            
            .input-area {
                padding: 20px;
                border-top: 1px solid #e9ecef;
                background: #f8f9fa;
            }
            
            .input-form {
                display: flex;
                gap: 10px;
                align-items: flex-end;
            }
            
            .message-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                outline: none;
                font-size: 16px;
                resize: none;
                min-height: 20px;
                max-height: 120px;
                font-family: inherit;
                line-height: 1.4;
            }
            
            .message-input:focus {
                border-color: #667eea;
            }
            
            .send-button {
                padding: 12px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: transform 0.2s;
                min-width: 80px;
            }
            
            .send-button:hover:not(:disabled) {
                transform: translateY(-2px);
            }
            
            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .scrollbar-hide {
                scrollbar-width: none;
                -ms-overflow-style: none;
            }
            
            .scrollbar-hide::-webkit-scrollbar {
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                🤖 MCP Research Assistant
            </div>
            
            <div class="status">
                <div class="status-indicator">
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText">Connecting...</span>
                </div>
                <div id="sessionInfo">Session: <span id="sessionId">-</span></div>
            </div>
            
            <div class="messages scrollbar-hide" id="messages">
                <div class="message assistant">
                    <div class="avatar assistant">🤖</div>
                    <div class="message-content">
                        Hello! I'm your research assistant. I can help you analyze histopathology images, search for scientific papers, and provide detailed analysis. What would you like to explore today?
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <form class="input-form" id="messageForm">
                    <textarea 
                        class="message-input" 
                        id="messageInput" 
                        placeholder="Ask me anything about your research..."
                        rows="1"
                    ></textarea>
                    <button type="submit" class="send-button" id="sendButton">Send</button>
                </form>
            </div>
        </div>
        
        <script>
            class ChatApp {
                constructor() {
                    this.sessionId = this.generateSessionId();
                    this.ws = null;
                    this.isConnected = false;
                    this.messageQueue = [];
                    
                    this.initElements();
                    this.setupEventListeners();
                    this.connect();
                }
                
                generateSessionId() {
                    return 'session-' + Math.random().toString(36).substr(2, 9);
                }
                
                initElements() {
                    this.messagesContainer = document.getElementById('messages');
                    this.messageForm = document.getElementById('messageForm');
                    this.messageInput = document.getElementById('messageInput');
                    this.sendButton = document.getElementById('sendButton');
                    this.statusDot = document.getElementById('statusDot');
                    this.statusText = document.getElementById('statusText');
                    this.sessionIdSpan = document.getElementById('sessionId');
                    
                    this.sessionIdSpan.textContent = this.sessionId.slice(-6);
                }
                
                setupEventListeners() {
                    this.messageForm.addEventListener('submit', (e) => {
                        e.preventDefault();
                        this.sendMessage();
                    });
                    
                    this.messageInput.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            this.sendMessage();
                        }
                    });
                    
                    this.messageInput.addEventListener('input', () => {
                        this.autoResize();
                    });
                }
                
                autoResize() {
                    this.messageInput.style.height = 'auto';
                    this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
                }
                
                connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
                    
                    this.ws = new WebSocket(wsUrl);
                    
                    this.ws.onopen = () => {
                        this.isConnected = true;
                        this.updateStatus('Connected', true);
                        this.sendButton.disabled = false;
                        
                        // Send queued messages
                        while (this.messageQueue.length > 0) {
                            const message = this.messageQueue.shift();
                            this.ws.send(JSON.stringify(message));
                        }
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    };
                    
                    this.ws.onclose = () => {
                        this.isConnected = false;
                        this.updateStatus('Disconnected', false);
                        this.sendButton.disabled = true;
                        
                        // Attempt to reconnect after 3 seconds
                        setTimeout(() => {
                            if (!this.isConnected) {
                                this.updateStatus('Reconnecting...', false);
                                this.connect();
                            }
                        }, 3000);
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.updateStatus('Connection error', false);
                    };
                }
                
                updateStatus(text, connected) {
                    this.statusText.textContent = text;
                    if (connected) {
                        this.statusDot.classList.add('connected');
                    } else {
                        this.statusDot.classList.remove('connected');
                    }
                }
                
                sendMessage() {
                    const message = this.messageInput.value.trim();
                    if (!message) return;
                    
                    // Add user message to chat
                    this.addMessage('user', message);
                    
                    // Clear input
                    this.messageInput.value = '';
                    this.autoResize();
                    
                    // Show typing indicator
                    this.showTypingIndicator();
                    
                    // Send message via WebSocket
                    const wsMessage = {
                        type: 'user_message',
                        content: message
                    };
                    
                    if (this.isConnected) {
                        this.ws.send(JSON.stringify(wsMessage));
                    } else {
                        this.messageQueue.push(wsMessage);
                        this.updateStatus('Queued message...', false);
                    }
                }
                
                handleMessage(data) {
                    switch (data.type) {
                        case 'assistant_message':
                            this.hideTypingIndicator();
                            this.addMessage('assistant', data.content);
                            break;
                        case 'error':
                            this.hideTypingIndicator();
                            this.addMessage('assistant', `Error: ${data.content}`);
                            break;
                        case 'status':
                            this.updateStatus(data.content, this.isConnected);
                            break;
                    }
                }
                
                addMessage(sender, content) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${sender}`;
                    
                    const avatar = document.createElement('div');
                    avatar.className = `avatar ${sender}`;
                    avatar.textContent = sender === 'user' ? '👤' : '🤖';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    
                    if (sender === 'assistant') {
                        // Parse markdown and sanitize HTML for assistant messages
                        const html = marked.parse(content);
                        messageContent.innerHTML = DOMPurify.sanitize(html);
                    } else {
                        // Plain text for user messages
                        messageContent.textContent = content;
                    }
                    
                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(messageContent);
                    
                    this.messagesContainer.appendChild(messageDiv);
                    this.scrollToBottom();
                }
                
                showTypingIndicator() {
                    if (document.getElementById('typingIndicator')) return;
                    
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message assistant';
                    messageDiv.id = 'typingIndicator';
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'avatar assistant';
                    avatar.textContent = '🤖';
                    
                    const typingDiv = document.createElement('div');
                    typingDiv.className = 'typing-indicator';
                    typingDiv.style.display = 'flex';
                    
                    const dotsDiv = document.createElement('div');
                    dotsDiv.className = 'typing-dots';
                    
                    for (let i = 0; i < 3; i++) {
                        const dot = document.createElement('div');
                        dot.className = 'typing-dot';
                        dotsDiv.appendChild(dot);
                    }
                    
                    typingDiv.appendChild(dotsDiv);
                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(typingDiv);
                    
                    this.messagesContainer.appendChild(messageDiv);
                    this.scrollToBottom();
                }
                
                hideTypingIndicator() {
                    const indicator = document.getElementById('typingIndicator');
                    if (indicator) {
                        indicator.remove();
                    }
                }
                
                scrollToBottom() {
                    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
                }
            }
            
            // Initialize the chat app when the page loads
            document.addEventListener('DOMContentLoaded', () => {
                new ChatApp();
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                user_message = message_data["content"]
                
                # Add user message to session history
                manager.chat_sessions[session_id].append({
                    "role": "user", 
                    "content": user_message
                })
                
                # Send status update
                await manager.send_message(session_id, {
                    "type": "status",
                    "content": "Processing..."
                })
                
                try:
                    if agent is None:
                        await manager.send_message(session_id, {
                            "type": "error",
                            "content": "Agent not initialized. Please check server configuration."
                        })
                        continue
                    
                    # Prepare agent input with conversation history
                    agent_input = {"messages": manager.chat_sessions[session_id]}
                    
                    # Get response from agent
                    response = await agent.ainvoke(agent_input)
                    
                    # Extract content from response
                    if hasattr(response, 'content'):
                        response_content = response.content
                    elif isinstance(response, dict) and 'messages' in response:
                        # Get the last message content
                        last_message = response['messages'][-1]
                        if hasattr(last_message, 'content'):
                            response_content = last_message.content
                        else:
                            response_content = str(last_message)
                    else:
                        response_content = str(response)
                    
                    # Add assistant response to session history
                    manager.chat_sessions[session_id].append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # Send response to client
                    await manager.send_message(session_id, {
                        "type": "assistant_message",
                        "content": response_content
                    })
                    
                except Exception as e:
                    error_message = f"Error processing request: {str(e)}"
                    print(f"Agent error: {e}")
                    
                    await manager.send_message(session_id, {
                        "type": "error",
                        "content": error_message
                    })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Client {session_id} disconnected")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "tools_loaded": len(tools),
        "active_sessions": len(manager.active_connections)
    }

if __name__ == "__main__":
    print("🚀 Starting MCP Chatbot Web Interface...")
    print("📋 Open your browser and go to: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the server")
    uvicorn.run(
        "web_app:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
        log_level="info"
    )