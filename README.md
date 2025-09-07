# Smart Resume Reviewer
## How to create a virtual environment in VS Code

Open the terminal in the VS Code and run these commands

In Powershell

1. `  python -m venv myenv  `
2. `  .\myenv\Scripts\Activate.ps1  `

In Linux

1. `  python -m venv myenv  `
2. `  source myenv\bin\Activate  `

## How to run the python file

In Powershell

1. `  pip install -r requirements.txt  `
2. `  Copy-Item .env.example .env  `

   Visit [https://console.groq.com/home](https://console.groq.com/home): to create your API Key. Copy it and store it carefully. In the .env file, paste the API key in place of "your_api_key_here".
3. `  streamlit run streamlit_app.py  `

This will open the web application in the local host. 

We have used Streamlit Cloud to deploy the app. The GROQ API KEY is added in the Secrets or Environment Variables.

Check Out the APP here: [Smart Resume Reviewer](https://smartresumereviewer-5crsutzysp2jzvyanvkd7h.streamlit.app/)
