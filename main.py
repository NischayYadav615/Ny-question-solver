import os
import json
import base64
from flask import Flask, request, render_template_string, session, jsonify
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import uuid
import datetime

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCfiA0TjeSEUFqJkgYtbLzjsbEdNW_ZTpk"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

# Store messages in memory (use a database in production)
messages = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NY AI - Advanced Chat Assistant</title>
    
    <!-- MathJax Configuration -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                packages: {'[+]': ['ams', 'newcommand', 'configmacros']}
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        adjustMathJaxForMobile();
                    });
                }
            }
        };
        
        function adjustMathJaxForMobile() {
            const mathElements = document.querySelectorAll('.MathJax');
            mathElements.forEach(el => {
                el.style.maxWidth = '100%';
                el.style.overflowX = 'auto';
                el.style.overflowY = 'hidden';
            });
        }
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
    
    <style>
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0; 
        }
        
        :root {
            --primary: #667eea;
            --primary-dark: #5a67d8;
            --secondary: #764ba2;
            --accent: #ff6b6b;
            --accent-light: #ffd93d;
            --success: #48bb78;
            --warning: #ed8936;
            --bg-primary: #f8fafc;
            --bg-secondary: #edf2f7;
            --text-primary: #2d3748;
            --text-secondary: #4a5568;
            --text-light: #718096;
            --border: #e2e8f0;
            --shadow: 0 10px 40px rgba(0,0,0,0.1);
            --shadow-lg: 0 20px 60px rgba(0,0,0,0.15);
            --radius: 16px;
            --radius-lg: 24px;
        }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow: hidden;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        /* Enhanced Header */
        .chat-header {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 50%, var(--success) 100%);
            color: white;
            padding: 25px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            flex-shrink: 0;
            min-height: 90px;
        }
        
        .chat-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
            animation: headerShine 6s ease-in-out infinite;
        }
        
        @keyframes headerShine {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.7; }
        }
        
        .chat-title {
            display: flex;
            flex-direction: column;
            gap: 5px;
            position: relative;
            z-index: 1;
        }
        
        .ny-ai-logo {
            font-size: 2.2rem;
            font-weight: 900;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            letter-spacing: -1px;
            margin: 0;
        }
        
        .chat-subtitle {
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 400;
        }
        
        .chat-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
            z-index: 1;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.25);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        .fullscreen-toggle, .clear-chat-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 18px;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .fullscreen-toggle:hover, .clear-chat-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        /* Enhanced Messages Area with Fixed Layout */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 30px;
            background: var(--bg-primary);
            position: relative;
            scroll-behavior: smooth;
            height: calc(100vh - 90px - 120px);
            min-height: 0;
        }
        
        /* Enhanced scrollbar */
        .chat-messages::-webkit-scrollbar {
            width: 14px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 7px;
            margin: 10px 0;
            border: 1px solid var(--border);
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 7px;
            border: 2px solid var(--bg-secondary);
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--primary-dark), var(--accent));
            box-shadow: inset 0 1px 5px rgba(0,0,0,0.2);
        }
        
        .chat-messages::-webkit-scrollbar-thumb:active {
            background: linear-gradient(135deg, var(--accent), var(--primary));
        }
        
        .message-wrapper {
            display: flex;
            flex-direction: column;
            gap: 25px;
            width: 100%;
        }
        
        .message-group {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 25px;
            opacity: 0;
            transform: translateY(30px);
            animation: slideInMessage 0.6s ease forwards;
            width: 100%;
            max-width: 100%;
        }
        
        @keyframes slideInMessage {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-group.user {
            flex-direction: row-reverse;
            justify-content: flex-start;
        }
        
        .message-avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: white;
            font-size: 18px;
            flex-shrink: 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
        }
        
        .message-group.user .message-avatar {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }
        
        .message-group.bot .message-avatar {
            background: linear-gradient(135deg, var(--success) 0%, var(--accent-light) 100%);
        }
        
        .message-avatar::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at center, rgba(255,255,255,0.3) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .message-avatar:hover::before {
            opacity: 1;
        }
        
        .message-content {
            flex: 1;
            max-width: calc(100% - 80px);
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 0;
        }
        
        .message-bubble {
            background: white;
            padding: 20px 25px;
            border-radius: var(--radius);
            box-shadow: 0 6px 25px rgba(0,0,0,0.08);
            position: relative;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            max-width: 100%;
            width: 100%;
            box-sizing: border-box;
        }
        
        .message-group.user .message-bubble {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-bottom-right-radius: 8px;
        }
        
        .message-group.bot .message-bubble {
            background: white;
            border-left: 4px solid var(--success);
            border-bottom-left-radius: 8px;
        }
        
        .message-text {
            line-height: 1.7;
            font-size: 1rem;
            word-break: break-word;
            overflow-wrap: break-word;
            width: 100%;
            max-width: 100%;
        }
        
        .message-text * {
            max-width: 100%;
            box-sizing: border-box;
        }
        
        .message-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
            color: var(--text-light);
            margin-top: 8px;
        }
        
        .message-group.user .message-meta {
            color: rgba(255, 255, 255, 0.8);
        }
        
        .message-time {
            font-weight: 500;
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 20px 0;
            opacity: 0;
            animation: fadeIn 0.5s ease forwards;
        }
        
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
            background: white;
            padding: 15px 20px;
            border-radius: var(--radius);
            border-left: 4px solid var(--warning);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--warning);
            animation: typingBounce 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes typingBounce {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1.2); opacity: 1; }
        }
        
        /* Enhanced Math expressions */
        .math-expression, .MathJax, .MathJax_Display {
            max-width: 100% !important;
            width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            padding: 15px !important;
            background: var(--bg-secondary) !important;
            border-radius: 10px !important;
            margin: 15px 0 !important;
            border-left: 4px solid var(--accent-light) !important;
            font-family: 'Courier New', monospace !important;
            scroll-behavior: smooth !important;
            box-sizing: border-box !important;
            -webkit-overflow-scrolling: touch !important;
        }
        
        .MathJax_Display::-webkit-scrollbar {
            height: 8px;
        }
        
        .MathJax_Display::-webkit-scrollbar-track {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 4px;
        }
        
        .MathJax_Display::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        /* Enhanced Input Area */
        .chat-input-area {
            background: white;
            padding: 25px 30px;
            border-top: 2px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 15px;
            flex-shrink: 0;
            min-height: 120px;
            max-height: 200px;
            position: relative;
        }
        
        .input-wrapper {
            display: flex;
            align-items: flex-end;
            gap: 15px;
            position: relative;
        }
        
        .message-input {
            flex: 1;
            min-height: 50px;
            max-height: 120px;
            padding: 15px 20px;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            font-family: inherit;
            resize: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: var(--bg-primary);
            line-height: 1.5;
            overflow-y: auto;
        }
        
        .message-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: white;
            transform: translateY(-2px);
        }
        
        .message-input::-webkit-scrollbar {
            width: 6px;
        }
        
        .message-input::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 3px;
        }
        
        .message-input::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }
        
        .send-button {
            background: linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .send-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.6s;
        }
        
        .send-button:hover::before {
            left: 100%;
        }
        
        .send-button:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4);
        }
        
        .send-button:active {
            transform: translateY(-1px) scale(1.02);
        }
        
        .send-button:disabled {
            background: var(--text-light);
            cursor: not-allowed;
            transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .input-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9rem;
            color: var(--text-light);
        }
        
        .char-counter {
            font-weight: 500;
        }
        
        .input-hints {
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
        }
        
        .hint {
            color: var(--text-light);
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
            }
            
            .chat-header {
                padding: 20px;
                flex-wrap: wrap;
                min-height: auto;
            }
            
            .ny-ai-logo {
                font-size: 1.8rem;
            }
            
            .chat-subtitle {
                font-size: 0.9rem;
            }
            
            .chat-messages {
                padding: 20px 15px;
                height: calc(100vh - 140px);
            }
            
            .message-content {
                max-width: calc(100% - 60px);
            }
            
            .message-avatar {
                width: 35px;
                height: 35px;
                font-size: 14px;
            }
            
            .chat-input-area {
                padding: 15px;
                min-height: 100px;
            }
            
            .message-input {
                font-size: 16px;
                min-height: 44px;
            }
            
            .send-button {
                width: 44px;
                height: 44px;
                font-size: 18px;
            }
            
            .input-controls {
                flex-direction: column;
                gap: 10px;
                align-items: flex-start;
            }
            
            .MathJax_Display {
                padding: 10px !important;
                margin: 10px 0 !important;
                font-size: 0.9rem !important;
            }
        }
        
        /* Loading states */
        .loading {
            opacity: 0.7;
            pointer-events: none;
        }
        
        .message-group.loading .message-bubble {
            background: var(--bg-secondary);
            animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: -200px 0; }
            100% { background-position: calc(200px + 100%) 0; }
        }
        
        /* Fullscreen mode */
        .fullscreen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            border-radius: 0;
        }
        
        /* Custom animations */
        .bounce-in {
            animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        @keyframes bounceIn {
            0% {
                opacity: 0;
                transform: scale(0.3) translateY(50px);
            }
            50% {
                opacity: 1;
                transform: scale(1.05) translateY(-10px);
            }
            70% {
                transform: scale(0.9) translateY(0);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="chat-container" id="chatContainer">
        <div class="chat-header">
            <div class="chat-title">
                <h1 class="ny-ai-logo">NY AI</h1>
                <p class="chat-subtitle">Advanced Chat Assistant</p>
            </div>
            <div class="chat-controls">
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    Online
                </div>
                <button class="fullscreen-toggle" onclick="toggleFullscreen()" title="Toggle Fullscreen">
                    ⛶
                </button>
                <button class="clear-chat-btn" onclick="clearChat()" title="Clear Chat">
                    🗑️
                </button>
            </div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message-wrapper" id="messageWrapper">
                <!-- Welcome message -->
                <div class="message-group bot bounce-in">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <div class="message-bubble">
                            <div class="message-text">
                                Welcome to NY AI! I'm your advanced chat assistant. I can help you with:
                                <br><br>
                                • <strong>Mathematical problems</strong> with step-by-step solutions
                                <br>
                                • <strong>Academic questions</strong> across various subjects
                                <br>
                                • <strong>General assistance</strong> and information
                                <br><br>
                                Feel free to ask me anything! I support LaTeX math expressions too: $E = mc^2$
                            </div>
                            <div class="message-meta">
                                <span class="message-time">Just now</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="chat-input-area">
            <div class="input-wrapper">
                <textarea 
                    id="messageInput" 
                    class="message-input" 
                    placeholder="Type your message here... (supports LaTeX: $x^2 + y^2 = z^2$)"
                    rows="1"
                    maxlength="2000"
                ></textarea>
                <button id="sendButton" class="send-button" onclick="sendMessage()">
                    ➤
                </button>
            </div>
            <div class="input-controls">
                <div class="char-counter">
                    <span id="charCount">0</span>/2000
                </div>
                <div class="input-hints">
                    <span class="hint">💡 Try math expressions with $...$ or $$...$$</span>
                    <span class="hint">⌨️ Press Ctrl+Enter to send</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let messageCount = 0;
        let isTyping = false;
        
        // Auto-resize textarea
        const messageInput = document.getElementById('messageInput');
        const charCount = document.getElementById('charCount');
        const sendButton = document.getElementById('sendButton');
        const chatMessages = document.getElementById('chatMessages');
        const messageWrapper = document.getElementById('messageWrapper');
        
        messageInput.addEventListener('input', function() {
            // Auto resize
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            
            // Update character count
            const count = this.value.length;
            charCount.textContent = count;
            
            // Color coding for character count
            if (count > 1800) {
                charCount.style.color = 'var(--accent)';
            } else if (count > 1500) {
                charCount.style.color = 'var(--warning)';
            } else {
                charCount.style.color = 'var(--text-light)';
            }
            
            // Enable/disable send button
            sendButton.disabled = count === 0 || count > 2000 || isTyping;
        });
        
        // Keyboard shortcuts
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    sendMessage();
                } else if (!e.shiftKey) {
                    // Allow Enter for new lines, Shift+Enter for sending
                }
            }
        });
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || isTyping) return;
            
            // Add user message
            addMessage('user', message);
            
            // Clear input
            messageInput.value = '';
            messageInput.style.height = 'auto';
            charCount.textContent = '0';
            charCount.style.color = 'var(--text-light)';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Simulate API call (replace with actual API call)
            setTimeout(() => {
                hideTypingIndicator();
                const response = generateResponse(message);
                addMessage('bot', response);
            }, 1000 + Math.random() * 2000);
        }
        
        function addMessage(sender, text) {
            messageCount++;
            const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            const messageGroup = document.createElement('div');
            messageGroup.className = `message-group ${sender}`;
            messageGroup.style.animationDelay = '0.1s';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = sender === 'user' ? '👤' : '🤖';
            
            const content = document.createElement('div');
            content.className = 'message-content';
            
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            
            const messageText = document.createElement('div');
            messageText.className = 'message-text';
            messageText.innerHTML = processMessageText(text);
            
            const meta = document.createElement('div');
            meta.className = 'message-meta';
            meta.innerHTML = `<span class="message-time">${timestamp}</span>`;
            
            bubble.appendChild(messageText);
            bubble.appendChild(meta);
            content.appendChild(bubble);
            messageGroup.appendChild(avatar);
            messageGroup.appendChild(content);
            
            messageWrapper.appendChild(messageGroup);
            scrollToBottom();
            
            // Process MathJax
            if (window.MathJax && text.includes('$')) {
                MathJax.typesetPromise([messageText]).then(() => {
                    adjustMathJaxForMobile();
                    scrollToBottom();
                });
            }
        }
        
        function processMessageText(text) {
            // Convert line breaks to <br>
            text = text.replace(/\n/g, '<br>');
            
            // Process LaTeX expressions (basic preprocessing)
            text = text.replace(/\$\$(.*?)\$\$/g, '$$$$1$$');
            text = text.replace(/\$(.*?)\$/g, '$$$1$$');
            
            return text;
        }
        
        function showTypingIndicator() {
            if (isTyping) return;
            isTyping = true;
            sendButton.disabled = true;
            
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.id = 'typingIndicator';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '🤖';
            
            const dots = document.createElement('div');
            dots.className = 'typing-dots';
            dots.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
            
            typingDiv.appendChild(avatar);
            typingDiv.appendChild(dots);
            messageWrapper.appendChild(typingDiv);
            scrollToBottom();
        }
        
        function hideTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.remove();
            }
            isTyping = false;
            sendButton.disabled = messageInput.value.trim().length === 0;
        }
        
        function generateResponse(message) {
            const lowerMessage = message.toLowerCase();
            
            // Math-related responses
            if (lowerMessage.includes('math') || lowerMessage.includes('equation') || lowerMessage.includes('solve')) {
                return `I'd be happy to help with math! Here's an example of solving a quadratic equation:

For the equation $ax^2 + bx + c = 0$, the solution is:

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

This is the quadratic formula. Would you like me to solve a specific equation for you?`;
            }
            
            // Science responses
            if (lowerMessage.includes('physics') || lowerMessage.includes('science')) {
                return `Physics is fascinating! Here are some fundamental equations:

**Einstein's Mass-Energy Equivalence:**
$$E = mc^2$$

**Newton's Second Law:**
$$F = ma$$

**Kinematic Equation:**
$$v^2 = u^2 + 2as$$

What specific physics topic would you like to explore?`;
            }
            
            // Greeting responses
            if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey')) {
                return `Hello! 👋 Great to meet you! I'm NY AI, your advanced assistant. I can help you with:

• **Mathematics** - from basic arithmetic to advanced calculus
• **Physics & Sciences** - explanations and problem solving  
• **Academic Questions** - across multiple subjects
• **General Assistance** - information and guidance

What would you like to work on today?`;
            }
            
            // Default responses
            const responses = [
                `That's an interesting question! Let me think about it...

Based on what you've asked, I can provide several perspectives. Would you like me to elaborate on any particular aspect?`,
                
                `Great question! Here's what I can tell you:

This topic involves several key concepts that we should explore step by step. What specific area would you like me to focus on?`,
                
                `I understand you're asking about this topic. Let me break it down:

There are multiple ways to approach this, and I'd be happy to explain the methodology. Would you prefer a detailed explanation or a quick overview?`
            ];
            
            return responses[Math.floor(Math.random() * responses.length)];
        }
        
        function scrollToBottom() {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        }
        
        function toggleFullscreen() {
            const container = document.getElementById('chatContainer');
            container.classList.toggle('fullscreen');
            
            // Update viewport height for mobile
            if (container.classList.contains('fullscreen')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        }
        
        function clearChat() {
            if (confirm('Are you sure you want to clear the chat history?')) {
                messageWrapper.innerHTML = `
                    <div class="message-group bot bounce-in">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            <div class="message-bubble">
                                <div class="message-text">
                                    Chat cleared! I'm ready to help you with new questions.
                                </div>
                                <div class="message-meta">
                                    <span class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                messageCount = 0;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            messageInput.focus();
            scrollToBottom();
            
            // Process any existing MathJax content
            if (window.MathJax) {
                MathJax.typesetPromise().then(() => {
                    adjustMathJaxForMobile();
                });
            }
        });
        
        // Handle window resize for responsive math
        window.addEventListener('resize', function() {
            if (window.MathJax) {
                setTimeout(adjustMathJaxForMobile, 100);
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if message:
        # Add user message
        user_msg = {
            'id': len(messages),
            'sender': 'user',
            'message': message,
            'timestamp': datetime.datetime.now().strftime('%H:%M')
        }
        messages.append(user_msg)
        
        # Generate bot response (you can integrate with Gemini API here)
        bot_response = generate_bot_response(message)
        bot_msg = {
            'id': len(messages),
            'sender': 'bot',
            'message': bot_response,
            'timestamp': datetime.datetime.now().strftime('%H:%M')
        }
        messages.append(bot_msg)
        
        return jsonify({
            'success': True,
            'user_message': user_msg,
            'bot_message': bot_msg
        })
    
    return jsonify({'success': False, 'error': 'Empty message'})

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)

def generate_bot_response(message):
    """Enhanced bot responses with math support"""
    message_lower = message.lower()
    
    if 'math' in message_lower or 'equation' in message_lower:
        return """I'd be happy to help with math! Here's an example of solving a quadratic equation:

For the equation $ax^2 + bx + c = 0$, the solution is:

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

This is the quadratic formula. Would you like me to solve a specific equation for you?"""
    
    elif 'physics' in message_lower or 'science' in message_lower:
        return """Physics is fascinating! Here are some fundamental equations:

**Einstein's Mass-Energy Equivalence:**
$$E = mc^2$$

**Newton's Second Law:**
$$F = ma$$

**Kinematic Equation:**
$$v^2 = u^2 + 2as$$

What specific physics topic would you like to explore?"""
    
    elif any(greeting in message_lower for greeting in ['hello', 'hi', 'hey']):
        return """Hello! 👋 Great to meet you! I'm NY AI, your advanced assistant. I can help you with:

• **Mathematics** - from basic arithmetic to advanced calculus
• **Physics & Sciences** - explanations and problem solving  
• **Academic Questions** - across multiple subjects
• **General Assistance** - information and guidance

What would you like to work on today?"""
    
    elif 'time' in message_lower:
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')} ⏰"
    
    elif 'date' in message_lower:
        return f"Today's date is {datetime.datetime.now().strftime('%B %d, %Y')} 📅"
    
    else:
        responses = [
            """That's an interesting question! Let me think about it...

Based on what you've asked, I can provide several perspectives. Would you like me to elaborate on any particular aspect?""",
            
            """Great question! Here's what I can tell you:

This topic involves several key concepts that we should explore step by step. What specific area would you like me to focus on?""",
            
            """I understand you're asking about this topic. Let me break it down:

There are multiple ways to approach this, and I'd be happy to explain the methodology. Would you prefer a detailed explanation or a quick overview?"""
        ]
        
        import random
        return random.choice(responses)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
