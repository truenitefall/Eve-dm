import streamlit as st
from groq import Groq
import json
import urllib.parse
import re

# --- CONFIG ---
st.set_page_config(page_title="Eve: Hybrid DM", layout="wide")

# --- GLOBAL STORE (Shared World) ---
@st.cache_resource
def get_global_state():
    return {
        "world_history": [],
        "game_log": [],
        "phase": "Session 0",
        "current_image": "https://pollinations.ai/p/cyberpunk%20city%20with%20magic%20neon",
        "agents": {}
    }

world = get_global_state()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- LOCAL STORE (Private Character Sheet) ---
if "my_char_log" not in st.session_state:
    st.session_state.my_char_log = []
if "my_name" not in st.session_state:
    st.session_state.my_name = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    
    if not st.session_state.my_name:
        name_input = st.text_input("Identify yourself (Name):")
        if st.button("Login"):
            st.session_state.my_name = name_input
            st.rerun()
    else:
        st.write(f"Logged in as: **{st.session_state.my_name}**")
        st.write(f"**Phase:** {world['phase']}")
    
    st.divider()
    st.subheader("📡 Visual Feed")
    st.image(world["current_image"])
    
    if st.button("🔄 Sync with Table"):
        st.rerun()

# --- MAIN INTERFACE ---
if world["phase"] == "Session 0":
    st.header("✨ Phase 1: World History")
    if not world["world_history"]:
        if st.button("Generate World History"):
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are Eve. Narrate the history of New Cyre. End with IMAGE-PROMPT: (desc)."}],
                temperature=0.8
            )
            ans = r.choices[0].message.content
            world["world_history"].append(ans)
            if 'IMAGE-PROMPT:' in ans:
                p = ans.split("IMAGE-PROMPT:")[-1].strip()
                world["current_image"] = f"https://pollinations.ai/p/{urllib.parse.quote(p)}"
            st.rerun()
    
    for msg in world["world_history"]:
        st.markdown(re.sub(r'IMAGE-PROMPT:.*', '', msg))
    
    if st.button("Proceed to Character Creation"):
        world["phase"] = "Character Creation"
        st.rerun()

elif world["phase"] == "Character Creation":
    st.header(f"🧬 Agent Creation: {st.session_state.my_name}")
    st.info("This chat is PRIVATE. Tell Eve what kind of character you want to be.")
    
    for msg in st.session_state.my_char_log:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("Talk to Eve about your character..."):
        st.session_state.my_char_log.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are Eve. Help this player build a Modern 5e character. Be specific with stats."}] + st.session_state.my_char_log,
            temperature=0.7
        )
        ans = r.choices[0].message.content
        st.session_state.my_char_log.append({"role": "assistant", "content": ans})
        st.rerun()
    
    if st.button("I am Ready! Join Campaign"):
        world["agents"][st.session_state.my_name] = "Ready"
        # If everyone is ready (or you decide), move to campaign
        if st.checkbox("Admin: Force Start Campaign"):
            world["phase"] = "Active Campaign"
            st.rerun()

elif world["phase"] == "Active Campaign":
    st.header("⚔️ Live Campaign")
    # Shared game log
    for msg in world["game_log"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if g_input := st.chat_input("Speak/Action..."):
        full_input = f"{st.session_state.my_name}: {g_input}"
        world["game_log"].append({"role": "user", "content": full_input})
        
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are Eve. DM this shared game."}] + world["game_log"],
            temperature=0.7
        )
        ans = r.choices[0].message.content
        world["game_log"].append({"role": "assistant", "content": ans})
        st.rerun()
      
