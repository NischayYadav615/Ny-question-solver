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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyAHwDXsTEwtcXFlSHgBhTHzugthtNdaVio"
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
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        adjustMathJaxForMobile();
                    });
                }
            }
        };
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
            overflow-x: hidden;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .main-wrapper {
            background: rgba(255, 255, 255, 0.95);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Header Styles */
        .header {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 50%, var(--success) 100%);
            color: white;
            padding: 50px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
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
        
        .ny-ai-logo {
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 15px;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            letter-spacing: -2px;
            position: relative;
            z-index: 1;
        }
        
        .header h1 { 
            font-size: 2.8rem; 
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }
        
        .header p { 
            font-size: 1.2rem; 
            opacity: 0.95; 
            font-weight: 400;
            position: relative;
            z-index: 1;
        }
        
        .ny-ai-badge {
            position: absolute;
            top: 20px;
            right: 30px;
            background: rgba(255,255,255,0.25);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 600;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        /* Main Content */
        .main-content { 
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px; 
            padding: 40px;
            min-height: 600px;
            position: relative;
        }
        
        .left-panel, .right-panel {
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        
        /* Input Section */
        .input-section {
            background: var(--bg-primary);
            border-radius: var(--radius);
            padding: 30px;
            border: 2px solid transparent;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .input-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .input-section:hover::before {
            opacity: 1;
        }
        
        .input-section:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }
        
        .input-section h3 {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
            position: relative;
            z-index: 1;
        }
        
        .tab-buttons {
            display: flex;
            gap: 12px;
            margin-bottom: 25px;
            position: relative;
            z-index: 1;
        }
        
        .tab-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 30px;
            background: var(--border);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 600;
            font-size: 0.95rem;
            position: relative;
            overflow: hidden;
        }
        
        .tab-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }
        
        .tab-btn:hover::before {
            left: 100%;
        }
        
        .tab-btn.active {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }
        
        .tab-content { 
            display: none; 
            position: relative;
            z-index: 1;
        }
        .tab-content.active { 
            display: block; 
            animation: fadeInUp 0.4s ease-out;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .file-upload {
            border: 3px dashed var(--border);
            border-radius: var(--radius);
            padding: 50px 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: white;
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
            background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
            transition: all 0.4s ease;
            transform: translate(-50%, -50%);
            border-radius: 50%;
        }
        
        .file-upload:hover::before {
            width: 200px;
            height: 200px;
        }
        
        .file-upload:hover, .file-upload.drag-over {
            border-color: var(--primary);
            background: rgba(102, 126, 234, 0.05);
            transform: scale(1.02);
        }
        
        .file-upload div {
            position: relative;
            z-index: 1;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 1.1rem;
        }
        
        .file-upload small {
            position: relative;
            z-index: 1;
            color: var(--text-light);
            display: block;
            margin-top: 10px;
        }
        
        input[type="url"] {
            width: 100%;
            padding: 18px 20px;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            transition: all 0.3s ease;
            background: white;
            font-family: inherit;
        }
        
        input[type="url"]:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-1px);
        }
        
        .solve-btn {
            background: linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);
            color: white;
            padding: 20px 40px;
            border: none;
            border-radius: var(--radius);
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
            margin-top: 25px;
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
        }
        
        .solve-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.6s;
        }
        
        .solve-btn:hover::before {
            left: 100%;
        }
        
        .solve-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(255, 107, 107, 0.4);
        }
        
        .solve-btn:active {
            transform: translateY(-1px);
        }
        
        .solve-btn:disabled {
            background: var(--text-light);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .image-preview {
            max-width: 100%;
            border-radius: var(--radius);
            margin: 20px 0;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease;
        }
        
        .image-preview:hover {
            transform: scale(1.02);
        }
        
        /* Enhanced Solution Area - Fixed Width Structure */
        .solution-area {
            background: var(--bg-primary);
            border-radius: var(--radius);
            padding: 0;
            position: relative;
            overflow: hidden;
            min-height: 600px;
            max-height: 800px;
            display: flex;
            flex-direction: column;
            width: 100%;
        }
        
        .solution-header {
            padding: 25px 30px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            position: sticky;
            top: 0;
            z-index: 10;
            flex-shrink: 0;
            min-height: 80px;
        }
        
        .solution-header h3 {
            font-size: 1.4rem;
            font-weight: 600;
            margin: 0;
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .solution-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-shrink: 0;
        }
        
        .fullscreen-btn, .zoom-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 16px;
            backdrop-filter: blur(10px);
            flex-shrink: 0;
        }
        
        .fullscreen-btn:hover, .zoom-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        .solution-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 30px;
            scroll-behavior: smooth;
            position: relative;
            height: calc(100% - 80px);
            min-height: 0;
        }
        
        /* Enhanced scrollbar with better visibility */
        .solution-content::-webkit-scrollbar {
            width: 14px;
        }
        
        .solution-content::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 7px;
            margin: 5px 0;
            border: 1px solid var(--border);
        }
        
        .solution-content::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 7px;
            border: 2px solid var(--bg-secondary);
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .solution-content::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--primary-dark), var(--accent));
            box-shadow: inset 0 1px 5px rgba(0,0,0,0.2);
        }
        
        .solution-content::-webkit-scrollbar-thumb:active {
            background: linear-gradient(135deg, var(--accent), var(--primary));
        }
        
        .solution-sequence {
            display: flex;
            flex-direction: column;
            gap: 25px;
            width: 100%;
            min-width: 0;
        }
        
        .solution-step {
            background: white;
            border-radius: var(--radius);
            padding: 25px;
            border-left: 5px solid var(--accent);
            box-shadow: 0 6px 25px rgba(0,0,0,0.08);
            opacity: 0;
            transform: translateY(30px);
            animation: slideInStep 0.6s ease forwards;
            position: relative;
            overflow: hidden;
            word-wrap: break-word;
            width: 100%;
            box-sizing: border-box;
            max-width: 100%;
        }
        
        .solution-step:nth-child(1) { animation-delay: 0.1s; }
        .solution-step:nth-child(2) { animation-delay: 0.2s; }
        .solution-step:nth-child(3) { animation-delay: 0.3s; }
        .solution-step:nth-child(4) { animation-delay: 0.4s; }
        .solution-step:nth-child(5) { animation-delay: 0.5s; }
        .solution-step:nth-child(6) { animation-delay: 0.6s; }
        
        @keyframes slideInStep {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .step-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            font-weight: 700;
            color: var(--text-primary);
            font-size: 1.1rem;
            flex-wrap: wrap;
        }
        
        .step-number {
            background: linear-gradient(135deg, var(--accent), var(--primary));
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
            flex-shrink: 0;
        }
        
        .step-title {
            flex: 1;
            min-width: 0;
            word-break: break-word;
        }
        
        .step-content {
            line-height: 1.8;
            color: var(--text-secondary);
            word-break: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }
        
        .step-content * {
            max-width: 100%;
            box-sizing: border-box;
        }
        
        /* Enhanced Math expressions with better containment */
        .math-expression, .MathJax, .MathJax_Display {
            max-width: 100% !important;
            width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            padding: 15px;
            background: var(--bg-secondary);
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid var(--accent-light);
            font-family: 'Courier New', monospace;
            white-space: nowrap;
            scroll-behavior: smooth;
            box-sizing: border-box;
            -webkit-overflow-scrolling: touch;
        }
        
        .MathJax_Display {
            padding: 20px !important;
            margin: 20px 0 !important;
            background: var(--bg-secondary) !important;
            border-radius: 12px !important;
            border-left: 4px solid var(--primary) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        
        .MathJax_Display::-webkit-scrollbar {
            height: 10px;
        }
        
        .MathJax_Display::-webkit-scrollbar-track {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 5px;
        }
        
        .MathJax_Display::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 5px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        .MathJax_Display::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }
        
        /* Text content overflow handling */
        .step-content p, .step-content div, .step-content span {
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 100%;
        }
        
        .step-content pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-x: auto;
            max-width: 100%;
            padding: 15px;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin: 10px 0;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .step-content code {
            word-wrap: break-word;
            overflow-wrap: break-word;
            padding: 2px 6px;
            background: var(--bg-secondary);
            border-radius: 4px;
            font-size: 0.9em;
        }
        
        .step-content table {
            width: 100%;
            max-width: 100%;
            overflow-x: auto;
            display: block;
            white-space: nowrap;
        }
        
        .step-content img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .final-answer {
            background: linear-gradient(135deg, var(--success) 0%, #38a169 100%);
            color: white;
            padding: 25px;
            border-radius: var(--radius);
            text-align: center;
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 25px;
            box-shadow: 0 8px 25px rgba(72, 187, 120, 0.3);
        }
        
        /* Fullscreen Solution Modal */
        .fullscreen-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            backdrop-filter: blur(10px);
        }
        
        .fullscreen-modal.active {
            display: flex;
            flex-direction: column;
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .fullscreen-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1001;
        }
        
        .fullscreen-header h3 {
            font-size: 1.6rem;
            margin: 0;
        }
        
        .fullscreen-controls {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .close-fullscreen {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s ease;
        }
        
        .close-fullscreen:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        .fullscreen-content {
            flex: 1;
            overflow-y: auto;
            padding: 40px;
            background: var(--bg-primary);
            scroll-behavior: smooth;
        }
        
        .fullscreen-content::-webkit-scrollbar {
            width: 16px;
        }
        
        .fullscreen-content::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 8px;
        }
        
        .fullscreen-content::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 8px;
            border: 3px solid var(--bg-secondary);
        }
        
        /* Enhanced Sequence Navigation - Fixed Position */
        .sequence-nav {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            background: var(--bg-primary);
            padding: 15px 0;
            z-index: 5;
            border-bottom: 2px solid var(--border);
            width: 100%;
            box-sizing: border-box;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .sequence-nav::-webkit-scrollbar {
            height: 6px;
        }
        
        .sequence-nav::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 3px;
        }
        
        .sequence-nav::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }
        
        .sequence-btn {
            padding: 12px 20px;
            border: 2px solid var(--primary);
            background: white;
            color: var(--primary);
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 14px;
            font-weight: 600;
            position: relative;
            overflow: hidden;
            white-space: nowrap;
            flex-shrink: 0;
            min-width: 100px;
            text-align: center;
        }
        
        .sequence-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
            transition: left 0.5s;
        }
        
        .sequence-btn:hover::before {
            left: 100%;
        }
        
        .sequence-btn.active, .sequence-btn:hover {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }
        
        /* Chat Area */
        .chat-area {
            background: var(--bg-primary);
            border-radius: var(--radius);
            padding: 30px;
            height: 500px;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        
        .chat-area h3 {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            background: white;
            margin-bottom: 20px;
            scroll-behavior: smooth;
        }
        
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }
        
        .message {
            margin-bottom: 18px;
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 85%;
            word-wrap: break-word;
            animation: messageSlideIn 0.4s ease-out;
            position: relative;
            overflow-x: auto;
        }
        
        @keyframes messageSlideIn {
            from { 
                opacity: 0; 
                transform: translateY(20px) scale(0.95); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
            }
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 8px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .ai-message {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-bottom-left-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        
        .ai-message .math-expression, .ai-message .MathJax {
            background: white;
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
            border-left: 3px solid var(--primary);
            overflow-x: auto;
        }
        
        .chat-input-area {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid var(--border);
            border-radius: 25px;
            outline: none;
            font-size: 16px;
            transition: all 0.3s ease;
            background: white;
            font-family: inherit;
        }
        
        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-btn {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
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
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .send-btn:hover {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .send-btn:active {
            transform: scale(0.95);
        }
        
        /* Loading Animation */
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid var(--bg-secondary);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Status Messages */
        .error {
            background: linear-gradient(135deg, #fed7d7, #feb2b2);
            color: var(--error-color);
            padding: 20px;
            border-radius: var(--radius);
            margin: 15px 0;
            border-left: 5px solid var(--error-color);
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .success {
            background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
            color: var(--success);
            padding: 20px;
            border-radius: var(--radius);
            margin: 15px 0;
            border-left: 5px solid var(--success);
        }
        
        /* Scroll to Top Button */
        .scroll-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, var(--accent), var(--primary));
            color: white;
            border: none;
            border-radius: 50%;
            width: 55px;
            height: 55px;
            cursor: pointer;
            font-size: 20px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 100;
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        }
        
        .scroll-to-top.visible {
            opacity: 1;
            visibility: visible;
        }
        
        .scroll-to-top:hover {
            transform: scale(1.1) translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.5);
        }
        
        /* Solution Navigation Dots */
        .solution-nav-dots {
            position: fixed;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 50;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .solution-nav-dots.visible {
            opacity: 1;
            visibility: visible;
        }
        
        .nav-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(102, 126, 234, 0.3);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .nav-dot:hover, .nav-dot.active {
            background: var(--primary);
            transform: scale(1.3);
        }
        
        .nav-dot::after {
            content: attr(data-step);
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--text-primary);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .nav-dot:hover::after {
            opacity: 1;
            visibility: visible;
        }
        
        /* Zoom Controls */
        .zoom-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 12px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        
        .zoom-btn {
            background: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .zoom-level {
            color: white;
            font-size: 14px;
            min-width: 50px;
            text-align: center;
        }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 25px;
                padding: 30px;
            }
            
            .container {
                padding: 15px;
            }
            
            .solution-nav-dots {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .header {
                padding: 40px 20px;
            }
            
            .header h1 {
                font-size: 2.2rem;
            }
            
            .ny-ai-logo {
                font-size: 2.5rem;
            }
            
            .ny-ai-badge {
                position: static;
                display: inline-block;
                margin-bottom: 20px;
            }
            
            .main-content {
                padding: 20px;
            }
            
            .input-section, .solution-area, .chat-area {
                padding: 20px;
            }
            
            .solution-content {
                padding: 20px;
            }
            
            .tab-buttons {
                flex-direction: column;
                gap: 8px;
            }
            
            .sequence-nav {
                gap: 8px;
                padding: 10px 0;
            }
            
            .sequence-btn {
                padding: 10px 16px;
                font-size: 13px;
            }
            
            .chat-area {
                height: 400px;
            }
            
            .solution-header {
                padding: 20px;
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            
            .solution-controls {
                width: 100%;
                justify-content: center;
            }
            
            .fullscreen-content {
                padding: 20px;
            }
            
            .scroll-to-top {
                bottom: 20px;
                right: 20px;
                width: 50px;
                height: 50px;
                font-size: 18px;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 10px;
            }
            
            .header {
                padding: 30px 15px;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
            
            .ny-ai-logo {
                font-size: 2rem;
            }
            
            .main-content {
                padding: 15px;
                gap: 20px;
            }
            
            .message {
                max-width: 95%;
                padding: 12px 16px;
            }
            
            .solution-step {
                padding: 20px;
            }
            
            .step-header {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            
            .sequence-nav {
                justify-content: center;
            }
            
            .MathJax_Display {
                padding: 15px !important;
                font-size: 14px !important;
            }
        }
        
        /* Custom scrollbar for webkit browsers */
        * {
            scrollbar-width: thin;
            scrollbar-color: var(--primary) var(--bg-secondary);
        }
        
        *::-webkit-scrollbar {
            height: 8px;
            width: 8px;
        }
        
        *::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        *::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }
        
        *::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-wrapper">
            <div class="header">
                <div class="ny-ai-badge">Powered by NY AI</div>
                <div class="ny-ai-logo">🧠 NY AI</div>
                <h1>Advanced JEE Question Solver</h1>
                <p>Next-Gen AI with OCR, MathJax Rendering & Sequential Solutions</p>
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
                        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid var(--accent);">
                            <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">{{ extracted_text }}</pre>
                        </div>
                    </div>
                    {% endif %}
                </div>
                
                <div class="right-panel">
                    <div class="solution-area">
                        <div class="solution-header">
                            <h3>✅ Sequential Solution by NY AI</h3>
                            <div class="solution-controls">
                                <div class="zoom-controls">
                                    <button class="zoom-btn" onclick="adjustZoom(-0.1)" title="Zoom Out">−</button>
                                    <span class="zoom-level" id="zoomLevel">100%</span>
                                    <button class="zoom-btn" onclick="adjustZoom(0.1)" title="Zoom In">+</button>
                                </div>
                                <button class="fullscreen-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">⛶</button>
                            </div>
                        </div>
                        
                        <div class="solution-content" id="solutionContent">
                            {% if solution_sequence %}
                            <div class="sequence-nav" id="sequenceNav">
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
                                        <div class="step-title">{{ step.title }}</div>
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
                            <div style="text-align: center; color: var(--text-light); padding: 60px 20px;">
                                <div style="font-size: 4rem; margin-bottom: 20px; opacity: 0.7;">🤖</div>
                                <h3 style="margin-bottom: 10px; color: var(--text-secondary);">Ready to Solve!</h3>
                                <p>Upload an image or provide a URL to get started with NY AI's advanced problem-solving capabilities.</p>
                            </div>
                            {% endif %}
                            {% endif %}
                            
                            {% if error %}
                            <div class="error">{{ error }}</div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="chat-area">
                        <h3>💬 Chat with NY AI</h3>
                        <div class="chat-messages" id="chatMessages">
                            {% for message in chat_history %}
                            <div class="message {{ 'user-message' if message.role == 'user' else 'ai-message' }}">
                                {{ message.content|safe }}
                            </div>
                            {% endfor %}
                            
                            {% if not chat_history %}
                            <div style="text-align: center; color: var(--text-light); padding: 40px 20px;">
                                <div style="font-size: 2.5rem; margin-bottom: 15px; opacity: 0.6;">💭</div>
                                <p>Ask me anything about the solution or related concepts!</p>
                            </div>
                            {% endif %}
                        </div>
                        
                        <div class="chat-input-area">
                            <input type="text" class="chat-input" id="chatInput" placeholder="Ask follow-up questions to NY AI..." onkeypress="handleChatKeyPress(event)">
                            <button class="send-btn" onclick="sendChatMessage()">➤</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Fullscreen Modal -->
    <div class="fullscreen-modal" id="fullscreenModal">
        <div class="fullscreen-header">
            <h3>✅ Sequential Solution by NY AI - Full Screen</h3>
            <div class="fullscreen-controls">
                <div class="zoom-controls">
                    <button class="zoom-btn" onclick="adjustFullscreenZoom(-0.1)" title="Zoom Out">−</button>
                    <span class="zoom-level" id="fullscreenZoomLevel">100%</span>
                    <button class="zoom-btn" onclick="adjustFullscreenZoom(0.1)" title="Zoom In">+</button>
                </div>
                <button class="close-fullscreen" onclick="toggleFullscreen()" title="Exit Fullscreen">✕</button>
            </div>
        </div>
        <div class="fullscreen-content" id="fullscreenContent">
            <!-- Content will be dynamically inserted here -->
        </div>
    </div>

    <!-- Scroll to Top Button -->
    <button class="scroll-to-top" id="scrollToTop" onclick="scrollToTop()" title="Scroll to Top">↑</button>

    <!-- Solution Navigation Dots -->
    <div class="solution-nav-dots" id="solutionNavDots">
        <!-- Dots will be dynamically generated -->
    </div>

    <script>
        let currentZoom = 1;
        let fullscreenZoom = 1;
        
        // Enhanced tab switching with animations
        function switchTab(tabName) {
            // Hide all tab contents with fade out
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.opacity = '0';
                tab.style.transform = 'translateY(10px)';
                setTimeout(() => {
                    tab.classList.remove('active');
                }, 150);
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab with fade in
            setTimeout(() => {
                const targetTab = document.getElementById(tabName + '-tab');
                targetTab.classList.add('active');
                targetTab.style.opacity = '1';
                targetTab.style.transform = 'translateY(0)';
                event.target.classList.add('active');
            }, 150);
        }
        
        // Enhanced step navigation with smooth scrolling
        function showStep(stepIndex) {
            // Hide all steps with smooth transition
            document.querySelectorAll('.solution-step').forEach((step, index) => {
                step.style.opacity = '0';
                step.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    step.style.display = 'none';
                }, 200);
            });
            
            // Remove active from all sequence buttons
            document.querySelectorAll('.sequence-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected step with animation
            setTimeout(() => {
                const targetStep = document.getElementById('step-' + stepIndex);
                targetStep.style.display = 'block';
                setTimeout(() => {
                    targetStep.style.opacity = '1';
                    targetStep.style.transform = 'translateY(0)';
                }, 50);
                
                event.target.classList.add('active');
                updateNavDots(stepIndex);
                
                // Smooth scroll to step
                targetStep.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest'
                });
                
                // Re-render MathJax for the visible step
                if (window.MathJax) {
                    MathJax.typesetPromise([targetStep]).then(() => {
                        adjustMathJaxForMobile();
                    });
                }
            }, 200);
        }
        
        // Fullscreen functionality
        function toggleFullscreen() {
            const modal = document.getElementById('fullscreenModal');
            const isActive = modal.classList.contains('active');
            
            if (!isActive) {
                // Enter fullscreen
                const solutionContent = document.getElementById('solutionContent');
                const fullscreenContent = document.getElementById('fullscreenContent');
                
                // Clone content to fullscreen modal
                fullscreenContent.innerHTML = solutionContent.innerHTML;
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
                
                // Re-render MathJax in fullscreen
                if (window.MathJax) {
                    MathJax.typesetPromise([fullscreenContent]).then(() => {
                        adjustMathJaxForMobile();
                    });
                }
            } else {
                // Exit fullscreen
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
        
        // Zoom functionality
        function adjustZoom(delta) {
            currentZoom = Math.max(0.5, Math.min(2, currentZoom + delta));
            const content = document.getElementById('solutionContent');
            content.style.transform = `scale(${currentZoom})`;
            content.style.transformOrigin = 'top left';
            document.getElementById('zoomLevel').textContent = Math.round(currentZoom * 100) + '%';
            
            // Re-adjust MathJax after zoom
            setTimeout(() => adjustMathJaxForMobile(), 100);
        }
        
        function adjustFullscreenZoom(delta) {
            fullscreenZoom = Math.max(0.5, Math.min(2, fullscreenZoom + delta));
            const content = document.getElementById('fullscreenContent');
            content.style.transform = `scale(${fullscreenZoom})`;
            content.style.transformOrigin = 'top left';
            document.getElementById('fullscreenZoomLevel').textContent = Math.round(fullscreenZoom * 100) + '%';
            
            // Re-adjust MathJax after zoom
            setTimeout(() => adjustMathJaxForMobile(), 100);
        }
        
        // Scroll to top functionality
        function scrollToTop() {
            const solutionContent = document.getElementById('solutionContent');
            if (solutionContent) {
                solutionContent.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            } else {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
        }
        
        // Update navigation dots
        function updateNavDots(activeIndex) {
            document.querySelectorAll('.nav-dot').forEach((dot, index) => {
                dot.classList.toggle('active', index === activeIndex);
            });
        }
        
        // Generate navigation dots
        function generateNavDots() {
            const steps = document.querySelectorAll('.solution-step');
            const navDots = document.getElementById('solutionNavDots');
            
            if (steps.length > 1) {
                navDots.innerHTML = '';
                steps.forEach((step, index) => {
                    const dot = document.createElement('div');
                    dot.className = `nav-dot ${index === 0 ? 'active' : ''}`;
                    dot.setAttribute('data-step', `Step ${index + 1}`);
                    dot.onclick = () => {
                        document.querySelector(`.sequence-btn:nth-child(${index + 1})`).click();
                    };
                    navDots.appendChild(dot);
                });
                navDots.classList.add('visible');
            }
        }
        
        // Enhanced MathJax handling for mobile
        function adjustMathJaxForMobile() {
            document.querySelectorAll('.MathJax, .MathJax_Display').forEach(math => {
                math.style.overflowX = 'auto';
                math.style.maxWidth = '100%';
                math.style.fontSize = window.innerWidth < 768 ? '14px' : '16px';
                
                // Add touch scrolling for mobile
                if ('ontouchstart' in window) {
                    math.style.webkitOverflowScrolling = 'touch';
                }
            });
        }
        
        // Enhanced image preview with animation
        function previewImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Remove existing preview
                    const existingPreview = document.getElementById('imagePreview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    
                    // Create new preview with animation
                    const preview = document.createElement('img');
                    preview.id = 'imagePreview';
                    preview.className = 'image-preview';
                    preview.src = e.target.result;
                    preview.style.opacity = '0';
                    preview.style.transform = 'scale(0.9)';
                    
                    input.parentNode.appendChild(preview);
                    
                    // Animate in
                    setTimeout(() => {
                        preview.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                        preview.style.opacity = '1';
                        preview.style.transform = 'scale(1)';
                    }, 50);
                }
                reader.readAsDataURL(input.files[0]);
            }
        }
        
        // Enhanced drag and drop with better visual feedback
        const fileUpload = document.querySelector('.file-upload');
        let dragCounter = 0;
        
        fileUpload.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            fileUpload.classList.add('drag-over');
        });
        
        fileUpload.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                fileUpload.classList.remove('drag-over');
            }
        });
        
        fileUpload.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        fileUpload.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            fileUpload.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = document.getElementById('imageFile');
                fileInput.files = files;
                previewImage(fileInput);
                
                // Visual feedback for successful drop
                fileUpload.style.background = 'rgba(72, 187, 120, 0.1)';
                fileUpload.style.borderColor = 'var(--success)';
                setTimeout(() => {
                    fileUpload.style.background = '';
                    fileUpload.style.borderColor = '';
                }, 1000);
            }
        });
        
        // Enhanced form submission with better loading states
        document.getElementById('questionForm').addEventListener('submit', function(e) {
            const solveBtn = document.getElementById('solveBtn');
            const loading = document.getElementById('loading');
            
            // Show loading state
            if (loading) {
                loading.style.display = 'block';
                loading.style.opacity = '0';
                setTimeout(() => {
                    loading.style.transition = 'opacity 0.3s ease';
                    loading.style.opacity = '1';
                }, 50);
            }
            
            // Disable and animate button
            solveBtn.disabled = true;
            solveBtn.innerHTML = '🔄 NY AI Analyzing...';
            solveBtn.style.transform = 'scale(0.98)';
            
            // Add pulsing animation to button
            solveBtn.style.animation = 'pulse 2s infinite';
        });
        
        // Enhanced chat functionality
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
            
            // Add user message with animation
            addMessageToChat(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
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
            
            // Remove empty state if present
            const emptyState = chatMessages.querySelector('[style*="text-align: center"]');
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.innerHTML = message;
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(20px) scale(0.95)';
            
            chatMessages.appendChild(messageDiv);
            
            // Animate message in
            setTimeout(() => {
                messageDiv.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0) scale(1)';
            }, 50);
            
            // Smooth scroll to bottom
            setTimeout(() => {
                chatMessages.scrollTo({
                    top: chatMessages.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
            
            // Re-render MathJax for new messages
            if (window.MathJax) {
                MathJax.typesetPromise([messageDiv]).then(() => {
                    adjustMathJaxForMobile();
                });
            }
        }
        
        function showTypingIndicator() {
            const chatMessages = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing-indicator';
            typingDiv.className = 'message ai-message';
            typingDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="display: flex; gap: 4px;">
                        <div style="width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out;"></div>
                        <div style="width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out 0.2s;"></div>
                        <div style="width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out 0.4s;"></div>
                    </div>
                    <span style="color: var(--text-light); font-size: 0.9rem;">NY AI is thinking...</span>
                </div>
            `;
            
            // Add typing animation
            const typingStyle = document.createElement('style');
            typingStyle.textContent = `
                @keyframes typing {
                    0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
                    30% { opacity: 1; transform: scale(1); }
                }
            `;
            document.head.appendChild(typingStyle);
            
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        }
        
        function hideTypingIndicator() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.style.opacity = '0';
                typingIndicator.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    typingIndicator.remove();
                }, 300);
            }
        }
        
        // Scroll event handlers
        function handleScroll() {
            const scrollToTopBtn = document.getElementById('scrollToTop');
            const solutionContent = document.getElementById('solutionContent');
            
            if (solutionContent) {
                const scrollTop = solutionContent.scrollTop;
                const scrollHeight = solutionContent.scrollHeight;
                const clientHeight = solutionContent.clientHeight;
                
                // Show/hide scroll to top button
                if (scrollTop > 200) {
                    scrollToTopBtn.classList.add('visible');
                } else {
                    scrollToTopBtn.classList.remove('visible');
                }
                
                // Update active step based on scroll position
                updateActiveStepOnScroll();
            }
        }
        
        function updateActiveStepOnScroll() {
            const steps = document.querySelectorAll('.solution-step:not([style*="display: none"])');
            const solutionContent = document.getElementById('solutionContent');
            
            if (steps.length === 0 || !solutionContent) return;
            
            const scrollTop = solutionContent.scrollTop;
            const containerTop = solutionContent.offsetTop;
            
            let activeStepIndex = 0;
            
            steps.forEach((step, index) => {
                const stepTop = step.offsetTop - containerTop;
                if (scrollTop >= stepTop - 100) {
                    activeStepIndex = index;
                }
            });
            
            // Update navigation dots
            updateNavDots(activeStepIndex);
        }
        
        // Initialize everything when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Set up initial tab transitions
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            });
            
            // Set up solution steps transitions
            document.querySelectorAll('.solution-step').forEach(step => {
                step.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            });
            
            // Add scroll event listener
            const solutionContent = document.getElementById('solutionContent');
            if (solutionContent) {
                solutionContent.addEventListener('scroll', handleScroll);
            }
            
            // Generate navigation dots if steps exist
            setTimeout(() => {
                generateNavDots();
            }, 500);
            
            // Initialize MathJax with proper configuration for mobile
            if (window.MathJax) {
                MathJax.typesetPromise().then(() => {
                    adjustMathJaxForMobile();
                });
                
                // Configure MathJax for dynamic content
                MathJax.config.tex.inlineMath = [['$', '$'], ['\\(', '\\)']];
                MathJax.config.tex.displayMath = [['$$', '$$'], ['\\[', '\\]']];
            }
            
            // Add smooth scrolling to all internal links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
            
            // Handle window resize for responsive adjustments
            window.addEventListener('resize', () => {
                adjustMathJaxForMobile();
                
                // Hide navigation dots on mobile
                const navDots = document.getElementById('solutionNavDots');
                if (window.innerWidth <= 1024) {
                    navDots.classList.remove('visible');
                } else if (document.querySelectorAll('.solution-step').length > 1) {
                    navDots.classList.add('visible');
                }
            });
        });
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Enter to submit form
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const form = document.getElementById('questionForm');
                if (form) {
                    form.dispatchEvent(new Event('submit'));
                }
            }
            
            // Escape to exit fullscreen or clear chat input
            if (e.key === 'Escape') {
                const fullscreenModal = document.getElementById('fullscreenModal');
                if (fullscreenModal.classList.contains('active')) {
                    toggleFullscreen();
                } else {
                    const chatInput = document.getElementById('chatInput');
                    if (chatInput && document.activeElement === chatInput) {
                        chatInput.value = '';
                        chatInput.blur();
                    }
                }
            }
            
            // F11 or F for fullscreen toggle
            if (e.key === 'F11' || (e.key === 'f' && !e.ctrlKey && !e.metaKey)) {
                e.preventDefault();
                toggleFullscreen();
            }
            
            // Arrow keys for step navigation
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const activeBtn = document.querySelector('.sequence-btn.active');
                if (activeBtn) {
                    const buttons = Array.from(document.querySelectorAll('.sequence-btn'));
                    const currentIndex = buttons.indexOf(activeBtn);
                    let newIndex;
                    
                    if (e.key === 'ArrowLeft') {
                        newIndex = Math.max(0, currentIndex - 1);
                    } else {
                        newIndex = Math.min(buttons.length - 1, currentIndex + 1);
                    }
                    
                    if (newIndex !== currentIndex) {
                        buttons[newIndex].click();
                    }
                }
            }
        });
        
        // Performance optimization: Lazy load images
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                        }
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
        
        // Add pulse animation for loading button
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        `;
        document.head.appendChild(style);
        
        // Touch gestures for mobile
        if ('ontouchstart' in window) {
            let touchStartX = 0;
            let touchStartY = 0;
            
            document.addEventListener('touchstart', function(e) {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            });
            
            document.addEventListener('touchend', function(e) {
                if (!touchStartX || !touchStartY) return;
                
                const touchEndX = e.changedTouches[0].clientX;
                const touchEndY = e.changedTouches[0].clientY;
                
                const diffX = touchStartX - touchEndX;
                const diffY = touchStartY - touchEndY;
                
                // Only process horizontal swipes that are longer than vertical
                if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                    const activeBtn = document.querySelector('.sequence-btn.active');
                    if (activeBtn) {
                        const buttons = Array.from(document.querySelectorAll('.sequence-btn'));
                        const currentIndex = buttons.indexOf(activeBtn);
                        let newIndex;
                        
                        if (diffX > 0) { // Swipe left - next step
                            newIndex = Math.min(buttons.length - 1, currentIndex + 1);
                        } else { // Swipe right - previous step
                            newIndex = Math.max(0, currentIndex - 1);
                        }
                        
                        if (newIndex !== currentIndex) {
                            buttons[newIndex].click();
                        }
                    }
                }
                
                touchStartX = 0;
                touchStartY = 0;
            });
        }
        
        // Auto-save zoom preferences
        function saveZoomPreference() {
            localStorage.setItem('jee-solver-zoom', currentZoom);
            localStorage.setItem('jee-solver-fullscreen-zoom', fullscreenZoom);
        }
        
        function loadZoomPreference() {
            const savedZoom = localStorage.getItem('jee-solver-zoom');
            const savedFullscreenZoom = localStorage.getItem('jee-solver-fullscreen-zoom');
            
            if (savedZoom) {
                currentZoom = parseFloat(savedZoom);
                const content = document.getElementById('solutionContent');
                if (content) {
                    content.style.transform = `scale(${currentZoom})`;
                    content.style.transformOrigin = 'top left';
                    document.getElementById('zoomLevel').textContent = Math.round(currentZoom * 100) + '%';
                }
            }
            
            if (savedFullscreenZoom) {
                fullscreenZoom = parseFloat(savedFullscreenZoom);
                document.getElementById('fullscreenZoomLevel').textContent = Math.round(fullscreenZoom * 100) + '%';
            }
        }
        
        // Override zoom functions to save preferences
        const originalAdjustZoom = adjustZoom;
        const originalAdjustFullscreenZoom = adjustFullscreenZoom;
        
        adjustZoom = function(delta) {
            originalAdjustZoom(delta);
            saveZoomPreference();
        };
        
        adjustFullscreenZoom = function(delta) {
            originalAdjustFullscreenZoom(delta);
            saveZoomPreference();
        };
        
        // Load preferences on page load
        setTimeout(loadZoomPreference, 100);
        
        // Accessibility improvements
        document.addEventListener('keydown', function(e) {
            // Add focus management for keyboard navigation
            if (e.key === 'Tab') {
                // Ensure focus is visible
                document.documentElement.classList.add('keyboard-nav');
            }
        });
        
        document.addEventListener('mousedown', function() {
            document.documentElement.classList.remove('keyboard-nav');
        });
        
        // Add CSS for keyboard navigation
        const accessibilityStyle = document.createElement('style');
        accessibilityStyle.textContent = `
            .keyboard-nav *:focus {
                outline: 2px solid var(--primary) !important;
                outline-offset: 2px !important;
            }
        `;
        document.head.appendChild(accessibilityStyle);
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
    
    # Split by sections
    sections = []
    current_section = ""
    current_title = ""
    
    lines = solution_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Check if line is a section header
        if line.startswith('**SECTION') and line.endswith('**'):
            # Save previous section
            if current_title and current_section:
                sections.append({
                    'title': current_title,
                    'content': current_section.strip()
                })
            
            # Start new section
            current_title = line.replace('**SECTION', '').replace('**', '').strip()
            if ':' in current_title:
                current_title = current_title.split(':', 1)[1].strip()
            current_section = ""
        
        elif line.startswith('**') and line.endswith('**') and current_section:
            # Sub-header within section
            current_section += f"<h4 style='color: #ff6b6b; margin: 15px 0 10px 0;'>{line.replace('**', '')}</h4>\n"
        
        else:
            # Regular content
            if line:
                current_section += line + "\n"
    
    # Add the last section
    if current_title and current_section:
        sections.append({
            'title': current_title,
            'content': current_section.strip()
        })
    
    # If no sections found, create a single section
    if not sections and solution_text:
        sections.append({
            'title': 'Complete Solution',
            'content': solution_text
        })
    
    return sections

@app.route('/', methods=['GET', 'POST'])
def home():
    # Initialize session variables
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    image_url = None
    solution_sequence = None
    error = None
    extracted_text = None
    
    if request.method == 'POST':
        try:
            # Get inputs
            image_url = request.form.get('image_url', '').strip()
            
            image_data = None
            has_image = False
            
            # Handle file upload
            if 'image_file' in request.files and request.files['image_file'].filename:
                file = request.files['image_file']
                if file and file.filename != '':
                    try:
                        # Validate file type
                        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        
                        if file_ext not in allowed_extensions:
                            error = "Please upload a valid image file (PNG, JPG, JPEG, GIF, WebP)."
                        else:
                            image_data = file.read()
                            # Create data URL for display
                            image_b64 = base64.b64encode(image_data).decode('utf-8')
                            image_url = f"data:image/{file_ext};base64,{image_b64}"
                            has_image = True
                    except Exception as e:
                        error = f"Error processing uploaded file: {str(e)}"
            
            # Handle URL input
            elif image_url:
                if image_url.startswith('data:'):
                    # Data URL - extract base64 data
                    try:
                        header, data = image_url.split(',', 1)
                        image_data = base64.b64decode(data)
                        has_image = True
                    except Exception as e:
                        error = f"Error processing data URL: {str(e)}"
                else:
                    # External URL
                    has_image = True
            
            # Validate input
            if not has_image:
                error = "Please provide an image (upload or URL)."
            
            elif not error:
                # Create enhanced prompt for sequential solution
                prompt = create_sequential_prompt(None, has_image)
                
                # Call Gemini API
                solution = call_gemini_vision(prompt, image_data, image_url)
                
                # Parse solution into sequence
                solution_sequence = parse_solution_into_sequence(solution)
                
                # Extract text for display purposes
                extract_prompt = """Please extract ALL text content from this image, including:
                - Question text
                - Mathematical equations and expressions (format with LaTeX when possible)
                - Numbers, measurements, and units
                - Any labels or annotations
                - Multiple choice options if present
                
                Format the extracted text clearly and preserve the original structure. Use LaTeX notation for mathematical expressions."""
                
                extracted_text = call_gemini_vision(extract_prompt, image_data, image_url)
                
                # Store context in session for chat
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
        
        # Get current context
        context = session.get('current_context', {})
        
        # Build context-aware prompt
        chat_prompt = f"""You are NY AI, continuing a conversation about a JEE question. Here's the context:

EXTRACTED TEXT: {context.get('extracted_text', 'N/A')}

USER'S FOLLOW-UP QUESTION: {user_message}

Please provide a helpful, detailed response. Use LaTeX notation for mathematical expressions ($ for inline, $$ for display math). 
If the user is asking for clarification, provide more detailed explanations. If asking about related concepts, explain those as well.
Always maintain the NY AI persona - be confident, helpful, and educational."""
        
        # Get AI response
        ai_response = call_gemini_vision(chat_prompt)
        
        # Add to chat history
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
        
        # Keep only last 20 messages to prevent session overflow
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
