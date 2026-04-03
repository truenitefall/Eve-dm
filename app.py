import streamlit as st
from groq import Groq
import json
import urllib.parse
import re

# --- CONFIG ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

# Custom CSS for the HUD and general vibe
st.markdown("""
    <style>
    .status-board {
        background-color: #1a1a2e; border: 2px solid #00d4ff; padding: 15px;
        border-radius: 10px; color: #e0e0e0; font-family: sans-serif;
        margin-bottom: 20px; position: sticky; top: 0; z-index: 999;
    }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "phase" not in st.session_state:
    st.session_state.phase = "Session 0"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}
if "current_image_url" not in st.session_state:
    # Default starting image
    st.session_state.current_image_url = "https://pollinations.ai/p/cyberpunk%20city%20with%20magic%20neon"

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Phase:** {st.session_state.phase}")
    
    with st.expander("Register Agents", expanded=(not st.session_state.game_started)):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = {"concept": p_concept}
                if st.session_state.game_started:
                    st.session_state.messages.append({"role": "system", "content": f"System Alert: {p_name} joined. Concept: {p_concept}."})
                st.success(f"{p_name} registered.")

    st.divider()
    
    # --- VISUAL FEED (FIXED) ---
    st.subheader("📡 Visual Feed")
    st.image(st.session_state.current_image_url, caption="Eve's Visual Construct")
    
    if st.button("🔄 Refresh Image"):
        st.rerun()

    st.divider()
    # Save/Load for Brad
    campaign_data = {"party": st.session_state.party, "messages": st.session_state.messages, "game_started": st.session_state.game_started, "phase": st.session_state.phase, "img": st.session_state.current_image_url}
    st.download_button("💾 Save (BRAD)", json.dumps(campaign_data), file_name="new_cyre_save.json")
    
    uploaded_file = st.file_uploader("📂 Load (BRAD)", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        st.session_state.update(data)
        st.rerun()

# --- THE STATUS HUD ---
if st.session_state.game_started:
    st.markdown(f"""<div class="status-board"><b>📍 NEW CYRE</b> | <b>🎭 {st.session_state.phase}</b> | <b>👥 AGENTS:</b> {', '.join(st.session_state.party.keys())}</div>""", unsafe_allow_html=True)

# --- MAIN ENGINE ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    if st.button("🚀 INITIATE SESSION 0"):
        if st.session_state.party:
            party_info = "\n".join([f"{n}: {d['concept']}" for n, d in st.session_state.party.items()])
            sys_prompt = f"""You are Eve, the DM. Setting: New Cyre. Party: {party_info}. 
            To update the visual feed, end your message with: IMAGE-PROMPT: (description)."""
            
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}], temperature=0.8)
            ans = response.choices[0].message.content
            
            if 'IMAGE-PROMPT:' in ans:
                p = ans.split("IMAGE-PROMPT:")[-1].strip()
                st.session_state.current_image_url = f"https://pollinations.ai/p/{urllib.parse.quote(p)}"

            st.session_state.messages.append({"role": "system", "content": sys_prompt})
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.game_started = True
            st.rerun()
else:
    # Phase Controls
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.phase == "Session 0" and st.button("✅ Start Char Creation"):
            st.session_state.phase = "Character Creation"
            st.rerun()
    with c2:
        if st.session_state.phase == "Character Creation" and st.button("⚔️ START CAMPAIGN"):
            st.session_state.phase = "Active Campaign"
            st.rerun()

    # Chat Display
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            # Clean prompt tags for the chat bubbles
            clean_text = re.sub(r'IMAGE-PROMPT:.*', '', msg["content"]).strip()
            if clean_text:
                with st.chat_message(msg["role"]): st.markdown(clean_text)

    # Input
    if u_input := st.chat_input("Speak or type..."):
        st.session_state.messages.append({"role": "user", "content": u_input})
        with st.chat_message("user"): st.markdown(u_input)
        with st.chat_message("assistant"):
            r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages, temperature=0.7)
            ans = r.choices[0].message.content
            if 'IMAGE-PROMPT:' in ans:
                p = ans.split("IMAGE-PROMPT:")[-1].strip()
                st.session_state.current_image_url = f"https://pollinations.ai/p/{urllib.parse.quote(p)}"
            st.markdown(re.sub(r'IMAGE-PROMPT:.*', '', ans).strip())
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()
