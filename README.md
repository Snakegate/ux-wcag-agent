# 🧠 Web Usability & Accessibility Auditor (Built with Vibe Coding)

This project is an AI-powered tool that audits live websites based on:
- ✅ Nielsen's 10 Usability Heuristics
- ✅ WCAG 2.2 Accessibility Guidelines

Built entirely with Cursor, Streamlit, and OpenAI — no prior coding experience needed.

## 🔍 What It Does
- Crawls a webpage
- Detects WCAG issues (e.g. color contrast, missing alt text)
- Evaluates usability heuristics using GPT
- Exports results to Notion

## ⚙️ Tech Stack
- Cursor (AI IDE)
- Python
- Streamlit
- Playwright
- BeautifulSoup
- OpenAI API
- Notion API

## 📂 Project Structure
your_project/
├── audit.py ← Core audit logic
├── audit_app.py ← Streamlit app UI
├── .env ← Secret keys (not committed)
└── requirements.txt ← Python dependencies
## 🚀 Getting Started
1. Clone the repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ux-wcag-agent.git
   cd ux-wcag-agent
2.  Create virtual environment:
   python3 -m venv venv
source venv/bin/activate
3. Install dependencies:
   pip install -r requirements.txt
playwright install
4. Run the app:
   streamlit run audit_app.py

🧪 Example Output
Screenshot + JSON + Notion export...
💬 Feedback or Issues?
Feel free to open an issue or contribute via PR.

yaml
Would you like me to generate this content and drop it into your current `README.md` so you can just copy/paste it on GitHub?



