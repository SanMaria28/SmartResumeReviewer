# Smart Resume Reviewer - Complete AI-Powered Resume Analysis Tool
# Updated version - Role descriptions removed for cleaner interface

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

# Custom CSS for enhanced UI
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
    .report-section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .input-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    .input-section.selected {
        border-color: #1f77b4;
        background-color: #e3f2fd;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .section-divider {
        border-top: 3px solid #1f77b4;
        margin: 2rem 0;
    }
    .highlight-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session States
session_vars = ['form_submitted', 'resume', 'job_desc', 'resume_filename', 'selected_job_role', 'analysis_results']
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

def generate_comprehensive_report(resume, job_desc, job_role):
    """Generate detailed analysis report using Groq LLM"""
    try:
        if not api_key:
            return "❌ Error: GROQ_API_KEY not found. Please check your .env file."
        
        client = Groq(api_key=api_key)
        
        # Get job role context
        role_context = ""
        if job_role in JOB_ROLES and job_role != "Custom Role":
            role_info = JOB_ROLES[job_role]
            role_context = f"""
**Target Role Context:**
- Position: {job_role}
- Key Skills Expected: {', '.join(role_info['key_skills'])}
- Experience Focus Areas: {', '.join(role_info.get('experience_focus', []))}
"""

        prompt = f"""
You are an expert AI Resume Analyst and Senior Career Coach. Analyze the candidate's resume against the specific job requirements and provide a comprehensive report with actionable recommendations.

{role_context}

# COMPREHENSIVE RESUME ANALYSIS

## SECTION 1: EXECUTIVE SUMMARY
- Overall match percentage assessment
- Top 3 strengths identified
- Top 3 areas requiring immediate attention
- Competitive positioning analysis

## SECTION 2: DETAILED EVALUATION (Score each out of 5)

### Technical Skills Alignment (X/5)
- Current skills analysis vs. required skills
- Gap identification and specific missing skills
- Recommendations for skill additions

### Professional Experience Relevance (X/5)
- Experience alignment with role requirements
- Career progression analysis
- Industry background assessment

### Achievements & Impact (X/5)
- Quantification quality assessment
- Impact demonstration analysis
- Results communication effectiveness

### Education & Certifications (X/5)
- Educational background relevance
- Certification analysis
- Continuous learning evidence

### ATS Optimization (X/5)
- Keyword density analysis
- Format compatibility assessment
- Industry terminology usage

### Professional Presentation (X/5)
- Visual layout assessment
- Information hierarchy
- Writing quality and professionalism

## SECTION 3: PRIORITY UPGRADE PLAN

### CRITICAL UPGRADES (Implement in 24-48 hours)
1. [Specific action with location and example]
2. [Specific action with location and example]
3. [Specific action with location and example]

### CONTENT IMPROVEMENTS
- Skills Section: [Specific changes needed]
- Experience Section: [Bullet point improvements with examples]
- Education Section: [Relevance enhancements]
- Professional Summary: [Rewrite suggestions]

### ATS OPTIMIZATION
- Primary keywords to add: [List top 10 keywords]
- Format improvements: [Specific formatting changes]
- Section headers: [Recommended headers]

### IMPLEMENTATION ROADMAP
Phase 1 (Week 1): [Immediate actions]
Phase 2 (Week 2): [Content development]
Phase 3 (Week 3): [Advanced optimization]

# ANALYSIS INPUTS:
**Resume:**
{resume}

**Job Description:**
{job_desc}

Please provide detailed, specific, and actionable recommendations with concrete examples.
"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=3500
        )
        
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error generating report: {str(e)}. Please check your API key and try again."

def extract_scores(text):
    """Extract numerical scores from the analysis report"""
    try:
        patterns = [
            r'(\d+(?:\.\d+)?)/5',
            r'Score[:\s]*(\d+(?:\.\d+)?)/5',
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*5'
        ]
        
        scores = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            scores.extend([float(match) for match in matches])
        
        unique_scores = []
        for score in scores:
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

def get_score_color_class(score):
    """Return CSS class based on score range"""
    if score >= 80:
        return "score-high"
    elif score >= 60:
        return "score-medium"
    else:
        return "score-low"

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

def validate_inputs(resume_text, job_description):
    """Validate inputs meet minimum requirements"""
    errors = []
    
    if len(resume_text.strip()) < 150:
        errors.append("❌ Resume content seems too short. Please provide a complete resume with all sections.")
    
    if len(job_description.strip()) < 100:
        errors.append("❌ Job description seems too short. Please provide a detailed job description.")
    
    return errors

# Sidebar Configuration
with st.sidebar:
    st.markdown("## 📋 How to Use")
    st.markdown("""
    ### 🚀 Quick Start:
    1. **Select job role** from dropdown
    2. **Choose input method** (PDF upload or text paste)
    3. **Provide resume content**
    4. **Customize job description**
    5. **Click Analyze** for comprehensive report
    
    ### 📊 What You'll Get:
    - **Detailed scoring** across 6 criteria
    - **ATS compatibility analysis**
    - **Comprehensive upgrade plan**
    - **Industry-specific recommendations**
    - **Implementation roadmap**
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
        
        # Job Role Selection - REMOVED ROLE DESCRIPTIONS
        st.markdown("## 🎯 Target Job Role Selection")
        selected_role = st.selectbox(
            "Choose your target job role:",
            options=list(JOB_ROLES.keys()),
            index=0,
            help="Select the job role you're applying for. This will customize the analysis and recommendations."
        )
        
        st.markdown("---")
        
        # Resume Input Section
        st.markdown("## 📄 Resume Input Method")
        
        input_method = st.radio(
            "Choose how you want to provide your resume:",
            options=["📁 Upload PDF File", "📝 Paste Resume Text"],
            index=0,
            horizontal=True,
            help="Select your preferred method for providing your resume content."
        )
        
        resume_text = ""
        resume_filename = ""
        
        # PDF Upload Option
        if input_method == "📁 Upload PDF File":
            st.markdown("### 📁 PDF Resume Upload")
            
            uploaded_file = st.file_uploader(
                "Choose your resume file (PDF format only)",
                type="pdf",
                help="Upload a PDF version of your resume. Ensure the text is selectable (not a scanned image).",
                key="pdf_uploader"
            )
            
            if uploaded_file is not None:
                st.success(f"✅ Uploaded: **{uploaded_file.name}**")
                resume_filename = uploaded_file.name
                
                with st.spinner("🔍 Extracting text from PDF..."):
                    resume_text = extract_pdf_text(uploaded_file)
                
                if "Warning" not in resume_text and "Could not extract" not in resume_text:
                    st.success("✅ Text extracted successfully!")
                    
                    with st.expander("📖 Preview Extracted Text", expanded=False):
                        word_count = len(resume_text.split())
                        col1, col2 = st.columns(2)
                        col1.metric("Words", word_count)
                        col2.metric("Estimated Pages", max(1, word_count // 250))
                        
                        st.text_area(
                            "Extracted Resume Text:",
                            value=resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text,
                            height=200,
                            disabled=True,
                            key="pdf_preview"
                        )
                else:
                    st.error(resume_text)
        
        # Text Paste Option
        else:
            st.markdown("### 📝 Paste Resume Text")
            
            resume_text = st.text_area(
                "Paste your complete resume text below:",
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

EDUCATION
====================================
Master of Science in Data Science | University of California, Berkeley | 2019
Bachelor of Science in Statistics | UCLA | 2017

SKILLS
====================================
• Programming: Python, R, SQL, Java
• Machine Learning: Scikit-learn, TensorFlow, PyTorch
• Data Visualization: Tableau, Power BI, Matplotlib
=====================================

💡 Tips for best results:
- Include all sections (Summary, Experience, Education, Skills)
- Use quantified achievements with specific numbers/percentages
- Include relevant keywords from your target job""",
                height=500,
                help="Copy your complete resume text and paste it here. Include all sections for comprehensive analysis.",
                key="resume_text_input"
            )
            
            if resume_text:
                words = len(resume_text.split())
                characters = len(resume_text)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("📝 Words", words)
                col2.metric("🔤 Characters", characters)
                col3.metric("⏱️ Est. Read Time", f"{max(1, words // 200)} min")
                
                resume_filename = f"pasted_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        st.markdown("---")
        
        # Job Description Section
        st.markdown("## 💼 Job Description Customization")
        
        if selected_role == "Custom Role":
            default_desc = """Enter your custom job description here...

Include:
- Job title and company information
- Role responsibilities and requirements
- Required skills and qualifications  
- Experience level needed"""
            st.info("💡 **Custom Role Selected**: Please provide a detailed job description below.")
        else:
            role_info = JOB_ROLES[selected_role]
            default_desc = f"""**Job Title:** {selected_role}

**Job Description:**
We are seeking a skilled {selected_role} to join our growing team and contribute to our mission of delivering exceptional results.

**Key Responsibilities:**
• Lead and execute complex projects in {selected_role.lower()} domain
• Collaborate with cross-functional teams to deliver high-impact solutions
• Analyze requirements and develop innovative approaches to solve business challenges
• Drive continuous improvement and best practices implementation
• Mentor junior team members and contribute to knowledge sharing

**Required Qualifications:**
• Bachelor's degree in related field (Master's preferred)
• 3+ years of relevant professional experience
• Strong proficiency in: {', '.join(role_info['key_skills'][:8])}
• Experience with: {', '.join(role_info.get('experience_focus', [])[:5])}
• Excellent communication and collaboration skills
• Strong analytical and problem-solving abilities

**Preferred Qualifications:**
• Advanced degree in relevant field
• Industry certifications
• Experience with: {', '.join(role_info['key_skills'][8:12]) if len(role_info['key_skills']) > 8 else 'additional relevant technologies'}
• Leadership experience
• Track record of successful project delivery

**What We Offer:**
• Competitive salary and comprehensive benefits package
• Professional development opportunities and career growth
• Collaborative and innovative work environment
• Flexible work arrangements and work-life balance

Please customize this template with specific details from the actual job posting you're applying for."""

        job_description = st.text_area(
            "Review and customize the job description:",
            value=default_desc,
            height=300,
            help="Customize this description to match the exact job posting you're applying for.",
            key="job_description_input"
        )
        
        st.session_state.selected_job_role = selected_role
        st.session_state.job_desc = job_description
        
        st.markdown("---")
        
        # Form submission section
        st.markdown("## 🚀 Generate Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            submitted = st.form_submit_button(
                "🔍 Generate Comprehensive Resume Analysis", 
                type="primary",
                use_container_width=True
            )
        
        with col2:
            clear_form = st.form_submit_button(
                "🗑️ Clear Form",
                use_container_width=True
            )
        
        if clear_form:
            for key in session_vars:
                if key in st.session_state:
                    st.session_state[key] = "" if key != 'form_submitted' else False
            st.rerun()
        
        if submitted:
            if not api_key:
                st.error("❌ **API Configuration Required**: Please set up your GROQ_API_KEY in a .env file.")
            elif job_description and resume_text:
                st.session_state.resume = resume_text
                st.session_state.resume_filename = resume_filename
                
                validation_errors = validate_inputs(resume_text, job_description)
                
                if validation_errors:
                    st.error("**Please address the following issues:**")
                    for error in validation_errors:
                        st.write(error)
                else:
                    st.session_state.form_submitted = True
                    st.rerun()
            else:
                st.warning("⚠️ Please provide both your resume and job description to proceed.")

# Results and Report Section
if st.session_state.form_submitted:
    st.markdown("---")
    
    # Analysis header
    st.markdown(f"## 📊 Analysis Results for: **{st.session_state.selected_job_role}**")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: ATS Analysis
    status_text.text("🔍 Step 1/4: Calculating ATS compatibility...")
    progress_bar.progress(25)
    
    ats_score = calculate_similarity_bert(st.session_state.resume, st.session_state.job_desc)
    ats_percentage = round(ats_score * 100, 1)
    
    # Step 2: AI Analysis
    status_text.text("🤖 Step 2/4: Generating comprehensive AI analysis...")
    progress_bar.progress(50)
    
    comprehensive_report = generate_comprehensive_report(
        st.session_state.resume, 
        st.session_state.job_desc, 
        st.session_state.selected_job_role
    )
    
    # Step 3: Score Extraction
    status_text.text("📈 Step 3/4: Calculating detailed scores...")
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
            help="Semantic similarity with job requirements"
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
    st.markdown("### 📝 Comprehensive Analysis Report")
    
    if "Error" in comprehensive_report:
        st.error(comprehensive_report)
    else:
        # Display report sections
        report_sections = comprehensive_report.split("##")
        
        for section in report_sections:
            if section.strip():
                section_content = section.strip()
                if any(keyword in section_content.upper() for keyword in ["UPGRADE", "ACTION PLAN"]):
                    st.markdown("## " + section_content)
                else:
                    st.markdown("## " + section_content)
    
    st.markdown("---")
    
    # Export Section
    st.markdown("### 📥 Export & Next Steps")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Complete report
        detailed_report = f"""
SMART RESUME REVIEWER - ANALYSIS REPORT
======================================
Target Role: {st.session_state.selected_job_role}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PERFORMANCE SCORES:
==================
• ATS Compatibility: {ats_percentage}%
• Overall Evaluation: {overall_percentage}%
• Assessment: {assessment_level}

COMPREHENSIVE ANALYSIS:
======================
{comprehensive_report}

IMPLEMENTATION CHECKLIST:
========================
□ Review priority upgrades
□ Add missing keywords
□ Quantify achievements
□ Improve formatting
□ Re-analyze updated resume

Generated by Smart Resume Reviewer AI
"""
        
        st.download_button(
            "📄 Download Complete Report",
            detailed_report,
            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
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
            **Quick Wins for {st.session_state.selected_job_role}:**
            
            ⚡ **Immediate Actions:**
            • Add quantified achievements with numbers
            • Include keywords from job description
            • Update professional summary
            • Ensure consistent formatting
            
            📈 **Strategic Improvements:**
            • Research relevant certifications
            • Rewrite experience bullets with action verbs
            • Create tailored versions for applications
            • Track application success rates
            """)

# Footer
st.markdown("---")
st.markdown("### 🚀 Smart Resume Reviewer - Comprehensive Career Optimization")
st.markdown("**Transform Your Career with AI-Powered Resume Intelligence**")

# Feature grid using columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **📊 Advanced Analytics**
    
    6-point evaluation system with detailed scoring
    """)

with col2:
    st.markdown("""
    **🤖 AI Intelligence**
    
    Powered by cutting-edge language models
    """)

with col3:
    st.markdown("""
    **📋 Actionable Insights**
    
    Specific, implementable recommendations
    """)

with col4:
    st.markdown("""
    **📈 Progress Tracking**
    
    Multiple export formats for monitoring improvement
    """)

st.markdown("---")
st.markdown("*💡 Best Practices: Upload complete resumes • Use specific job descriptions • Implement priority changes first • Re-analyze after updates*")
st.markdown("**Ready to optimize your next resume? Start a new analysis above! 🎯**")

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