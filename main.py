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
    <title>NY AI - Advanced JEE Question Solver</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true
            },
            svg: {
                fontCache: 'global'
            }
        };
    </script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --dark: #1e293b;
            --light: #f8fafc;
            --glass: rgba(255, 255, 255, 0.1);
            --glass-border: rgba(255, 255, 255, 0.2);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* Animated Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
            animation: backgroundMove 20s ease-in-out infinite;
            z-index: -1;
        }

        @keyframes backgroundMove {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(1deg); }
        }

        /* Floating Elements */
        .floating-shapes {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }

        .shape {
            position: absolute;
            opacity: 0.1;
            animation: float 15s ease-in-out infinite;
        }

        .shape:nth-child(1) {
            top: 10%;
            left: 10%;
            width: 80px;
            height: 80px;
            background: var(--primary);
            border-radius: 50%;
            animation-delay: 0s;
        }

        .shape:nth-child(2) {
            top: 20%;
            right: 10%;
            width: 120px;
            height: 120px;
            background: var(--secondary);
            border-radius: 30%;
            animation-delay: 5s;
        }

        .shape:nth-child(3) {
            bottom: 20%;
            left: 20%;
            width: 100px;
            height: 100px;
            background: var(--accent);
            border-radius: 20%;
            animation-delay: 10s;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
            33% { transform: translateY(-30px) translateX(20px) rotate(120deg); }
            66% { transform: translateY(20px) translateX(-20px) rotate(240deg); }
        }

        /* Header */
        .header {
            text-align: center;
            padding: 40px 20px;
            color: white;
            position: relative;
            z-index: 10;
        }

        .header h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #fff 0%, #e0e7ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: glow 3s ease-in-out infinite alternate;
        }

        .header .subtitle {
            font-size: clamp(1rem, 2vw, 1.3rem);
            opacity: 0.9;
            margin-bottom: 30px;
        }

        @keyframes glow {
            from { filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.3)); }
            to { filter: drop-shadow(0 0 30px rgba(255, 255, 255, 0.6)); }
        }

        /* Main Layout */
        .main-wrapper {
            padding: 0 20px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        /* Glass Morphism Cards */
        .glass-card {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        }

        .glass-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
            border-color: rgba(255, 255, 255, 0.3);
        }

        /* Input Section */
        .input-section h3 {
            color: white;
            font-size: 1.4rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .tab-buttons {
            display: flex;
            gap: 8px;
            margin-bottom: 25px;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 16px;
        }

        .tab-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            background: transparent;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .tab-btn.active {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            transform: scale(1.02);
        }

        .tab-btn:hover:not(.active) {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease-in-out;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .file-upload {
            border: 3px dashed rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(255, 255, 255, 0.05);
            color: white;
        }

        .file-upload:hover {
            border-color: rgba(255, 255, 255, 0.5);
            background: rgba(255, 255, 255, 0.1);
            transform: scale(1.02);
        }

        .file-upload.drag-over {
            border-color: var(--accent);
            background: rgba(6, 182, 212, 0.1);
            transform: scale(1.05);
        }

        input[type="url"], input[type="text"], textarea {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        input::placeholder, textarea::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.1);
        }

        .solve-btn {
            background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            width: 100%;
            margin-top: 25px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(16, 185, 129, 0.4);
        }

        .solve-btn:disabled {
            background: rgba(156, 163, 175, 0.5);
            cursor: not-allowed;
            transform: none;
        }

        /* Solution Area */
        .solution-area {
            min-height: 300px;
            position: relative;
        }

        .solution-area h3 {
            color: white;
            font-size: 1.4rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .solution-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 25px;
            color: #374151;
            line-height: 1.8;
            font-size: 15px;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
            min-height: 200px;
            animation: slideIn 0.6s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .empty-state {
            text-align: center;
            color: rgba(255, 255, 255, 0.7);
            padding: 60px 20px;
        }

        .empty-state .icon {
            font-size: 4rem;
            margin-bottom: 20px;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.7; }
            50% { transform: scale(1.1); opacity: 1; }
        }

        /* Chat Area */
        .chat-area {
            height: 400px;
            display: flex;
            flex-direction: column;
        }

        .chat-area h3 {
            color: white;
            font-size: 1.4rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .chat-messages {
            flex: 1;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 20px;
            overflow-y: auto;
            margin-bottom: 15px;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .message {
            margin-bottom: 15px;
            padding: 12px 18px;
            border-radius: 20px;
            max-width: 85%;
            animation: messageSlide 0.4s ease-out;
        }

        @keyframes messageSlide {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .user-message {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 8px;
        }

        .ai-message {
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            color: #374151;
            border-bottom-left-radius: 8px;
        }

        .chat-input-area {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .chat-input {
            flex: 1;
            padding: 14px 20px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            resize: none;
            max-height: 100px;
        }

        .chat-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.1);
        }

        .send-btn {
            background: linear-gradient(135deg, var(--accent) 0%, #0891b2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .send-btn:hover {
            transform: scale(1.1) rotate(15deg);
            box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
        }

        /* Features Grid */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .feature-card {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            color: white;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: rotate 4s linear infinite;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .feature-card:hover::before {
            opacity: 1;
        }

        .feature-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(255, 255, 255, 0.3);
        }

        @keyframes rotate {
            to { transform: rotate(360deg); }
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            position: relative;
            z-index: 2;
        }

        .feature-card h4 {
            font-size: 1.2rem;
            margin-bottom: 10px;
            position: relative;
            z-index: 2;
        }

        .feature-card p {
            opacity: 0.9;
            position: relative;
            z-index: 2;
        }

        /* Question Sequence */
        .question-sequence {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 30px;
            color: white;
        }

        .sequence-header {
            font-size: 1.4rem;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sequence-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .sequence-step {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .sequence-step:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-4px);
        }

        .step-number {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px;
            font-weight: bold;
            font-size: 1.1rem;
        }

        /* Loading Animation */
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            color: white;
        }

        .spinner {
            width: 50px;
            height: 50px;
            margin: 0 auto 20px;
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-text {
            font-size: 1.1rem;
            margin-bottom: 10px;
        }

        .loading-subtext {
            font-size: 0.9rem;
            opacity: 0.7;
        }

        /* Image Preview */
        .image-preview {
            max-width: 100%;
            max-height: 300px;
            border-radius: 16px;
            margin: 20px 0;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
            object-fit: contain;
        }

        /* Extracted Text */
        .extracted-text {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid var(--accent);
            color: #374151;
            font-family: 'Fira Code', monospace;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        /* Status Messages */
        .status-message {
            padding: 16px 20px;
            border-radius: 12px;
            margin: 15px 0;
            font-weight: 500;
            animation: slideIn 0.5s ease-out;
        }

        .error {
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .success {
            background: rgba(16, 185, 129, 0.1);
            color: #6ee7b7;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Responsive Design */
        @media (max-width: 968px) {
            .content-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .features-grid {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            }
            
            .sequence-steps {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .main-wrapper {
                padding: 0 15px 30px;
            }
            
            .glass-card {
                padding: 20px;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-buttons {
                flex-direction: column;
            }
            
            .tab-btn {
                flex: none;
            }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
    </style>
</head>
<body>
    <div class="floating-shapes">
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
    </div>

    <div class="header">
        <h1>🤖 NY AI</h1>
        <p class="subtitle">Advanced JEE Question Solver with AI-Powered Analysis</p>
    </div>

    <div class="main-wrapper">
        <!-- Features Grid -->
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h4>Advanced OCR</h4>
                <p>Extract text and equations from complex mathematical images with high precision</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧮</div>
                <h4>Mathematical Rendering</h4>
                <p>Beautiful mathematical expressions rendered with MathJax for perfect clarity</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h4>Interactive Chat</h4>
                <p>Ask follow-up questions and get detailed explanations for better understanding</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h4>Step-by-Step Analysis</h4>
                <p>Comprehensive breakdown of solutions with concept explanations</p>
            </div>
        </div>

        <!-- Solution Sequence -->
        <div class="question-sequence">
            <div class="sequence-header">
                <span>🎯</span>
                <span>Solution Process</span>
            </div>
            <div class="sequence-steps">
                <div class="sequence-step">
                    <div class="step-number">1</div>
                    <h5>Question Analysis</h5>
                    <p>Identify subject, topic & difficulty</p>
                </div>
                <div class="sequence-step">
                    <div class="step-number">2</div>
                    <h5>Text Extraction</h5>
                    <p>OCR processing & content parsing</p>
                </div>
                <div class="sequence-step">
                    <div class="step-number">3</div>
                    <h5>Concept Mapping</h5>
                    <p>Link relevant formulas & principles</p>
                </div>
                <div class="sequence-step">
                    <div class="step-number">4</div>
                    <h5>Solution Generation</h5>
                    <p>Step-by-step problem solving</p>
                </div>
                <div class="sequence-step">
                    <div class="step-number">5</div>
                    <h5>Verification</h5>
                    <p>Cross-check & alternative methods</p>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="content-grid">
            <!-- Input Panel -->
            <div class="glass-card input-section">
                <h3>📤 Input Question</h3>
                
                <div class="tab-buttons">
                    <button class="tab-btn active" onclick="switchTab('image')">📷 Image</button>
                    <button class="tab-btn" onclick="switchTab('url')">🔗 URL</button>
                    <button class="tab-btn" onclick="switchTab('text')">📝 Text</button>
                </div>
                
                <form method="POST" enctype="multipart/form-data" id="questionForm">
                    <div id="image-tab" class="tab-content active">
                        <div class="file-upload" onclick="document.getElementById('imageFile').click()">
                            <div style="font-size: 2rem; margin-bottom: 10px;">📁</div>
                            <div style="font-size: 1.1rem; margin-bottom: 5px;">Click to upload or drag & drop</div>
                            <small style="opacity: 0.7;">Supports JPG, PNG, GIF, WebP</small>
                            <input type="file" id="imageFile" name="image_file" accept="image/*" style="display: none;" onchange="previewImage(this)">
                        </div>
                    </div>
                    
                    <div id="url-tab" class="tab-content">
                        <input type="url" name="image_url" placeholder="🔗 Paste image URL here..." value="{{ image_url or '' }}">
                    </div>
                    
                    <div id="text-tab" class="tab-content">
                        <textarea name="question_text" rows="8" placeholder="📝 Type or paste your JEE question here...">{{ question_text or '' }}</textarea>
                    </div>
                    
                    <button type="submit" class="solve-btn" id="solveBtn">
                        <span id="solveText">🧠 Analyze & Solve Question</span>
                    </button>
                </form>

                {% if image_url %}
                <div style="margin-top: 20px;">
                    <h4 style="color: white; margin-bottom: 15px;">🖼️ Input Image</h4>
                    <img src="{{ image_url }}" class="image-preview" alt="Question Image">
                </div>
                {% endif %}
                
                {% if extracted_text %}
                <div style="margin-top: 20px;">
                    <h4 style="color: white; margin-bottom: 15px;">📄 Extracted Text</h4>
                    <div class="extracted-text">
                        <pre style="white-space: pre-wrap; font-family: inherit;">{{ extracted_text }}</pre>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- Solution Panel -->
            <div class="glass-card solution-area">
                <h3>✅ Solution</h3>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div class="loading-text">Analyzing with NY AI...</div>
                    <div class="loading-subtext">Processing question and generating solution</div>
                </div>
                
                {% if solution %}
                <div class="solution-content" id="solutionContent">
                    <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">{{ solution }}</pre>
                </div>
                {% else %}
                <div class="empty-state">
                    <div class="icon">🤔</div>
                    <h4>Ready to Solve</h4>
                    <p>Upload an image, provide a URL, or type a question to get started!</p>
                </div>
                {% endif %}
                
                {% if error %}
                <div class="status-message error">{{ error }}</div>
                {% endif %}
            </div>
        </div>

        <!-- Chat Section -->
        <div class="glass-card chat-area">
            <h3>💬 Chat with NY AI</h3>
            <div class="chat-messages" id="chatMessages">
                {% for message in chat_history %}
                <div class="message {{ 'user-message' if message.role == 'user' else 'ai-message' }}">
                    {{ message.content }}
                </div>
                {% endfor %}
                {% if not chat_history %}
                <div style="text-align: center; color: #94a3b8; padding: 40px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">💭</div>
                    <p>Start a conversation about the question or ask for clarifications!</p>
                </div>
                {% endif %}
            </div>
            
            <div class="chat-input-area">
                <textarea class="chat-input" id="chatInput" placeholder="Ask follow-up questions..." rows="1" onkeypress="handleChatKeyPress(event)" oninput="autoResize(this)"></textarea>
                <button class="send-btn" onclick="sendChatMessage()">➤</button>
            </div>
        </div>
    </div>

    <script>
        // Tab Management
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

        // Image Preview
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.getElementById('imagePreview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = 'imagePreview';
                        preview.className = 'image-preview';
                        
                        const container = document.createElement('div');
                        container.style.marginTop = '20px';
                        const title = document.createElement('h4');
                        title.style.color = 'white';
                        title.style.marginBottom = '15px';
                        title.textContent = '🖼️ Preview';
                        container.appendChild(title);
                        container.appendChild(preview);
                        
                        input.closest('.glass-card').appendChild(container);
                    }
                    preview.src = e.target.result;
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        // Drag and Drop
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

        // Form Submission
        document.getElementById('questionForm').addEventListener('submit', function(e) {
            const loading = document.getElementById('loading');
            const solveBtn = document.getElementById('solveBtn');
            const solveText = document.getElementById('solveText');
            
            loading.style.display = 'block';
            solveBtn.disabled = true;
            solveText.textContent = '🔄 Analyzing...';
            
            // Hide empty state if visible
            const emptyState = document.querySelector('.empty-state');
            if (emptyState) {
                emptyState.style.display = 'none';
            }
        });

        // Chat Functionality
        function handleChatKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatMessage();
            }
        }

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
        }

        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessageToChat(message, 'user');
            input.value = '';
            input.style.height = 'auto';
            
            // Show typing indicator
            const typingIndicator = addTypingIndicator();
            
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
                removeTypingIndicator(typingIndicator);
                if (data.response) {
                    addMessageToChat(data.response, 'ai');
                    // Re-render MathJax for new content
                    MathJax.typesetPromise();
                } else if (data.error) {
                    addMessageToChat('❌ Error: ' + data.error, 'ai');
                }
            })
            .catch(error => {
                removeTypingIndicator(typingIndicator);
                addMessageToChat('❌ Connection error: ' + error.message, 'ai');
            });
        }

        function addMessageToChat(message, role) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.innerHTML = message.replace(/\n/g, '<br>');
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Remove empty state if present
            const emptyState = chatMessages.querySelector('[style*="text-align: center"]');
            if (emptyState) {
                emptyState.remove();
            }
        }

        function addTypingIndicator() {
            const chatMessages = document.getElementById('chatMessages');
            const indicator = document.createElement('div');
            indicator.className = 'message ai-message';
            indicator.innerHTML = '<span style="opacity: 0.6;">🤔 NY AI is thinking...</span>';
            indicator.id = 'typing-indicator';
            chatMessages.appendChild(indicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return indicator;
        }

        function removeTypingIndicator(indicator) {
            if (indicator && indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        }

        // Initialize MathJax rendering for existing content
        document.addEventListener('DOMContentLoaded', function() {
            if (window.MathJax) {
                MathJax.typesetPromise();
            }
        });

        // Animate elements on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe all cards
        document.querySelectorAll('.glass-card, .feature-card').forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });

        // Add smooth scrolling
        document.documentElement.style.scrollBehavior = 'smooth';
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
        
        return "No valid response from NY AI."
        
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    except json.JSONDecodeError as e:
        return f"Failed to parse API response: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def create_enhanced_prompt(question_text=None, has_image=False):
    """Create an enhanced prompt for better JEE question analysis with MathJax formatting."""
    
    base_prompt = """You are NY AI, an expert JEE (Joint Entrance Examination) tutor with deep knowledge in Physics, Chemistry, and Mathematics. 

IMPORTANT: Format all mathematical expressions using LaTeX notation for MathJax rendering:
- Inline math: $expression$ 
- Display math: $$expression$$
- Use proper LaTeX syntax for fractions, integrals, summations, etc.

TASK: Analyze and solve the provided JEE question with exceptional detail and accuracy.

INSTRUCTIONS:
1. **Question Analysis**: Identify subject area, topic, and difficulty level
2. **Text Extraction**: If image provided, extract ALL text, equations, and diagrams
3. **Concept Identification**: Key concepts and formulas (formatted with LaTeX)
4. **Step-by-Step Solution**: Detailed, methodical solution with proper math formatting
5. **Final Answer**: Clear final answer with units if applicable
6. **Alternative Methods**: If applicable, mention other solution approaches
7. **Common Mistakes**: Point out typical errors students make

FORMAT YOUR RESPONSE AS:

📋 **QUESTION ANALYSIS**
[Subject area, topic, difficulty level]

📄 **EXTRACTED CONTENT** (if image provided)
[All text, equations, and diagram descriptions with LaTeX formatting]

🔑 **KEY CONCEPTS**
[Relevant formulas and principles - use LaTeX notation]
Example: The quadratic formula is $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$

📝 **DETAILED SOLUTION**
[Step-by-step solution with explanations and LaTeX math]

✅ **FINAL ANSWER**
[Clear final answer with proper LaTeX formatting and units]

⚠️ **COMMON MISTAKES TO AVOID**
[Typical errors students make in similar problems]

💡 **ALTERNATIVE APPROACHES** (if applicable)
[Other methods to solve the problem]

🎯 **CONCEPT REINFORCEMENT**
[Related JEE topics and practice suggestions]
"""
    
    if question_text:
        base_prompt += f"\n\nQUESTION TEXT:\n{question_text}"
    
    if has_image:
        base_prompt += "\n\nIMAGE: Please analyze the provided image carefully for any visual information, diagrams, graphs, or mathematical expressions. Extract and format all mathematical content using proper LaTeX notation."
    
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
            
            # Validate input
            if not question_text and not has_image:
                error = "Please provide either an image or text question."
            
            elif not error:
                prompt = create_enhanced_prompt(question_text, has_image)
                
                if has_image:
                    solution = call_gemini_vision(prompt, image_data, image_url)
                else:
                    solution = call_gemini_vision(prompt)
                
                # Extract text if image was provided
                if has_image and not error:
                    extract_prompt = """Extract ALL text content from this image including:
                    - Question text
                    - Mathematical equations (format with LaTeX for MathJax)
                    - Numbers, measurements, units
                    - Labels, annotations, multiple choice options
                    
                    Format extracted text clearly with proper LaTeX notation for mathematical expressions."""
                    
                    extracted_text = call_gemini_vision(extract_prompt, image_data, image_url)
                
                # Store context for chat
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
        
        chat_prompt = f"""You are NY AI, continuing a conversation about a JEE question. Here's the context:

ORIGINAL QUESTION: {context.get('question_text', 'N/A')}
EXTRACTED TEXT: {context.get('extracted_text', 'N/A')}
PREVIOUS SOLUTION: {context.get('solution', 'N/A')}

USER'S FOLLOW-UP QUESTION: {user_message}

IMPORTANT: Use LaTeX notation for all mathematical expressions:
- Inline math: $expression$
- Display math: $$expression$$

Provide a helpful, detailed response with proper mathematical formatting. If explaining concepts, use clear LaTeX notation for formulas and equations."""
        
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
        
        # Keep only last 20 messages
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

# Vercel-specific configuration
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'NY AI JEE Solver'})

# For Vercel deployment
def handler(request):
    return app(request.environ, start_response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
