import os
import json
import base64
from flask import Flask, request, render_template_string, session, jsonify
import requests
from dotenv import load_dotenv
import re
from PIL import Image, ImageEnhance, ImageFilter
import io

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDHFTMIgNpOSwOnGRhgaL2Y960BYV2O56s"
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

def process_image_with_pil(image_data):
    """Process image using PIL for better quality."""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        max_size = (1920, 1920)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95, optimize=True)
        processed_data = output.getvalue()
        
        return processed_data, img.size
        
    except Exception as e:
        raise Exception(f"PIL processing failed: {str(e)}")

def enhance_math_notation(text):
    """Convert text to proper MathJax notation."""
    
    math_blocks = []
    def preserve_math(match):
        math_blocks.append(match.group(0))
        return f"__MATH_BLOCK_{len(math_blocks)-1}__"
    
    text = re.sub(r'\$[^$]+\$', preserve_math, text)
    text = re.sub(r'\\\[[^\]]+\\\]', preserve_math, text)
    
    conversions = [
        (r'(\w+)\s*=\s*([^,\n\.;]+)', r'$\1 = \2$'),
        (r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$'),
        (r'\(([^)]+)\)/\(([^)]+)\)', r'$\\frac{\1}{\2}$'),
        (r'(\w+)\^(\d+)', r'$\1^{\2}$'),
        (r'(\w+)\^{([^}]+)}', r'$\1^{\2}$'),
        (r'(\w+)²', r'$\1^2$'),
        (r'(\w+)³', r'$\1^3$'),
        (r'(\w)_(\d+)', r'$\1_{\2}$'),
        (r'√\(([^)]+)\)', r'$\\sqrt{\1}$'),
        (r'sqrt\(([^)]+)\)', r'$\\sqrt{\1}$'),
        (r'sin\s*\(([^)]+)\)', r'$\\sin(\1)$'),
        (r'cos\s*\(([^)]+)\)', r'$\\cos(\1)$'),
        (r'tan\s*\(([^)]+)\)', r'$\\tan(\1)$'),
        (r'sec\s*\(([^)]+)\)', r'$\\sec(\1)$'),
        (r'csc\s*\(([^)]+)\)', r'$\\csc(\1)$'),
        (r'cot\s*\(([^)]+)\)', r'$\\cot(\1)$'),
        (r'log\s*\(([^)]+)\)', r'$\\log(\1)$'),
        (r'ln\s*\(([^)]+)\)', r'$\\ln(\1)$'),
        (r'\bpi\b', r'$\\pi$'),
        (r'\btheta\b', r'$\\theta$'),
        (r'\balpha\b', r'$\\alpha$'),
        (r'\bbeta\b', r'$\\beta$'),
        (r'\bgamma\b', r'$\\gamma$'),
        (r'\bdelta\b', r'$\\delta$'),
        (r'\bomega\b', r'$\\omega$'),
        (r'\bphi\b', r'$\\phi$'),
        (r'\blambda\b', r'$\\lambda$'),
        (r'\binfinity\b', r'$\\infty$'),
        (r'(\d+)\s*degrees?', r'$\1^\\circ$'),
        (r'(\d+)°', r'$\1^\\circ$'),
        (r'\[([MLT\^A\-\d\s]+)\]', r'$[\1]$'),
        (r'→', r'$\\rightarrow$'),
        (r'<->', r'$\\leftrightarrow$'),
        (r'±', r'$\\pm$'),
        (r'\s*\*\s*', r' $\\times$ '),
        (r'∫', r'$\\int$'),
        (r'd/dx', r'$\\frac{d}{dx}$'),
        (r'∂/∂(\w+)', r'$\\frac{\\partial}{\\partial \1}$'),
    ]
    
    for pattern, replacement in conversions:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    for i, block in enumerate(math_blocks):
        text = text.replace(f"__MATH_BLOCK_{i}__", block)
    
    return text

def contains_equation(text):
    """Check if text contains mathematical equations."""
    equation_patterns = [
        r'\w+\s*=\s*[^,\n\.]+',
        r'\d+\s*[+\-×÷]\s*\d+',
        r'[a-zA-Z]\s*=\s*\d+',
    ]
    return any(re.search(pattern, text) for pattern in equation_patterns)

def contains_formula(text):
    """Check if text contains mathematical formulas."""
    formula_patterns = [
        r'sin|cos|tan|log|ln|sqrt|∫|∑|∏',
        r'[a-zA-Z]+\^[0-9]+',
        r'[a-zA-Z]+_[0-9]+',
        r'π|θ|α|β|γ|δ|ω|φ|λ',
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in formula_patterns)

def format_mathematical_solution(text):
    """Format mathematical solution with proper sequencing."""
    
    text = re.sub(r'<[^>]+>', '', text)
    
    sections = []
    lines = text.split('\n')
    current_section = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            continue
        current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    formatted_html = ""
    step_counter = 1
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        section_lower = section.lower()
        
        if any(keyword in section_lower for keyword in ['analysis', 'given', 'question', 'problem']):
            formatted_html += f'<div class="analysis-section"><span class="section-label">📋 Analysis</span><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
        
        elif any(keyword in section_lower for keyword in ['step', 'solution', 'approach', 'method']):
            formatted_html += f'<div class="step-section"><span class="step-label">Step {step_counter}</span><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
            step_counter += 1
        
        elif any(keyword in section_lower for keyword in ['answer', 'result', 'final', 'conclusion']):
            formatted_html += f'<div class="answer-section">✅ <strong>Final Answer:</strong><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
        
        elif contains_equation(section):
            formatted_html += f'<div class="equation-section"><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
        
        elif contains_formula(section):
            formatted_html += f'<div class="formula-section"><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
        
        else:
            formatted_html += f'<div class="text-section"><div class="tex2jax_process">{enhance_math_notation(section)}</div></div>'
    
    return formatted_html

def create_advanced_prompt(question_text=None, has_image=False):
    """Create optimized prompt for sequential solutions."""
    
    prompt = """You are NY AI, an advanced JEE problem solver. Provide solutions in clear, logical sequence.

SOLUTION FORMAT:

🔍 **PROBLEM ANALYSIS**
- Subject: [Physics/Chemistry/Mathematics]
- Topic: [Specific area]
- Given information and what to find

📐 **SOLUTION APPROACH**
- Key formulas needed
- Strategy explanation

🔢 **STEP-BY-STEP SOLUTION**

Step 1: [Clear first step]
[Mathematical work]

Step 2: [Next logical step]
[Continue calculations]

Step 3: [Continue sequentially]
[Show all work clearly]

✅ **FINAL ANSWER**
[Clear result with units]

REQUIREMENTS:
- Show logical progression
- Explain each step
- Use proper notation
- Avoid scattered calculations
- Clear final answer
- Verify reasonableness"""

    if question_text:
        prompt += f"\n\nQUESTION: {question_text}"
    
    if has_image:
        prompt += "\n\nIMAGE: Analyze all mathematical content in the image."
    
    return prompt

def call_gemini_vision(prompt, image_data=None, image_url=None):
    """Call NY AI with PIL-processed images."""
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    parts = [{"text": prompt}]
    
    if image_data:
        try:
            processed_data, img_size = process_image_with_pil(image_data)
            image_b64 = base64.b64encode(processed_data).decode('utf-8')
            
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_b64
                }
            })
            
            return call_api_with_parts(parts), f"{img_size[0]}×{img_size[1]} pixels, PIL enhanced"
            
        except Exception as e:
            return f"Error processing image: {str(e)}", None
    
    elif image_url and not image_url.startswith('data:'):
        try:
            response = requests.get(image_url, timeout=15)
            if response.status_code == 200:
                processed_data, img_size = process_image_with_pil(response.content)
                image_b64 = base64.b64encode(processed_data).decode('utf-8')
                
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_b64
                    }
                })
                
                return call_api_with_parts(parts), f"{img_size[0]}×{img_size[1]} pixels, PIL enhanced"
                
        except Exception as e:
            return f"Error downloading image: {str(e)}", None
    
    return call_api_with_parts(parts), None

def call_api_with_parts(parts):
    """Make API call to NY AI."""
    
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 32,
            "topP": 0.8,
            "maxOutputTokens": 8192,
        }
    }
    
    try:
        response = requests.post(GEMINI_VISION_URL, 
                               headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}, 
                               json=payload, 
                               timeout=45)
        response.raise_for_status()
        
        result = response.json()
        
        if "candidates" in result and len(result["candidates"]) > 0:
            content = result["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                raw_text = parts[0].get("text", "No response generated.")
                formatted_text = format_mathematical_solution(raw_text)
                return formatted_text
        
        return "No valid response from NY AI."
        
    except Exception as e:
        return f"NY AI request failed: {str(e)}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NY AI - JEE Solver</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1625 50%, #2d1b3d 100%);
            min-height: 100vh;
            color: #e2e8f0;
            padding: 20px;
        }
        
        .main-wrapper {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            animation: fadeInDown 1s ease-out;
        }
        
        .brand-badge {
            display: inline-block;
            background: linear-gradient(135deg, #ff4081, #00d4ff);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 15px;
            animation: pulse 2s infinite;
        }
        
        .title {
            font-size: 3.8rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00d4ff 0%, #ff4081 50%, #ffeb3b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #94a3b8;
            font-weight: 300;
        }
        
        .workspace {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 30px;
            animation: fadeInUp 1s ease-out 0.2s both;
        }
        
        .input-side {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(25px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            height: fit-content;
            position: sticky;
            top: 20px;
        }
        
        .solution-side {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(25px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .section-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .input-tabs {
            display: flex;
            background: rgba(30, 41, 59, 0.6);
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 10px 12px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: #94a3b8;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 13px;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #00d4ff, #ff4081);
            color: white;
        }
        
        .tab-panel {
            display: none;
        }
        
        .tab-panel.active {
            display: block;
            animation: fadeIn 0.3s ease-out;
        }
        
        .upload-zone {
            border: 2px dashed #334155;
            border-radius: 14px;
            padding: 35px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(30, 41, 59, 0.3);
        }
        
        .upload-zone:hover {
            border-color: #00d4ff;
            background: rgba(0, 212, 255, 0.05);
        }
        
        .upload-icon {
            font-size: 2.2rem;
            margin-bottom: 12px;
            color: #00d4ff;
        }
        
        input[type="url"], textarea {
            width: 100%;
            padding: 14px 18px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid #334155;
            border-radius: 10px;
            color: #f1f5f9;
            font-size: 15px;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }
        
        .solve-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #00d4ff 0%, #ff4081 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        
        .solve-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(0, 212, 255, 0.3);
        }
        
        .solve-btn:disabled {
            background: #475569;
            cursor: not-allowed;
            transform: none;
        }
        
        .image-preview {
            max-width: 100%;
            border-radius: 12px;
            margin: 15px 0;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 60px 20px;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(148, 163, 184, 0.2);
            border-top: 4px solid #00d4ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        .solution-content {
            color: #e2e8f0;
            line-height: 1.8;
            font-size: 15px;
        }
        
        .analysis-section {
            background: rgba(0, 212, 255, 0.1);
            border-left: 4px solid #00d4ff;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }
        
        .step-section {
            background: rgba(30, 41, 59, 0.4);
            border-left: 4px solid #64748b;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            position: relative;
        }
        
        .step-label {
            display: inline-block;
            background: linear-gradient(135deg, #00d4ff, #ff4081);
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .section-label {
            display: inline-block;
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .equation-section {
            background: rgba(255, 64, 129, 0.1);
            border: 1px solid rgba(255, 64, 129, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 12px 0;
            font-family: 'JetBrains Mono', monospace;
            color: #ff4081;
        }
        
        .formula-section {
            background: rgba(255, 235, 59, 0.1);
            border: 1px solid rgba(255, 235, 59, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 12px 0;
            font-family: 'JetBrains Mono', monospace;
            color: #ffeb3b;
        }
        
        .answer-section {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
            border: 2px solid #22c55e;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            color: #22c55e;
        }
        
        .text-section {
            margin: 15px 0;
            line-height: 1.8;
            color: #cbd5e1;
        }
        
        .chat-area {
            margin-top: 30px;
            border-top: 1px solid rgba(148, 163, 184, 0.1);
            padding-top: 25px;
        }
        
        .chat-messages {
            height: 280px;
            overflow-y: auto;
            background: rgba(30, 41, 59, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .message {
            margin-bottom: 12px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 85%;
        }
        
        .user-msg {
            background: linear-gradient(135deg, #00d4ff, #ff4081);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .ai-msg {
            background: rgba(51, 65, 85, 0.8);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        
        .chat-input-area {
            display: flex;
            gap: 12px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid #334155;
            border-radius: 20px;
            color: #f1f5f9;
            outline: none;
        }
        
        .send-btn {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #00d4ff, #ff4081);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .send-btn:hover {
            transform: scale(1.1);
        }
        
        .empty-display {
            text-align: center;
            padding: 80px 20px;
            color: #64748b;
        }
        
        .empty-icon {
            font-size: 3.5rem;
            margin-bottom: 20px;
            opacity: 0.6;
        }
        
        .error-msg {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            padding: 16px;
            border-radius: 10px;
            margin: 15px 0;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 1024px) {
            .workspace {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .input-side {
                position: static;
            }
            
            .title {
                font-size: 2.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <div class="brand-badge">Powered by NY AI</div>
            <div class="title">JEE Solver</div>
            <div class="subtitle">Advanced Mathematical Problem Solving</div>
        </div>
        
        <div class="workspace">
            <div class="input-side">
                <div class="section-title">📝 Question Input</div>
                
                <div class="input-tabs">
                    <button class="tab active" onclick="switchTab('upload')">📷 Upload</button>
                    <button class="tab" onclick="switchTab('url')">🔗 URL</button>
                    <button class="tab" onclick="switchTab('text')">✏️ Type</button>
                </div>
                
                <form method="POST" enctype="multipart/form-data" id="solverForm">
                    <div id="upload-panel" class="tab-panel active">
                        <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
                            <div class="upload-icon">📁</div>
                            <div><strong>Upload Image</strong></div>
                            <div style="font-size: 13px; color: #64748b; margin-top: 8px;">
                                Drag &amp; drop or click to browse
                            </div>
                            <input type="file" id="fileInput" name="image_file" accept="image/*" style="display: none;" onchange="handleFileUpload(this)">
                        </div>
                    </div>
                    
                    <div id="url-panel" class="tab-panel">
                        <input type="url" name="image_url" placeholder="Paste image URL..." value="{% if image_url %}{{ image_url }}{% endif %}">
                    </div>
                    
                    <div id="text-panel" class="tab-panel">
                        <textarea name="question_text" rows="6" placeholder="Type your JEE question here...">{% if question_text %}{{ question_text }}{% endif %}</textarea>
                    </div>
                    
                    <button type="submit" class="solve-btn" id="solveBtn">
                        🧠 Solve with NY AI
                    </button>
                </form>
                
                {% raw %}{% if image_url %}{% endraw %}
                <div style="margin-top: 20px;">
                    <div style="font-size: 14px; color: #94a3b8; margin-bottom: 10px;">📷 Image</div>
                    <img src="{% raw %}{{ image_url }}{% endraw %}" class="image-preview" alt="Question">
                </div>
                {% raw %}{% endif %}{% endraw %}
                
                {% raw %}{% if image_info %}{% endraw %}
                <div style="margin-top: 15px; padding: 12px; background: rgba(0, 212, 255, 0.1); border-radius: 8px; font-size: 13px; color: #00d4ff;">
                    <strong>Image Info:</strong> {% raw %}{{ image_info }}{% endraw %}
                </div>
                {% raw %}{% endif %}{% endraw %}
            </div>
            
            <div class="solution-side">
                <div class="section-title">✨ NY AI Solution</div>
                
                <div class="loading" id="loadingState">
                    <div class="spinner"></div>
                    <div><strong>NY AI is analyzing...</strong></div>
                    <div style="color: #64748b; margin-top: 8px;">Processing mathematical expressions</div>
                </div>
                
                {% raw %}{% if solution %}{% endraw %}
                <div class="solution-content">
                    {% raw %}{{ solution|safe }}{% endraw %}
                </div>
                {% raw %}{% else %}{% endraw %}
                <div class="empty-display">
                    <div class="empty-icon">🤖</div>
                    <h3>NY AI Ready</h3>
                    <p>Upload an image or type a question to get started</p>
                </div>
                {% raw %}{% endif %}{% endraw %}
                
                {% raw %}{% if error %}{% endraw %}
                <div class="error-msg">
                    <strong>⚠️ Error:</strong> {% raw %}{{ error }}{% endraw %}
                </div>
                {% raw %}{% endif %}{% endraw %}
                
                <div class="chat-area">
                    <div class="section-title">💬 Chat with NY AI</div>
                    
                    <div class="chat-messages" id="chatBox">
                        {% raw %}{% for msg in chat_history %}{% endraw %}
                        <div class="message {% raw %}{{ 'user-msg' if msg.role == 'user' else 'ai-msg' }}{% endraw %}">
                            {% raw %}{{ msg.content }}{% endraw %}
                        </div>
                        {% raw %}{% endfor %}{% endraw %}
                    </div>
                    
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" id="chatInput" placeholder="Ask NY AI for clarification..." onkeypress="handleEnterKey(event)">
                        <button class="send-btn" onclick="sendMessage()">→</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                tags: 'ams',
                macros: {
                    R: "\\mathbb{R}",
                    C: "\\mathbb{C}",
                    N: "\\mathbb{N}",
                    Z: "\\mathbb{Z}",
                    Q: "\\mathbb{Q}",
                    deg: "^\\circ",
                    frac: ["\\frac{#1}{#2}", 2]
                }
            },
            svg: {
                fontCache: 'global',
                displayAlign: 'center'
            },
            startup: {
                ready: () => {
                    MathJax.startup.defaultReady();
                    formatSolutionContent();
                }
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                processHtmlClass: 'tex2jax_process'
            }
        };
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName + '-panel').classList.add('active');
            event.target.classList.add('active');
        }
        
        function handleFileUpload(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    let preview = document.getElementById('imagePreview');
                    if (!preview) {
                        const previewDiv = document.createElement('div');
                        previewDiv.innerHTML = `
                            <div style="font-size: 14px; color: #94a3b8; margin-bottom: 10px;">📷 Preview</div>
                            <img id="imagePreview" class="image-preview" alt="Preview">
                        `;
                        input.closest('.input-side').appendChild(previewDiv);
                        preview = document.getElementById('imagePreview');
                    }
                    
                    preview.src = e.target.result;
                    gsap.fromTo(preview, 
                        { opacity: 0, scale: 0.9 }, 
                        { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.7)" }
                    );
                };
                
                reader.readAsDataURL(file);
            }
        }
        
        const dropZone = document.querySelector('.upload-zone');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#00d4ff';
            dropZone.style.backgroundColor = 'rgba(0, 212, 255, 0.1)';
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = '#334155';
            dropZone.style.backgroundColor = 'rgba(30, 41, 59, 0.3)';
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#334155';
            dropZone.style.backgroundColor = 'rgba(30, 41, 59, 0.3)';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
                handleFileUpload(document.getElementById('fileInput'));
            }
        });
        
        document.getElementById('solverForm').addEventListener('submit', function() {
            const loading = document.getElementById('loadingState');
            const btn = document.getElementById('solveBtn');
            
            loading.classList.add('active');
            btn.disabled = true;
            btn.textContent = '🔄 Processing...';
        });
        
        function handleEnterKey(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addChatMessage(message, 'user');
            input.value = '';
            
            const typingMsg = document.createElement('div');
            typingMsg.className = 'message ai-msg';
            typingMsg.innerHTML = '🤔 NY AI is thinking...';
            typingMsg.id = 'typing';
            document.getElementById('chatBox').appendChild(typingMsg);
            
            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('typing').remove();
                if (data.response) {
                    addChatMessage(data.response, 'ai');
                } else {
                    addChatMessage('Error: ' + (data.error || 'Unknown error'), 'ai');
                }
            })
            .catch(error => {
                document.getElementById('typing').remove();
                addChatMessage('Connection error: ' + error.message, 'ai');
            });
        }
        
        function addChatMessage(text, role) {
            const chatBox = document.getElementById('chatBox');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}-msg tex2jax_process`;
            msgDiv.innerHTML = enhance_math_notation(text);
            
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            MathJax.typesetPromise([msgDiv]).then(() => {
                gsap.fromTo(msgDiv, 
                    { opacity: 0, x: role === 'user' ? 30 : -30 }, 
                    { opacity: 1, x: 0, duration: 0.4, ease: "power2.out" }
                );
            }).catch((err) => console.log('MathJax error:', err));
        }
        
        function formatSolutionContent() {
            const solutionDiv = document.querySelector('.solution-content');
            if (solutionDiv) {
                MathJax.typesetPromise([solutionDiv]).then(() => {
                    gsap.fromTo(solutionDiv.children, 
                        { opacity: 0, y: 20 }, 
                        { opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: "power2.out" }
                    );
                }).catch((err) => console.log('MathJax error:', err));
            }
        }
        
        function enhance_math_notation(text) {
            const conversions = [
                [/(\w+)\s*=\s*([^,\n\.;]+)/g, '$\\1 = \\2$'],
                [/(\d+)\/(\d+)/g, '$\\frac{\\1}{\\2}$'],
                [/(\w+)\^(\d+)/g, '$\\1^{\\2}$'],
                [/(\w)_(\d+)/g, '$\\1_{\\2}$'],
                [/sqrt\(([^)]+)\)/gi, '$\\sqrt{\\1}$'],
                [/sin\s*\(([^)]+)\)/gi, '$\\sin(\\1)$'],
                [/cos\s*\(([^)]+)\)/gi, '$\\cos(\\1)$'],
                [/tan\s*\(([^)]+)\)/gi, '$\\tan(\\1)$'],
                [/\bpi\b/gi, '$\\pi$'],
                [/\btheta\b/gi, '$\\theta$'],
                [/\balpha\b/gi, '$\\alpha$'],
                [/\bbeta\b/gi, '$\\beta$'],
                [/(\d+)\s*degrees?/gi, '$\\1^\\circ$'],
                [/\[([MLT\^A\-\d\s]+)\]/g, '$[\\1]$'],
                [/→/g, '$\\rightarrow$'],
                [/±/g, '$\\pm$']
            ];
            
            conversions.forEach(([pattern, replacement]) => {
                text = text.replace(pattern, replacement);
            });
            
            return text;
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    image_url = None
    solution = None
    error = None
    question_text = None
    image_info = None
    
    if request.method == 'POST':
        try:
            image_url = request.form.get('image_url', '').strip()
            question_text = request.form.get('question_text', '').strip()
            
            image_data = None
            has_image = False
            
            if 'image_file' in request.files and request.files['image_file'].filename:
                file = request.files['image_file']
                if file and file.filename != '':
                    try:
                        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
                        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        
                        if file_ext not in allowed_extensions:
                            error = "Please upload a valid image file."
                        else:
                            image_data = file.read()
                            processed_data, img_size = process_image_with_pil(image_data)
                            image_b64 = base64.b64encode(processed_data).decode('utf-8')
                            image_url = f"data:image/jpeg;base64,{image_b64}"
                            image_info = f"{img_size[0]}×{img_size[1]} pixels, PIL enhanced"
                            has_image = True
                    except Exception as e:
                        error = f"Error processing image: {str(e)}"
            
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
                prompt = create_advanced_prompt(question_text, has_image)
                
                if has_image:
                    solution, img_info = call_gemini_vision(prompt, image_data, image_url)
                    if img_info:
                        image_info = img_info
                else:
                    solution, _ = call_gemini_vision(prompt)
                
                session['current_context'] = {
                    'question_text': question_text,
                    'solution': solution,
                    'has_image': has_image,
                    'subject_area': 'JEE'
                }
                
        except Exception as e:
            error = f"An unexpected error occurred: {str(e)}"
    
    return render_template_string(HTML_TEMPLATE,
                                image_url=image_url,
                                solution=solution,
                                error=error,
                                question_text=question_text,
                                image_info=image_info,
                                chat_history=session.get('chat_history', []))

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        context = session.get('current_context', {})
        
        chat_prompt = f"""You are NY AI continuing a JEE problem discussion.

CONTEXT:
- Original Question: {context.get('question_text', 'Image-based question')}
- Previous Solution: {context.get('solution', 'Not available')}

USER'S QUESTION: {user_message}

Provide clear, educational response with proper mathematical notation and sequential format."""
        
        ai_response, _ = call_gemini_vision(chat_prompt)
        
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({'role': 'user', 'content': user_message})
        session['chat_history'].append({'role': 'ai', 'content': ai_response})
        
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
    print("🚀 NY AI JEE Solver Starting...")
    print("🎯 Features: PIL Processing, MathJax Rendering, Sequential Solutions")
    print("🌐 Server: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
