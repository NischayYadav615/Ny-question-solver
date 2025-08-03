import os
import json
import base64
from flask import Flask, request, render_template_string, session, jsonify
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import uuid

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyAHwDXsTEwtcXFlSHgBhTHzugthtNdaVio"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NY AI - JEE Question Solver</title>
    
    <!-- MathJax Configuration -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            }
        };
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
    
    <style>
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --accent: #f093fb;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #f87171;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #e2e8f0;
            --border: #e5e7eb;
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 10px -2px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 24px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
        }

        .logo {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }

        .tagline {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 500;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .input-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            background: var(--bg-tertiary);
            padding: 0.25rem;
            border-radius: 12px;
        }

        .tab-btn {
            flex: 1;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: 10px;
            background: transparent;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background: var(--bg-primary);
            color: var(--primary);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .file-upload {
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: var(--bg-secondary);
            position: relative;
            overflow: hidden;
        }

        .file-upload::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
            transition: left 0.5s;
        }

        .file-upload:hover::before {
            left: 100%;
        }

        .file-upload:hover {
            border-color: var(--primary);
            background: rgba(102, 126, 234, 0.05);
            transform: scale(1.02);
        }

        .file-upload.drag-over {
            border-color: var(--primary);
            background: rgba(102, 126, 234, 0.1);
            transform: scale(1.05);
        }

        .url-input {
            width: 100%;
            padding: 1rem;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: var(--bg-primary);
        }

        .url-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .solve-btn {
            width: 100%;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
            position: relative;
            overflow: hidden;
        }

        .solve-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .solve-btn:hover::before {
            left: 100%;
        }

        .solve-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .solve-btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            transform: none;
        }

        .image-preview {
            max-width: 100%;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: var(--shadow);
        }

        .solution-area {
            min-height: 400px;
            position: relative;
        }

        .step-nav {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .step-btn {
            padding: 0.5rem 1rem;
            border: 2px solid var(--primary);
            background: var(--bg-primary);
            color: var(--primary);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.875rem;
            font-weight: 600;
        }

        .step-btn:hover,
        .step-btn.active {
            background: var(--primary);
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .solution-step {
            background: var(--bg-primary);
            border-radius: 16px;
            padding: 1.5rem;
            border-left: 4px solid var(--primary);
            box-shadow: var(--shadow);
            opacity: 0;
            transform: translateY(20px);
            animation: slideIn 0.6s ease forwards;
        }

        @keyframes slideIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .step-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .step-number {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
        }

        .step-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .step-content {
            color: var(--text-primary);
            line-height: 1.8;
        }

        .math-container {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid var(--accent);
            overflow-x: auto;
            max-width: 100%;
        }

        .math-container::-webkit-scrollbar {
            height: 6px;
        }

        .math-container::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 3px;
        }

        .math-container::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }

        .chat-section {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            height: 500px;
            display: flex;
            flex-direction: column;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 1rem;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 12px;
            scroll-behavior: smooth;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 3px;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }

        .message {
            margin-bottom: 1rem;
            padding: 1rem 1.25rem;
            border-radius: 18px;
            max-width: 85%;
            animation: messageSlide 0.3s ease-out;
            position: relative;
            overflow-x: auto;
        }

        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .user-message {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 6px;
        }

        .ai-message {
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-bottom-left-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .message::-webkit-scrollbar {
            height: 4px;
        }

        .message::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
        }

        .message::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
        }

        .chat-input-area {
            display: flex;
            gap: 0.75rem;
            align-items: end;
        }

        .chat-input {
            flex: 1;
            padding: 1rem;
            border: 2px solid var(--border);
            border-radius: 20px;
            resize: none;
            min-height: 50px;
            max-height: 120px;
            font-family: inherit;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .send-btn {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .send-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .loading {
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--bg-tertiary);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem;
            text-align: center;
            color: var(--text-secondary);
        }

        .empty-state .icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        .error-message {
            background: rgba(248, 113, 113, 0.1);
            color: var(--error);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(248, 113, 113, 0.2);
            margin: 1rem 0;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .main-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }

            .logo {
                font-size: 2rem;
            }

            .card {
                padding: 1rem;
            }

            .chat-section {
                height: 400px;
            }

            .step-nav {
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }

            .step-nav::-webkit-scrollbar {
                height: 4px;
            }

            .step-nav::-webkit-scrollbar-track {
                background: var(--bg-tertiary);
                border-radius: 2px;
            }

            .step-nav::-webkit-scrollbar-thumb {
                background: var(--primary);
                border-radius: 2px;
            }
        }

        /* Animation for typing indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 1.25rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 18px;
            border-bottom-left-radius: 6px;
            max-width: 85%;
            margin-bottom: 1rem;
        }

        .typing-dots {
            display: flex;
            gap: 0.25rem;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--text-secondary);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🧠 NY AI</div>
            <div class="tagline">Advanced JEE Question Solver with Sequential Analysis</div>
        </div>

        <div class="main-grid">
            <div class="input-panel">
                <div class="card">
                    <div class="card-title">
                        <span>📤</span>
                        Upload Question
                    </div>
                    
                    <div class="input-tabs">
                        <button class="tab-btn active" onclick="switchTab('image')">📷 Image</button>
                        <button class="tab-btn" onclick="switchTab('url')">🔗 URL</button>
                    </div>
                    
                    <form method="POST" enctype="multipart/form-data" id="questionForm">
                        <div id="image-tab" class="tab-content active">
                            <div class="file-upload" onclick="document.getElementById('imageFile').click()">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Drop your image here</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">or click to browse</div>
                                <input type="file" id="imageFile" name="image_file" accept="image/*" style="display: none;" onchange="previewImage(this)">
                            </div>
                        </div>
                        
                        <div id="url-tab" class="tab-content">
                            <input type="url" name="image_url" class="url-input" placeholder="🔗 Paste image URL here..." value="{{ image_url or '' }}">
                        </div>
                        
                        <button type="submit" class="solve-btn" id="solveBtn">
                            🚀 Analyze with NY AI
                        </button>
                    </form>
                </div>
                
                {% if image_url %}
                <div class="card">
                    <div class="card-title">
                        <span>🖼️</span>
                        Uploaded Image
                    </div>
                    <img src="{{ image_url }}" class="image-preview" alt="Question Image">
                </div>
                {% endif %}
            </div>
            
            <div class="solution-panel">
                <div class="card solution-area">
                    <div class="card-title">
                        <span>✨</span>
                        Solution Analysis
                    </div>
                    
                    {% if solution_sequence %}
                    <div class="step-nav">
                        {% for i in range(solution_sequence|length) %}
                        <button class="step-btn {% if i == 0 %}active{% endif %}" onclick="showStep({{ i }})">
                            Step {{ i + 1 }}
                        </button>
                        {% endfor %}
                    </div>
                    
                    {% for step in solution_sequence %}
                    <div class="solution-step" id="step-{{ loop.index0 }}" {% if loop.index0 != 0 %}style="display: none;"{% endif %}>
                        <div class="step-header">
                            <div class="step-number">{{ loop.index }}</div>
                            <div class="step-title">{{ step.title }}</div>
                        </div>
                        <div class="step-content">
                            <div class="math-container">{{ step.content|safe }}</div>
                        </div>
                    </div>
                    {% endfor %}
                    {% else %}
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>NY AI is analyzing your question...</p>
                    </div>
                    
                    {% if not solution_sequence %}
                    <div class="empty-state">
                        <div class="icon">🤖</div>
                        <p>Upload an image to get started with NY AI's analysis</p>
                    </div>
                    {% endif %}
                    {% endif %}
                    
                    {% if error %}
                    <div class="error-message">{{ error }}</div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="chat-section">
            <div class="card-title">
                <span>💬</span>
                Chat with NY AI
            </div>
            <div class="chat-messages" id="chatMessages">
                {% for message in chat_history %}
                <div class="message {{ 'user-message' if message.role == 'user' else 'ai-message' }}">
                    {{ message.content|safe }}
                </div>
                {% endfor %}
            </div>
            
            <div class="chat-input-area">
                <textarea class="chat-input" id="chatInput" placeholder="Ask follow-up questions..." onkeypress="handleChatKeyPress(event)" rows="1"></textarea>
                <button class="send-btn" onclick="sendChatMessage()">➤</button>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function showStep(stepIndex) {
            document.querySelectorAll('.solution-step').forEach(step => {
                step.style.display = 'none';
            });
            
            document.querySelectorAll('.step-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById('step-' + stepIndex).style.display = 'block';
            event.target.classList.add('active');
            
            if (window.MathJax) {
                MathJax.typesetPromise([document.getElementById('step-' + stepIndex)]);
            }
        }
        
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.getElementById('imagePreview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = 'imagePreview';
                        preview.className = 'image-preview';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                }
                reader.readAsDataURL(input.files[0]);
            }
        }
        
        // Enhanced drag and drop
        const fileUpload = document.querySelector('.file-upload');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUpload.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            fileUpload.classList.add('drag-over');
        }
        
        function unhighlight(e) {
            fileUpload.classList.remove('drag-over');
        }
        
        fileUpload.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                document.getElementById('imageFile').files = files;
                previewImage(document.getElementById('imageFile'));
            }
        }
        
        // Auto-resize textarea
        const chatInput = document.getElementById('chatInput');
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Form submission
        document.getElementById('questionForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'flex';
            document.getElementById('solveBtn').disabled = true;
            document.getElementById('solveBtn').textContent = '🔄 Analyzing...';
        });
        
        // Chat functionality with animations
        function handleChatKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatMessage();
            }
        }
        
        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessageToChat(message, 'user');
            input.value = '';
            input.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                hideTypingIndicator();
                if (data.response) {
                    addMessageToChat(data.response, 'ai');
                } else if (data.error) {
                    addMessageToChat('Error: ' + data.error, 'ai');
                }
            })
            .catch(error => {
                hideTypingIndicator();
                addMessageToChat('Error: ' + error.message, 'ai');
            });
        }
        
        function addMessageToChat(message, role) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.innerHTML = message;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            if (window.MathJax) {
                MathJax.typesetPromise([messageDiv]);
            }
        }
        
        function showTypingIndicator() {
            const chatMessages = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'typing-indicator';
            typingDiv.innerHTML = `
                <span>NY AI is thinking</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            `;
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTypingIndicator() {
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
        
        // Initialize MathJax rendering
        document.addEventListener('DOMContentLoaded', function() {
            if (window.MathJax) {
                MathJax.typesetPromise();
            }
        });
    </script>
</body>
</html>
"""

def encode_image_to_base64(image_data):
    """Convert image data to base64 string."""
    if isinstance(image_data, bytes):
        return base64.b64encode(image_data).decode('utf-8')
    return image_data

def call_gemini_vision(prompt, image_data=None, image_url=None):
    """Enhanced Gemini API call with vision capabilities."""
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    parts = [{"text": prompt}]
    
    # Add image data if provided
    if image_data:
        try:
            if isinstance(image_data, bytes):
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_b64 = image_data
                
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_b64
                }
            })
        except Exception as e:
            return f"Error processing image: {str(e)}"
    
    elif image_url and not image_url.startswith('data:'):
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                image_b64 = base64.b64encode(response.content).decode('utf-8')
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_b64
                    }
                })
        except Exception as e:
            return f"Error downloading image: {str(e)}"
    
    payload = {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        }
    }
    
    try:
        response = requests.post(GEMINI_VISION_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "candidates" in result and len(result["candidates"]) > 0:
            content = result["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                return parts[0].get("text", "No response generated.")
        
        return "No valid response from Gemini API."
        
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    except json.JSONDecodeError as e:
        return f"Failed to parse API response: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def create_sequential_prompt(question_text=None, has_image=False):
    """Create an enhanced prompt for sequential JEE question analysis."""
    
    base_prompt = """You are NY AI, an expert JEE (Joint Entrance Examination) tutor with deep knowledge in Physics, Chemistry, and Mathematics.

TASK: Analyze and solve the provided JEE question with a structured, sequential approach.

IMPORTANT: Format all mathematical expressions using LaTeX notation for MathJax rendering. Use $ for inline math and $$ for display math.

RESPONSE FORMAT - Provide exactly 6 structured sections:

**SECTION 1: QUESTION ANALYSIS**
- Subject area and topic identification
- Difficulty level assessment
- Key concepts overview

**SECTION 2: TEXT & CONTENT EXTRACTION**
- Extract all text, equations, and visual elements
- Describe any diagrams or graphs
- List multiple choice options if present

**SECTION 3: CONCEPT IDENTIFICATION**
- List relevant formulas (use LaTeX: $F = ma$, $E = mc^2$, etc.)
- Identify key principles and laws
- Required mathematical tools

**SECTION 4: SOLUTION STRATEGY**
- Outline the solution approach
- Identify the sequence of steps needed
- Choose the most efficient method

**SECTION 5: DETAILED CALCULATION**
- Step-by-step mathematical solution
- Show all work with proper LaTeX formatting
- Include intermediate results and explanations

**SECTION 6: FINAL ANSWER & VERIFICATION**
- Clear final answer with units
- Verification of the result
- Common mistakes to avoid

Each section should be clearly separated and use proper LaTeX formatting for all mathematical expressions."""
    
    if question_text:
        base_prompt += f"\n\nQUESTION TEXT:\n{question_text}"
    
    if has_image:
        base_prompt += "\n\nIMAGE: Please analyze the provided image carefully for any additional visual information, diagrams, graphs, or mathematical expressions."
    
    return base_prompt

def parse_solution_into_sequence(solution_text):
    """Parse the solution into sequential steps for better display."""
    if not solution_text:
        return []
    
    sections = []
    current_section = ""
    current_title = ""
    
    lines = solution_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('**SECTION') and line.endswith('**'):
            if current_title and current_section:
                sections.append({
                    'title': current_title,
                    'content': current_section.strip()
                })
            
            current_title = line.replace('**SECTION', '').replace('**', '').strip()
            if ':' in current_title:
                current_title = current_title.split(':', 1)[1].strip()
            current_section = ""
        
        elif line.startswith('**') and line.endswith('**') and current_section:
            current_section += f"<h4 style='color: var(--primary); margin: 15px 0 10px 0; font-weight: 600;'>{line.replace('**', '')}</h4>\n"
        
        else:
            if line:
                current_section += line + "\n"
    
    if current_title and current_section:
        sections.append({
            'title': current_title,
            'content': current_section.strip()
        })
    
    if not sections and solution_text:
        sections.append({
            'title': 'Complete Solution',
            'content': solution_text
        })
    
    return sections

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    image_url = None
    solution_sequence = None
    error = None
    extracted_text = None
    
    if request.method == 'POST':
        try:
            image_url = request.form.get('image_url', '').strip()
            
            image_data = None
            has_image = False
            
            # Handle file upload
            if 'image_file' in request.files and request.files['image_file'].filename:
                file = request.files['image_file']
                if file and file.filename != '':
                    try:
                        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        
                        if file_ext not in allowed_extensions:
                            error = "Please upload a valid image file (PNG, JPG, JPEG, GIF, WebP)."
                        else:
                            image_data = file.read()
                            image_b64 = base64.b64encode(image_data).decode('utf-8')
                            image_url = f"data:image/{file_ext};base64,{image_b64}"
                            has_image = True
                    except Exception as e:
                        error = f"Error processing uploaded file: {str(e)}"
            
            # Handle URL input
            elif image_url:
                if image_url.startswith('data:'):
                    try:
                        header, data = image_url.split(',', 1)
                        image_data = base64.b64decode(data)
                        has_image = True
                    except Exception as e:
                        error = f"Error processing data URL: {str(e)}"
                else:
                    has_image = True
            
            if not has_image:
                error = "Please provide an image (upload or URL)."
            
            elif not error:
                prompt = create_sequential_prompt(None, has_image)
                solution = call_gemini_vision(prompt, image_data, image_url)
                solution_sequence = parse_solution_into_sequence(solution)
                
                extract_prompt = """Please extract ALL text content from this image, including:
                - Question text
                - Mathematical equations and expressions (format with LaTeX when possible)
                - Numbers, measurements, and units
                - Any labels or annotations
                - Multiple choice options if present
                
                Format the extracted text clearly and preserve the original structure. Use LaTeX notation for mathematical expressions."""
                
                extracted_text = call_gemini_vision(extract_prompt, image_data, image_url)
                
                session['current_context'] = {
                    'extracted_text': extracted_text,
                    'solution_sequence': solution_sequence,
                    'has_image': has_image
                }
                
        except Exception as e:
            error = f"An unexpected error occurred: {str(e)}"
    
    return render_template_string(HTML_TEMPLATE,
                                image_url=image_url,
                                solution_sequence=solution_sequence,
                                error=error,
                                extracted_text=extracted_text,
                                chat_history=session.get('chat_history', []))

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        context = session.get('current_context', {})
        
        chat_prompt = f"""You are NY AI, continuing a conversation about a JEE question. Here's the context:

EXTRACTED TEXT: {context.get('extracted_text', 'N/A')}

USER'S FOLLOW-UP QUESTION: {user_message}

Please provide a helpful, detailed response. Use LaTeX notation for mathematical expressions ($ for inline, $$ for display math). 
If the user is asking for clarification, provide more detailed explanations. If asking about related concepts, explain those as well.
Always maintain the NY AI persona - be confident, helpful, and educational."""
        
        ai_response = call_gemini_vision(chat_prompt)
        
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({
            'role': 'user',
            'content': user_message
        })
        
        session['chat_history'].append({
            'role': 'ai',
            'content': ai_response
        })
        
        if len(session['chat_history']) > 20:
            session['chat_history'] = session['chat_history'][-20:]
        
        session.modified = True
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    session.modified = True
    return jsonify({'success': True})

# Vercel serverless function
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
