import os
import json
import base64
import logging
from flask import Flask, request, render_template_string, session, jsonify, redirect, url_for
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import uuid
import datetime
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCfiA0TjeSEUFqJkgYtbLzjsbEdNW_ZTpk"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
DATABASE_NAME = 'jee_solver.db'

# Initialize database
def init_db():
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS solutions (
                id TEXT PRIMARY KEY,
                question_text TEXT,
                solution_steps TEXT,
                subject TEXT,
                difficulty TEXT,
                timestamp DATETIME,
                user_id TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at DATETIME
            )
        ''')
        conn.commit()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes, maximum-scale=5.0">
    <title>JEE Question Solver by Nischay - Advanced Problem Solver</title>
    
    <!-- Preload resources -->
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧠</text></svg>">
    
    <!-- MathJax Configuration -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                packages: {'[+]': ['ams', 'newcommand', 'configmacros', 'physics', 'chemistry']}
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        optimizeMathDisplay();
                    });
                }
            }
        };
        
        function optimizeMathDisplay() {
            const mathElements = document.querySelectorAll('.MathJax, .MathJax_Display');
            mathElements.forEach(el => {
                el.style.maxWidth = '100%';
                el.style.overflowX = 'auto';
                el.style.overflowY = 'hidden';
                el.style.webkitOverflowScrolling = 'touch';
            });
        }
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js" async></script>
    
    <style>
        /* Advanced CSS Variables System */
        :root {
            /* Brand Colors */
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --primary-light: #3b82f6;
            --secondary: #7c3aed;
            --accent: #f59e0b;
            --accent-secondary: #ef4444;
            
            /* JEE Subject Colors */
            --physics: #0ea5e9;
            --chemistry: #10b981;
            --mathematics: #8b5cf6;
            
            /* Semantic Colors */
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
            --info: #06b6d4;
            
            /* Neutral Colors */
            --white: #ffffff;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            
            /* Background Colors */
            --bg-primary: var(--white);
            --bg-secondary: var(--gray-50);
            --bg-tertiary: var(--gray-100);
            --bg-accent: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            
            /* Text Colors */
            --text-primary: var(--gray-900);
            --text-secondary: var(--gray-700);
            --text-muted: var(--gray-500);
            --text-inverse: var(--white);
            
            /* Border & Shadow */
            --border: var(--gray-200);
            --border-hover: var(--gray-300);
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            
            /* Spacing */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            --spacing-2xl: 3rem;
            
            /* Border Radius */
            --radius-sm: 0.375rem;
            --radius: 0.5rem;
            --radius-md: 0.75rem;
            --radius-lg: 1rem;
            --radius-xl: 1.5rem;
            --radius-full: 9999px;
            
            /* Typography */
            --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-size-xs: 0.75rem;
            --font-size-sm: 0.875rem;
            --font-size-base: 1rem;
            --font-size-lg: 1.125rem;
            --font-size-xl: 1.25rem;
            --font-size-2xl: 1.5rem;
            --font-size-3xl: 1.875rem;
            --font-size-4xl: 2.25rem;
            
            /* Transitions */
            --transition: all 0.15s ease-in-out;
            --transition-slow: all 0.3s ease-in-out;
            
            /* Layout */
            --header-height: 4rem;
            --sidebar-width: 16rem;
            --container-padding: 1.5rem;
        }
        
        /* Dark mode */
        [data-theme="dark"] {
            --bg-primary: var(--gray-900);
            --bg-secondary: var(--gray-800);
            --bg-tertiary: var(--gray-700);
            --text-primary: var(--gray-100);
            --text-secondary: var(--gray-300);
            --text-muted: var(--gray-400);
            --border: var(--gray-700);
            --border-hover: var(--gray-600);
        }
        
        /* Reset & Base Styles */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        html {
            font-size: 16px;
            scroll-behavior: smooth;
            -webkit-text-size-adjust: 100%;
        }
        
        body {
            font-family: var(--font-family);
            font-size: var(--font-size-base);
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-secondary);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            overflow-x: hidden;
        }
        
        /* Layout Components */
        .app-wrapper {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Enhanced Header */
        .header {
            background: var(--bg-accent);
            color: var(--text-inverse);
            padding: 0 var(--container-padding);
            height: var(--header-height);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: var(--shadow-md);
        }
        
        .header::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                transparent 50%, 
                rgba(255, 255, 255, 0.05) 100%);
            pointer-events: none;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
            position: relative;
            z-index: 1;
        }
        
        .logo-icon {
            width: 2.5rem;
            height: 2.5rem;
            background: rgba(255, 255, 255, 0.2);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: var(--transition);
        }
        
        .logo-icon:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        
        .logo-content h1 {
            font-size: var(--font-size-xl);
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.125rem;
        }
        
        .logo-content .tagline {
            font-size: var(--font-size-xs);
            font-weight: 500;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
            position: relative;
            z-index: 1;
        }
        
        .header-stats {
            display: flex;
            gap: var(--spacing-lg);
            font-size: var(--font-size-sm);
            font-weight: 600;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            padding: var(--spacing-sm) var(--spacing-md);
            background: rgba(255, 255, 255, 0.1);
            border-radius: var(--radius-full);
            backdrop-filter: blur(10px);
        }
        
        .header-actions {
            display: flex;
            gap: var(--spacing-sm);
        }
        
        .header-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: var(--text-inverse);
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--radius);
            cursor: pointer;
            transition: var(--transition);
            font-size: var(--font-size-sm);
            font-weight: 500;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .header-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }
        
        /* Main Content */
        .main-container {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            min-height: calc(100vh - var(--header-height));
        }
        
        /* Input Section */
        .input-section {
            background: var(--bg-primary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .section-header {
            padding: var(--spacing-xl) var(--container-padding) var(--spacing-lg);
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
        }
        
        .section-title {
            font-size: var(--font-size-xl);
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--spacing-xs);
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }
        
        .section-subtitle {
            font-size: var(--font-size-sm);
            color: var(--text-muted);
            font-weight: 500;
        }
        
        .input-content {
            flex: 1;
            padding: var(--container-padding);
            display: flex;
            flex-direction: column;
            gap: var(--spacing-xl);
            overflow-y: auto;
        }
        
        /* Subject Selection */
        .subject-selector {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            border: 2px solid var(--border);
            transition: var(--transition);
        }
        
        .subject-selector:hover {
            border-color: var(--border-hover);
        }
        
        .subject-title {
            font-size: var(--font-size-lg);
            font-weight: 600;
            margin-bottom: var(--spacing-md);
            color: var(--text-primary);
        }
        
        .subject-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: var(--spacing-md);
        }
        
        .subject-option {
            position: relative;
            cursor: pointer;
        }
        
        .subject-option input[type="radio"] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .subject-label {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-lg) var(--spacing-md);
            border: 2px solid var(--border);
            border-radius: var(--radius-md);
            transition: var(--transition);
            background: var(--bg-primary);
        }
        
        .subject-option input[type="radio"]:checked + .subject-label {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.05);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .subject-icon {
            font-size: 1.5rem;
            margin-bottom: var(--spacing-xs);
        }
        
        .subject-name {
            font-weight: 600;
            font-size: var(--font-size-sm);
            text-align: center;
        }
        
        /* Enhanced Tab System */
        .tab-container {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            border: 2px solid var(--border);
            overflow: hidden;
        }
        
        .tab-header {
            display: flex;
            background: var(--bg-tertiary);
        }
        
        .tab-button {
            flex: 1;
            padding: var(--spacing-lg);
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            position: relative;
        }
        
        .tab-button.active {
            color: var(--primary);
            background: var(--bg-primary);
        }
        
        .tab-button::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary);
            transform: scaleX(0);
            transition: var(--transition);
        }
        
        .tab-button.active::after {
            transform: scaleX(1);
        }
        
        .tab-content {
            padding: var(--spacing-xl);
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeInUp 0.3s ease-out;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Enhanced File Upload */
        .file-upload-area {
            border: 3px dashed var(--border);
            border-radius: var(--radius-lg);
            padding: var(--spacing-2xl);
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            background: var(--bg-primary);
            position: relative;
            overflow: hidden;
        }
        
        .file-upload-area:hover,
        .file-upload-area.dragover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.02);
            transform: scale(1.01);
        }
        
        .upload-icon {
            font-size: 3rem;
            color: var(--primary);
            margin-bottom: var(--spacing-lg);
            display: block;
        }
        
        .upload-text {
            font-size: var(--font-size-lg);
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: var(--spacing-sm);
        }
        
        .upload-hint {
            font-size: var(--font-size-sm);
            color: var(--text-muted);
        }
        
        .file-input {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
        }
        
        /* Image Preview */
        .image-preview {
            margin-top: var(--spacing-lg);
            border-radius: var(--radius-lg);
            overflow: hidden;
            border: 1px solid var(--border);
            background: var(--bg-primary);
            display: none;
        }
        
        .preview-image {
            width: 100%;
            height: auto;
            max-height: 300px;
            object-fit: contain;
        }
        
        .preview-footer {
            padding: var(--spacing-md);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
        }
        
        .preview-info {
            font-size: var(--font-size-sm);
            color: var(--text-muted);
        }
        
        .remove-button {
            background: var(--error);
            color: var(--text-inverse);
            border: none;
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--radius);
            cursor: pointer;
            font-size: var(--font-size-sm);
            font-weight: 500;
            transition: var(--transition);
        }
        
        .remove-button:hover {
            background: #dc2626;
            transform: translateY(-1px);
        }
        
        /* URL Input */
        .url-input {
            width: 100%;
            padding: var(--spacing-lg);
            border: 2px solid var(--border);
            border-radius: var(--radius-lg);
            font-size: var(--font-size-base);
            font-family: inherit;
            transition: var(--transition);
            background: var(--bg-primary);
        }
        
        .url-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        /* Solve Button */
        .solve-button {
            background: var(--bg-accent);
            color: var(--text-inverse);
            border: none;
            padding: var(--spacing-lg) var(--spacing-2xl);
            border-radius: var(--radius-lg);
            font-size: var(--font-size-lg);
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition);
            width: 100%;
            margin-top: var(--spacing-xl);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: var(--shadow-lg);
        }
        
        .solve-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }
        
        .solve-button:disabled {
            background: var(--gray-400);
            cursor: not-allowed;
            transform: none;
            box-shadow: var(--shadow-sm);
        }
        
        /* Solution Section */
        .solution-section {
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
        }
        
        .solution-header {
            padding: var(--spacing-xl) var(--container-padding);
            background: var(--bg-accent);
            color: var(--text-inverse);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }
        
        .solution-title {
            font-size: var(--font-size-xl);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
        }
        
        .solution-actions {
            display: flex;
            gap: var(--spacing-sm);
        }
        
        .action-button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: var(--text-inverse);
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--radius);
            cursor: pointer;
            transition: var(--transition);
            font-size: var(--font-size-sm);
            backdrop-filter: blur(10px);
        }
        
        .action-button:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .solution-content {
            flex: 1;
            padding: var(--container-padding);
            overflow-y: auto;
            background: var(--bg-secondary);
        }
        
        /* Enhanced scrollbar */
        .solution-content::-webkit-scrollbar {
            width: 8px;
        }
        
        .solution-content::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: var(--radius);
        }
        
        .solution-content::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: var(--radius);
        }
        
        .solution-content::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }
        
        /* Solution Steps */
        .solution-steps {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-xl);
        }
        
        .solution-step {
            background: var(--bg-primary);
            border-radius: var(--radius-lg);
            padding: var(--spacing-xl);
            border-left: 4px solid var(--primary);
            box-shadow: var(--shadow-md);
            opacity: 0;
            transform: translateY(20px);
            animation: slideIn 0.5s ease-out forwards;
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
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
        }
        
        .step-number {
            background: var(--primary);
            color: var(--text-inverse);
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: var(--font-size-sm);
        }
        
        .step-title {
            font-size: var(--font-size-lg);
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .step-content {
            line-height: 1.8;
            color: var(--text-secondary);
            font-size: var(--font-size-base);
        }
        
        /* Math expressions */
        .math-expression,
        .MathJax,
        .MathJax_Display {
            background: var(--bg-tertiary) !important;
            padding: var(--spacing-lg) !important;
            border-radius: var(--radius) !important;
            margin: var(--spacing-lg) 0 !important;
            border-left: 3px solid var(--accent) !important;
            overflow-x: auto !important;
            max-width: 100% !important;
        }
        
        /* Empty State */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: var(--spacing-2xl);
        }
        
        .empty-icon {
            font-size: 4rem;
            margin-bottom: var(--spacing-lg);
            opacity: 0.5;
        }
        
        .empty-title {
            font-size: var(--font-size-2xl);
            font-weight: 700;
            margin-bottom: var(--spacing-md);
            color: var(--text-secondary);
        }
        
        .empty-subtitle {
            font-size: var(--font-size-base);
            color: var(--text-muted);
            max-width: 400px;
            line-height: 1.6;
        }
        
        /* Loading State */
        .loading-overlay {
            position: absolute;
            inset: 0;
            background: rgba(255, 255, 255, 0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .loading-spinner {
            width: 3rem;
            height: 3rem;
            border: 3px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: var(--spacing-lg);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-size: var(--font-size-lg);
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: var(--spacing-sm);
        }
        
        .loading-subtitle {
            font-size: var(--font-size-sm);
            color: var(--text-muted);
        }
        
        /* Progress Bar */
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
            background: var(--bg-accent);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        /* Notifications */
        .notification {
            position: fixed;
            top: var(--spacing-lg);
            right: var(--spacing-lg);
            padding: var(--spacing-lg);
            border-radius: var(--radius-lg);
            color: var(--text-inverse);
            font-weight: 600;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            max-width: 350px;
            box-shadow: var(--shadow-xl);
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success { background: var(--success); }
        .notification.error { background: var(--error); }
        .notification.warning { background: var(--warning); }
        .notification.info { background: var(--info); }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .main-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            
            .input-section {
                border-right: none;
                border-bottom: 1px solid var(--border);
            }
        }
        
        @media (max-width: 768px) {
            :root {
                --header-height: 3.5rem;
                --container-padding: 1rem;
            }
            
            .header {
                padding: 0 var(--container-padding);
                flex-wrap: wrap;
                height: auto;
                min-height: var(--header-height);
            }
            
            .logo-section {
                order: 1;
                flex: 1;
            }
            
            .header-controls {
                order: 2;
                width: 100%;
                margin-top: var(--spacing-md);
                justify-content: space-between;
            }
            
            .header-stats {
                display: none;
            }
            
            .subject-options {
                grid-template-columns: 1fr;
            }
            
            .tab-header {
                flex-direction: column;
            }
            
            .solution-header {
                padding: var(--spacing-lg) var(--container-padding);
            }
            
            .solution-title {
                font-size: var(--font-size-lg);
            }
            
            .solution-actions {
                flex-wrap: wrap;
            }
        }
        
        @media (max-width: 480px) {
            .logo-content h1 {
                font-size: var(--font-size-lg);
            }
            
            .section-title {
                font-size: var(--font-size-lg);
            }
            
            .solve-button {
                padding: var(--spacing-md) var(--spacing-lg);
                font-size: var(--font-size-base);
            }
            
            .step-header {
                flex-direction: column;
                align-items: flex-start;
                gap: var(--spacing-sm);
            }
            
            .step-number {
                align-self: flex-start;
            }
        }
        
        /* Touch-friendly interactions */
        @media (hover: none) and (pointer: coarse) {
            .header-btn,
            .action-button,
            .solve-button {
                min-height: 44px;
            }
            
            .file-upload-area {
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
        
        /* Print styles */
        @media print {
            .header,
            .input-section,
            .solution-header {
                display: none;
            }
            
            .main-container {
                grid-template-columns: 1fr;
            }
            
            .solution-content {
                padding: 0;
                overflow: visible;
            }
            
            .solution-step {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ccc;
                margin-bottom: var(--spacing-lg);
            }
        }
    </style>
</head>
<body>
    <div class="progress-container" id="progressContainer">
        <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <div class="app-wrapper">
        <header class="header">
            <div class="logo-section">
                <div class="logo-icon">🧠</div>
                <div class="logo-content">
                    <h1>JEE Solver by Nischay</h1>
                    <div class="tagline">Advanced AI Problem Solver</div>
                </div>
            </div>
            <div class="header-controls">
                <div class="header-stats">
                    <div class="stat-item">
                        <span>📚</span>
                        <span>Physics</span>
                    </div>
                    <div class="stat-item">
                        <span>⚗️</span>
                        <span>Chemistry</span>
                    </div>
                    <div class="stat-item">
                        <span>📐</span>
                        <span>Mathematics</span>
                    </div>
                </div>
                <div class="header-actions">
                    <button class="header-btn" onclick="toggleTheme()">🌓</button>
                    <button class="header-btn" onclick="toggleFullscreen()">⛶</button>
                    <button class="header-btn" onclick="showHistory()">📊</button>
                </div>
            </div>
        </header>
        
        <main class="main-container">
            <section class="input-section">
                <div class="section-header">
                    <h2 class="section-title">
                        <span>📤</span>
                        Upload Question
                    </h2>
                    <p class="section-subtitle">Select subject and upload your JEE question for detailed solution</p>
                </div>
                
                <div class="input-content">
                    <!-- Subject Selection -->
                    <div class="subject-selector">
                        <h3 class="subject-title">Select Subject</h3>
                        <div class="subject-options">
                            <div class="subject-option">
                                <input type="radio" name="subject" value="physics" id="physics" checked>
                                <label for="physics" class="subject-label">
                                    <div class="subject-icon">⚡</div>
                                    <div class="subject-name">Physics</div>
                                </label>
                            </div>
                            <div class="subject-option">
                                <input type="radio" name="subject" value="chemistry" id="chemistry">
                                <label for="chemistry" class="subject-label">
                                    <div class="subject-icon">🧪</div>
                                    <div class="subject-name">Chemistry</div>
                                </label>
                            </div>
                            <div class="subject-option">
                                <input type="radio" name="subject" value="mathematics" id="mathematics">
                                <label for="mathematics" class="subject-label">
                                    <div class="subject-icon">📊</div>
                                    <div class="subject-name">Mathematics</div>
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Input Tabs -->
                    <div class="tab-container">
                        <div class="tab-header">
                            <button class="tab-button active" onclick="switchTab('upload')">
                                🖼️ Image Upload
                            </button>
                            <button class="tab-button" onclick="switchTab('url')">
                                🔗 Image URL
                            </button>
                        </div>
                        
                        <div class="tab-content active" id="uploadTab">
                            <div class="file-upload-area" onclick="document.getElementById('fileInput').click()">
                                <input type="file" id="fileInput" class="file-input" accept="image/*" onchange="handleFileUpload(event)">
                                <div class="upload-icon">📷</div>
                                <div class="upload-text">Upload JEE Question</div>
                                <div class="upload-hint">Click here or drag & drop image (JPG, PNG, WebP - Max 10MB)</div>
                            </div>
                            
                            <div class="image-preview" id="imagePreview">
                                <img class="preview-image" id="previewImage" alt="Question preview">
                                <div class="preview-footer">
                                    <div class="preview-info" id="previewInfo"></div>
                                    <button class="remove-button" onclick="removeImage()">Remove</button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content" id="urlTab">
                            <input type="url" class="url-input" id="urlInput" 
                                   placeholder="https://example.com/jee-question.jpg" 
                                   onchange="handleUrlInput()">
                        </div>
                    </div>
                    
                    <button class="solve-button" id="solveButton" onclick="solveQuestion()" disabled>
                        🚀 Solve JEE Question
                    </button>
                </div>
            </section>
            
            <section class="solution-section">
                <div class="solution-header">
                    <h2 class="solution-title">
                        <span>✅</span>
                        Detailed Solution
                    </h2>
                    <div class="solution-actions">
                        <button class="action-button" onclick="copySolution()" title="Copy Solution">📋</button>
                        <button class="action-button" onclick="downloadSolution()" title="Download PDF">💾</button>
                        <button class="action-button" onclick="shareSolution()" title="Share">📤</button>
                        <button class="action-button" onclick="printSolution()" title="Print">🖨️</button>
                    </div>
                </div>
                
                <div class="solution-content" id="solutionContent">
                    <div class="empty-state">
                        <div class="empty-icon">🎯</div>
                        <div class="empty-title">Ready to Solve!</div>
                        <div class="empty-subtitle">
                            Upload a JEE question image to get step-by-step solutions with detailed explanations, 
                            formulas, and conceptual insights by Nischay's AI solver.
                        </div>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <script>
        // Global application state
        let currentQuestion = null;
        let currentSolution = null;
        let isDarkMode = localStorage.getItem('theme') === 'dark';
        let selectedSubject = 'physics';
        
        // Initialize application
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
            initializeDragDrop();
            initializeTheme();
            trackSubjectSelection();
        });
        
        function initializeApp() {
            console.log('JEE Solver by Nischay - Initialized');
            updateSolveButtonState();
        }
        
        function initializeTheme() {
            if (isDarkMode) {
                document.documentElement.setAttribute('data-theme', 'dark');
            }
        }
        
        function toggleTheme() {
            isDarkMode = !isDarkMode;
            if (isDarkMode) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            }
        }
        
        function trackSubjectSelection() {
            document.querySelectorAll('input[name="subject"]').forEach(radio => {
                radio.addEventListener('change', function() {
                    selectedSubject = this.value;
                    console.log('Subject selected:', selectedSubject);
                });
            });
        }
        
        // Tab management
        function switchTab(tabName) {
            // Update buttons
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            updateSolveButtonState();
        }
        
        // Drag and drop functionality
        function initializeDragDrop() {
            const uploadArea = document.querySelector('.file-upload-area');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
            });
            
            uploadArea.addEventListener('drop', handleFileDrop, false);
        }
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function handleFileDrop(e) {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload({ target: { files: files } });
            }
        }
        
        // File handling
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            if (!validateFile(file)) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                displayImagePreview(e.target.result, file);
                currentQuestion = e.target.result;
                updateSolveButtonState();
            };
            reader.readAsDataURL(file);
        }
        
        function validateFile(file) {
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            
            if (!allowedTypes.includes(file.type)) {
                showNotification('Please upload a valid image file (JPG, PNG, GIF, WebP)', 'error');
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
            const img = document.getElementById('previewImage');
            const info = document.getElementById('previewInfo');
            
            img.src = src;
            info.textContent = `${file.name} (${formatFileSize(file.size)})`;
            preview.style.display = 'block';
        }
        
        function handleUrlInput() {
            const url = document.getElementById('urlInput').value.trim();
            if (url && isValidImageUrl(url)) {
                currentQuestion = url;
                updateSolveButtonState();
            } else {
                currentQuestion = null;
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
            currentQuestion = null;
            updateSolveButtonState();
        }
        
        function updateSolveButtonState() {
            const solveBtn = document.getElementById('solveButton');
            const hasInput = currentQuestion !== null;
            
            solveBtn.disabled = !hasInput;
            solveBtn.style.opacity = hasInput ? '1' : '0.6';
        }
        
        // Question solving
        async function solveQuestion() {
            if (!currentQuestion) {
                showNotification('Please upload a question image first', 'error');
                return;
            }
            
            showProgress();
            showLoadingState();
            
            try {
                updateProgress(25);
                
                const payload = {
                    image: currentQuestion,
                    subject: selectedSubject,
                    timestamp: new Date().toISOString()
                };
                
                updateProgress(50);
                
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
                    showNotification('Question solved successfully! 🎉', 'success');
                } else {
                    throw new Error(result.error || 'Failed to solve question');
                }
                
                updateProgress(100);
                
            } catch (error) {
                console.error('Error solving question:', error);
                showNotification('Failed to solve question. Please try again.', 'error');
                displayError(error.message);
            } finally {
                hideProgress();
                setTimeout(hideLoadingState, 500);
            }
        }
        
        function displaySolution(solution) {
            const content = document.getElementById('solutionContent');
            
            if (!solution || !solution.steps || solution.steps.length === 0) {
                displayError('No solution steps received');
                return;
            }
            
            let html = '<div class="solution-steps">';
            
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
                    optimizeMathDisplay();
                });
            }
        }
        
        function processStepContent(content) {
            // Convert line breaks
            content = content.replace(/\n/g, '<br>');
            
            // Process markdown
            content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
            
            // Process LaTeX
            content = content.replace(/\$\$([\s\S]*?)\$\$/g, '$$$$1$$');
            content = content.replace(/\$([^$\n]+)\$/g, '$$$$1$$');
            
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
        
        // UI States
        function showLoadingState() {
            const content = document.getElementById('solutionContent');
            content.innerHTML = `
                <div class="loading-overlay">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Solving JEE Question...</div>
                    <div class="loading-subtitle">AI is analyzing and generating step-by-step solution</div>
                </div>
            `;
        }
        
        function hideLoadingState() {
            const overlay = document.querySelector('.loading-overlay');
            if (overlay) {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.remove(), 300);
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
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.classList.add('show'), 100);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
        
        // Feature functions
        function copySolution() {
            if (!currentSolution) {
                showNotification('No solution to copy', 'warning');
                return;
            }
            
            let text = `JEE Question Solution by Nischay\n${'='.repeat(50)}\n\n`;
            text += `Subject: ${selectedSubject.toUpperCase()}\n\n`;
            
            currentSolution.steps.forEach((step, index) => {
                text += `${index + 1}. ${step.title || `Step ${index + 1}`}\n`;
                text += `${step.content || step.text || ''}\n\n`;
            });
            
            navigator.clipboard.writeText(text).then(() => {
                showNotification('Solution copied to clipboard! 📋', 'success');
            }).catch(() => {
                showNotification('Failed to copy solution', 'error');
            });
        }
        
        function downloadSolution() {
            if (!currentSolution) {
                showNotification('No solution to download', 'warning');
                return;
            }
            
            let content = `JEE Question Solution by Nischay\n`;
            content += `${'='.repeat(50)}\n\n`;
            content += `Subject: ${selectedSubject.toUpperCase()}\n`;
            content += `Date: ${new Date().toLocaleDateString()}\n\n`;
            
            currentSolution.steps.forEach((step, index) => {
                content += `${index + 1}. ${step.title || `Step ${index + 1}`}\n`;
                content += `${step.content || step.text || ''}\n\n`;
            });
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jee-solution-${selectedSubject}-${new Date().toISOString().slice(0, 10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            showNotification('Solution downloaded! 💾', 'success');
        }
        
        function shareSolution() {
            if (!currentSolution) {
                showNotification('No solution to share', 'warning');
                return;
            }
            
            if (navigator.share) {
                navigator.share({
                    title: 'JEE Solution by Nischay',
                    text: 'Check out this detailed JEE solution!',
                    url: window.location.href
                }).catch(() => fallbackShare());
            } else {
                fallbackShare();
            }
        }
        
        function fallbackShare() {
            navigator.clipboard.writeText(window.location.href).then(() => {
                showNotification('Link copied to clipboard! 📤', 'success');
            }).catch(() => {
                showNotification('Sharing not supported', 'error');
            });
        }
        
        function printSolution() {
            if (!currentSolution) {
                showNotification('No solution to print', 'warning');
                return;
            }
            window.print();
        }
        
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {
                    showNotification('Fullscreen not supported', 'error');
                });
            } else {
                document.exitFullscreen();
            }
        }
        
        function showHistory() {
            showNotification('Solution history feature coming soon! 📊', 'info');
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
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/solve', methods=['POST'])
def solve_question():
    try:
        data = request.get_json()
        image_data = data.get('image')
        subject = data.get('subject', 'general')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'})
        
        logger.info(f"Processing {subject} question")
        
        # Simulate OCR and solution generation
        extracted_text = extract_question_text(image_data)
        solution = generate_jee_solution(extracted_text, subject)
        
        # Store in database
        solution_id = str(uuid.uuid4())
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.execute('''
                INSERT INTO solutions (id, question_text, solution_steps, subject, difficulty, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (solution_id, extracted_text, json.dumps(solution), subject, 'medium', 
                  datetime.datetime.now(), session.get('user_id', 'anonymous')))
            conn.commit()
        
        return jsonify({
            'success': True,
            'solution': solution,
            'solution_id': solution_id,
            'extracted_text': extracted_text,
            'subject': subject
        })
        
    except Exception as e:
        logger.error(f"Error in solve_question: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your question'
        })

def extract_question_text(image_data):
    """Extract text from image using OCR (mock implementation)"""
    # In production, use Google Vision API or Tesseract
    sample_questions = {
        'physics': "A particle of mass 2 kg is moving with velocity 10 m/s. Find the kinetic energy.",
        'chemistry': "Balance the equation: H2 + O2 → H2O",
        'mathematics': "Solve the integral: ∫(x² + 2x + 1)dx"
    }
    return sample_questions.get('physics', "Sample JEE question detected")

def generate_jee_solution(question_text, subject):
    """Generate detailed JEE solution steps"""
    
    solutions = {
        'physics': {
            'steps': [
                {
                    'title': 'Given Information',
                    'content': f'**Question:** {question_text}\n\n**Given:**\n• Mass (m) = 2 kg\n• Velocity (v) = 10 m/s\n\n**To Find:** Kinetic Energy (K.E.)'
                },
                {
                    'title': 'Formula Application',
                    'content': 'The kinetic energy of a particle is given by:\n\n$$KE = \\frac{1}{2}mv^2$$\n\nWhere:\n• m = mass of the particle\n• v = velocity of the particle'
                },
                {
                    'title': 'Substitution',
                    'content': 'Substituting the given values:\n\n$$KE = \\frac{1}{2} \\times 2 \\times (10)^2$$\n\n$$KE = \\frac{1}{2} \\times 2 \\times 100$$'
                },
                {
                    'title': 'Calculation',
                    'content': '$$KE = \\frac{1}{2} \\times 2 \\times 100 = 1 \\times 100 = 100 \\text{ J}$$\n\nTherefore, the kinetic energy of the particle is **100 Joules**.'
                },
                {
                    'title': 'Verification & Concept',
                    'content': '**Verification:** Units check out correctly (kg⋅m²⋅s⁻² = J) ✓\n\n**Key Concept:** Kinetic energy represents the energy possessed by a body due to its motion. It depends on both mass and the square of velocity, making velocity the more significant factor.'
                }
            ]
        },
        'chemistry': {
            'steps': [
                {
                    'title': 'Unbalanced Equation',
                    'content': f'**Question:** {question_text}\n\n**Unbalanced equation:**\n$$\\ce{H2 + O2 -> H2O}$$'
                },
                {
                    'title': 'Atom Count Analysis',
                    'content': '**Reactants:**\n• H atoms: 2\n• O atoms: 2\n\n**Products:**\n• H atoms: 2\n• O atoms: 1\n\n**Issue:** Oxygen atoms are not balanced (2 ≠ 1)'
                },
                {
                    'title': 'Balancing Steps',
                    'content': 'To balance oxygen atoms, we need 2 water molecules:\n\n$$\\ce{H2 + O2 -> 2H2O}$$\n\nNow checking:\n• H atoms: Left = 2, Right = 4 (unbalanced)\n• O atoms: Left = 2, Right = 2 (balanced)'
                },
                {
                    'title': 'Final Balancing',
                    'content': 'To balance hydrogen atoms, we need 2 H₂ molecules:\n\n$$\\ce{2H2 + O2 -> 2H2O}$$\n\n**Final check:**\n• H atoms: Left = 4, Right = 4 ✓\n• O atoms: Left = 2, Right = 2 ✓'
                },
                {
                    'title': 'Balanced Equation',
                    'content': '**Balanced chemical equation:**\n\n$$\\ce{2H2 + O2 -> 2H2O}$$\n\nThis represents the combustion of hydrogen gas to form water vapor.'
                }
            ]
        },
        'mathematics': {
            'steps': [
                {
                    'title': 'Given Integral',
                    'content': f'**Problem:** {question_text}\n\n$$\\int (x^2 + 2x + 1) dx$$\n\nWe need to find the antiderivative of this polynomial function.'
                },
                {
                    'title': 'Power Rule Application',
                    'content': 'Using the power rule for integration:\n\n$$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$$\n\nWe integrate each term separately:\n\n$$\\int (x^2 + 2x + 1) dx = \\int x^2 dx + \\int 2x dx + \\int 1 dx$$'
                },
                {
                    'title': 'Term-by-term Integration',
                    'content': '**First term:** $\\int x^2 dx = \\frac{x^3}{3}$\n\n**Second term:** $\\int 2x dx = 2 \\cdot \\frac{x^2}{2} = x^2$\n\n**Third term:** $\\int 1 dx = x$'
                },
                {
                    'title': 'Combining Results',
                    'content': '$$\\int (x^2 + 2x + 1) dx = \\frac{x^3}{3} + x^2 + x + C$$\n\nWhere C is the constant of integration.'
                },
                {
                    'title': 'Alternative Recognition',
                    'content': '**Note:** The integrand can be factored:\n\n$$x^2 + 2x + 1 = (x+1)^2$$\n\nSo alternatively:\n$$\\int (x+1)^2 dx = \\frac{(x+1)^3}{3} + C = \\frac{x^3 + 3x^2 + 3x + 1}{3} + C$$\n\nBoth methods give the same result!'
                }
            ]
        }
    }
    
    return solutions.get(subject, solutions['physics'])

@app.route('/history')
def get_history():
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.execute('''
                SELECT id, question_text, subject, difficulty, timestamp 
                FROM solutions 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'question_text': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                    'subject': row[2],
                    'difficulty': row[3],
                    'timestamp': row[4]
                })
            
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch history'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
