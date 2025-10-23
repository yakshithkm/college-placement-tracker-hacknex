🎓 College Placement Tracker

A Flask-based web application that helps students and administrators track placement readiness efficiently.

🚀 Features
-Student registration and logi
-Resume analysis and automatic skill scorin
-Aptitude and certification trackin
-Real-time readiness score visualizatio
-Admin dashboard with search, top performers, and CSV expor
-Responsive and modern UI

🧰 Tech Stack
-Frontend: HTML, CSS, JavaScript (Chart.js)
-Backend: Python (Flask Framework)
-Database: SQLite
-Libraries: PyPDF2, python-docx

⚙️ Setup Instructions
# 1. Clone the repository
git clone https://github.com/yakshithkm/college-placement-tracker-hacknex.git

# 2. Navigate to the project folder
cd college-placement-tracker-hacknex

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask app
python app.py

Open your browser and go to: http://localhost:5000/

📂 Folder Structure
college-placement-tracker/
│
├── app.py
├── database.db
├── requirements.txt
├── README.md
│
├── static/
│   ├── style.css
│   └── bg.jpg
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin_login.html
│   └── admin_dashboard.html
│
└── uploads/

🧮 Readiness Formula
Readiness Score = (Resume Score × 0.4) + (Aptitude Avg × 0.4) + (Certifications × 10)

📊 Admin Features
-View all student readiness data
-Search and filter results
-Export reports as CSV
-View top performers

💡 Future Enhancements
-AI-powered resume evaluation
-Company-specific placement predictions
-Automated email alerts and reports
-Integration with LinkedIn and career APIs

📘 Developed For
HackNex 2025 — College Placement Tracker
Department of Computer Science & Engineering
KVG College of Engineering, Sullia, D.K, Karnataka.