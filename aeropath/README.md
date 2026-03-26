# AeroPath Complete Setup

## Setup Instructions

1. Install Python dependencies:
   ```bash
   cd aeropath
   pip install -r requirements.txt
   ```

2. Generate the dataset & train the ML model:
   ```bash
   cd aeropath
   python data_generator.py
   python predict.py
   ```

3. Start the Flask Application:
   ```bash
   cd aeropath
   python app.py
   ```

4. View the Dashboard:
   Open your web browser and navigate to: **http://localhost:5000**
