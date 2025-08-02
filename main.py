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
app.secret_key = os.urandom(24)  # For session management

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDHFTMIgNpOSwOnGRhgaL2Y960BYV2O56s"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NY AI - Advanced JEE Question Solver</title>
    
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
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .main-wrapper {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ffd93d 50%, #6bcf7f 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }
        
        .ny-ai-logo {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header h1 { 
            font-size: 2.5rem; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p { 
            font-size: 1.1rem; 
            opacity: 0.9; 
        }
        
        .main-content { 
            display: flex; 
            gap: 20px; 
            padding: 30px;
            min-height: calc(100vh - 200px);
        }
        .left-panel { flex: 1; max-width: 500px; }
        .right-panel { flex: 2; }
        
        .input-section {
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 2px dashed #e2e8f0;
            transition: all 0.3s ease;
        }
        .input-section:hover { border-color: #ff6b6b; }
        
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            background: #e2e8f0;
            color: #64748b;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .tab-btn.active {
            background: #ff6b6b;
            color: white;
        }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .file-upload {
            border: 3px dashed #cbd5e1;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #f1f5f9;
        }
        .file-upload:hover {
            border-color: #ff6b6b;
            background: #fff5f5;
        }
        .file-upload.drag-over {
            border-color: #ff6b6b;
            background: #fff1f1;
            transform: scale(1.02);
        }
        
        input[type="url"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="url"]:focus {
            outline: none;
            border-color: #ff6b6b;
        }
        
        .solve-btn {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }
        .solve-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 107, 107, 0.3);
        }
        .solve-btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
            transform: none;
        }
        
        .image-preview {
            max-width: 100%;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .solution-area {
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            min-height: 300px;
        }
        
        .solution-sequence {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .solution-step {
            background: white;
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #ff6b6b;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            opacity: 0;
            transform: translateY(20px);
            animation: slideIn 0.6s ease forwards;
        }
        
        .solution-step:nth-child(1) { animation-delay: 0.1s; }
        .solution-step:nth-child(2) { animation-delay: 0.2s; }
        .solution-step:nth-child(3) { animation-delay: 0.3s; }
        .solution-step:nth-child(4) { animation-delay: 0.4s; }
        .solution-step:nth-child(5) { animation-delay: 0.5s; }
        .solution-step:nth-child(6) { animation-delay: 0.6s; }
        
        @keyframes slideIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .step-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            font-weight: 600;
            color: #374151;
        }
        
        .step-number {
            background: #ff6b6b;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: bold;
        }
        
        .step-content {
            line-height: 1.8;
            color: #374151;
        }
        
        .math-expression {
            background: #f1f5f9;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            border-left: 3px solid #ffd93d;
        }
        
        .final-answer {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: bold;
            margin-top: 20px;
        }
        
        .chat-area {
            background: #f8fafc;
            border-radius: 15px;
            padding: 25px;
            height: 400px;
            display: flex;
            flex-direction: column;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            background: white;
            margin-bottom: 15px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
        }
        
        .user-message {
            background: #ff6b6b;
            color: white;
            margin-left: auto;
        }
        
        .ai-message {
            background: #e5e7eb;
            color: #374151;
        }
        
        .chat-input-area {
            display: flex;
            gap: 10px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 25px;
            outline: none;
        }
        
        .send-btn {
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .send-btn:hover {
            background: #ee5a52;
            transform: scale(1.1);
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f1f5f9;
        }
        
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            border-top: 4px solid #ff6b6b;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f4f6;
            border-top: 4px solid #ff6b6b;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee2e2;
            color: #dc2626;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .success {
            background: #dcfce7;
            color: #16a34a;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .ny-ai-badge {
            position: absolute;
            top: 10px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .sequence-nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .sequence-btn {
            padding: 8px 16px;
            border: 2px solid #ff6b6b;
            background: white;
            color: #ff6b6b;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        
        .sequence-btn.active, .sequence-btn:hover {
            background: #ff6b6b;
            color: white;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            .header h1 {
                font-size: 2rem;
            }
            .ny-ai-logo {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <div class="ny-ai-badge">Powered by NY AI</div>
            <div class="ny-ai-logo">🧠 NY AI</div>
            <h1>Advanced JEE Question Solver</h1>
            <p>Next-Gen AI with OCR, MathJax Rendering & Sequential Solutions</p>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">📸</div>
                <h3>Image Analysis</h3>
                <p>Advanced OCR with formula recognition</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔗</div>
                <h3>URL Support</h3>
                <p>Direct image URL processing</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Sequential Solutions</h3>
                <p>Step-by-step organized approach</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔬</div>
                <h3>MathJax Rendering</h3>
                <p>Beautiful mathematical expressions</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3>Interactive Chat</h3>
                <p>Ask follow-up questions</p>
            </div>
        </div>
        
        <div class="main-content">
            <div class="left-panel">
                <div class="input-section">
                    <h3>📤 Input Question</h3>
                    
                    <div class="tab-buttons">
                        <button class="tab-btn active" onclick="switchTab('image')">📷 Image</button>
                        <button class="tab-btn" onclick="switchTab('url')">🔗 URL</button>
                    </div>
                    
                    <form method="POST" enctype="multipart/form-data" id="questionForm">
                        <div id="image-tab" class="tab-content active">
                            <div class="file-upload" onclick="document.getElementById('imageFile').click()">
                                <div>📁 Click to upload or drag & drop image</div>
                                <small>Supports JPG, PNG, GIF, WebP</small>
                                <input type="file" id="imageFile" name="image_file" accept="image/*" style="display: none;" onchange="previewImage(this)">
                            </div>
                        </div>
                        
                        <div id="url-tab" class="tab-content">
                            <input type="url" name="image_url" placeholder="🔗 Paste image URL here..." value="{{ image_url or '' }}">
                        </div>
                        
                        <button type="submit" class="solve-btn" id="solveBtn">
                            🧠 Analyze & Solve with NY AI
                        </button>
                    </form>
                </div>
                
                {% if image_url %}
                <div class="input-section">
                    <h3>🖼️ Input Image</h3>
                    <img src="{{ image_url }}" class="image-preview" alt="Question Image">
                </div>
                {% endif %}
                
                {% if extracted_text %}
                <div class="input-section">
                    <h3>📄 Extracted Text</h3>
                    <div style="background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #ff6b6b;">
                        <pre style="white-space: pre-wrap; font-family: inherit;">{{ extracted_text }}</pre>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="right-panel">
                <div class="solution-area">
                    <h3>✅ Sequential Solution by NY AI</h3>
                    
                    {% if solution_sequence %}
                    <div class="sequence-nav">
                        {% for i in range(solution_sequence|length) %}
                        <button class="sequence-btn {% if i == 0 %}active{% endif %}" onclick="showStep({{ i }})">
                            Step {{ i + 1 }}
                        </button>
                        {% endfor %}
                    </div>
                    
                    <div class="solution-sequence">
                        {% for step in solution_sequence %}
                        <div class="solution-step" id="step-{{ loop.index0 }}" {% if loop.index0 != 0 %}style="display: none;"{% endif %}>
                            <div class="step-header">
                                <div class="step-number">{{ loop.index }}</div>
                                <div>{{ step.title }}</div>
                            </div>
                            <div class="step-content">
                                {{ step.content|safe }}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>NY AI is analyzing your question...</p>
                    </div>
                    
                    {% if not solution %}
                    <div style="text-align: center; color: #9ca3af; padding: 40px;">
                        <div style="font-size: 3rem; margin-bottom: 15px;">🤖</div>
                        <p>Upload an image or provide a URL to get started with NY AI!</p>
                    </div>
                    {% endif %}
                    {% endif %}
                    
                    {% if error %}
                    <div class="error">{{ error }}</div>
                    {% endif %}
                </div>
                
                <div class="chat-area">
                    <h3>💬 Chat with NY AI</h3>
                    <div class="chat-messages" id="chatMessages">
                        {% for message in chat_history %}
                        <div class="message {{ 'user-message' if message.role == 'user' else 'ai-message' }}">
                            {{ message.content|safe }}
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" id="chatInput" placeholder="Ask follow-up questions to NY AI..." onkeypress="handleChatKeyPress(event)">
                        <button class="send-btn" onclick="sendChatMessage()">➤</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function showStep(stepIndex) {
            // Hide all steps
            document.querySelectorAll('.solution-step').forEach(step => {
                step.style.display = 'none';
            });
            
            // Remove active from all sequence buttons
            document.querySelectorAll('.sequence-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected step
            document.getElementById('step-' + stepIndex).style.display = 'block';
            event.target.classList.add('active');
            
            // Re-render MathJax for the visible step
            if (window.MathJax) {
                MathJax.typesetPromise([document.getElementById('step-' + stepIndex)]);
            }
        }
        
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview if it doesn't exist
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
        
        // Drag and drop functionality
        const fileUpload = document.querySelector('.file-upload');
        
        fileUpload.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUpload.classList.add('drag-over');
        });
        
        fileUpload.addEventListener('dragleave', () => {
            fileUpload.classList.remove('drag-over');
        });
        
        fileUpload.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUpload.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('imageFile').files = files;
                previewImage(document.getElementById('imageFile'));
            }
        });
        
        // Form submission with loading
        document.getElementById('questionForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('solveBtn').disabled = true;
            document.getElementById('solveBtn').textContent = 'NY AI Analyzing...';
        });
        
        // Chat functionality
        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }
        
        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessageToChat(message, 'user');
            input.value = '';
            
            // Send to server
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.response) {
                    addMessageToChat(data.response, 'ai');
                } else if (data.error) {
                    addMessageToChat('Error: ' + data.error, 'ai');
                }
            })
            .catch(error => {
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
            
            // Re-render MathJax for new messages
            if (window.MathJax) {
                MathJax.typesetPromise([messageDiv]);
            }
        }
        
        // Initialize MathJax rendering on page load
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
            # Handle both base64 string and bytes
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
        # For external URLs, download and encode
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
