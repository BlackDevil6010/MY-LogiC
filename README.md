# Contract Clause Extraction & Risk Flags System

A production-grade system for analyzing legal contracts for risk clauses using Legal BERT.

## Features
- **Contract Upload**: Drag & Drop PDF, DOCX, and TXT files.
- **Clause Extraction**: Automatic segmentation of contracts into logical clauses.
- **Risk Analysis**: Powered by HuggingFace Transformers and `nlpaueb/legal-bert-base-uncased`.
- **Dashboard**: Beautiful Glassmorphism UI with real-time analytics.

## Tech Stack
- **Backend**: Python 3.11+, Flask, PostgreSQL, SQLAlchemy, Transformers, PyTorch, PyPDF2
- **Frontend**: HTML5, Vanilla JS, CSS3 (Glassmorphism), Chart.js

## Run Locally

### 1. Prerequisites
- Python 3.11+
- PostgreSQL server running locally on port 5432
- Node.js/npm (optional, for frontend serving if you prefer, but you can just open `index.html`)

### 2. Database Setup
Create the database:
```bash
psql -U postgres -f init_db.sql
```
*(adjust your connection parameters as needed)*

### 3. Backend Setup
Navigate to the `backend` directory (if you run from root, adjust the path):
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 4. Run the Backend
Set environment variables if your DB credentials differ from the default (`postgresql://postgres:postgres@localhost:5432/contract_analyzer`):
```bash
export DATABASE_URL="postgresql://youruser:yourpassword@localhost:5432/contract_analyzer"
```

Start the Flask server:
```bash
python -m backend.app
```
*Note: On the first run, the Legal BERT model will be downloaded (approx. 400MB) which may take a few minutes.*

### 5. Run the Frontend
Simply open `frontend/index.html` in your web browser. 
For the best experience, run a local static server:
```bash
cd frontend
python -m http.server 8000
```
Then navigate to `http://localhost:8000` in your browser.

## Architecture Decisions
- **App Factory Pattern**: The Flask app uses the application factory pattern (`create_app`) for better testing and modularity.
- **Singleton Model Loading**: The `RiskAnalyzer` preloads the BERT model at startup to avoid reloading it on every request, which is crucial for reasonable API latency.
- **Clean Architecture**: Services (`clause_extractor.py`, `risk_analyzer.py`), utilities (`file_parser.py`), and routing (`contract_routes.py`) are strictly separated.
- **Vanilla JS**: The frontend avoids heavy frameworks (React/Vue) to meet the requirement strictly relying on ES6 modularity and lightweight dom updates, while delivering a highly polished aesthetic.


#OUTPUT SCREENSHOT

<img width="1919" height="978" alt="image" src="https://github.com/user-attachments/assets/b39e885c-9de1-403f-a560-7bce5974d9fd" />



<img width="1919" height="996" alt="image" src="https://github.com/user-attachments/assets/6e70333c-e13b-482c-b756-ef33694ce233" />


<img width="1916" height="985" alt="image" src="https://github.com/user-attachments/assets/090a96c8-6c8f-4985-bdcf-6e32221bcbdf" />


<img width="1916" height="987" alt="image" src="https://github.com/user-attachments/assets/2b52085e-c517-4b68-b205-9e1083e8c744" />


<img width="1915" height="977" alt="image" src="https://github.com/user-attachments/assets/ae796b25-875a-41d1-a49b-5b737198da71" />


<img width="1917" height="986" alt="image" src="https://github.com/user-attachments/assets/d70cd627-72e2-4144-9ede-d016662cf7ea" />

