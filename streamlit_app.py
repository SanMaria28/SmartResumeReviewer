# Smart Resume Reviewer - Complete AI-Powered Resume Analysis Tool
# Clean version - Removed boxes and metrics display

import streamlit as st
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
import re
from dotenv import load_dotenv
import os
import tempfile
from datetime import datetime
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Page configuration
st.set_page_config(
    page_title="🤖 Smart Resume Reviewer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI - REMOVED WHITE BARS AND BOXES
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #e3f2fd, #f0f2f6);
        border-radius: 10px;
    }
    .score-container {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #1f77b4;
    }
    .upgrade-section {
        background-color: #e8f4fd;
        padding: 2rem;
        border-radius: 15px;
        border-left: 8px solid #1f77b4;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .disclaimer-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #6c757d;
        margin: 2rem 0;
        font-size: 0.9em;
        color: #6c757d;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    
    /* Hide Streamlit default elements that create white bars */
    .stFileUploader > div:first-child {
        display: none;
    }
    
    /* Clean up file uploader styling */
    .stFileUploader {
        background-color: transparent;
    }
    
    /* Remove extra spacing and borders */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Session States
session_vars = ['form_submitted', 'resume', 'resume_filename', 'selected_job_role', 'custom_job_desc', 'analysis_results']
for var in session_vars:
    if var not in st.session_state:
        st.session_state[var] = "" if var != 'form_submitted' else False

# Comprehensive job roles database
JOB_ROLES = {
    "Data Scientist": {
        "description": "Analyzes complex datasets to extract actionable insights, builds predictive models using machine learning algorithms, and creates data-driven solutions to solve business problems.",
        "key_skills": ["Python", "R", "SQL", "Machine Learning", "Statistics", "Data Visualization", "Pandas", "NumPy", "Scikit-learn", "TensorFlow"],
        "experience_focus": ["Model Development", "Data Analysis", "Statistical Modeling", "Feature Engineering", "A/B Testing"],
        "industry_keywords": ["predictive modeling", "data mining", "neural networks", "deep learning", "data science", "analytics"]
    },
    "Software Engineer": {
        "description": "Designs, develops, tests, and maintains software applications and systems using various programming languages and technologies.",
        "key_skills": ["Java", "Python", "JavaScript", "C++", "React", "Node.js", "SQL", "Git", "Docker", "AWS"],
        "experience_focus": ["Software Development", "Code Review", "System Architecture", "API Development", "Testing"],
        "industry_keywords": ["software development", "programming", "coding", "debugging", "version control", "agile"]
    },
    "Product Manager": {
        "description": "Drives product strategy, vision, and roadmap development while collaborating with cross-functional teams.",
        "key_skills": ["Product Strategy", "Market Research", "User Experience Design", "Data Analysis", "Project Management", "Stakeholder Management"],
        "experience_focus": ["Product Roadmapping", "Feature Prioritization", "User Research", "Market Analysis"],
        "industry_keywords": ["product management", "product strategy", "user stories", "product roadmap", "market research"]
    },
    "Digital Marketing Specialist": {
        "description": "Develops and executes comprehensive digital marketing strategies across multiple channels.",
        "key_skills": ["SEO/SEM", "Google Analytics", "Social Media Marketing", "Content Marketing", "Email Marketing", "PPC Advertising"],
        "experience_focus": ["Campaign Management", "Content Creation", "Social Media Strategy", "Performance Analysis"],
        "industry_keywords": ["digital marketing", "SEO", "SEM", "social media", "content marketing", "conversion rates"]
    },
    "Business Analyst": {
        "description": "Analyzes business processes and works with stakeholders to implement data-driven solutions.",
        "key_skills": ["Business Analysis", "Requirements Gathering", "Process Mapping", "SQL", "Excel", "Power BI"],
        "experience_focus": ["Process Analysis", "Requirements Documentation", "Data Analysis", "Process Improvement"],
        "industry_keywords": ["business analysis", "process improvement", "requirements gathering", "business intelligence"]
    },
    "UI/UX Designer": {
        "description": "Creates intuitive and engaging user interfaces and experiences for digital products.",
        "key_skills": ["User Research", "Wireframing", "Prototyping", "Visual Design", "Figma", "Sketch", "Adobe Creative Suite", "User Testing"],
        "experience_focus": ["User Experience Design", "User Interface Design", "User Research", "Prototyping", "Usability Testing"],
        "industry_keywords": ["UI design", "UX design", "user experience", "user interface", "wireframing", "prototyping"]
    },
    "DevOps Engineer": {
        "description": "Bridges the gap between development and operations teams by implementing CI/CD pipelines and managing infrastructure.",
        "key_skills": ["CI/CD", "Docker", "Kubernetes", "AWS/Azure/GCP", "Terraform", "Jenkins", "Git", "Linux"],
        "experience_focus": ["Infrastructure Management", "Automation", "CI/CD Pipeline Development", "Cloud Architecture"],
        "industry_keywords": ["devops", "CI/CD", "infrastructure", "automation", "cloud computing", "containerization"]
    },
    "Sales Representative": {
        "description": "Builds and maintains relationships with prospects and customers to drive revenue growth.",
        "key_skills": ["Relationship Building", "Negotiation", "CRM Systems", "Lead Generation", "Sales Process", "Communication"],
        "experience_focus": ["Lead Generation", "Customer Relationship Management", "Sales Presentations", "Contract Negotiation"],
        "industry_keywords": ["sales", "business development", "lead generation", "customer acquisition", "revenue growth"]
    },
    "Financial Analyst": {
        "description": "Analyzes financial data and creates comprehensive financial models to support strategic business decisions.",
        "key_skills": ["Financial Modeling", "Excel", "Financial Analysis", "Forecasting", "Budgeting", "Valuation", "SQL"],
        "experience_focus": ["Financial Modeling", "Budget Analysis", "Forecasting", "Investment Analysis", "Financial Reporting"],
        "industry_keywords": ["financial analysis", "financial modeling", "budgeting", "forecasting", "investment analysis"]
    },
    "Human Resources Manager": {
        "description": "Manages comprehensive HR functions including talent acquisition and employee relations.",
        "key_skills": ["Recruitment", "Performance Management", "Employee Relations", "HR Policies", "Training & Development", "HRIS"],
        "experience_focus": ["Talent Acquisition", "Employee Development", "Performance Management", "HR Policy Development"],
        "industry_keywords": ["human resources", "talent acquisition", "employee relations", "performance management"]
    },
    "Content Writer": {
        "description": "Creates compelling, engaging, and SEO-optimized written content across various platforms.",
        "key_skills": ["Content Writing", "SEO Writing", "Research", "Editing", "Social Media Content", "Content Strategy"],
        "experience_focus": ["Content Creation", "Content Strategy", "SEO Optimization", "Editorial Management"],
        "industry_keywords": ["content writing", "content marketing", "SEO writing", "copywriting", "content strategy"]
    },
    "Custom Role": {
        "description": "Enter your own job description below",
        "key_skills": [],
        "experience_focus": [],
        "industry_keywords": []
    }
}

# Title and Header
st.markdown("""
<div class="main-header">
    <h1>🤖 Smart Resume Reviewer</h1>
    <h3>AI-Powered Resume Analysis & Comprehensive Upgrade Recommendations</h3>
    <p>Get detailed, personalized feedback to optimize your resume for any job role</p>
</div>
""", unsafe_allow_html=True)

# Functions
@st.cache_data
def load_similarity_model():
    """Load the sentence transformer model with caching"""
    try:
        return SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    except Exception as e:
        st.error(f"Error loading similarity model: {str(e)}")
        return None

def extract_pdf_text(uploaded_file):
    """Extract text from uploaded PDF file"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        extracted_text = extract_text(tmp_file_path)
        os.unlink(tmp_file_path)
        
        if not extracted_text.strip():
            return "Warning: No text could be extracted from this PDF. Please ensure your PDF contains selectable text."
        
        return extracted_text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return "Could not extract text from the PDF file. Please try with a different PDF."

def calculate_similarity_bert(text1, text2):
    """Calculate semantic similarity between resume and job description"""
    try:
        model = load_similarity_model()
        if model is None:
            return 0.0
        
        embeddings1 = model.encode([text1])
        embeddings2 = model.encode([text2])
        
        similarity = cosine_similarity(embeddings1, embeddings2)[0][0]
        return round(similarity, 3)
    except Exception as e:
        st.error(f"Error calculating similarity: {str(e)}")
        return 0.0

def generate_comprehensive_report(resume, job_role, custom_job_desc=""):
    """Generate CONCISE, CREATIVE analysis report using Groq LLM"""
    try:
        if not api_key:
            return "❌ Error: GROQ_API_KEY not found. Please check your .env file."
        
        client = Groq(api_key=api_key)
        
        # Get job role context
        role_context = ""
        if job_role in JOB_ROLES and job_role != "Custom Role":
            role_info = JOB_ROLES[job_role]
            role_context = f"""
**🎯 TARGET ROLE**: {job_role}
**Key Skills**: {', '.join(role_info['key_skills'][:8])}
**Focus Areas**: {', '.join(role_info.get('experience_focus', [])[:4])}
"""

        # Determine which job description to use
        if custom_job_desc.strip():
            # Use custom job description if provided
            job_desc = custom_job_desc.strip()
            job_source = "custom job description provided by user"
        elif job_role in JOB_ROLES and job_role != "Custom Role":
            # Use standard job description
            role_info = JOB_ROLES[job_role]
            job_desc = f"""We are seeking a skilled {job_role} with 3+ years experience in: {', '.join(role_info['key_skills'][:8])}. Strong proficiency in: {', '.join(role_info.get('experience_focus', [])[:5])}."""
            job_source = f"standard {job_role} requirements"
        else:
            job_desc = "General professional role requiring relevant experience and skills."
            job_source = "general professional requirements"

        prompt = f"""
You are an expert AI Career Consultant. Create a CONCISE, PROFESSIONAL resume analysis report with creative visual elements. Keep it focused and actionable - maximum 800 words total.

{role_context}

# 🎯 RESUME ANALYSIS REPORT
**Target Position**: {job_role} | **Analysis Date**: {datetime.now().strftime('%B %d, %Y')}

---

## 📊 EXECUTIVE SCORECARD

**OVERALL MATCH**: [X]%

```
PERFORMANCE BREAKDOWN:
├── Technical Skills    : [X]/10 ⭐⭐⭐⭐⭐⭐⭐⭐⚪⚪
├── Experience Match   : [X]/10 ⭐⭐⭐⭐⭐⭐⭐⚪⚪⚪
├── Achievement Impact : [X]/10 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⚪
├── ATS Compatibility  : [X]/10 ⭐⭐⭐⭐⭐⭐⭐⭐⚪⚪
└── Professional Format: [X]/10 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
```

**🏆 COMPETITIVE POSITION**: [Strong Candidate/Needs Development/Excellent Match]

---

## 🔍 KEY FINDINGS

### ✅ STRENGTHS
- [Top 3 specific strengths with examples]

### ⚠️ IMPROVEMENT AREAS  
- [Top 3 specific areas needing attention]

### 📈 MARKET POSITION
- [1-2 sentences on competitive positioning for {job_role}]

---

## ⚡ PRIORITY ACTION PLAN

### 🔥 IMMEDIATE WINS (24-48 Hours)
1. **[SPECIFIC ACTION]**: Add quantified result - "Increased [metric] by X%"
   - **Location**: Experience section, [specific bullet]
   - **Impact**: +[X]% match improvement

2. **[SPECIFIC ACTION]**: Include keywords: "[skill1], [skill2], [skill3]"
   - **Location**: Skills section & summary
   - **Impact**: +[X]% ATS score

3. **[SPECIFIC ACTION]**: Enhance summary with: "[specific language]"
   - **Location**: Top of resume
   - **Impact**: Stronger first impression

### 📋 CONTENT OPTIMIZATION
```
SKILLS UPGRADE:
├── ADD: [3-4 missing {job_role} skills]
├── REMOVE: [2-3 outdated skills]
└── REORGANIZE: [Priority order for {job_role}]

EXPERIENCE ENHANCEMENT:
├── QUANTIFY: [Add specific numbers/percentages]
├── CONTEXTUALIZE: [Include project scope]  
└── IMPACT: [Connect to business outcomes]
```

---

## 🎯 SUCCESS METRICS

**TARGET IMPROVEMENTS:**
- ATS Score: 75%+ (Current: [X]%)
- Interview Rate: +25% improvement expected
- Response Time: <2 weeks average

**📅 IMPLEMENTATION TIMELINE:**
- Week 1: Complete all Priority Actions
- Week 2: Content optimization & formatting
- Week 3: Test optimized resume with 5+ applications

---

## 💡 {job_role.upper()} SPECIFIC INSIGHTS

**🔑 KEY SUCCESS FACTORS:**
- [2-3 most important elements for {job_role} success]

**📈 MARKET TRENDS:**
- [1-2 current trends affecting {job_role} hiring]

**🚀 COMPETITIVE EDGE:**
- [Unique positioning strategy for {job_role}]

---

**⚡ QUICK WIN SUMMARY:** Focus on quantifying achievements, adding {job_role} keywords, and optimizing for ATS compatibility. Expected results: 25-30% improvement in application success rate.

---

# ANALYSIS INPUTS:
**Target Role**: {job_role}
**Resume Content**: {resume}
**Job Requirements**: {job_desc}

IMPORTANT: 
- Keep total response under 800 words
- Use REAL numbers for all scoring (X/10, X%)
- Include SPECIFIC, actionable recommendations
- Create VISUAL text elements (progress bars, trees, checklists)
- Focus on highest-impact improvements
- Include role-specific insights for {job_role}
- Use engaging, professional language
"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1200
        )
        
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error generating report: {str(e)}. Please check your API key and try again."

def extract_scores(text):
    """Extract numerical scores from the analysis report"""
    try:
        patterns = [
            r'(\d+(?:\.\d+)?)/10',
            r'(\d+(?:\.\d+)?)/5',
            r'Score[:\s]*(\d+(?:\.\d+)?)/5',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*5'
        ]
        
        scores = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            scores.extend([float(match) for match in matches])
        
        # Convert 10-point scores to 5-point scale
        converted_scores = []
        for score in scores:
            if score > 5:  # Assume it's a 10-point score
                converted_scores.append(score / 2)
            else:
                converted_scores.append(score)
        
        unique_scores = []
        for score in converted_scores:
            if 0 <= score <= 5 and score not in unique_scores:
                unique_scores.append(score)
        
        return unique_scores[:6]
    except Exception as e:
        st.warning(f"Could not extract scores: {str(e)}")
        return []

def calculate_percentage_score(scores):
    """Convert scores to percentage"""
    if not scores:
        return 0.0
    avg_score = sum(scores) / len(scores)
    percentage = (avg_score / 5) * 100
    return round(percentage, 1)

def get_assessment_level(ats_score, overall_score):
    """Get assessment level based on scores"""
    avg_score = (ats_score * 100 + overall_score) / 2
    if avg_score >= 85:
        return "🟢 Excellent Match", "Outstanding alignment with job requirements. You're highly competitive for this role."
    elif avg_score >= 70:
        return "🟡 Strong Candidate", "Good foundation with some areas for strategic improvement."
    elif avg_score >= 55:
        return "🟠 Moderate Fit", "Solid potential but requires focused enhancement in key areas."
    else:
        return "🔴 Needs Development", "Significant improvements needed to be competitive for this role."

def validate_inputs(resume_text):
    """Validate inputs meet minimum requirements"""
    errors = []
    
    if len(resume_text.strip()) < 150:
        errors.append("❌ Resume content seems too short. Please provide a complete resume with all sections.")
    
    return errors

# Sidebar Configuration
with st.sidebar:
    st.markdown("## 📋 How to Use")
    st.markdown("""
    ### 🚀 Quick Start:
    1. **Select job role** from dropdown
    2. **Upload PDF OR paste text** (either method works)
    3. **Add specific job description** (optional)
    4. **Click Analyze** for focused report
    
    ### 📊 What You'll Get:
    - **Concise professional report** (under 800 words)
    - **Visual scoring with progress bars**
    - **Priority action plan** with specific steps
    - **Quick wins** for immediate impact
    - **Success metrics** and timeline
    """)
    
    st.markdown("---")
    st.markdown("## ⚙️ Setup")
    if not api_key:
        st.error("🚨 **GROQ_API_KEY Required!**")
        st.markdown("""
        1. Get free key: [Groq Console](https://console.groq.com/)
        2. Create `.env` file:
        ```
        GROQ_API_KEY=your_key_here
        ```
        3. Restart application
        """)
    else:
        st.success("✅ API Key Configured")

# Main Application Interface
if not st.session_state.form_submitted:
    with st.form("comprehensive_resume_analysis_form", clear_on_submit=False):
        
        # Job Role Selection
        st.markdown("## 🎯 Target Job Role Selection")
        selected_role = st.selectbox(
            "Choose your target job role:",
            options=list(JOB_ROLES.keys()),
            index=0,
            help="Select the job role you're applying for. This will customize the analysis and recommendations."
        )
        
        st.markdown("---")
        
        # Resume Input Section
        st.markdown("## 📄 Resume Input Options")
        st.info("💡 **Choose either method to provide your resume - both work independently:**")
        
        # Initialize variables for both input methods
        pdf_text = ""
        pasted_text = ""
        resume_filename = ""
        
        # PDF Upload Section
        st.markdown("### 📁 Option 1: Upload PDF Resume")
        
        uploaded_file = st.file_uploader(
            "Choose your resume file (PDF format only)",
            type="pdf",
            help="Upload a PDF version of your resume. Ensure the text is selectable (not a scanned image).",
            key="pdf_uploader"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ PDF Uploaded: **{uploaded_file.name}**")
                resume_filename = uploaded_file.name
            with col2:
                file_size = len(uploaded_file.getvalue()) / 1024  # KB
                st.info(f"📄 {file_size:.1f} KB")
            
            with st.spinner("🔍 Extracting text from PDF..."):
                pdf_text = extract_pdf_text(uploaded_file)
            
            if "Warning" not in pdf_text and "Could not extract" not in pdf_text:
                st.success("✅ Text extracted successfully!")
                
                with st.expander("📖 Preview Extracted Text", expanded=False):
                    word_count = len(pdf_text.split())
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Words", word_count)
                    col2.metric("Characters", len(pdf_text))
                    col3.metric("Estimated Pages", max(1, word_count // 250))
                    
                    st.text_area(
                        "Extracted Resume Text:",
                        value=pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text,
                        height=200,
                        disabled=True,
                        key="pdf_preview"
                    )
            else:
                st.error(pdf_text)
                pdf_text = ""
        
        st.markdown("---")
        
        # Text Paste Section
        st.markdown("### 📝 Option 2: Paste Resume Text")
        
        pasted_text = st.text_area(
            "Paste your complete resume text here:",
            placeholder="""📝 Paste your complete resume here...

Example format:
=====================================
JOHN SMITH
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith

PROFESSIONAL SUMMARY
====================================
Experienced Data Scientist with 5+ years of expertise in machine learning and statistical analysis. Proven track record of developing predictive models that increased revenue by 25%.

EXPERIENCE
====================================
Senior Data Scientist | TechCorp Inc. | Jan 2021 - Present
• Led team of 4 data scientists in developing ML models for customer churn prediction, reducing churn by 30%
• Implemented automated data pipeline processing 10M+ records daily
• Collaborated with product teams to deploy 15+ predictive models into production

Data Scientist | DataTech Solutions | Jun 2019 - Dec 2020  
• Built recommendation system using collaborative filtering, increasing user engagement by 45%
• Performed A/B testing on 100K+ users, optimizing conversion rates by 25%
• Created interactive dashboards using Tableau, utilized by 50+ stakeholders daily

EDUCATION
====================================
Master of Science in Data Science | University of California, Berkeley | 2019
Bachelor of Science in Statistics | UCLA | 2017

SKILLS
====================================
• Programming: Python, R, SQL, Java
• Machine Learning: Scikit-learn, TensorFlow, PyTorch
• Data Visualization: Tableau, Power BI, Matplotlib
• Big Data: Spark, Hadoop, AWS, Google Cloud Platform
• Statistics: Regression Analysis, Hypothesis Testing, Time Series Analysis
=====================================

💡 Tips for best results:
- Include ALL sections (Summary, Experience, Education, Skills)
- Use quantified achievements with specific numbers/percentages
- Include relevant keywords from your target job
- Maintain clear formatting with section headers""",
            height=400,
            help="Copy your complete resume text and paste it here. Include all sections for comprehensive analysis.",
            key="resume_text_input"
        )
        
        if pasted_text:
            # Real-time statistics for pasted text
            words = len(pasted_text.split())
            characters = len(pasted_text)
            lines = len([line for line in pasted_text.split('\n') if line.strip()])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 Words", words)
            col2.metric("🔤 Characters", characters)
            col3.metric("📄 Lines", lines)
            col4.metric("⏱️ Read Time", f"{max(1, words // 200)} min")
            
            # Content quality check for pasted text
            resume_lower = pasted_text.lower()
            quality_checks = []
            
            if any(section in resume_lower for section in ['experience', 'work history', 'employment']):
                quality_checks.append("✅ Experience section detected")
            if 'education' in resume_lower:
                quality_checks.append("✅ Education section detected")
            if any(section in resume_lower for section in ['skill', 'technical', 'competenc']):
                quality_checks.append("✅ Skills section detected")
            if any(section in resume_lower for section in ['summary', 'objective', 'profile']):
                quality_checks.append("✅ Summary/Objective section detected")
            if '@' in pasted_text and any(contact in resume_lower for contact in ['phone', 'email', 'linkedin']):
                quality_checks.append("✅ Contact information detected")
            if any(char.isdigit() for char in pasted_text):
                quality_checks.append("✅ Quantified achievements detected")
            
            if quality_checks:
                with st.expander("✅ Content Quality Assessment", expanded=False):
                    for check in quality_checks:
                        st.write(check)
                    
                    quality_score = len(quality_checks)
                    if quality_score >= 5:
                        st.success(f"🌟 Excellent quality! ({quality_score}/6 criteria met)")
                    elif quality_score >= 3:
                        st.info(f"👍 Good quality ({quality_score}/6 criteria met)")
                    else:
                        st.warning(f"⚠️ Consider adding missing sections ({quality_score}/6 criteria met)")
            
            if not resume_filename:
                resume_filename = f"pasted_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Determine final resume content
        final_resume_text = ""
        input_source = ""
        
        if pdf_text and pasted_text:
            st.warning("⚠️ **Both PDF and text provided. Using PDF content for analysis.** If you prefer to use pasted text, clear the PDF upload above.")
            final_resume_text = pdf_text
            input_source = "PDF Upload"
        elif pdf_text:
            final_resume_text = pdf_text
            input_source = "PDF Upload"
        elif pasted_text:
            final_resume_text = pasted_text
            input_source = "Text Paste"
        else:
            final_resume_text = ""
            input_source = "None"
        
        st.markdown("---")
        
        # OPTIONAL JOB DESCRIPTION SECTION - CLEANED UP
        st.markdown("### 🎯 Optional: Specific Job Description")
        
        st.info("💡 **Optional Enhancement**: Paste a specific job description for more targeted analysis. If left blank, we'll use standard requirements for your selected role.")
        
        custom_job_description = st.text_area(
            "Paste the specific job description you're applying for (optional):",
            placeholder="""📋 Paste the actual job posting here for more precise analysis...

Example:
=====================================
Senior Data Scientist - TechCorp Inc.
San Francisco, CA | Remote Options Available

About the Role:
We're seeking a Senior Data Scientist to join our growing AI team. You'll work on cutting-edge machine learning projects that directly impact millions of users worldwide.

Key Responsibilities:
• Develop and deploy machine learning models for recommendation systems
• Collaborate with product teams to identify data science opportunities
• Build scalable data pipelines handling 100M+ daily events
• Lead A/B testing initiatives to optimize user experience
• Mentor junior data scientists and promote best practices

Requirements:
• Master's/PhD in Computer Science, Statistics, or related field
• 5+ years experience in machine learning and data science
• Expert-level Python programming and ML libraries (scikit-learn, TensorFlow, PyTorch)
• Experience with big data technologies (Spark, Hadoop, AWS)
• Strong communication skills and experience working with cross-functional teams
• Previous experience with recommendation systems preferred

What We Offer:
• Competitive salary: $150,000 - $200,000 + equity
• Comprehensive benefits and 4 weeks PTO
• Remote work flexibility
• $5,000 annual learning budget
=====================================

Benefits of adding specific job description:
• More accurate keyword matching
• Targeted skill gap analysis  
• Company-specific recommendations
• Higher ATS compatibility score""",
            height=300,
            help="Adding a specific job description will make the analysis more targeted and accurate for your application.",
            key="custom_job_desc_input"
        )
        
        st.markdown("---")
        
        # Form submission section
        st.markdown("## 🚀 Generate Analysis Report")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button(
                "🎯 Generate AI-Powered Resume Analysis", 
                type="primary",
                use_container_width=True
            )
        
        with col2:
            clear_form = st.form_submit_button(
                "🗑️ Clear Form",
                use_container_width=True
            )
        
        # Show current input status
        if final_resume_text:
            word_count = len(final_resume_text.split())
            st.success(f"✅ Resume content ready from **{input_source}** ({word_count} words)")
            if custom_job_description:
                st.info("✅ Custom job description provided - Analysis will be more targeted!")
        else:
            st.warning("⚠️ Please provide resume content using either PDF upload OR text paste")
        
        # AI DISCLAIMER SECTION
        st.markdown("---")
        st.markdown('<div class="disclaimer-section">', unsafe_allow_html=True)
        st.markdown("""
        **🤖 AI-Powered Analysis Disclaimer**
        
        This application uses artificial intelligence (AI) technology to analyze your resume and provide career recommendations. Please note:
        
        • **AI Analysis**: All resume evaluations and recommendations are generated using advanced AI language models
        • **Data Privacy**: Your resume content is processed securely and is not stored permanently on our servers
        • **Recommendations**: AI-generated suggestions should be considered as guidance - use your professional judgment for implementation
        • **Accuracy**: While our AI strives for accuracy, please verify all recommendations before applying to your resume
        • **Human Review**: Consider having your updated resume reviewed by human career professionals for additional perspective
        
        By using this service, you acknowledge that the analysis is AI-generated and should be used as a supplementary career development tool.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if clear_form:
            for key in session_vars:
                if key in st.session_state:
                    st.session_state[key] = "" if key != 'form_submitted' else False
            st.rerun()
        
        if submitted:
            if not api_key:
                st.error("❌ **API Configuration Required**: Please set up your GROQ_API_KEY in a .env file.")
                st.info("Get your free API key from [Groq Console](https://console.groq.com/) and create a .env file with: `GROQ_API_KEY=your_key_here`")
            elif final_resume_text:
                st.session_state.resume = final_resume_text
                st.session_state.resume_filename = resume_filename
                st.session_state.selected_job_role = selected_role
                st.session_state.custom_job_desc = custom_job_description
                
                validation_errors = validate_inputs(final_resume_text)
                
                if validation_errors:
                    st.error("**Please address the following issues:**")
                    for error in validation_errors:
                        st.write(error)
                else:
                    st.session_state.form_submitted = True
                    st.rerun()
            else:
                st.warning("⚠️ Please provide your resume content using either PDF upload OR text paste to proceed.")

# Results and Report Section
if st.session_state.form_submitted:
    st.markdown("---")
    
    # Analysis header
    st.markdown(f"## 📊 Analysis Report for: **{st.session_state.selected_job_role}**")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Analysis preparation
    status_text.text("🎯 Step 1/4: Analyzing job requirements...")
    progress_bar.progress(25)
    
    # Generate job description for similarity calculation
    if st.session_state.custom_job_desc.strip():
        comparison_job_desc = st.session_state.custom_job_desc.strip()
    elif st.session_state.selected_job_role in JOB_ROLES and st.session_state.selected_job_role != "Custom Role":
        role_info = JOB_ROLES[st.session_state.selected_job_role]
        comparison_job_desc = f"{role_info['description']} Key skills: {', '.join(role_info['key_skills'])} Experience areas: {', '.join(role_info.get('experience_focus', []))}"
    else:
        comparison_job_desc = "Professional role requiring relevant experience and skills."
    
    ats_score = calculate_similarity_bert(st.session_state.resume, comparison_job_desc)
    ats_percentage = round(ats_score * 100, 1)
    
    # Step 2: AI Analysis
    status_text.text("🤖 Step 2/4: Generating AI analysis...")
    progress_bar.progress(50)
    
    comprehensive_report = generate_comprehensive_report(
        st.session_state.resume, 
        st.session_state.selected_job_role,
        st.session_state.custom_job_desc
    )
    
    # Step 3: Score Extraction
    status_text.text("📈 Step 3/4: Calculating performance metrics...")
    progress_bar.progress(75)
    
    report_scores = extract_scores(comprehensive_report)
    overall_percentage = calculate_percentage_score(report_scores)
    
    # Step 4: Complete
    status_text.text("✅ Analysis complete!")
    progress_bar.progress(100)
    
    assessment_level, assessment_desc = get_assessment_level(ats_score, overall_percentage)
    
    # Clear progress
    import time
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()
    
    # Executive Summary Dashboard
    st.markdown("### 📊 Performance Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🤖 ATS Compatibility",
            f"{ats_percentage}%",
            help=f"Semantic similarity with {st.session_state.selected_job_role} requirements"
        )
    
    with col2:
        st.metric(
            "📋 Overall Score", 
            f"{overall_percentage}%",
            help="Comprehensive evaluation across all criteria"
        )
    
    with col3:
        improvement_potential = 100 - overall_percentage
        st.metric(
            "🚀 Growth Potential",
            f"+{improvement_potential}%",
            help="Available improvement opportunity"
        )
    
    # Overall Assessment
    st.info(f"**{assessment_level}**: {assessment_desc}")
    
    # Show analysis type without metrics
    if st.session_state.custom_job_desc.strip():
        st.success("🎯 **Targeted Analysis**: Used your specific job description for precise recommendations")
    else:
        st.info(f"📊 **General Analysis**: Used standard {st.session_state.selected_job_role} requirements")
    
    # Individual Scores Breakdown
    if report_scores:
        st.markdown("### 📊 Detailed Score Breakdown")
        
        score_categories = [
            "Technical Skills",
            "Experience", 
            "Achievements",
            "Education",
            "ATS Optimization",
            "Presentation"
        ]
        
        cols = st.columns(3)
        for i, (category, score) in enumerate(zip(score_categories, report_scores)):
            col_idx = i % 3
            with cols[col_idx]:
                percentage = round((score / 5) * 100, 1)
                st.metric(category, f"{percentage}%", f"{score}/5")
    
    st.markdown("---")
    
    # Comprehensive Report Display
    st.markdown("### 📝 Analysis Report")
    st.markdown("*Focused, actionable recommendations for immediate impact.*")
    
    if "Error" in comprehensive_report:
        st.error(comprehensive_report)
    else:
        st.markdown(comprehensive_report)
    
    st.markdown("---")
    
    # Export Section
    st.markdown("### 📥 Export Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_type_text = "TARGETED" if st.session_state.custom_job_desc.strip() else "GENERAL"
        detailed_report = f"""
🎯 RESUME ANALYSIS REPORT
═══════════════════════════════════════════════════════════════════════════════

📋 EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════════
Target Role: {st.session_state.selected_job_role}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Type: {analysis_type_text} - AI-Generated

📊 PERFORMANCE SCORES
═══════════════════════════════════════════════════════════════════════════════
• ATS Compatibility: {ats_percentage}%
• Overall Performance: {overall_percentage}%
• Assessment: {assessment_level}
• Growth Potential: +{100-overall_percentage}% improvement available

🎯 INDIVIDUAL SCORES
═══════════════════════════════════════════════════════════════════════════════
{chr(10).join([f'• {cat}: {score}/5 ({round((score/5)*100, 1)}%)' for cat, score in zip(['Technical Skills', 'Experience', 'Achievements', 'Education', 'ATS Optimization', 'Presentation'], report_scores)])}

📋 DETAILED ANALYSIS & RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════
{comprehensive_report}

⚡ IMPLEMENTATION GUIDE
═══════════════════════════════════════════════════════════════════════════════
1. Complete Priority Actions within 48 hours
2. Implement content optimizations in Week 1
3. Test optimized resume with 5+ applications
4. Track response rates and adjust strategy

✅ SUCCESS TARGETS
═══════════════════════════════════════════════════════════════════════════════
□ ATS Score: 75%+ (Current: {ats_percentage}%)
□ Overall Score: 85%+ (Current: {overall_percentage}%)
□ Interview Rate: +25% improvement expected
□ Response Time: <2 weeks average

═══════════════════════════════════════════════════════════════════════════════
Generated by Smart Resume Reviewer AI - Career Intelligence Platform
For optimization: Re-analyze your updated resume after improvements
═══════════════════════════════════════════════════════════════════════════════
"""
        
        st.download_button(
            "📄 Download Report",
            detailed_report,
            file_name=f"resume_analysis_{st.session_state.selected_job_role.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        if st.button("🔄 Analyze Different Resume", use_container_width=True):
            for key in session_vars:
                if key in st.session_state:
                    st.session_state[key] = "" if key != 'form_submitted' else False
            st.rerun()
    
    with col3:
        if st.button("💡 Quick Tips", use_container_width=True):
            st.info(f"""
            **🎯 Quick Wins for {st.session_state.selected_job_role}:**
            
            **⚡ 24-Hour Actions:**
            • Add 2-3 quantified achievements with specific metrics
            • Include trending keywords from job descriptions
            • Optimize professional summary for impact
            
            **📈 This Week:**
            • Reorganize skills by priority for {st.session_state.selected_job_role}
            • Rewrite 3-5 experience bullets with results focus
            • Ensure consistent formatting and ATS compatibility
            
            **🎯 Expected Results:**
            • 25-30% improvement in application response rates
            • Better ATS parsing and keyword matching
            • Stronger first impression with hiring managers
            """)

# Footer
st.markdown("---")
st.markdown("### 🚀 Smart Resume Reviewer - AI-Powered Career Intelligence")
st.markdown("**Get Concise, Actionable Resume Insights**")

# Feature grid using columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **📊 Focused Reports**
    
    Concise analysis with actionable insights
    """)

with col2:
    st.markdown("""
    **🤖 AI-Powered**
    
    Smart analysis with visual elements
    """)

with col3:
    st.markdown("""
    **⚡ Quick Wins**
    
    Priority actions for immediate impact
    """)

with col4:
    st.markdown("""
    **🎯 Optional Targeting**
    
    Custom job description analysis
    """)

st.markdown("---")
st.markdown("*💡 AI-Powered Strategy: Smart insights • Quick wins • Measurable results • Immediate impact*")
st.markdown("**Ready for AI-powered resume optimization? Generate your analysis above! 🎯**")

# Error handling
try:
    import streamlit
    import pdfminer
    import sentence_transformers
    import sklearn
    import groq
except ImportError as e:
    st.error(f"""
    ❌ **Missing Dependencies**
    
    Please install the required packages:
    ```bash
    pip install streamlit pdfminer.six sentence-transformers scikit-learn groq python-dotenv
    ```
    
    Error: {str(e)}
    """)