
# 🤖 Smart Resume Reviewer

An **AI-powered resume analysis and optimization tool** that provides personalized, actionable feedback to help you tailor your resume for your target job role.  

Supports PDF upload and text paste inputs, offers optional job description-based targeted analysis, and generates professional reports with clear scoring and strategic recommendations.

---

## ✨ Features

- 📄 Upload your resume as a PDF or paste plain text.  
- 🎯 Optional: Paste a specific job description for targeted analysis.  
- 🤖 AI-powered semantic analysis for ATS compatibility and skill alignment.  
- ⭐ Professional scoring on:
  - Technical Skills  
  - Experience  
  - Achievements  
  - Education  
  - ATS Optimization  
  - Presentation  
- 📊 Visual star ratings and progress bars for clarity.  
- 🛠️ Actionable **priority improvement plans** to boost your resume.  
- 📥 Export detailed AI-generated reports.  
- ⚠️ Transparent **AI usage disclaimer** for user awareness.  

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.8+  
- Git installed  
- A free API key from [Groq Console](https://console.groq.com/)  

---

### ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/smart-resume-reviewer.git
   cd smart-resume-reviewer

2. **Create and activate a virtual environment:**

   #### macOS/Linux

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   #### Windows (PowerShell)

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   #### Windows (CMD)

   ```cmd
   python -m venv venv
   .\venv\Scripts\activate.bat
   ```

3. **Install dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and add your API key:

   ```bash
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```
   Or in terminal:
   ```bash
   echo "GROQ_API_KEY=your_actual_groq_api_key_here" > .env
   ```

---

## ▶️ Running the Application

Start the app with:

```bash
streamlit run streamlit_app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📝 Usage

1. Select your **target job role**.
2. Upload a **PDF resume** or paste your resume text.
3. (Optional) Paste a **job description** for more personalized analysis.
4. Click **Generate AI-Powered Resume Analysis**.
5. Review your **personalized report** with scores and actionable insights.
6. Download the **detailed report** if desired.

---

## 📊 Understanding the Report

* **ATS Compatibility** → Semantic similarity between resume & job description.
* **Technical Skills** → Alignment of skills with role requirements.
* **Experience** → Work history relevance.
* **Achievements** → Quantified impacts and results.
* **Education** → Relevance of academic background.
* **Presentation** → Formatting, clarity, and layout quality.

---

## 👥 Contributors

This project was collaboratively developed by:

* [San Maria Joby](https://github.com/SanMaria28)
* [Joel Jacob Roji](https://github.com/JoelJacobRoji)
* [Darain Brit A](https://github.com/Darain-Brit-A)
* [Darren Samuel D'cruz](https://github.com/Darren-Dcruz)
  
---

## ☁️ Deployment Options

* Deploy on:

  * [Streamlit Community Cloud](https://smartresumereviewer-5crsutzysp2jzvyanvkd7h.streamlit.app/)

## Submission Report
* Links:
  
  * [Google Drive Link](https://drive.google.com/drive/folders/19f86xZsWnPxChjbc1QsEmXIqj-lwGKT3?usp=sharing)
  * [Demo Video URL](https://docs.google.com/videos/d/1z7SanLyHeTatoa20yFn0_YCvYgGhdbFPK8cWyqs_f8A/edit?usp=sharing)
  * [Presentation URL](https://drive.google.com/file/d/1C-e3V2KxWkVmRCkHVfGrigZT1E81zmPB/view?usp=sharing)
   
## 📜 License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.



