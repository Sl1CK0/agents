# import streamlit as st
# import google.generativeai as genai
# import sqlite3
# import json
# import streamlit.components.v1 as components
# import os
# import re

# # --- 1. CONFIGURATION ---
# # --- 1. CONFIGURATION ---
# model = None

# try:
#     # PRIORITY 1: Check Streamlit Secrets (.streamlit/secrets.toml)
#     if "GOOGLE_API_KEY" in st.secrets:
#         api_key = st.secrets["GOOGLE_API_KEY"]
    
#     # PRIORITY 2: Check Session State (if loaded via Home.py)
#     elif "api_key" in st.session_state:
#         api_key = st.session_state["api_key"]


#     # Configure Gemini with the found key
#     genai.configure(api_key=api_key)
    
#     # Initialize Model (Gemini 2.5 Flash with low temp for precision)
#     model = genai.GenerativeModel('gemini-2.5-flash-lite', generation_config={"temperature": 0.2})

# except Exception as e:
#     st.error(f"❌ Configuration Error: {e}")
#     st.warning("Please check your API Key in .streamlit/secrets.toml or Home.py")
# # --- 2. ROBUST DATABASE PATHING ---
# # Ensures we share the DB with the Plan Agent
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# ROOT_DIR = os.path.dirname(CURRENT_DIR)
# DB_PATH = os.path.join(ROOT_DIR, 'ips_sdlc.db')

# def init_design_db():
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
#         c.execute('''CREATE TABLE IF NOT EXISTS page_designs
#                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
#                       project_id INTEGER,
#                       page_title TEXT, 
#                       html_code TEXT, 
#                       status TEXT,
#                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
#         conn.commit()
#         conn.close()
#     except Exception as e:
#         st.error(f"❌ Database Init Error: {e}")

# def get_approved_blueprints():
#     if not os.path.exists(DB_PATH): return []
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         c = conn.cursor()
#         plans = c.execute("SELECT id, project_name, structured_plan FROM project_plans WHERE status='APPROVED' ORDER BY id DESC").fetchall()
#         conn.close()
#         return plans
#     except Exception as e:
#         return []

# def save_approved_design(project_id, page_title, html_code):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     exists = c.execute("SELECT id FROM page_designs WHERE project_id=? AND page_title=?", (project_id, page_title)).fetchone()
#     if exists:
#         c.execute("UPDATE page_designs SET html_code=?, status='APPROVED' WHERE id=?", (html_code, exists[0]))
#     else:
#         c.execute("INSERT INTO page_designs (project_id, page_title, html_code, status) VALUES (?, ?, ?, 'APPROVED')",
#                   (project_id, page_title, html_code))
#     conn.commit()
#     conn.close()

# # --- 3. UTILS (Cleaner & Fullscreen) ---
# def clean_ai_response(text):
#     """Extracts code from Markdown blocks"""
#     pattern = r"```(?:html)?(.*?)```"
#     match = re.search(pattern, text, re.DOTALL)
#     if match: return match.group(1).strip()
#     return text.strip()

# def add_fullscreen_feature(html_code):
#     """Injects the Fullscreen Toggle Button"""
#     fullscreen_script = """
#     <div id="fs-controls" style="position: fixed; bottom: 30px; right: 30px; z-index: 9999;">
#         <button onclick="toggleFullScreen()" 
#                 style="background: #111827; color: #fff; border: 1px solid #374151; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
#             ⛶ Full Screen
#         </button>
#     </div>
#     <script>
#     function toggleFullScreen() {
#       if (!document.fullscreenElement) { document.documentElement.requestFullscreen(); } 
#       else { if (document.exitFullscreen) { document.exitFullscreen(); } }
#     }
#     </script>
#     """
#     if "</body>" in html_code: return html_code.replace("</body>", fullscreen_script + "</body>")
#     return html_code + fullscreen_script

# # --- 4. NEXT LEVEL AI LOGIC ---
# def generate_page_design(page_spec, project_name):
#     if not model: return "ERROR: Model not loaded."
    
#     prompt = f"""
#     You are a Senior UI/UX Engineer.
#     PROJECT: {project_name} | PAGE: {page_spec.get('title')}
#     COMPONENTS: {json.dumps(page_spec.get('components'))}
    
#     *** DESIGN SPECIFICATIONS (NEXT LEVEL) ***
#     1. STACK: HTML5 + Tailwind CSS (CDN).
#     2. FONTS: Google Fonts 'Inter'.
    
#     3. 📸 IMAGES (MANDATORY):
#        - Use 'https://picsum.photos/seed/{{random_keyword}}/800/600' for hero images.
#        - Use 'https://i.pravatar.cc/150?img={{random_number}}' for avatars.
    
#     4. 📊 GRAPHS & CHARTS (CRITICAL):
#        - Use Chart.js <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
#        - **IMPORTANT:** Wrap all Chart.js code inside:
#          document.addEventListener("DOMContentLoaded", function() {{ ... }});
    
#     5. INTERACTIVITY: Buttons must have hover states.
    
#     OUTPUT: RETURN ONLY THE RAW HTML CODE.
#     """

#     try:
#         # 1. Setup the "Live Canvas" placeholder
#         preview_container = st.empty()
#         status_text = st.empty()
        
#         full_text = ""
#         chunk_counter = 0
        
#         # 2. Stream the response
#         response = model.generate_content(prompt, stream=True)
        
#         status_text.caption("🎨 AI is painting... (Preview updates every few seconds to prevent flickering)")
        
#         for chunk in response:
#             full_text += chunk.text
#             chunk_counter += 1
            
#             # 3. "Stop-Motion" Update: Only refresh canvas every 15 chunks
#             # This minimizes the "Iframe Flash" while still showing progress.
#             if chunk_counter % 15 == 0:
#                 # Clean the partial HTML so it doesn't break the iframe
#                 partial_html = clean_ai_response(full_text)
                
#                 # Only render if we have a valid HTML start tag to avoid ugly text rendering
#                 if "<!DOCTYPE" in partial_html or "<html" in partial_html:
#                      with preview_container.container():
#                         # We use a shorter height during building to focus on active area
#                         components.html(partial_html, height=750, scrolling=True)

#         # 4. Final Polish: Clear status and show final result
#         status_text.empty()
#         final_html = clean_ai_response(full_text)
#         final_html = add_fullscreen_feature(final_html)
        
#         # Force one final render to ensure everything is perfect
#         with preview_container.container():
#              components.html(final_html, height=750, scrolling=True)
             
#         return final_html

#     except Exception as e:
#         return f"<h1>AI Error</h1><p>{str(e)}</p>"
# def refine_page_design(current_code, feedback, page_spec):
#     if not model: return "ERROR: Model not loaded."
#     prompt = f"""
#     Refine this HTML based on feedback.
#     CURRENT CODE: {current_code}
#     FEEDBACK: "{feedback}"
    
#     RULES:
#     - Keep the Chart.js graphs if they exist.
#     - Keep the Tailwind styling.
#     - If user asks for a chart, add Chart.js logic.
    
#     OUTPUT: RETURN ONLY THE UPDATED HTML CODE.
#     """
#     try:
#         result = model.generate_content(prompt)
#         raw_html = clean_ai_response(result.text)
#         if "toggleFullScreen" not in raw_html: return add_fullscreen_feature(raw_html)
#         return raw_html
#     except Exception as e:
#         return f"<h1>AI Error</h1><p>{str(e)}</p>"

# # --- 5. MAIN UI ---
# def main():
#     try:
#         st.set_page_config(page_title="Design Agent Pro", layout="wide", page_icon="🎨")
#     except: pass
    
#     st.title("🎨 Design Agent (Pro Max)")
#     st.caption("Now with Graphs, Charts & Real Images.")
    
#     init_design_db()

#     plans = get_approved_blueprints()
#     if not plans:
#         st.warning("⚠️ No Blueprints found. Run Plan Agent first.")
#         st.stop()

#     # SIDEBAR
#     with st.sidebar:
#         st.header("Project Select")
#         project_opts = {f"{p[1]}": p for p in plans}
#         selected_proj_name = st.selectbox("Blueprint:", list(project_opts.keys()))
#         project_id = project_opts[selected_proj_name][0]
#         blueprint = json.loads(project_opts[selected_proj_name][2])
        
#         st.divider()
#         st.header("Page Navigation")
#         pages = blueprint.get('pages', [])
#         page_names = [p['title'] for p in pages]
#         selected_page_title = st.radio("Select Page to Edit:", page_names)
#         target_page = next(p for p in pages if p['title'] == selected_page_title)

#     # MAIN WORKSPACE
#     col1, col2 = st.columns([1, 2.5], gap="large")
#     session_key = f"code_{project_id}_{selected_page_title}"

#     with col1:
#         st.subheader(f"🛠️ Controls: {selected_page_title}")
        
#         if st.button(f"✨ Generate Visuals", type="primary", use_container_width=True):
#             if not model: st.error("❌ Check API Key")
#             else:
#                 with st.spinner("Generating Charts & Visuals..."):
#                     code = generate_page_design(target_page, blueprint['project_name'])
#                     st.session_state[session_key] = code
#                     st.toast("Design Generated!", icon="🎨")

#         if session_key in st.session_state:
#             st.divider()
#             st.markdown("### 💬 Refine")
#             feedback = st.text_area("Adjustment:", placeholder="e.g. Change the chart to a Line chart, make the images smaller...")
            
#             if st.button("Apply Changes", use_container_width=True):
#                 with st.spinner("Refining..."):
#                     new_code = refine_page_design(st.session_state[session_key], feedback, target_page)
#                     st.session_state[session_key] = new_code
#                     st.rerun()

#     with col2:
#         st.subheader("🖥️ Preview")
#         if session_key in st.session_state:
#             html_code = st.session_state[session_key]
            
#             with st.container(border=True):
#                 components.html(html_code, height=750, scrolling=True)
            
#             if st.button("💾 Approve & Save"):
#                 save_approved_design(project_id, selected_page_title, html_code)
#                 st.success("Design saved!")
#         else:
#             st.info("👈 Select a page and click 'Generate'.")

# if __name__ == "__main__":
#     main()
import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import streamlit.components.v1 as components
import os
import re

# --- 1. CONFIGURATION ---
model = None
try:
    # Check secrets (Cloud) or session state (Local)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    elif "api_key" in st.session_state:
        api_key = st.session_state["api_key"]
    else:
        api_key = "AIzaSy..." # Fallback for local testing only
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite', generation_config={"temperature": 0.2})
except Exception as e:
    st.error(f"Configuration Error: {e}")

# --- 2. DATABASE ---
# Robust path finding for Cloud Hosting
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(ROOT_DIR, 'ips_sdlc.db')

def init_design_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS page_designs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      project_id INTEGER,
                      page_title TEXT, 
                      html_code TEXT, 
                      status TEXT,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    except: pass

def get_approved_blueprints():
    if not os.path.exists(DB_PATH): return []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Fetch plans. Note: On Cloud reboot, this might be empty if not persistent.
        plans = c.execute("SELECT id, project_name, structured_plan FROM project_plans WHERE status='APPROVED' ORDER BY id DESC").fetchall()
        conn.close()
        return plans
    except: return []

def save_approved_design(project_id, page_title, html_code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    exists = c.execute("SELECT id FROM page_designs WHERE project_id=? AND page_title=?", (project_id, page_title)).fetchone()
    if exists:
        c.execute("UPDATE page_designs SET html_code=?, status='APPROVED' WHERE id=?", (html_code, exists[0]))
    else:
        c.execute("INSERT INTO page_designs (project_id, page_title, html_code, status) VALUES (?, ?, ?, 'APPROVED')",
                  (project_id, page_title, html_code))
    conn.commit()
    conn.close()

# --- 3. UTILS ---
def clean_ai_response(text):
    pattern = r"```(?:html)?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.strip()

def add_fullscreen_feature(html_code):
    fullscreen_script = """
    <div id="fs-controls" style="position: fixed; bottom: 30px; right: 30px; z-index: 9999;">
        <button onclick="toggleFullScreen()" 
                style="background: #111827; color: #fff; border: 1px solid #374151; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            ⛶ Full Screen
        </button>
    </div>
    <script>
    function toggleFullScreen() {
      if (!document.fullscreenElement) { document.documentElement.requestFullscreen(); } 
      else { if (document.exitFullscreen) { document.exitFullscreen(); } }
    }
    </script>
    """
    if "</body>" in html_code: return html_code.replace("</body>", fullscreen_script + "</body>")
    return html_code + fullscreen_script

# --- 4. GENERATION LOGIC ---
def generate_page_design(page_spec, project_name, theme_style):
    if not model: return "ERROR: Model not loaded."
    
    prompt = f"""
    You are a Senior UI/UX Engineer.
    PROJECT: {project_name} | PAGE: {page_spec.get('title')}
    THEME STYLE: {theme_style} (Strictly enforce this look)
    COMPONENTS: {json.dumps(page_spec.get('components'))}
    
    *** DESIGN SPECIFICATIONS ***
    1. STACK: HTML5 + Tailwind CSS (CDN).
    2. VISUALS:
       - Use 'https://picsum.photos/seed/{{random}}/800/600' for images.
       - Use 'https://i.pravatar.cc/150?img={{random}}' for avatars.
       - If theme is 'Dark', use 'bg-slate-900 text-white'.
       
    3. GRAPHS:
       - Use Chart.js <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
       - Wrap Chart logic in: document.addEventListener("DOMContentLoaded", ...)
    
    4. INTERACTIVITY: Buttons must have hover states.
    
    OUTPUT: RAW HTML CODE ONLY.
    """

    try:
        # LIVE STREAMING PREVIEW
        preview_container = st.empty()
        full_text = ""
        chunk_counter = 0
        
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            full_text += chunk.text
            chunk_counter += 1
            # Update preview every ~20 chunks to avoid strobe effect
            if chunk_counter % 20 == 0:
                 partial_html = clean_ai_response(full_text)
                 if "<html" in partial_html:
                     with preview_container.container():
                        components.html(partial_html, height=750, scrolling=True)

        final_html = add_fullscreen_feature(clean_ai_response(full_text))
        
        # Final render
        with preview_container.container():
             components.html(final_html, height=750, scrolling=True)
             
        return final_html

    except Exception as e:
        return f"<h1>AI Error</h1><p>{str(e)}</p>"

# --- 5. MAIN UI ---
def main():
    try: st.set_page_config(page_title="Design Agent", layout="wide", page_icon="🎨")
    except: pass
    
    st.title("🎨 Design Agent")
    init_design_db()

    plans = get_approved_blueprints()
    if not plans:
        st.warning("⚠️ No Blueprints found. Run Plan Agent first.")
        st.stop()

    with st.sidebar:
        st.header("1. Configuration")
        # PROJECT SELECT
        project_opts = {f"{p[1]}": p for p in plans}
        selected_proj_name = st.selectbox("Select Project:", list(project_opts.keys()))
        project_id = project_opts[selected_proj_name][0]
        blueprint = json.loads(project_opts[selected_proj_name][2])
        
        # THEME SELECT (New Feature!)
        theme = st.selectbox("Visual Theme:", [
            "Modern SaaS (White/Blue)", 
            "Netflix Dark (Black/Red)", 
            "Spotify Dark (Black/Green)", 
            "Playful (Pastel/Rounded)"
        ])
        
        st.divider()
        st.header("2. Page Select")
        pages = blueprint.get('pages', [])
        page_names = [p['title'] for p in pages]
        selected_page_title = st.radio("Target Page:", page_names)
        target_page = next(p for p in pages if p['title'] == selected_page_title)

    col1, col2 = st.columns([1, 3], gap="large")
    session_key = f"code_{project_id}_{selected_page_title}"

    with col1:
        st.subheader("Controls")
        
        if st.button(f"✨ Generate Design", type="primary", use_container_width=True):
            if not model: st.error("❌ Check API Key")
            else:
                with st.spinner("Streaming Code..."):
                    code = generate_page_design(target_page, blueprint['project_name'], theme)
                    st.session_state[session_key] = code
                    st.toast("Design Ready!", icon="✅")

        # DOWNLOAD BUTTON (New Feature!)
        if session_key in st.session_state:
            st.divider()
            html_data = st.session_state[session_key]
            st.download_button(
                label="📥 Download HTML File",
                data=html_data,
                file_name=f"{selected_page_title.lower().replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

    with col2:
        st.subheader("Live Preview")
        if session_key in st.session_state:
            html_code = st.session_state[session_key]
            # No need to render here again if the generator did it, 
            # but we keep it for persistence on refresh
            components.html(html_code, height=750, scrolling=True)
            
            if st.button("💾 Save to DB"):
                save_approved_design(project_id, selected_page_title, html_code)
                st.success("Saved!")
        else:
            st.info("👈 Select a page and theme to begin.")

if __name__ == "__main__":
    main()