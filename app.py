import streamlit as st
from groq import Groq
import json
import urllib.parse
import re

# --- CONFIG ---
st.set_page_config(page_title="Eve: Shared Modern DM", layout="wide")

# --- SHARED DATA STORE (The "Global Table") ---
# This allows everyone on the link to see the same data.
@st.cache_resource
def get_global_state():
    return {
        "game_started": False,
        "phase": "Session 0",
        "messages": [],
        "party": {},
        "current_image_url": "https://pollinations.ai/p/cyberpunk%20city%20with%20magic%20neon"
    }

game_state = get_global_state()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    st.write(f"**Phase:** {game_state['phase']}")
    
    with st.expander("Register Agents"):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept")
        if st.button("Add to Game"):
            if p_name:
                game_state["party"][p_name] = {"concept": p_concept}
                st.success(f"{p_name} registered!")
                st.rerun()

    st.divider()
    st.subheader("📡 Visual Feed")
    st.image(game_state["current_image_url"], caption="Shared Visual")
    
    if st.button("🔄 Sync/Refresh Table"):
        st.rerun()

    if st.button("🗑️ Reset Global Game"):
        game_state.update(get_global_state.__wrapped__())
        st.rerun()

# --- THE STATUS HUD ---
if game_state["game_started"]:
    st.markdown(f"""<div style="background:#1a1a2e; border:2px solid #00d4ff; padding:10px; border-radius:10px; color:white; margin-bottom:20px;">
        <b>📍 NEW CYRE</b> | <b>🎭 {game_state['phase']}</b> | <b>👥 AGENTS:</b> {', '.join(game_state['party'].keys())}
    </div>""", unsafe_allow_html=True)

# --- MAIN ENGINE ---
if not game_state["game_started"]:
    st.header("✨ Project: New Cyre")
    if st.button("🚀 INITIATE SHARED SESSION"):
        if game_state["party"]:
            party_info = "\n".join([f"{n}: {d['concept']}" for n, d in game_state["party"].items()])
            sys_prompt = f"System: You are Eve, the DM. Setting: New Cyre. Party: {party_info}. End with IMAGE-PROMPT: (desc)."
            
            r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}], temperature=0.8)
            ans = r.choices[0].message.content
            
            if 'IMAGE-PROMPT:' in ans:
                p = ans.split("IMAGE-PROMPT:")[-1].strip()
                game_state["current_image_url"] = f"https://pollinations.ai/p/{urllib.parse.quote(p)}"

            game_state["messages"].append({"role": "system", "content": sys_prompt})
            game_state["messages"].append({"role": "assistant", "content": ans})
            game_state["game_started"] = True
            st.rerun()
else:
    # Phase Controls
    c1, c2 = st.columns(2)
    with c1:
        if game_state["phase"] == "Session 0" and st.button("✅ Start Char Creation"):
            game_state["phase"] = "Character Creation"
            # Force Eve to give the class options immediately
            creation_prompt = "Update: Start Character Creation. Eve, provide the list of modern class archetypes now."
            game_state["messages"].append({"role": "system", "content": creation_prompt})
            r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=game_state["messages"], temperature=0.7)
            game_state["messages"].append({"role": "assistant", "content": r.choices[0].message.content})
            st.rerun()

    # Chat Display
    for msg in game_state["messages"]:
        if msg["role"] != "system":
            clean_text = re.sub(r'IMAGE-PROMPT:.*', '', msg["content"]).strip()
            if clean_text:
                with st.chat_message(msg["role"]): st.markdown(clean_text)

    # Input
    if u_input := st.chat_input("Enter action..."):
        game_state["messages"].append({"role": "user", "content": u_input})
        r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=game_state["messages"], temperature=0.7)
        ans = r.choices[0].message.content
        if 'IMAGE-PROMPT:' in ans:
            p = ans.split("IMAGE-PROMPT:")[-1].strip()
            game_state["current_image_url"] = f"https://pollinations.ai/p/{urllib.parse.quote(p)}"
        game_state["messages"].append({"role": "assistant", "content": ans})
        st.rerun()
      
