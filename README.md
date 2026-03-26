# AeroPath AI 🚦🚑
**Urban Traffic Intelligence Command & Emergency Vehicle Preemption**

AeroPath AI is an intelligent, multimodal smart mobility command center designed to optimize urban traffic flow using real-time IoT telemetry, predictive machine learning, and artificial intelligence.

## 🌟 Key Features
* **Predictive ML Routing:** Anticipates traffic spikes using a Machine Learning model (RandomForest) and instantly reroutes civilians to maintain grid equilibrium.
* **Emergency Vehicle Preemption (EVP):** Authorized ambulance drivers broadcast live GPS coordinates, triggering a priority "Green Wave" to automatically coordinate traffic signals and clear their path.
* **Conversational AI Command:** An embedded chatbot (LangChain / Ollama) fully aware of the live physical terrain for rapid decision-making using natural language.
* **Secure Access / RBAC:** Firebase Authentication securely handles Multi-Tier Access, distinguishing seamlessly between Private Civilian Users and Emergency Personnel.

## 🛠️ Technology Stack
* **Frontend:** HTML5, CSS3, Vanilla JS, Leaflet.js (Mapping), OSRM (Routing)
* **Backend:** Python 3, Flask / FastAPI, Threading
* **Machine Learning:** Scikit-Learn (`RandomForestClassifier`), Pandas, NumPy
* **AI Integration:** LangChain, Ollama
* **Authentication & Identity:** Google Firebase (Client SDK & Admin SDK)
* **External Services:** Open-Meteo (Weather API), Nominatim Geocoder

## 🗂️ Project Structure
```text
AI-TITANS/
│
├── aeropath/
│   ├── backend/
│   │   ├── app.py                # Main backend server & routing
│   │   ├── firebase_auth.py      # Secure Firebase token verification
│   │   ├── predict.py            # ML prediction loader
│   │   ├── green_wave.py         # EVP / Ambulance priority logic
│   │   ├── chatbot.py            # Langchain AI chatbot setup
│   │   ├── alerts.py             # Alert system
│   │   ├── requirements.txt      # Python dependencies
│   │   └── firebase-service-account.json # (Ignored) Firebase credentials
│   │
│   └── frontend/
│       ├── login.html            # Firebase Auth UI (Sign In / Sign Up)
│       ├── index.html            # Live Map / Routing UI
│       ├── dashboard.html        # Telemetry / Analytics UI
│       └── style.css             # UI styling
│
├── README.md                     # Project documentation
└── .gitignore                    # Ignored files & secrets
```

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.9+ installed
* A Firebase Project with Email/Password Authentication enabled.

### 2. Configure Firebase
1. Navigate to the Firebase Console and copy your **Web App Config**.
2. Paste the config into `aeropath/frontend/login.html`, `index.html`, and `dashboard.html`.
3. Generate a **Service Account Private Key** (JSON) from Firebase Project Settings.
4. Save the key as `aeropath/backend/firebase-service-account.json`.

### 3. Install Backend Dependencies
Open a terminal in the `aeropath/backend` folder and run:
```bash
pip install -r requirements.txt
```

### 4. Run the Server
Start the simulation and API server:
```bash
cd aeropath/backend
python app.py
```

### 5. Access the Application
Open your web browser and navigate to:
```text
http://localhost:5000/
```
From here, you can sign up as a Private User or an Ambulance Driver.
