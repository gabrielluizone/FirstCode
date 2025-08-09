# Required pip installs:
# pip install opencv-python
# pip install ultralytics
# pip install requests
# pip install supervision
# pip install pillow
# pip install torch
# pip install flask
# Abaixo talvez não precise
# pip install webbrowser
# pip install base64

import os
import cv2
from ultralytics import YOLO, YOLOE
import requests
import logging
import supervision as sv
from PIL import Image
import torch
from flask import Flask, render_template, request, jsonify, Response
import webbrowser
import threading
import base64
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('ultralytics').setLevel(logging.WARNING)

# Force CPU usage
torch.set_default_device('cpu')

app = Flask(__name__)

class YOLODetector:
    def __init__(self):
        self.model = None
        self.capture = None
        self.is_running = False
        self.current_frame = None
        self.model_map = {
            '1': "yolov8n.pt",
            '2': "Vo5.pt", 
            '3': "To9.pt",
            '4': "yoloe-11s-seg-pf.pt"
        }
        self.is_yoloe = False
        self.confidence_threshold = 0.5
        self.fps_setting = 30
        self.frame_delay = 0.033  # Default ~30 FPS
        
    def download_model(self, model_name, model_choice):
        """Download model if it doesn't exist"""
        if not os.path.exists(model_name) and model_choice in ['2', '3']:
            print(f"Downloading model {model_name}...")
            try:
                url = f"https://github.com/gabrielluizone/Vangard-OilWatch/raw/main/models/{model_name}"
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(model_name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                print(f"Model {model_name} downloaded successfully!")
                return True
            except Exception as e:
                print(f"Error downloading model: {e}")
                if os.path.exists(model_name) and os.path.getsize(model_name) == 0:
                    os.remove(model_name)
                return False
        return True
    
    def load_model(self, model_choice, confidence):
        """Load the selected YOLO model"""
        try:
            model_name = self.model_map.get(model_choice, "Vo5.pt")
            self.confidence_threshold = confidence / 100.0
            self.is_yoloe = model_choice == '4'
            
            # Download model if needed
            if not self.download_model(model_name, model_choice):
                return False, "Failed to download model"
            
            # Load model
            if self.is_yoloe:
                self.model = YOLOE(model_name)
            else:
                self.model = YOLO(model_name, verbose=False).to('cpu')
                
            return True, f"Model {model_name} loaded successfully"
        except Exception as e:
            return False, f"Error loading model: {str(e)}"
    
    def setup_camera(self, camera_option, ip_address=None, fps=30):
        """Setup camera capture"""
        try:
            if self.capture:
                self.capture.release()
            
            # Set FPS configuration
            self.fps_setting = fps
            self.frame_delay = 1.0 / fps  # Calculate delay between frames
                
            if camera_option == '2' and ip_address:
                # IP Camera
                rtsp_url = f"rtsp://admin:dataoverseas1@{ip_address}"
                self.capture = cv2.VideoCapture(rtsp_url)
                # Try to set FPS for IP camera (may not work on all cameras)
                self.capture.set(cv2.CAP_PROP_FPS, fps)
            else:
                # Local camera
                camera_index = int(camera_option)
                self.capture = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.capture.set(cv2.CAP_PROP_FPS, fps)
            
            # Test if camera is working
            ret, frame = self.capture.read()
            if not ret:
                return False, "Failed to read from camera"
                
            return True, f"Camera setup successful (FPS: {fps})"
        except Exception as e:
            return False, f"Camera setup error: {str(e)}"
    
    def start_detection(self):
        """Start the detection loop"""
        self.is_running = True
        detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        detection_thread.start()
    
    def stop_detection(self):
        """Stop the detection"""
        self.is_running = False
        if self.capture:
            self.capture.release()
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            try:
                ret, frame = self.capture.read()
                if not ret:
                    break
                
                if self.model is None:
                    continue
                    
                # Process frame with YOLO using supervision for all models
                if self.is_yoloe:
                    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    results = self.model.predict(pil_image, conf=self.confidence_threshold, verbose=False, device='cpu')
                else:
                    results = self.model(frame, conf=self.confidence_threshold, verbose=False, device='cpu')
                
                # Use supervision annotation for all models
                detections = sv.Detections.from_ultralytics(results[0] if isinstance(results, list) else results)
                frame = sv.LabelAnnotator().annotate(
                    sv.BoxAnnotator().annotate(frame.copy(), detections=detections),
                    detections=detections
                )
                
                # Store current frame
                self.current_frame = frame.copy()
                
                # Use configured FPS delay
                time.sleep(self.frame_delay)
                
            except Exception as e:
                print(f"Detection error: {e}")
                break
    
    def get_frame(self):
        """Get the current processed frame"""
        if self.current_frame is not None:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', self.current_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                return base64.b64encode(frame_bytes).decode('utf-8')
        return None

# Global detector instance
detector = YOLODetector()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/load_model', methods=['POST'])
def load_model():
    """Load YOLO model"""
    data = request.json
    model_choice = data.get('model')
    confidence = data.get('confidence', 50)
    
    success, message = detector.load_model(model_choice, confidence)
    return jsonify({'success': success, 'message': message})

@app.route('/api/setup_camera', methods=['POST'])
def setup_camera():
    """Setup camera"""
    data = request.json
    camera_option = data.get('camera')
    ip_address = data.get('ip_address')
    fps = data.get('fps', 30)
    
    success, message = detector.setup_camera(camera_option, ip_address, fps)
    return jsonify({'success': success, 'message': message})

@app.route('/api/start_detection', methods=['POST'])
def start_detection():
    """Start detection"""
    try:
        detector.start_detection()
        return jsonify({'success': True, 'message': 'Detection started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop_detection', methods=['POST'])
def stop_detection():
    """Stop detection"""
    detector.stop_detection()
    return jsonify({'success': True, 'message': 'Detection stopped'})

@app.route('/api/get_frame')
def get_frame():
    """Get current frame"""
    frame_data = detector.get_frame()
    return jsonify({'frame': frame_data, 'timestamp': datetime.now().isoformat()})

@app.template_global()
def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # HTML Template
    html_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Detecção Avançado - Data Overseas</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #202124;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(82, 98, 186, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(82, 98, 186, 0.2) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(82, 98, 186, 0.15) 0%, transparent 50%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            color: #e8eaed;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            flex: 1;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
            padding: 25px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        .logo {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid rgba(82, 98, 186, 0.5);
            box-shadow: 0 4px 20px rgba(82, 98, 186, 0.3);
        }

        .header-content {
            text-align: left;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 5px;
            background: linear-gradient(135deg, #5262ba 0%, #7c4dff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: none;
        }

        .company-name {
            font-size: 1.2em;
            color: #5262ba;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .header p {
            opacity: 0.8;
            font-size: 1.1em;
            color: #bdc1c6;
        }

        .main-content {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
            height: calc(100vh - 180px);
        }

        .control-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            overflow-y: auto;
        }

        .video-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .section {
            margin-bottom: 25px;
            padding: 20px;
            background: rgba(82, 98, 186, 0.08);
            border-radius: 15px;
            border: 1px solid rgba(82, 98, 186, 0.2);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .section h3 {
            margin-bottom: 15px;
            color: #e8eaed;
            font-size: 1.2em;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            opacity: 0.9;
        }

        select, input, button {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(82, 98, 186, 0.3);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.2);
            color: #e8eaed;
            font-size: 16px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        select:focus, input:focus {
            outline: none;
            border-color: #5262ba;
            background: rgba(0, 0, 0, 0.3);
            box-shadow: 0 0 0 3px rgba(82, 98, 186, 0.2);
        }

        button {
            cursor: pointer;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        button:hover {
            background: rgba(82, 98, 186, 0.2);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(82, 98, 186, 0.3);
        }

        .btn-primary {
            background: linear-gradient(135deg, #5262ba 0%, #7c4dff 100%);
            border: none;
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, #00c851 0%, #00ff88 100%);
            border: none;
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff4444 0%, #ff6b88 100%);
            border: none;
            color: white;
        }

        .video-container {
            width: 100%;
            max-width: 100%;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
            border: 2px solid rgba(82, 98, 186, 0.2);
            cursor: pointer;
            position: relative;
        }

        .video-feed {
            width: 100%;
            height: auto;
            display: block;
        }

        .video-placeholder {
            width: 100%;
            height: 400px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: rgba(0, 0, 0, 0.7);
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.2em;
            border-radius: 15px;
        }

        .fullscreen-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.7);
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 10;
        }

        .video-container:hover .fullscreen-btn {
            opacity: 1;
        }

        .fullscreen-btn:hover {
            background: rgba(82, 98, 186, 0.8);
            transform: none;
            box-shadow: none;
        }

        /* Fullscreen modal styles */
        .fullscreen-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 9999;
            align-items: center;
            justify-content: center;
        }

        .fullscreen-modal.active {
            display: flex;
        }

        .fullscreen-video {
            max-width: 95%;
            max-height: 95%;
            border-radius: 10px;
            box-shadow: 0 0 50px rgba(82, 98, 186, 0.5);
        }

        .close-fullscreen {
            position: absolute;
            top: 20px;
            right: 30px;
            background: rgba(0, 0, 0, 0.7);
            border: none;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s ease;
        }

        .close-fullscreen:hover {
            background: rgba(82, 98, 186, 0.8);
        }

        .status {
            margin: 15px 0;
            padding: 12px;
            border-radius: 10px;
            font-weight: 500;
            text-align: center;
            transition: all 0.3s ease;
        }

        .status.success {
            background: rgba(0, 200, 81, 0.15);
            border: 1px solid rgba(0, 200, 81, 0.4);
            color: #00c851;
        }

        .status.error {
            background: rgba(255, 68, 68, 0.15);
            border: 1px solid rgba(255, 68, 68, 0.4);
            color: #ff4444;
        }

        .status.info {
            background: rgba(82, 98, 186, 0.15);
            border: 1px solid rgba(82, 98, 186, 0.4);
            color: #5262ba;
        }

        .hidden {
            display: none !important;
        }

        .confidence-display {
            text-align: center;
            margin-top: 5px;
            font-size: 0.9em;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }

        input::placeholder {
            color: rgba(232, 234, 237, 0.5);
        }

        option {
            background: #2d2e30;
            color: #e8eaed;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://lh3.googleusercontent.com/a/ACg8ocIkMlDotkGP_wgoJijomZIX2yROOcdmTVuLCcKjDrb3uesZRPM" 
                 alt="Data Overseas Logo" class="logo">
            <div class="header-content">
                <div class="company-name">Data Overseas</div>
                <h1><span class="material-icons" style="vertical-align: middle; margin-right: 30px;">visibility</span>Vanguard</h1>
                <p>Sistema de Detecção SSD com IA</p>
            </div>
        </div>

        <div class="main-content">
            <div class="control-panel">
                <div class="section">
                    <h3><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">psychology</span>Modelo de IA</h3>
                    <div class="form-group">
                        <label for="model-select">Escolha o Modelo:</label>
                        <select id="model-select">
                            <option value="1">Open-Treinado (Simples)</option>
                            <option value="2" selected>Overseas-Vo5 (Óleo)</option>
                            <option value="3">Overseas-To9 (Resíduos)</option>
                            <option value="4">Open-Treinado (Seg-4K)</option>
                        </select>
                    </div>
                    <div class="form-group" id="confidence-group">
                        <label for="confidence-slider">Confiança: <span id="confidence-value">50%</span></label>
                        <input type="range" id="confidence-slider" min="1" max="99" value="50">
                    </div>
                    <button class="btn-primary" onclick="loadModel()"><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">download</span>Carregar Modelo</button>
                </div>

                <div class="section">
                    <h3><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">videocam</span>Fonte de Vídeo</h3>
                    <div class="form-group">
                        <label for="camera-select">Escolha a Câmera:</label>
                        <select id="camera-select" onchange="toggleIPInput()">
                            <option value="0">Câmera Principal</option>
                            <option value="1">Webcam USB</option>
                            <option value="2">Câmera IP</option>
                        </select>
                    </div>
                    <div class="form-group hidden" id="ip-group">
                        <label for="ip-input">Endereço IP:</label>
                        <input type="text" id="ip-input" placeholder="192.168.1.64">
                    </div>
                    <div class="form-group hidden" id="fps-group">
                        <label for="fps-slider">FPS da Câmera: <span id="fps-value">30</span></label>
                        <input type="range" id="fps-slider" min="1" max="60" value="30">
                        <div style="font-size: 0.9em; opacity: 0.7; margin-top: 5px;">
                            Menor FPS = menor uso de banda/processamento
                        </div>
                    </div>
                    <button class="btn-primary" onclick="setupCamera()"><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">settings</span>Configurar Câmera</button>
                </div>

                <div class="section">
                    <h3><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">control_camera</span>Controles</h3>
                    <button class="btn-success" onclick="startDetection()"><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">play_arrow</span>Iniciar Detecção</button>
                    <button class="btn-danger" onclick="stopDetection()"><span class="material-icons" style="vertical-align: middle; margin-right: 8px;">stop</span>Parar Detecção</button>
                </div>

                <div id="status-messages"></div>
            </div>

            <div class="video-panel">
                <div class="video-container" onclick="toggleFullscreen()">
                    <button class="fullscreen-btn" onclick="event.stopPropagation(); toggleFullscreen()">
                        <span class="material-icons">fullscreen</span> Tela Cheia
                    </button>
                    <div id="video-placeholder" class="video-placeholder">
                        <span class="material-icons" style="font-size: 48px; margin-bottom: 10px;">videocam_off</span>
                        <div>Configure o modelo e a câmera para começar</div>
                    </div>
                    <img id="video-feed" class="video-feed hidden" alt="Sistema de Detecção Feed">
                </div>
                <div class="status info" style="margin-top: 15px;">
                    <div>Status: <span id="detection-status">Aguardando configuração</span></div>
                    <div style="font-size: 0.9em; opacity: 0.8; margin-top: 5px;">
                        Última atualização: <span id="last-update">--</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Fullscreen Modal -->
        <div id="fullscreen-modal" class="fullscreen-modal">
            <button class="close-fullscreen" onclick="closeFullscreen()"><span class="material-icons">close</span> Fechar</button>
            <img id="fullscreen-video" class="fullscreen-video" alt="Sistema de Detecção Fullscreen">
        </div>
    </div>

    <script>
        let detectionInterval = null;
        let isDetectionRunning = false;

        // Update confidence display
        document.getElementById('confidence-slider').addEventListener('input', function() {
            document.getElementById('confidence-value').textContent = this.value + '%';
        });

        // Update FPS display
        document.getElementById('fps-slider').addEventListener('input', function() {
            document.getElementById('fps-value').textContent = this.value;
        });

        // Toggle IP input visibility
        function toggleIPInput() {
            const cameraSelect = document.getElementById('camera-select');
            const ipGroup = document.getElementById('ip-group');
            const fpsGroup = document.getElementById('fps-group');
            
            if (cameraSelect.value === '2') {
                ipGroup.classList.remove('hidden');
                fpsGroup.classList.remove('hidden');
            } else {
                ipGroup.classList.add('hidden');
                fpsGroup.classList.add('hidden');
            }
        }

        // Update confidence group visibility
        document.getElementById('model-select').addEventListener('change', function() {
            const confidenceGroup = document.getElementById('confidence-group');
            if (this.value === '4') {
                confidenceGroup.classList.add('hidden');
            } else {
                confidenceGroup.classList.remove('hidden');
            }
        });

        function showStatus(message, type = 'info', duration = 5000) {
            const statusContainer = document.getElementById('status-messages');
            const statusDiv = document.createElement('div');
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
            
            statusContainer.appendChild(statusDiv);
            
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, duration);
        }

        function updateDetectionStatus(status) {
            document.getElementById('detection-status').textContent = status;
        }

        function updateTimestamp() {
            const now = new Date();
            document.getElementById('last-update').textContent = now.toLocaleTimeString();
        }

        async function loadModel() {
            const modelSelect = document.getElementById('model-select');
            const confidenceSlider = document.getElementById('confidence-slider');
            
            const modelChoice = modelSelect.value;
            const confidence = parseInt(confidenceSlider.value);
            
            showStatus('Carregando modelo...', 'info');
            updateDetectionStatus('Carregando modelo...');
            
            try {
                const response = await fetch('/api/load_model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: modelChoice,
                        confidence: confidence
                    }),
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(result.message, 'success');
                    updateDetectionStatus('Modelo carregado');
                } else {
                    showStatus(result.message, 'error');
                    updateDetectionStatus('Erro ao carregar modelo');
                }
                updateTimestamp();
            } catch (error) {
                showStatus('Erro na comunicação com o servidor', 'error');
                updateDetectionStatus('Erro de conexão');
            }
        }

        async function setupCamera() {
            const cameraSelect = document.getElementById('camera-select');
            const ipInput = document.getElementById('ip-input');
            const fpsSlider = document.getElementById('fps-slider');
            
            const cameraOption = cameraSelect.value;
            const ipAddress = ipInput.value;
            const fps = parseInt(fpsSlider.value);
            
            showStatus('Configurando câmera...', 'info');
            updateDetectionStatus('Configurando câmera...');
            
            try {
                const response = await fetch('/api/setup_camera', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        camera: cameraOption,
                        ip_address: ipAddress,
                        fps: fps
                    }),
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(result.message, 'success');
                    updateDetectionStatus('Câmera configurada');
                } else {
                    showStatus(result.message, 'error');
                    updateDetectionStatus('Erro na câmera');
                }
                updateTimestamp();
            } catch (error) {
                showStatus('Erro na comunicação com o servidor', 'error');
                updateDetectionStatus('Erro de conexão');
            }
        }

        async function startDetection() {
            if (isDetectionRunning) {
                showStatus('Detecção já está rodando', 'info');
                return;
            }

            showStatus('Iniciando detecção...', 'info');
            updateDetectionStatus('Iniciando...');
            
            try {
                const response = await fetch('/api/start_detection', {
                    method: 'POST',
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Detecção iniciada com sucesso', 'success');
                    updateDetectionStatus('Detectando...');
                    isDetectionRunning = true;
                    startVideoFeed();
                } else {
                    showStatus(result.message, 'error');
                    updateDetectionStatus('Erro ao iniciar');
                }
                updateTimestamp();
            } catch (error) {
                showStatus('Erro na comunicação com o servidor', 'error');
                updateDetectionStatus('Erro de conexão');
            }
        }

        async function stopDetection() {
            if (!isDetectionRunning) {
                showStatus('Detecção não está rodando', 'info');
                return;
            }

            showStatus('Parando detecção...', 'info');
            updateDetectionStatus('Parando...');
            
            try {
                const response = await fetch('/api/stop_detection', {
                    method: 'POST',
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Detecção parada', 'success');
                    updateDetectionStatus('Parado');
                    isDetectionRunning = false;
                    stopVideoFeed();
                } else {
                    showStatus(result.message, 'error');
                }
                updateTimestamp();
            } catch (error) {
                showStatus('Erro na comunicação com o servidor', 'error');
                updateDetectionStatus('Erro de conexão');
            }
        }

        function startVideoFeed() {
            if (detectionInterval) {
                clearInterval(detectionInterval);
            }
            
            detectionInterval = setInterval(updateFrame, 100); // 10 FPS display
        }

        function stopVideoFeed() {
            if (detectionInterval) {
                clearInterval(detectionInterval);
                detectionInterval = null;
            }
            
            const videoFeed = document.getElementById('video-feed');
            const videoPlaceholder = document.getElementById('video-placeholder');
            
            videoFeed.classList.add('hidden');
            videoPlaceholder.classList.remove('hidden');
            videoPlaceholder.textContent = 'Configure o modelo e a câmera para começar';
        }

        async function updateFrame() {
            if (!isDetectionRunning) return;
            
            try {
                const response = await fetch('/api/get_frame');
                const result = await response.json();
                
                if (result.frame) {
                    const videoFeed = document.getElementById('video-feed');
                    const videoPlaceholder = document.getElementById('video-placeholder');
                    const fullscreenVideo = document.getElementById('fullscreen-video');
                    
                    const imageData = 'data:image/jpeg;base64,' + result.frame;
                    videoFeed.src = imageData;
                    videoFeed.classList.remove('hidden');
                    videoPlaceholder.classList.add('hidden');
                    
                    // Update fullscreen image if modal is open
                    if (document.getElementById('fullscreen-modal').classList.contains('active')) {
                        fullscreenVideo.src = imageData;
                    }
                    
                    updateTimestamp();
                } else {
                    // No frame available
                    if (isDetectionRunning) {
                        updateDetectionStatus('Aguardando frame...');
                    }
                }
            } catch (error) {
                console.error('Error updating frame:', error);
                if (isDetectionRunning) {
                    updateDetectionStatus('Erro ao obter frame');
                }
            }
        }

        // Fullscreen functionality
        function toggleFullscreen() {
            const modal = document.getElementById('fullscreen-modal');
            const videoFeed = document.getElementById('video-feed');
            const fullscreenVideo = document.getElementById('fullscreen-video');
            
            if (!videoFeed.classList.contains('hidden')) {
                fullscreenVideo.src = videoFeed.src;
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }

        function closeFullscreen() {
            const modal = document.getElementById('fullscreen-modal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        // Close fullscreen with ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeFullscreen();
            }
        });

        // Initialize
        toggleIPInput();
        updateTimestamp();
    </script>
</body>
</html>'''
    # Write HTML template
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("📱 Interface disponível em: http://localhost:5000")
    
    # Adicionar abertura automática do navegador
    webbrowser.open('http://localhost:5000')
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)