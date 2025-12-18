import streamlit as st
import google.generativeai as genai
import json
import sqlite3
import os

# --- 1. CONFIGURATION ---
# --- 1. CONFIGURATION ---
model = None

try:
    # PRIORITY 1: Check Streamlit Secrets (.streamlit/secrets.toml)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    
    # PRIORITY 2: Check Session State (if loaded via Home.py)
    elif "api_key" in st.session_state:
        api_key = st.session_state["api_key"]

    # Configure Gemini with the found key
    genai.configure(api_key=api_key)
    
    # Initialize Model (Gemini 2.5 Flash with low temp for precision)
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.2})

except Exception as e:
    st.error(f"❌ Configuration Error: {e}")
    st.warning("Please check your API Key in .streamlit/secrets.toml or Home.py")
# --- 2. DATABASE PATHING ---
# We are in /pages/1_Plan_Agent.py. We want the DB in the ROOT folder.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(CURRENT_DIR)                
DB_FILE = os.path.join(ROOT_DIR, 'ips_sdlc.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS project_plans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  project_name TEXT, 
                  raw_input TEXT, 
                  structured_plan JSON, 
                  status TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# --- 3. AI LOGIC (HYBRID: ROBUST + VISIONARY) ---
def generate_master_blueprint(raw_input):
    if not model: return {"error": "Model not loaded. Check API Key."}
    
    prompt = f"""
    You are the Chief Software Architect. 
    Your job is to convert user requirements into a STRICT, DETAILED technical blueprint.
    
    INPUT REQUIREMENTS:
    "{raw_input}"
    
    *** CRITICAL RULES (DO NOT VIOLATE) ***
    1. EXHAUSTIVENESS: Create a separate entry in the 'pages' array for EVERY distinct screen mentioned. 
       - Do NOT combine pages.
    
    2. VISUAL STRATEGY (NEW): For every page, define the 'layout_style' (e.g. "Sidebar Dashboard", "Centered Card", "Split Screen") and a 'visual_desc' text describing the vibe.
    
    3. COMPONENT DETAIL: For each page, list specific UI components.
       - Give every component a unique 'element_id'.
       - 'type' can be: button, table, chart, form, navbar, sidebar, card.
    
    4. API LOGIC: For every interactive element, define the 'api_call'.
    
    REQUIRED JSON STRUCTURE:
    {{
      "project_name": "String",
      "global_theme": "String (e.g. 'Dark Mode Corporate')",
      "pages": [
        {{
          "page_id": "unique_id",
          "title": "Page Title",
          "route": "/route",
          "layout_style": "Sidebar with Topbar",
          "visual_desc": "A clean dashboard view with a 4-column metrics row at the top and a large data table below.",
          "components": [
             {{ "element_id": "btn_add", "type": "button", "label": "Add Item" }},
             {{ "element_id": "rev_chart", "type": "chart", "label": "Revenue Trend (Line)" }}
          ],
          "api_calls": [
             {{ "trigger": "btn_add", "method": "POST", "endpoint": "/api/items" }}
          ]
        }}
      ]
    }}
    
    OUTPUT: Return ONLY valid JSON.
    """
    
    try:
        result = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(result.text)
    except Exception as e:
        return {"error": f"AI Generation Failed: {str(e)}"}

def refine_blueprint(current_json, feedback):
    if not model: return {"error": "Model not loaded."}
    
    prompt = f"""
    Refine this Blueprint JSON based on user feedback.
    CURRENT BLUEPRINT: {json.dumps(current_json)}
    FEEDBACK: "{feedback}"
    
    TASK: Update the JSON strictly. Add/Remove pages or change details.
    OUTPUT: Return ONLY valid JSON.
    """
    try:
        result = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(result.text)
    except Exception as e:
        return {"error": f"Refinement Failed: {str(e)}"}

# --- 4. MAIN UI ---
def main():
    try: st.set_page_config(page_title="IPS Architect", layout="wide", page_icon="🏗️")
    except: pass

    st.title("🏗️ Plan Agent")
    st.caption("Step 1: Define your software requirements.")
    
    init_db()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🗄️ Project History")
        if os.path.exists(DB_FILE):
            try:
                conn = sqlite3.connect(DB_FILE)
                plans = conn.execute("SELECT id, project_name FROM project_plans ORDER BY id DESC LIMIT 10").fetchall()
                conn.close()
                for p in plans:
                    st.text(f"#{p[0]} {p[1]}")
            except:
                st.caption("No history yet.")
        
        st.divider()
        if st.button("🔥 Reset Database", key="btn_reset_db"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.warning("Database deleted. Refresh page.")
                st.rerun()

    # --- MAIN WORKSPACE ---
    col1, col2 = st.columns([1, 1.2], gap="large")

    # LEFT: INPUT
    with col1:
        st.subheader("1. Requirements")
        if "raw_text" not in st.session_state: st.session_state["raw_text"] = ""

        user_input = st.text_area("Describe the App:", 
                                  value=st.session_state["raw_text"], 
                                  height=250,
                                  placeholder="Example: I need a CRM with Login, Dashboard, Customer List, and Settings.")
        
        if st.button("🚀 Generate Blueprint", type="primary", use_container_width=True):
            if not user_input:
                st.warning("Please enter requirements.")
            else:
                with st.spinner("Architecting System..."):
                    bp = generate_master_blueprint(user_input)
                    if "error" in bp: st.error(bp['error'])
                    else:
                        st.session_state['blueprint'] = bp
                        st.session_state['raw_text'] = user_input
                        st.rerun()
        
        # Refinement
        if 'blueprint' in st.session_state:
            st.divider()
            st.markdown("### 🔧 Refine Plan")
            feedback = st.text_area("Feedback:", placeholder="e.g. Add a 'Forgot Password' page...")
            if st.button("🔄 Update Blueprint", use_container_width=True):
                with st.spinner("Refining..."):
                    new_bp = refine_blueprint(st.session_state['blueprint'], feedback)
                    st.session_state['blueprint'] = new_bp
                    st.rerun()

    # RIGHT: PREVIEW
    with col2:
        st.subheader("2. Blueprint Preview")
        
        if 'blueprint' in st.session_state:
            bp = st.session_state['blueprint']
            
            # Global Info
            st.info(f"Project: **{bp.get('project_name', 'Untitled')}** | Theme: **{bp.get('global_theme', 'Default')}**")
            
            pages = bp.get('pages', [])
            if not pages: st.error("No pages generated.")
            
            if pages:
                tabs = st.tabs([p['title'] for p in pages])
                for i, tab in enumerate(tabs):
                    with tab:
                        p = pages[i]
                        
                        # Visual / Layout Info (New)
                        st.markdown(f"**Layout:** `{p.get('layout_style', 'Standard')}`")
                        st.caption(f"🎨 {p.get('visual_desc', 'No visual description provided.')}")
                        st.divider()

                        st.markdown(f"**Route:** `{p.get('route')}`")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("#### 🧩 Components")
                            st.json(p.get('components'))
                        with c2:
                            st.markdown("#### 🔌 API Calls")
                            st.json(p.get('api_calls'))

            st.divider()
            if st.button("✅ Approve & Save", type="primary", use_container_width=True):
                try:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO project_plans (project_name, raw_input, structured_plan, status) VALUES (?, ?, ?, ?)",
                              (bp.get("project_name", "Untitled"), st.session_state['raw_text'], json.dumps(bp), "APPROVED"))
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success("Blueprint Saved! Switch to 'Design Agent' in the sidebar.")
                except Exception as e:
                    st.error(f"Save Failed: {e}")
        else:
            st.info("👈 Enter requirements to start.")

if __name__ == "__main__":
    main()