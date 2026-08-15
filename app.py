import os 
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from datetime import datetime
import secrets

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')

print(f"API Key loaded: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "No API key found!")
print(f"API Key length: {len(GEMINI_API_KEY)}")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = secrets.token_hex(16)  # For session management

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyBTamGGIA5q9PAhWLxh_igdVQopcUbcdcU')
genai.configure(api_key=GEMINI_API_KEY)

# System prompt for mental health support
SYSTEM_PROMPT = """You are WellMind AI, a compassionate mental health support companion. 

Your personality:
- Warm, empathetic, and non-judgmental
- Supportive but realistic
- You validate feelings before offering suggestions
- You keep responses natural and conversational (2-4 sentences usually)

Your approach:
- Listen actively and acknowledge emotions
- Ask gentle follow-up questions to understand better
- Offer coping strategies when appropriate
- Encourage professional help for serious concerns
- Never diagnose or replace therapy
- Be genuinely caring and human-like

Crisis protocol:
- If user mentions suicide, self-harm, or crisis → immediately show concern and strongly encourage crisis helpline
- Be direct but caring: "I'm really concerned about you. Please reach out to a crisis helpline immediately..."

Remember: You're a supportive friend, not a therapist. Be conversational and vary your responses naturally."""

# Store chat sessions with full context
chat_sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_session_id():
    """Get or create a unique session ID for the user"""
    if 'chat_session_id' not in session:
        session['chat_session_id'] = secrets.token_hex(8)
    return session['chat_session_id']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/medical-imaging')
def medical_imaging():
    return render_template('medical_imaging.html')

@app.route('/mental-health')
def mental_health():
    return render_template('mental_health.html')

@app.route('/outbreak-prediction')
def outbreak_prediction():
    return render_template('outbreak_prediction.html')

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    scan_type = request.form.get('scan_type', 'x-ray')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # TODO: Implement actual machine learning model here
        result = {
            'success': True,
            'scan_type': scan_type, 
            'prediction': 'Normal' if scan_type == 'xray' else 'No abnormalities detected',
            'confidence': 0.92,
            'details': 'This is a placeholder result. Integrate your trained model here.'
        }
        return jsonify(result)

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Use this model - it's available!
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # System prompt
        prompt = f"""You are WellMind AI, a compassionate mental health support assistant. 
        Provide brief, empathetic responses (2-3 sentences). Validate feelings and offer gentle support.
        
        User says: {user_message}
        
        Respond with empathy and support:"""

        # Generate response
        response = model.generate_content(prompt)
        ai_response = response.text

        # Detect crisis keywords
        crisis_keywords = ['suicide', 'kill myself', 'end my life', 'self-harm', 'hurt myself', 'crisis']
        show_crisis_resources = any(keyword in user_message.lower() for keyword in crisis_keywords)

        # Prepare response
        result = {'response': ai_response, 'resources': []}

        if show_crisis_resources:
            result['resources'] = [
                {'name': '🆘 National Suicide Prevention', 'contact': '988'},
                {'name': '📞 NIMHANS Helpline', 'contact': '080-46110007'},
                {'name': '🤝 Vandrevala Foundation', 'contact': '1860-2662-345'},
                {'name': '💚 iCall', 'contact': '9152987821'}
            ]
            result['urgent'] = True
        else:
            result['resources'] = [
                {'name': '📞 NIMHANS Helpline', 'contact': '080-46110007'},
                {'name': '🤝 Vandrevala Foundation', 'contact': '1860-2662-345'},
                {'name': '💚 iCall', 'contact': '9152987821'}
            ]

        return jsonify(result)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'response': "I'm here to support you, but I encountered a technical issue. Please know that your feelings are valid.",
            'resources': [
                {'name': '📞 NIMHANS Helpline', 'contact': '080-46110007'},
                {'name': '🤝 Vandrevala Foundation', 'contact': '1860-2662-345'},
                {'name': '💚 iCall', 'contact': '9152987821'}
            ]
        })

@app.route('/reset-chat', methods=['POST'])
def reset_chat():
    """Reset the chat session"""
    session_id = get_session_id()
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    session.pop('chat_session_id', None)
    return jsonify({'success': True, 'message': 'Chat session reset'})

@app.route('/predict-outbreak', methods=['POST'])
def predict_outbreak():
    data = request.get_json()
    disease = data.get('disease', '')
    location = data.get('location', '')

    # TODO: Implement actual prediction model here
    result = {
        'disease': disease,
        'location': location,
        'risk_level': 'Moderate',
        'predicted_cases': 150,
        'peak_period': 'August-September 2025',
        'recommendations': [
            'Increase mosquito control measures',
            'Conduct awareness campaigns',
            'Ensure adequate medical supplies'
        ]
    }
    return jsonify(result)


@app.route('/test-models')
def test_models():
    try:
        models = genai.list_models()
        model_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        return jsonify({'available_models': model_names})
    except Exception as e:
        return jsonify({'error': str(e)})
    
    
if __name__ == '__main__':
    app.run(debug=True)
