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
import re

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCfiA0TjeSEUFqJkgYtbLzjsbEdNW_ZTpk"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

# Store solutions in memory (use database in production)
solutions_store = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes, maximum-scale=5.0">
    <title>NY AI - Advanced Problem Solver</title>
    
    <!-- Preload critical resources -->
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    
    <!-- MathJax Configuration -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                packages: {'[+]': ['ams', 'newcommand', 'configmacros', 'physics']}
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        optimizeMathForDevice();
                    });
                }
            }
        };
        
        function optimizeMathForDevice() {
            const isMobile = window.innerWidth <= 768;
            const mathElements = document.querySelectorAll('.MathJax, .MathJax_Display');
            mathElements.forEach(el => {
                el.style.maxWidth = '100%';
                el.style.overflowX = 'auto';
                el.style.fontSize = isMobile ? '0.9rem' : '1rem';
                el.style.webkitOverflowScrolling = 'touch';
            });
        }
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js" async></script>
    
    <style>
        /* CSS Variables for theming */
        :root {
            --primary: #667eea;
            --primary-dark: #5a67d8;
            --primary-light: #a4cafe;
            --secondary: #764ba2;
            --accent: #ff6b6b;
            --accent-light: #ffd93d;
            --success: #48bb78;
            --warning: #ed8936;
            --error: #f56565;
            --info: #4299e1;
            
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #edf2f7;
            --bg-overlay: rgba(0, 0, 0, 0.5);
            
            --text-primary: #2d3748;
            --text-secondary: #4a5568;
            --text-light: #718096;
            --text-inverse: #ffffff;
            
            --border: #e2e8f0;
            --border-dark: #cbd5e0;
            
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            --shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
            --shadow-lg: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
            --shadow-xl: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
            
            --radius-sm: 6px;
            --radius: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-fast: all 0.15s ease-out;
            --transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            
            --header-height: 80px;
            --mobile-header-height: 70px;
            --input-height: 140px;
            --mobile-input-height: 120px;
        }
        
        /* Dark theme support */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #1a202c;
                --bg-secondary: #2d3748;
                --bg-tertiary: #4a5568;
                --text-primary: #f7fafc;
                --text-secondary: #e2e8f0;
                --text-light: #a0aec0;
                --border: #4a5568;
                --border-dark: #2d3748;
            }
        }
        
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            font-size: 16px;
            scroll-behavior: smooth;
            -webkit-text-size-adjust: 100%;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* Container and layout */
        .app-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            max-width: 1400px;
            margin: 0 auto;
            background: var(--bg-primary);
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
        }
        
        /* Enhanced Header */
        .header {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 50%, var(--success) 100%);
            color: var(--text-inverse);
            padding: 20px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1000;
            height: var(--header-height);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 70% 30%, rgba(255,255,255,0.1) 0%, transparent 50%);
            animation: headerShine 8s ease-in-out infinite;
            pointer-events: none;
        }
        
        @keyframes headerShine {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
        
        .header-content {
            display: flex;
            align-items: center;
            gap: 20px;
            position: relative;
            z-index: 1;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: inherit;
        }
        
        .logo-icon {
            width: 48px;
            height: 48px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: var(--transition);
        }
        
        .logo:hover .logo-icon {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.3);
        }
        
        .logo-text {
            display: flex;
            flex-direction: column;
        }
        
        .logo-title {
            font-size: 1.5rem;
            font-weight: 900;
            letter-spacing: -0.5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .logo-subtitle {
            font-size: 0.75rem;
            opacity: 0.9;
            font-weight: 500;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
            z-index: 1;
        }
        
        .control-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: var(--text-inverse);
            padding: 10px 12px;
            border-radius: var(--radius);
            cursor: pointer;
            transition: var(--transition);
            font-size: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
        }
        
        .control-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .control-btn:active {
            transform: translateY(0);
        }
        
        /* Main content area */
        .main-content {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            gap: 0;
            min-height: calc(100vh - var(--header-height));
            position: relative;
        }
        
        /* Input Panel */
        .input-panel {
            background: var(--bg-secondary);
            display: flex;
            flex-direction: column;
            position: relative;
            border-right: 1px solid var(--border);
        }
        
        .input-header {
            padding: 25px 30px 20px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-primary);
        }
        
        .input-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .input-subtitle {
            font-size: 0.9rem;
            color: var(--text-light);
            font-weight: 500;
        }
        
        .input-content {
            flex: 1;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 25px;
            overflow-y: auto;
        }
        
        /* Enhanced Tab System */
        .tab-container {
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            padding: 8px;
            box-shadow: var(--shadow-sm);
        }
        
        .tab-buttons {
            display: flex;
            gap: 4px;
            margin-bottom: 20px;
        }
        
        .tab-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: var(--radius);
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
            font-weight: 600;
            font-size: 0.9rem;
            position: relative;
            overflow: hidden;
        }
        
        .tab-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            opacity: 0;
            transition: var(--transition);
            border-radius: var(--radius);
        }
        
        .tab-btn.active::before {
            opacity: 1;
        }
        
        .tab-btn.active {
            color: var(--text-inverse);
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }
        
        .tab-btn span {
            position: relative;
            z-index: 1;
        }
        
        .tab-content {
            display: none;
            animation: fadeInUp 0.4s ease-out;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Enhanced File Upload */
        .file-upload-container {
            position: relative;
        }
        
        .file-upload {
            border: 3px dashed var(--border);
            border-radius: var(--radius-lg);
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            background: var(--bg-primary);
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
            transition: var(--transition-slow);
            transform: translate(-50%, -50%);
            border-radius: 50%;
        }
        
        .file-upload:hover::before,
        .file-upload.drag-over::before {
            width: 300px;
            height: 300px;
        }
        
        .file-upload:hover,
        .file-upload.drag-over {
            border-color: var(--primary);
            background: rgba(102, 126, 234, 0.05);
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 48px;
            color: var(--primary);
            margin-bottom: 15px;
            display: block;
            position: relative;
            z-index: 1;
        }
        
        .upload-text {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
            position: relative;
            z-index: 1;
        }
        
        .upload-hint {
            font-size: 0.9rem;
            color: var(--text-light);
            position: relative;
            z-index: 1;
        }
        
        .file-input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        /* Image Preview */
        .image-preview {
            margin-top: 20px;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow);
            display: none;
        }
        
        .preview-image {
            width: 100%;
            height: auto;
            max-height: 300px;
            object-fit: contain;
            background: var(--bg-tertiary);
        }
        
        .preview-controls {
            padding: 15px;
            background: var(--bg-primary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .preview-info {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .remove-btn {
            background: var(--error);
            color: var(--text-inverse);
            border: none;
            padding: 8px 16px;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: var(--transition);
        }
        
        .remove-btn:hover {
            background: #e53e3e;
            transform: translateY(-1px);
        }
        
        /* URL Input */
        .url-input {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid var(--border);
            border-radius: var(--radius-lg);
            font-size: 16px;
            font-family: inherit;
            transition: var(--transition);
            background: var(--bg-primary);
        }
        
        .url-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }
        
        .url-input::placeholder {
            color: var(--text-light);
        }
        
        /* Solve Button */
        .solve-btn {
            background: linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);
            color: var(--text-inverse);
            border: none;
            padding: 18px 30px;
            border-radius: var(--radius-lg);
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition);
            width: 100%;
            margin-top: 25px;
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            box-shadow: var(--shadow);
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
            box-shadow: var(--shadow-lg);
        }
        
        .solve-btn:active {
            transform: translateY(-1px);
        }
        
        .solve-btn:disabled {
            background: var(--text-light);
            cursor: not-allowed;
            transform: none;
            box-shadow: var(--shadow-sm);
        }
        
        .btn-text {
            position: relative;
            z-index: 1;
        }
        
        /* Solution Panel */
        .solution-panel {
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        
        .solution-header {
            padding: 25px 30px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: var(--text-inverse);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(20px);
        }
        
        .solution-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .solution-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .solution-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: var(--text-inverse);
            padding: 8px 12px;
            border-radius: var(--radius);
            cursor: pointer;
            transition: var(--transition);
            font-size: 14px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .solution-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        .solution-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 30px;
            background: var(--bg-secondary);
            position: relative;
            min-height: 0;
        }
        
        /* Enhanced scrollbar */
        .solution-content::-webkit-scrollbar,
        .input-content::-webkit-scrollbar {
            width: 12px;
        }
        
        .solution-content::-webkit-scrollbar-track,
        .input-content::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 6px;
            margin: 4px 0;
        }
        
        .solution-content::-webkit-scrollbar-thumb,
        .input-content::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 6px;
            border: 2px solid var(--bg-tertiary);
        }
        
        .solution-content::-webkit-scrollbar-thumb:hover,
        .input-content::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--primary-dark), var(--accent));
        }
        
        /* Solution Steps */
        .solution-sequence {
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        
        .solution-step {
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            padding: 25px;
            border-left: 5px solid var(--accent);
            box-shadow: var(--shadow);
            opacity: 0;
            transform: translateY(30px);
            animation: slideInStep 0.6s ease forwards;
            position: relative;
            overflow: hidden;
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
        }
        
        .step-number {
            background: linear-gradient(135deg, var(--accent), var(--primary));
            color: var(--text-inverse);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
            box-shadow: var(--shadow);
            flex-shrink: 0;
        }
        
        .step-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            flex: 1;
        }
        
        .step-content {
            line-height: 1.8;
            color: var(--text-secondary);
            word-break: break-word;
            overflow-wrap: break-word;
        }
        
        /* Enhanced Math expressions */
        .math-expression,
        .MathJax,
        .MathJax_Display {
            max-width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            padding: 20px !important;
            background: var(--bg-tertiary) !important;
            border-radius: var(--radius) !important;
            margin: 20px 0 !important;
            border-left: 4px solid var(--primary) !important;
            box-shadow: var(--shadow-sm) !important;
            scroll-behavior: smooth !important;
            -webkit-overflow-scrolling: touch !important;
        }
        
        /* Empty state */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 40px;
            color: var(--text-light);
        }
        
        .empty-icon {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            color: var(--text-secondary);
        }
        
        .empty-subtitle {
            font-size: 1rem;
            max-width: 300px;
            line-height: 1.6;
        }
        
        /* Loading states */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Progress bar */
        .progress-container {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.3);
            z-index: 10000;
            opacity: 0;
            transition: var(--transition);
        }
        
        .progress-container.active {
            opacity: 1;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--primary));
            width: 0%;
            transition: width 0.3s ease;
        }
        
        /* Mobile Responsive Design */
        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            
            .input-panel {
                border-right: none;
                border-bottom: 1px solid var(--border);
            }
            
            .solution-panel {
                border-top: 1px solid var(--border);
            }
        }
        
        @media (max-width: 768px) {
            :root {
                --header-height: var(--mobile-header-height);
            }
            
            .app-container {
                margin: 0;
                border-radius: 0;
                min-height: 100vh;
            }
            
            .header {
                padding: 15px 20px;
                height: var(--mobile-header-height);
            }
            
            .logo-icon {
                width: 40px;
                height: 40px;
                font-size: 20px;
            }
            
            .logo-title {
                font-size: 1.25rem;
            }
            
            .logo-subtitle {
                font-size: 0.7rem;
            }
            
            .main-content {
                min-height: calc(100vh - var(--mobile-header-height));
            }
            
            .input-content,
            .solution-content {
                padding: 20px;
            }
            
            .input-header {
                padding: 20px;
            }
            
            .tab-btn {
                padding: 10px 15px;
                font-size: 0.85rem;
            }
            
            .file-upload {
                padding: 30px 15px;
            }
            
            .upload-icon {
                font-size: 36px;
            }
            
            .upload-text {
                font-size: 1rem;
            }
            
            .solve-btn {
                padding: 16px 25px;
                font-size: 1rem;
            }
            
            .solution-step {
                padding: 20px;
            }
            
            .step-number {
                width: 32px;
                height: 32px;
                font-size: 14px;
            }
            
            .step-title {
                font-size: 1rem;
            }
            
            .MathJax_Display {
                padding: 15px !important;
                margin: 15px 0 !important;
                font-size: 0.9rem !important;
            }
        }
        
        @media (max-width: 480px) {
            .header {
                padding: 12px 15px;
            }
            
            .header-controls {
                gap: 8px;
            }
            
            .control-btn {
                width: 36px;
                height: 36px;
                font-size: 14px;
            }
            
            .input-content,
            .solution-content {
                padding: 15px;
            }
            
            .solution-step {
                padding: 15px;
                gap: 15px;
            }
            
            .tab-buttons {
                flex-direction: column;
                gap: 8px;
            }
            
            .tab-btn {
                text-align: center;
            }
        }
        
        /* Touch-friendly interactions */
        @media (hover: none) and (pointer: coarse) {
            .tab-btn,
            .control-btn,
            .solution-btn,
            .solve-btn {
                min-height: 44px;
                min-width: 44px;
            }
            
            .file-upload {
                min-height: 120px;
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --border: #000000;
                --text-light: #000000;
                --shadow: 0 2px 4px rgba(0,0,0,0.8);
            }
        }
        
        /* Print styles */
        @media print {
            .header,
            .input-panel,
            .solution-header {
                display: none;
            }
            
            .app-container {
                box-shadow: none;
                background: white;
            }
            
            .solution-content {
                padding: 0;
                overflow: visible;
            }
            
            .solution-step {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ccc;
                margin-bottom: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="progress-container" id="progressContainer">
        <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <div class="app-container">
        <header class="header">
            <div class="header-content">
                <a href="/" class="logo">
                    <div class="logo-icon">🧠</div>
                    <div class="logo-text">
                        <div class="logo-title">NY AI</div>
                        <div class="logo-subtitle">Problem Solver</div>
                    </div>
                </a>
            </div>
            <div class="header-controls">
                <button class="control-btn" onclick="toggleTheme()" title="Toggle Theme">🌓</button>
                <button class="control-btn" onclick="toggleFullscreen()" title="Fullscreen">⛶</button>
                <button class="control-btn" onclick="shareResults()" title="Share">📤</button>
            </div>
        </header>
        
        <main class="main-content">
            <section class="input-panel">
                <div class="input-header">
                    <h2 class="input-title">
                        <span>📤</span>
                        Input Question
                    </h2>
                    <p class="input-subtitle">Upload an image or provide a URL to get started</p>
                </div>
                
                <div class="input-content">
                    <div class="tab-container">
                        <div class="tab-buttons">
                            <button class="tab-btn active" onclick="switchTab('image')">
                                <span>🖼️ Image Upload</span>
                            </button>
                            <button class="tab-btn" onclick="switchTab('url')">
                                <span>🔗 Image URL</span>
                            </button>
                        </div>
                        
                        <div class="tab-content active" id="imageTab">
                            <div class="file-upload-container">
                                <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                                    <input type="file" id="fileInput" class="file-input" accept="image/*" onchange="handleFileSelect(event)">
                                    <div class="upload-icon">📷</div>
                                    <div class="upload-text">Click to upload or drag & drop</div>
                                    <div class="upload-hint">Supports: JPG, PNG, GIF, WebP (Max: 10MB)</div>
                                </div>
                                
                                <div class="image-preview" id="imagePreview">
                                    <img class="preview-image" id="previewImg" alt="Preview">
                                    <div class="preview-controls">
                                        <div class="preview-info" id="previewInfo"></div>
                                        <button class="remove-btn" onclick="removeImage()">Remove</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content" id="urlTab">
                            <input type="url" class="url-input" id="urlInput" placeholder="https://example.com/image.jpg" onchange="handleUrlInput()">
                        </div>
                    </div>
                    
                    <button class="solve-btn" id="solveBtn" onclick="solveProblem()" disabled>
                        <span class="btn-text">🚀 Solve Problem</span>
                    </button>
                </div>
            </section>
            
            <section class="solution-panel">
                <div class="solution-header">
                    <h2 class="solution-title">
                        <span>✅</span>
                        Sequential Solution by NY AI
                    </h2>
                    <div class="solution-controls">
                        <button class="solution-btn" onclick="copySolution()" title="Copy Solution">📋</button>
                        <button class="solution-btn" onclick="downloadSolution()" title="Download">💾</button>
                        <button class="solution-btn" onclick="printSolution()" title="Print">🖨️</button>
                    </div>
                </div>
                
                <div class="solution-content" id="solutionContent">
                    <div class="empty-state">
                        <div class="empty-icon">🎯</div>
                        <div class="empty-title">Ready to Solve!</div>
                        <div class="empty-subtitle">Upload an image or provide a URL to get started with NY AI's advanced problem-solving capabilities.</div>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <script>
        // Global variables
        let currentImage = null;
        let currentSolution = null;
        let isDarkMode = false;
        
        // Initialize application
        document.addEventListener('DOMContentLoaded', function() {
            initializeDragDrop();
            initializeTheme();
            initializeResponsive();
        });
        
        // Theme management
        function initializeTheme() {
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
                toggleTheme();
            }
        }
        
        function toggleTheme() {
            isDarkMode = !isDarkMode;
            document.documentElement.classList.toggle('dark', isDarkMode);
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        }
        
        // Responsive handling
        function initializeResponsive() {
            window.addEventListener('resize', debounce(() => {
                optimizeMathForDevice();
                adjustLayoutForViewport();
            }, 250));
        }
        
        function adjustLayoutForViewport() {
            const isMobile = window.innerWidth <= 768;
            const container = document.querySelector('.app-container');
            
            if (isMobile) {
                container.classList.add('mobile');
            } else {
                container.classList.remove('mobile');
            }
        }
        
        // Tab management
        function switchTab(tabName) {
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            // Reset solve button state
            updateSolveButtonState();
        }
        
        // Drag and drop functionality
        function initializeDragDrop() {
            const fileUpload = document.querySelector('.file-upload');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                fileUpload.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                fileUpload.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                fileUpload.addEventListener(eventName, unhighlight, false);
            });
            
            fileUpload.addEventListener('drop', handleDrop, false);
        }
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function highlight(e) {
            document.querySelector('.file-upload').classList.add('drag-over');
        }
        
        function unhighlight(e) {
            document.querySelector('.file-upload').classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                handleFileSelect({ target: { files: files } });
            }
        }
        
        // File handling
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            // Validate file
            if (!validateFile(file)) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                displayImagePreview(e.target.result, file);
                currentImage = e.target.result;
                updateSolveButtonState();
            };
            reader.readAsDataURL(file);
        }
        
        function validateFile(file) {
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            
            if (!allowedTypes.includes(file.type)) {
                showNotification('Please select a valid image file (JPG, PNG, GIF, WebP)', 'error');
                return false;
            }
            
            if (file.size > maxSize) {
                showNotification('File size must be less than 10MB', 'error');
                return false;
            }
            
            return true;
        }
        
        function displayImagePreview(src, file) {
            const preview = document.getElementById('imagePreview');
            const img = document.getElementById('previewImg');
            const info = document.getElementById('previewInfo');
            
            img.src = src;
            info.textContent = `${file.name} (${formatFileSize(file.size)})`;
            preview.style.display = 'block';
        }
        
        function handleUrlInput() {
            const url = document.getElementById('urlInput').value.trim();
            if (url && isValidImageUrl(url)) {
                currentImage = url;
                updateSolveButtonState();
            } else {
                currentImage = null;
                updateSolveButtonState();
            }
        }
        
        function isValidImageUrl(url) {
            try {
                new URL(url);
                return /\.(jpg|jpeg|png|gif|webp)$/i.test(url);
            } catch {
                return false;
            }
        }
        
        function removeImage() {
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('fileInput').value = '';
            currentImage = null;
            updateSolveButtonState();
        }
        
        function updateSolveButtonState() {
            const solveBtn = document.getElementById('solveBtn');
            const hasInput = currentImage !== null;
            
            solveBtn.disabled = !hasInput;
            solveBtn.style.opacity = hasInput ? '1' : '0.6';
        }
        
        // Problem solving
        async function solveProblem() {
            if (!currentImage) {
                showNotification('Please provide an image first', 'error');
                return;
            }
            
            showProgress();
            showLoading();
            
            try {
                updateProgress(25);
                
                // Prepare the request
                const payload = {
                    image: currentImage,
                    timestamp: new Date().toISOString()
                };
                
                updateProgress(50);
                
                // Make API request
                const response = await fetch('/solve', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });
                
                updateProgress(75);
                
                const result = await response.json();
                
                if (result.success) {
                    displaySolution(result.solution);
                    currentSolution = result.solution;
                    showNotification('Problem solved successfully!', 'success');
                } else {
                    throw new Error(result.error || 'Failed to solve problem');
                }
                
                updateProgress(100);
                
            } catch (error) {
                console.error('Error solving problem:', error);
                showNotification('Failed to solve problem. Please try again.', 'error');
                displayError(error.message);
            } finally {
                hideLoading();
                hideProgress();
            }
        }
        
        function displaySolution(solution) {
            const content = document.getElementById('solutionContent');
            
            if (!solution || !solution.steps || solution.steps.length === 0) {
                displayError('No solution steps received');
                return;
            }
            
            let html = '<div class="solution-sequence">';
            
            solution.steps.forEach((step, index) => {
                html += `
                    <div class="solution-step">
                        <div class="step-header">
                            <div class="step-number">${index + 1}</div>
                            <div class="step-title">${escapeHtml(step.title || `Step ${index + 1}`)}</div>
                        </div>
                        <div class="step-content">${processStepContent(step.content || step.text || '')}</div>
                    </div>
                `;
            });
            
            html += '</div>';
            content.innerHTML = html;
            
            // Process MathJax
            if (window.MathJax) {
                MathJax.typesetPromise([content]).then(() => {
                    optimizeMathForDevice();
                });
            }
        }
        
        function processStepContent(content) {
            // Convert line breaks
            content = content.replace(/\n/g, '<br>');
            
            // Process basic markdown
            content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            // Ensure LaTeX delimiters are properly formatted
            content = content.replace(/\$\$([\s\S]*?)\$\$/g, '$$$$1$$');
            content = content.replace(/\$([^$]+)\$/g, '$$$$1$$');
            
            return content;
        }
        
        function displayError(message) {
            const content = document.getElementById('solutionContent');
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div class="empty-title">Error</div>
                    <div class="empty-subtitle">${escapeHtml(message)}</div>
                </div>
            `;
        }
        
        // UI helpers
        function showLoading() {
            const content = document.getElementById('solutionContent');
            content.innerHTML = `
                <div class="loading-overlay">
                    <div class="loading-spinner"></div>
                </div>
            `;
        }
        
        function hideLoading() {
            const overlay = document.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
        
        function showProgress() {
            document.getElementById('progressContainer').classList.add('active');
        }
        
        function updateProgress(percent) {
            document.getElementById('progressBar').style.width = percent + '%';
        }
        
        function hideProgress() {
            setTimeout(() => {
                document.getElementById('progressContainer').classList.remove('active');
                document.getElementById('progressBar').style.width = '0%';
            }, 500);
        }
        
        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                z-index: 10000;
                transform: translateX(400px);
                transition: transform 0.3s ease;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;
            
            // Set background color based on type
            const colors = {
                success: '#48bb78',
                error: '#f56565',
                warning: '#ed8936',
                info: '#4299e1'
            };
            notification.style.background = colors[type] || colors.info;
            
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.style.transform = 'translateX(0)';
            }, 100);
            
            // Auto remove
            setTimeout(() => {
                notification.style.transform = 'translateX(400px)';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
        
        // Utility functions
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
        
        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
        
        // Feature functions
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    showNotification('Fullscreen not supported', 'error');
                });
            } else {
                document.exitFullscreen();
            }
        }
        
        function copySolution() {
            if (!currentSolution) {
                showNotification('No solution to copy', 'warning');
                return;
            }
            
            let text = 'NY AI Solution:\n\n';
            currentSolution.steps.forEach((step, index) => {
                text += `${index + 1}. ${step.title || `Step ${index + 1}`}\n`;
                text += `${step.content || step.text || ''}\n\n`;
            });
            
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Solution copied to clipboard!', 'success');
            }).catch(() => {
                showNotification('Failed to copy solution', 'error');
            });
        }
        
        function downloadSolution() {
            if (!currentSolution) {
                showNotification('No solution to download', 'warning');
                return;
            }
            
            let content = 'NY AI Solution\n' + '='.repeat(50) + '\n\n';
            currentSolution.steps.forEach((step, index) => {
                content += `${index + 1}. ${step.title || `Step ${index + 1}`}\n`;
                content += `${step.content || step.text || ''}\n\n`;
            });
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ny-ai-solution-${new Date().toISOString().slice(0, 10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            showNotification('Solution downloaded!', 'success');
        }
        
        function printSolution() {
            if (!currentSolution) {
                showNotification('No solution to print', 'warning');
                return;
            }
            
            window.print();
        }
        
        function shareResults() {
            if (!currentSolution) {
                showNotification('No solution to share', 'warning');
                return;
            }
            
            if (navigator.share) {
                navigator.share({
                    title: 'NY AI Solution',
                    text: 'Check out this solution from NY AI!',
                    url: window.location.href
                }).catch(() => {
                    fallbackShare();
                });
            } else {
                fallbackShare();
            }
        }
        
        function fallbackShare() {
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {
                showNotification('Link copied to clipboard!', 'success');
            }).catch(() => {
                showNotification('Sharing not supported', 'error');
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/solve', methods=['POST'])
def solve_problem():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'})
        
        # Extract text from image (mock implementation)
        extracted_text = extract_text_from_image(image_data)
        
        # Generate solution (mock implementation)
        solution = generate_solution(extracted_text)
        
        # Store solution
        solution_id = str(uuid.uuid4())
        solutions_store[solution_id] = {
            'solution': solution,
            'timestamp': datetime.datetime.now().isoformat(),
            'image': image_data
        }
        
        return jsonify({
            'success': True,
            'solution': solution,
            'solution_id': solution_id,
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        print(f"Error in solve_problem: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your request'
        })

def extract_text_from_image(image_data):
    """Mock function to extract text from image"""
    # In a real implementation, you would use OCR or vision API
    return "Sample mathematical equation: x^2 + 2x + 1 = 0"

def generate_solution(problem_text):
    """Mock function to generate solution steps"""
    # In a real implementation, you would use Gemini API
    return {
        'steps': [
            {
                'title': 'Problem Identification',
                'content': f'The problem given is: **{problem_text}**\n\nThis appears to be a quadratic equation that we need to solve.'
            },
            {
                'title': 'Apply Quadratic Formula',
                'content': 'For a quadratic equation of the form $ax^2 + bx + c = 0$, we use:\n\n$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\nIn our case: $a = 1$, $b = 2$, $c = 1$'
            },
            {
                'title': 'Calculate Discriminant',
                'content': 'The discriminant is:\n\n$$\\Delta = b^2 - 4ac = 2^2 - 4(1)(1) = 4 - 4 = 0$$\n\nSince $\\Delta = 0$, we have one repeated real root.'
            },
            {
                'title': 'Find the Solution',
                'content': 'Substituting into the quadratic formula:\n\n$$x = \\frac{-2 \\pm \\sqrt{0}}{2(1)} = \\frac{-2}{2} = -1$$\n\nTherefore, $x = -1$ is the solution.'
            },
            {
                'title': 'Verification',
                'content': 'Let\'s verify: $(-1)^2 + 2(-1) + 1 = 1 - 2 + 1 = 0$ ✓\n\nThe solution is correct!'
            }
        ]
    }

@app.route('/solution/<solution_id>')
def get_solution(solution_id):
    solution_data = solutions_store.get(solution_id)
    if not solution_data:
        return jsonify({'success': False, 'error': 'Solution not found'})
    
    return jsonify({
        'success': True,
        'solution': solution_data['solution'],
        'timestamp': solution_data['timestamp']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
