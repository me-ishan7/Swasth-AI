from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Production settings
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False

# Helper to resolve model path with fallback to models/ml/
def _model_path(filename: str) -> str:
    base_paths = [
        Path(__file__).parent / "models" / filename,
        Path(__file__).parent / "models" / "ml" / filename,
    ]
    for p in base_paths:
        if p.exists():
            return str(p)
    # Last resort: try relative working dir
    alt_paths = [
        Path("models") / filename,
        Path("models") / "ml" / filename,
    ]
    for p in alt_paths:
        if p.exists():
            return str(p)
    raise FileNotFoundError(f"Model file not found for {filename} in {base_paths + alt_paths}")

# Load ML models
diabetes_model = joblib.load(_model_path("diabetes_model.pkl"))
heart_model = joblib.load(_model_path("heart_disease_model.pkl"))
parkinsons_model = joblib.load(_model_path("parkinsons_model.pkl"))

# -------------------------
# Home route
# -------------------------
@app.route("/")
def home():
    return "ML Backend is running 🚀"

# -------------------------
# Diabetes prediction
# -------------------------
@app.route("/predict/diabetes", methods=["POST"])
def predict_diabetes():
    try:
        data = request.get_json()

        # Expected features
        expected_features = [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ]

        # Check missing features
        missing = [f for f in expected_features if f not in data]
        if missing:
            return jsonify({"error": f"Missing features: {missing}"}), 400

        # Prepare features in correct order
        features = np.array([[data[f] for f in expected_features]])

        prediction = diabetes_model.predict(features)
        result = "Diabetic" if prediction[0] == 1 else "Not Diabetic"
        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# Heart disease prediction
# -------------------------
@app.route("/predict/heart", methods=["POST"])
def predict_heart():
    try:
        data = request.get_json()

        # List all 13 features expected by your heart disease model
        expected_features = [
            "age", "sex", "cp", "trestbps", "chol",
            "fbs", "restecg", "thalach", "exang",
            "oldpeak", "slope", "ca", "thal"
        ]

        missing = [f for f in expected_features if f not in data]
        if missing:
            return jsonify({"error": f"Missing features: {missing}"}), 400

        features = np.array([[data[f] for f in expected_features]])
        prediction = heart_model.predict(features)
        result = "Heart Disease" if prediction[0] == 1 else "No Heart Disease"
        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# Parkinsons prediction
# -------------------------
@app.route("/predict/parkinsons", methods=["POST"])
def predict_parkinsons():
    try:
        data = request.get_json()

        # Replace these with the actual features your Parkinsons model expects
        expected_features = [
            "feature1", "feature2", "feature3"  # Add all features
        ]

        missing = [f for f in expected_features if f not in data]
        if missing:
            return jsonify({"error": f"Missing features: {missing}"}), 400

        features = np.array([[data[f] for f in expected_features]])
        prediction = parkinsons_model.predict(features)
        result = "Parkinsons" if prediction[0] == 1 else "No Parkinsons"
        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from utils.symptom_extractor import SymptomExtractor
from utils.doctor_finder import DoctorFinder
import pytesseract
from PIL import Image
import os
from faster_whisper import WhisperModel
import tempfile

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init components
extractor = SymptomExtractor("data/symptom_disease.csv")
finder = DoctorFinder("data/doctor_data.json")

# Use tiny model for whisper to keep resource usage low; faster-whisper will auto-download
whisper_model = WhisperModel("tiny", device="cpu")  # change device to "cuda" if you have GPU

@app.post("/analyze_text")
async def analyze_text(text: str = Form(...), lat: float = Form(None), lon: float = Form(None)):
    symptoms = extractor.extract_symptoms_from_text(text)
    diagnosis = extractor.diagnose(symptoms)
    # find doctors if location provided
    doctors = []
    if lat is not None and lon is not None:
        doctors = finder.find_nearest(lat, lon)
    return {"input_type": "text", "text": text, "symptoms": symptoms, "diagnosis": diagnosis, "nearest_doctors": doctors}

@app.post("/analyze_doc")
async def analyze_doc(file: UploadFile = File(...), lat: float = Form(None), lon: float = Form(None)):
    # expects an image (png/jpg) or PDF (PDF handling not implemented; convert to image offline)
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(contents)
    tmp.flush()
    tmp.close()
    try:
        img = Image.open(tmp.name)
        text = pytesseract.image_to_string(img)
    except Exception as e:
        text = ""
    finally:
        os.unlink(tmp.name)
    symptoms = extractor.extract_symptoms_from_text(text)
    diagnosis = extractor.diagnose(symptoms)
    doctors = []
    if lat is not None and lon is not None:
        doctors = finder.find_nearest(lat, lon)
    return {"input_type": "document", "ocr_text": text, "symptoms": symptoms, "diagnosis": diagnosis, "nearest_doctors": doctors}

@app.post("/analyze_voice")
async def analyze_voice(file: UploadFile = File(...), lat: float = Form(None), lon: float = Form(None)):
    # save file
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(contents)
    tmp.flush()
    tmp.close()
    # transcribe using faster-whisper
    segments, info = whisper_model.transcribe(tmp.name, beam_size=5)
    text = " ".join([seg.text for seg in segments])
    os.unlink(tmp.name)
    symptoms = extractor.extract_symptoms_from_text(text)
    diagnosis = extractor.diagnose(symptoms)
    doctors = []
    if lat is not None and lon is not None:
        doctors = finder.find_nearest(lat, lon)
    return {"input_type": "voice", "transcript": text, "symptoms": symptoms, "diagnosis": diagnosis, "nearest_doctors": doctors}
