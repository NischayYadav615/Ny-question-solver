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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDHFTMIgNpOSwOnGRhgaL2Y960BYV2O56s"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NY AI - Advanced Question Solver</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
    <style>
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0; 
        }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #2d1b69 100%);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* Animated background particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.3; }
            50% { transform: translateY(-20px) rotate(180deg); opacity: 0.8; }
        }
        
        /* Main content wrapper */
        .app-wrapper {
            position: relative;
            z-index: 2;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        
        /* Header with enhanced styling */
        .header {
            text-align: center;
            padding: 40px 0;
            animation: slideDown 0.8s ease-out;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header h1 {
            font-size: 3.5rem;
            background: linear-gradient(135deg, #4ade80, #06d6a0, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-weight: 800;
            text-shadow: 0 0 30px rgba(74, 222, 128, 0.3);
        }
        
        .header .brand {
            font-size: 4rem;
            font-weight: 900;
            color: #06d6a0;
            text-shadow: 0 0 40px rgba(6, 214, 160, 0.5);
            margin-bottom: 15px;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(6, 214, 160, 0.5); }
            to { text-shadow: 0 0 40px rgba(6, 214, 160, 0.8); }
        }
        
        .header p {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.3rem;
            font-weight: 300;
            letter-spacing: 0.5px;
        }
        
        /* Main grid layout */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            max-width: 1400px;
            margin: 0 auto;
            flex: 1;
            animation: fadeInUp 1s ease-out 0.3s both;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Panel styling */
        .panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 30px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #4ade80, #06d6a0, #3b82f6);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .panel:hover::before {
            opacity: 1;
        }
        
        .panel:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .panel h3 {
            color: #06d6a0;
            font-size: 1.5rem;
            margin-bottom: 25px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Tab system */
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 15px;
        }
        
        .tab-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            background: transparent;
            color: rgba(255, 255, 255, 0.6);
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            font-size: 14px;
        }
        
        .tab-btn.active {
            background: linear-gradient(135deg, #4ade80, #06d6a0);
            color: white;
            transform: scale(1.02);
            box-shadow: 0 8px 20px rgba(74, 222, 128, 0.3);
        }
        
        .tab-content {
            display: none;
            animation: slideIn 0.3s ease-out;
        }
        
        .tab-content.active { 
            display: block; 
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* File upload area */
        .file-upload {
            border: 2px dashed rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            padding: 50px 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.02);
            position: relative;
            overflow: hidden;
        }
        
        .file-upload::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: radial-gradient(circle, rgba(74, 222, 128, 0.1) 0%, transparent 70%);
            transition: all 0.3s ease;
            transform: translate(-50%, -50%);
            border-radius: 50%;
        }
        
        .file-upload:hover::before {
            width: 200px;
            height: 200px;
        }
        
        .file-upload:hover {
            border-color: #4ade80;
            background: rgba(74, 222, 128, 0.05);
            transform: scale(1.02);
        }
        
        .file-upload.drag-over {
            border-color: #06d6a0;
            background: rgba(6, 214, 160, 0.1);
            transform: scale(1.05);
        }
        
        .file-upload-content {
            position: relative;
            z-index: 1;
            color: rgba(255, 255, 255, 0.8);
        }
        
        .file-upload-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            display: block;
        }
        
        /* Input styling */
        input[type="url"], input[type="text"], textarea {
            width: 100%;
            padding: 18px 24px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        input[type="url"]::placeholder, 
        input[type="text"]::placeholder, 
        textarea::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        input[type="url"]:focus, 
        input[type="text"]:focus, 
        textarea:focus {
            outline: none;
            border-color: #4ade80;
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
        }
        
        /* Button styling */
        .solve-btn {
            background: linear-gradient(135deg, #4ade80 0%, #06d6a0 100%);
            color: white;
            padding: 20px 40px;
            border: none;
            border-radius: 15px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 25px;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }
        
        .solve-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            transition: all 0.5s ease;
            transform: translate(-50%, -50%);
        }
        
        .solve-btn:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .solve-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(74, 222, 128, 0.4);
        }
        
        .solve-btn:disabled {
            background: rgba(255, 255, 255, 0.1);
            cursor: not-allowed;
            transform: none;
        }
        
        /* Image preview */
        .image-preview {
            max-width: 100%;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Solution area */
        .solution-display {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
            padding: 30px;
            min-height: 300px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .solution-display::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #4ade80, #06d6a0, #3b82f6, #8b5cf6);
            background-size: 200% 100%;
            animation: shimmer 3s ease-in-out infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { background-position: -200% 0; }
            50% { background-position: 200% 0; }
        }
        
        .solution-content {
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.8;
            font-size: 16px;
        }
        
        .empty-state {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            padding: 60px 20px;
        }
        
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            animation: bounce 2s ease-in-out infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
        
        /* Chat area */
        .chat-area {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
            padding: 25px;
            height: 500px;
            display: flex;
            flex-direction: column;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 20px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            border-radius: 15px;
            background: rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .message {
            margin-bottom: 15px;
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 85%;
            animation: messageSlide 0.3s ease-out;
            position: relative;
        }
        
        @keyframes messageSlide {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            background: linear-gradient(135deg, #4ade80, #06d6a0);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .ai-message {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
            border-bottom-left-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .chat-input-area {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .chat-input:focus {
            border-color: #4ade80;
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
        }
        
        .send-btn {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .send-btn:hover {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            transform: scale(1.1) rotate(15deg);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
        }
        
        /* Sequence display */
        .sequence-display {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 20px;
            padding: 25px;
            margin-top: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .sequence-step {
            background: rgba(255, 255, 255, 0.05);
            margin: 15px 0;
            padding: 20px;
            border-radius: 15px;
            border-left: 4px solid #4ade80;
            transition: all 0.3s ease;
            animation: stepSlide 0.5s ease-out;
        }
        
        @keyframes stepSlide {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .sequence-step:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(5px);
        }
        
        .step-number {
            background: linear-gradient(135deg, #4ade80, #06d6a0);
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            font-size: 14px;
        }
        
        .step-content {
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
        }
        
        /* Loading animation */
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top: 4px solid #4ade80;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Status messages */
        .error, .success {
            padding: 18px 24px;
            border-radius: 15px;
            margin: 15px 0;
            font-weight: 600;
            animation: slideIn 0.3s ease-out;
        }
        
        .error {
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .success {
            background: rgba(74, 222, 128, 0.1);
            color: #86efac;
            border: 1px solid rgba(74, 222, 128, 0.3);
        }
        
        /* Responsive design */
        @media (max-width: 1024px) {
            .main-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .header h1 {
                font-size: 2.5rem;
            }
            
            .header .brand {
                font-size: 3rem;
            }
        }
        
        @media (max-width: 768px) {
            .app-wrapper {
                padding: 15px;
            }
            
            .panel {
                padding: 20px;
            }
            
            .header {
                padding: 20px 0;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .header .brand {
                font-size: 2.5rem;
            }
            
            .tab-buttons {
                flex-direction: column;
                gap: 8px;
            }
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #4ade80, #06d6a0);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #22c55e, #059669);
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    
    <div class="app-wrapper">
        <div class="header">
            <div class="brand">NY AI</div>
            <h1>Advanced Question Solver</h1>
            <p>Powered by Advanced AI with OCR, LaTeX & Interactive Chat</p>
        </div>
        
        <div class="main-grid">
            <div class="left-panel">
                <div class="panel">
                    <h3>📤 Input Question</h3>
                    
                    <div class="tab-buttons">
                        <button class="tab-btn active" onclick="switchTab('image')">📷 Image</button>
                        <button class="tab-btn" onclick="switchTab('url')">🔗 URL</button>
                        <button class="tab-btn" onclick="switchTab('text')">📝 Text</button>
                    </div>
                    
                    <form method="POST" enctype="multipart/form-data" id="questionForm">
                        <div id="image-tab" class="tab-content active">
                            <div class="file-upload" onclick="document.getElementById('imageFile').click()">
                                <div class="file-upload-content">
                                    <span class="file-upload-icon">📁</span>
                                    <div>Click to upload or drag & drop image</div>
                                    <small>Supports JPG, PNG, GIF, WebP</small>
                                </div>
                                <input type="file" id="imageFile" name="image_file" accept="image/*" style="display: none;" onchange="previewImage(this)">
                            </div>
                        </div>
                        
                        <div id="url-tab" class="tab-content">
                            <input type="url" name="image_url" placeholder="🔗 Paste image URL here..." value="{{ image_url or '' }}">
                        </div>
                        
                        <div id="text-tab" class="tab-content">
                            <textarea name="question_text" rows="8" placeholder="📝 Type or paste your question here...">{{ question_text or '' }}</textarea>
                        </div>
                        
                        <button type="submit" class="solve-btn" id="solveBtn">
                            <span>🧠 Analyze & Solve Question</span>
                        </button>
                    </form>
                </div>
                
                {% if image_url %}
                <div class="panel">
                    <h3>🖼️ Input Image</h3>
                    <img src="{{ image_url }}" class="image-preview" alt="Question Image">
                </div>
                {% endif %}
                
                {% if extracted_text %}
                <div class="panel">
                    <h3>📄 Extracted Text</h3>
                    <div class="solution-display">
                        <pre class="solution-content">{{ extracted_text }}</pre>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="right-panel">
                <div class="panel">
                    <h3>✅ Solution</h3>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Analyzing question with NY AI...</p>
                    </div>
                    
                    {% if solution %}
                    <div class="solution-display">
                        <div class="solution-content" id="solutionContent">{{ solution }}</div>
                    </div>
                    {% else %}
                    <div class="solution-display">
                        <div class="empty-state">
                            <div class="empty-state-icon">🤖</div>
                            <p>Upload an image, provide a URL, or type a question to get started!</p>
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if error %}
                    <div class="error">{{ error }}</div>
                    {% endif %}
                </div>
                
                {% if solution %}
                <div class="panel">
                    <h3>📋 Solution Sequence</h3>
                    <div class="sequence-display" id="sequenceDisplay">
                        <div class="loading" style="display: block;">
                            <div class="spinner"></div>
                            <p>Generating step sequence...</p>
                        </div>
                    </div>
                </div>
                {% endif %}
                
                <div class="chat-area">
                    <h3>💬 Chat with NY AI</h3>
                    <div class="chat-messages" id="chatMessages">
                        {% for message in chat_history %}
                        <div class="message {{ 'user-message' if message.role == 'user' else 'ai-message' }}">
                            {{ message.content }}
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" id="chatInput" placeholder="Ask follow-up questions..." onkeypress="handleChatKeyPress(event)">
                        <button class="send-btn" onclick="sendChatMessage()">➤</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 50;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
                particlesContainer.appendChild(particle);
            }
        }
        
        // Initialize MathJax
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
        
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
        
        // Enhanced form submission
        document.getElementById('questionForm').addEventListener('submit', function(e) {
            const formData = new FormData(this);
            const hasImage = document.getElementById('imageFile').files.length > 0;
            const hasUrl = formData.get('image_url').trim() !== '';
            const hasText = formData.get('question_text').trim() !== '';
            
            if (!hasImage && !hasUrl && !hasText) {
                e.preventDefault();
                showError('Please provide either an image or text question.');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('solveBtn').disabled = true;
            document.getElementById('solveBtn').innerHTML = '<span>🔄 Analyzing...</span>';
        });
        
        // Chat functionality
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
            
            // Show typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message ai-message';
            typingDiv.innerHTML = '<span style="opacity: 0.6;">NY AI is typing...</span>';
            typingDiv.id = 'typingIndicator';
            document.getElementById('chatMessages').appendChild(typingDiv);
            scrollChatToBottom();
            
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
                // Remove typing indicator
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
                
                if (data.response) {
                    addMessageToChat(data.response, 'ai');
                    // Re-render MathJax for new content
                    MathJax.typesetPromise([document.getElementById('chatMessages')]);
                } else if (data.error) {
                    addMessageToChat('Error: ' + data.error, 'ai');
                }
            })
            .catch(error => {
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
                addMessageToChat('Error: ' + error.message, 'ai');
            });
        }
        
        function addMessageToChat(message, role) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.textContent = message;
            chatMessages.appendChild(messageDiv);
            scrollChatToBottom();
        }
        
        function scrollChatToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Generate solution sequence
        function generateSolutionSequence() {
            const sequenceDisplay = document.getElementById('sequenceDisplay');
            if (!sequenceDisplay) return;
            
            fetch('/generate_sequence', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.sequence) {
                    sequenceDisplay.innerHTML = data.sequence;
                    MathJax.typesetPromise([sequenceDisplay]);
                } else {
                    sequenceDisplay.innerHTML = '<div class="error">Failed to generate sequence</div>';
                }
            })
            .catch(error => {
                sequenceDisplay.innerHTML = '<div class="error">Error generating sequence</div>';
            });
        }
        
        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            document.querySelector('.left-panel').appendChild(errorDiv);
            
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            
            // Generate sequence if solution exists
            if (document.getElementById('solutionContent')) {
                setTimeout(generateSolutionSequence, 1000);
            }
            
            // Render MathJax for existing content
            MathJax.typesetPromise();
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
    """Enhanced API call with vision capabilities."""
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    parts = [{"text": prompt}]
    
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
        
        return "No valid response from API."
        
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    except json.JSONDecodeError as e:
        return f"Failed to parse API response: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def create_enhanced_prompt(question_text=None, has_image=False):
    """Create an enhanced prompt for better question analysis."""
    
    base_prompt = """You are NY AI, an advanced question solver with expertise in Mathematics, Physics, and Chemistry.

TASK: Analyze and solve the provided question with exceptional detail and mathematical precision.

INSTRUCTIONS:
1. **Question Analysis**: Identify the subject area, topic, and difficulty level
2. **Text Extraction**: If there's an image, extract ALL text and mathematical expressions
3. **Concept Identification**: Identify key concepts, formulas, and principles needed
4. **Step-by-Step Solution**: Provide detailed, methodical solution with proper mathematical notation
5. **Final Answer**: Clearly state the final answer with appropriate units
6. **Verification**: Double-check calculations and reasoning
7. **Alternative Methods**: Mention other solution approaches if applicable

FORMAT YOUR RESPONSE WITH PROPER LATEX/MATH NOTATION:
Use $ for inline math: $x^2 + y^2 = z^2$
Use $$ for display math: $$\\int_{0}^{\\infty} e^{-x} dx = 1$$

📋 **QUESTION ANALYSIS**
[Subject area, topic, difficulty level]

📄 **EXTRACTED CONTENT** (if image provided)
[All text, equations, and diagram descriptions]

🔑 **KEY CONCEPTS & FORMULAS**
[Relevant formulas with proper LaTeX notation]

📝 **DETAILED SOLUTION**
[Step-by-step solution with mathematical expressions]

✅ **FINAL ANSWER**
[Clear final answer with units and proper formatting]

🔍 **VERIFICATION**
[Check calculations and logic]

💡 **ALTERNATIVE APPROACHES** (if applicable)
[Other solution methods]
"""
    
    if question_text:
        base_prompt += f"\n\nQUESTION TEXT:\n{question_text}"
    
    if has_image:
        base_prompt += "\n\nIMAGE: Analyze the provided image for visual information, diagrams, graphs, or mathematical expressions."
    
    return base_prompt

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    image_url = None
    solution = None
    error = None
    extracted_text = None
    question_text = None
    
    if request.method == 'POST':
        try:
            image_url = request.form.get('image_url', '').strip()
            question_text = request.form.get('question_text', '').strip()
            
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
            
            if not question_text and not has_image:
                error = "Please provide either an image or text question."
            
            elif not error:
                prompt = create_enhanced_prompt(question_text, has_image)
                
                if has_image:
                    solution = call_gemini_vision(prompt, image_data, image_url)
                else:
                    solution = call_gemini_vision(prompt)
                
                if has_image and not error:
                    extract_prompt = """Extract ALL text content from this image including:
                    - Question text and instructions
                    - Mathematical equations and expressions
                    - Numbers, measurements, and units
                    - Labels, annotations, and diagrams
                    - Multiple choice options if present
                    
                    Format the extracted text clearly with proper mathematical notation using LaTeX where appropriate."""
                    
                    extracted_text = call_gemini_vision(extract_prompt, image_data, image_url)
                
                session['current_context'] = {
                    'question_text': question_text,
                    'extracted_text': extracted_text,
                    'solution': solution,
                    'has_image': has_image
                }
                
        except Exception as e:
            error = f"An unexpected error occurred: {str(e)}"
    
    return render_template_string(HTML_TEMPLATE,
                                image_url=image_url,
                                solution=solution,
                                error=error,
                                extracted_text=extracted_text,
                                question_text=question_text,
                                chat_history=session.get('chat_history', []))

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        context = session.get('current_context', {})
        
        chat_prompt = f"""You are NY AI continuing a conversation about a question. Context:

ORIGINAL QUESTION: {context.get('question_text', 'N/A')}
EXTRACTED TEXT: {context.get('extracted_text', 'N/A')}
PREVIOUS SOLUTION: {context.get('solution', 'N/A')}

USER'S FOLLOW-UP: {user_message}

Provide a helpful response using proper LaTeX notation for mathematics. Use $ for inline math and $$ for display math."""
        
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

@app.route('/generate_sequence', methods=['POST'])
def generate_sequence():
    try:
        context = session.get('current_context', {})
        solution = context.get('solution', '')
        
        if not solution:
            return jsonify({'error': 'No solution available'}), 400
        
        sequence_prompt = f"""Based on the following solution, create a clear step-by-step sequence in HTML format:

SOLUTION: {solution}

Create an HTML sequence with the following structure:
- Each step should be in a div with class "sequence-step"
- Include a span with class "step-number" containing the step number
- Include a div with class "step-content" containing the step description
- Use proper LaTeX notation for mathematical expressions
- Make it visually appealing and easy to follow

Format like this:
<div class="sequence-step">
    <span class="step-number">1</span>
    <div class="step-content">Step description with $math$ notation</div>
</div>

Generate 5-8 clear, logical steps that break down the solution process."""
        
        sequence_html = call_gemini_vision(sequence_prompt)
        
        return jsonify({'sequence': sequence_html})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    session.modified = True
    return jsonify({'success': True})

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
