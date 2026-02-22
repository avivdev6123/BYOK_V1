"""
BYOK Router Chat UI — Streamlit (Milestone 4)

Multi-page app: Chat + API Keys management.
Sidebar has navigation, settings, and user avatar menu.
"""

import requests
import streamlit as st

st.set_page_config(page_title="BYOK Router", layout="wide", initial_sidebar_state="expanded")

PROVIDER_ACCOUNT_URLS = {
    "gemini": "https://aistudio.google.com/apikey",
    "openai": "https://platform.openai.com/account/billing",
    "anthropic": "https://console.anthropic.com/settings/billing",
}

# --- Session state defaults ---
for key, default in [
    ("messages", []),
    ("auth_token", None),
    ("username", None),
    ("user_id", None),
    ("api_url", "http://127.0.0.1:8000"),
    ("page", "Chat"),
    ("theme", "dark"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ──────────────────────────────────────────────────────────


def _headers() -> dict:
    if st.session_state.auth_token:
        return {"Authorization": f"Bearer {st.session_state.auth_token}"}
    return {}


def _bidi(text: str):
    """Render markdown text with automatic bidi direction (LTR/RTL)."""
    st.markdown(f'<div dir="auto">{text}</div>', unsafe_allow_html=True)


def format_rate_limit_error(detail: str) -> str | None:
    detail_lower = detail.lower()
    if "429" not in detail_lower and "quota" not in detail_lower and "rate" not in detail_lower:
        return None
    for provider, url in PROVIDER_ACCOUNT_URLS.items():
        if provider in detail_lower:
            return (
                f"The **{provider}** API has reached its usage limit. "
                f"Please upgrade your plan: [{provider} account]({url})"
            )
    return "An API provider has reached its usage limit. Please check your provider account."


def build_contextual_prompt(messages: list[dict], new_input: str) -> str:
    if not messages:
        return new_input
    parts = ["Previous conversation:"]
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        parts.append(f"{role}: {msg['content']}")
    parts.append("")
    parts.append(f"User: {new_input}")
    parts.append("")
    parts.append("Respond to the latest user message, using the conversation above as context.")
    return "\n".join(parts)


def _do_logout():
    api_url = st.session_state.api_url
    try:
        requests.post(f"{api_url}/v1/auth/logout", headers=_headers(), timeout=5)
    except requests.RequestException:
        pass
    st.session_state.auth_token = None
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.messages = []
    st.session_state.page = "Chat"
    st.rerun()


# ── Auth Gate ────────────────────────────────────────────────────────

def show_auth_page():
    st.title("BYOK Router")
    st.caption("Bring Your Own Key — LLM routing platform")

    api_url = st.text_input("Server URL", value=st.session_state.api_url, key="auth_api_url")
    st.session_state.api_url = api_url

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    try:
                        resp = requests.post(
                            f"{api_url}/v1/auth/login",
                            json={"username": username, "password": password},
                            timeout=10,
                        )
                        if resp.ok:
                            data = resp.json()
                            st.session_state.auth_token = data["session_token"]
                            st.session_state.username = data["username"]
                            st.session_state.user_id = data["user_id"]
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Login failed"))
                    except requests.RequestException as e:
                        st.error(f"Cannot reach server: {e}")

    with register_tab:
        with st.form("register_form"):
            new_user = st.text_input("Username", key="reg_user")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            submitted = st.form_submit_button("Register", use_container_width=True)
            if submitted:
                if not new_user or not new_pass:
                    st.error("Please fill in both fields.")
                elif len(new_user) < 3:
                    st.error("Username must be at least 3 characters.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        resp = requests.post(
                            f"{api_url}/v1/auth/register",
                            json={"username": new_user, "password": new_pass},
                            timeout=10,
                        )
                        if resp.ok:
                            data = resp.json()
                            st.session_state.auth_token = data["session_token"]
                            st.session_state.username = data["username"]
                            st.session_state.user_id = data["user_id"]
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Registration failed"))
                    except requests.RequestException as e:
                        st.error(f"Cannot reach server: {e}")


# ── Sidebar (authenticated) ─────────────────────────────────────────

def _theme_css():
    """Inject CSS for light or dark mode based on the Figma dashboard template."""
    is_dark = st.session_state.theme == "dark"

    if is_dark:
        # ── Dark mode tokens ──
        sidebar_bg = "#16162A"
        sidebar_border = "rgba(255,255,255,0.06)"
        main_bg = "#1A1A2E"
        text_primary = "#E2E8F0"
        text_muted = "#9CA3AF"
        text_section = "#4B5563"
        divider_color = "rgba(255,255,255,0.06)"
        nav_hover_bg = "rgba(99,102,241,0.08)"
        nav_hover_text = "#E2E8F0"
        nav_active_bg = "rgba(99,102,241,0.12)"
        nav_active_text = "#818CF8"
        help_color = "#6B7280"
        logout_color = "#F87171"
        logout_hover_bg = "rgba(248,113,113,0.08)"
        logout_hover_text = "#FCA5A5"
        expander_content_bg = "rgba(255,255,255,0.02)"
        expander_content_border = "rgba(255,255,255,0.06)"
        role_color = "#6B7280"
        avatar_shadow = "0 2px 8px rgba(232,69,124,0.3)"
    else:
        # ── Light mode tokens (from Figma left panel) ──
        sidebar_bg = "#FFFFFF"
        sidebar_border = "#F0F0F0"
        main_bg = "#FAFAFA"
        text_primary = "#1E293B"
        text_muted = "#64748B"
        text_section = "#94A3B8"
        divider_color = "#E2E8F0"
        nav_hover_bg = "rgba(99,102,241,0.06)"
        nav_hover_text = "#334155"
        nav_active_bg = "rgba(99,102,241,0.10)"
        nav_active_text = "#4F46E5"
        help_color = "#64748B"
        logout_color = "#EF4444"
        logout_hover_bg = "rgba(239,68,68,0.06)"
        logout_hover_text = "#DC2626"
        expander_content_bg = "#F8FAFC"
        expander_content_border = "#E2E8F0"
        role_color = "#94A3B8"
        avatar_shadow = "0 2px 8px rgba(232,69,124,0.2)"

    st.markdown(f"""
    <style>
    /* ── Sidebar container ── */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {sidebar_border};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0 !important;
    }}

    /* ── Profile header ── */
    .sb-profile {{
        display: flex; align-items: center; gap: 12px;
        padding: 20px 16px 16px;
    }}
    .sb-avatar {{
        width: 44px; height: 44px; border-radius: 50%;
        background: linear-gradient(135deg, #E8457C, #F06292);
        color: #fff; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 18px; flex-shrink: 0;
        box-shadow: {avatar_shadow};
    }}
    .sb-role {{
        font-size: 10px; color: {role_color}; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px;
    }}
    .sb-username {{
        font-size: 15px; font-weight: 600; color: {text_primary};
    }}

    /* ── Section labels ── */
    .sb-section {{
        font-size: 10px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.2px; color: {text_section}; padding: 20px 16px 8px;
    }}

    /* ── Divider ── */
    .sb-divider {{
        border: none; border-top: 1px solid {divider_color};
        margin: 4px 16px;
    }}

    /* ── Nav buttons ── */
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: {text_muted} !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 16px !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {nav_hover_bg} !important;
        color: {nav_hover_text} !important;
    }}

    /* ── Bottom items ── */
    .sb-bottom-help button {{
        color: {help_color} !important;
    }}
    .sb-bottom-logout button {{
        color: {logout_color} !important;
    }}
    .sb-bottom-logout button:hover {{
        background: {logout_hover_bg} !important;
        color: {logout_hover_text} !important;
    }}

    /* ── Active nav item highlight ── */
    .sb-nav-active button {{
        background: {nav_active_bg} !important;
        color: {nav_active_text} !important;
        font-weight: 600 !important;
    }}

    /* ── Expander in sidebar (Settings) ── */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {{
        color: {text_muted} !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        background: transparent !important;
        border: none !important;
    }}
    section[data-testid="stSidebar"] .streamlit-expanderContent {{
        background: {expander_content_bg} !important;
        border: 1px solid {expander_content_border} !important;
        border-radius: 8px !important;
    }}

    /* ── Main content area ── */
    .main .block-container {{
        background: {main_bg};
    }}
    .main {{
        background: {main_bg} !important;
    }}

    /* ── Header ── */
    header[data-testid="stHeader"] {{
        background: {main_bg} !important;
    }}

    /* ── Theme toggle button ── */
    .sb-theme-toggle {{
        display: flex; align-items: center; justify-content: center;
        gap: 6px; padding: 6px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 500; cursor: pointer;
        color: {text_muted};
        background: {'rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.04)'};
        border: 1px solid {divider_color};
        margin: 0 16px;
    }}

    /* ── Light mode overrides for main text ── */
    {"" if is_dark else '''
    .main .block-container, .main .block-container p,
    .main .block-container h1, .main .block-container h2, .main .block-container h3,
    .main .block-container span, .main .block-container label {{
        color: #1E293B !important;
    }}
    .stChatMessage {{
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
    }}
    .stChatInput > div {{
        background: #FFFFFF !important;
        border-color: #D1D5DB !important;
    }}
    .stChatInput textarea {{
        color: #1E293B !important;
    }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {{
        color: #334155 !important;
    }}
    '''}
    </style>
    """, unsafe_allow_html=True)


def show_sidebar():
    with st.sidebar:
        _theme_css()

        uname = st.session_state.username or "User"
        initial = uname[0].upper()
        current_page = st.session_state.page
        is_dark = st.session_state.theme == "dark"

        # ── User profile header ──
        st.markdown(
            f'<div class="sb-profile">'
            f'<div class="sb-avatar">{initial}</div>'
            f'<div>'
            f'<div class="sb-role">BYOK USER</div>'
            f'<div class="sb-username">{uname}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Theme toggle ──
        toggle_label = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(toggle_label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        # ── MAIN section ──
        st.markdown('<div class="sb-section">MAIN</div>', unsafe_allow_html=True)

        chat_wrap = "sb-nav-active" if current_page == "Chat" else ""
        keys_wrap = "sb-nav-active" if current_page == "API Keys" else ""

        st.markdown(f'<div class="{chat_wrap}">', unsafe_allow_html=True)
        if st.button("💬  Chat", key="nav_chat", use_container_width=True):
            st.session_state.page = "Chat"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="{keys_wrap}">', unsafe_allow_html=True)
        if st.button("🔑  API Keys", key="nav_keys", use_container_width=True):
            st.session_state.page = "API Keys"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        # ── SETTINGS section ──
        st.markdown('<div class="sb-section">SETTINGS</div>', unsafe_allow_html=True)

        with st.expander("⚙️  Settings"):
            st.session_state.api_url = st.text_input(
                "Server URL", value=st.session_state.api_url, label_visibility="collapsed",
            )
            if st.button("Clear chat history", key="clear_chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        # ── Bottom: Help + Logout ──
        st.markdown('<div style="flex:1;min-height:40px;"></div>', unsafe_allow_html=True)
        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        st.markdown('<div class="sb-bottom-help">', unsafe_allow_html=True)
        with st.popover("❓  Help", use_container_width=True):
            st.markdown("**BYOK Router** — Bring Your Own Key")
            st.markdown("Route prompts to the best LLM provider based on task type, cost, and latency.")
            st.markdown("- **Chat** — Send prompts and get routed completions")
            st.markdown("- **API Keys** — Manage your provider keys")
            st.link_button("Account Settings", "#", use_container_width=True, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-bottom-logout">', unsafe_allow_html=True)
        if st.button("🚪  Logout Account", key="sidebar_logout", use_container_width=True):
            _do_logout()
        st.markdown('</div>', unsafe_allow_html=True)


# ── API Keys Page ────────────────────────────────────────────────────

def show_keys_page():
    api_url = st.session_state.api_url

    st.title("API Key Management")
    st.caption("Add, edit, or remove your provider API keys. Keys are encrypted at rest.")

    # Fetch current keys
    try:
        keys_resp = requests.get(f"{api_url}/v1/keys", headers=_headers(), timeout=5)
        stored_keys = keys_resp.json().get("keys", []) if keys_resp.ok else []
    except requests.RequestException:
        stored_keys = []

    stored_providers = {k["provider"]: k for k in stored_keys}

    # Render 3 provider boxes in columns
    cols = st.columns(3)
    for i, prov in enumerate(["gemini", "openai", "anthropic"]):
        with cols[i]:
            with st.container(border=True):
                if prov in stored_providers:
                    matched = stored_providers[prov]
                    status = matched.get("status", "pending")

                    # Status tag
                    if status == "active":
                        bg, fg, label = "#166534", "#bbf7d0", "Active"
                    elif status == "invalid":
                        bg, fg, label = "#991b1b", "#fecaca", "Invalid"
                    else:
                        bg, fg, label = "#854d0e", "#fef08a", "Pending"

                    st.markdown(
                        f'### {prov.capitalize()} &nbsp; '
                        f'<span style="background:{bg};color:{fg};padding:3px 10px;'
                        f'border-radius:10px;font-size:12px;font-weight:600;'
                        f'vertical-align:middle;">{label}</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Key: `{matched['api_key_masked']}`")

                    # Expandable model list
                    models = matched.get("discovered_models") or []
                    if models:
                        with st.expander(f"Supported Models ({len(models)})"):
                            for m in models:
                                st.markdown(f"- `{m}`")
                    else:
                        st.caption("No models discovered")

                    # Action buttons
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("Revalidate", key=f"rev_{prov}", use_container_width=True):
                            with st.spinner("Validating..."):
                                try:
                                    requests.post(
                                        f"{api_url}/v1/keys/{prov}/revalidate",
                                        headers=_headers(),
                                        timeout=15,
                                    )
                                except requests.RequestException:
                                    pass
                            st.rerun()
                    with col_b:
                        if st.button("Edit", key=f"edit_{prov}", use_container_width=True):
                            st.session_state[f"confirm_edit_{prov}"] = True
                    with col_c:
                        if st.button("Remove", key=f"del_{prov}", use_container_width=True):
                            st.session_state[f"confirm_remove_{prov}"] = True

                    # Edit confirmation
                    if st.session_state.get(f"confirm_edit_{prov}"):
                        st.warning(f"Replace the **{prov}** API key?")
                        new_key = st.text_input(
                            "New API Key", type="password", key=f"edit_key_{prov}",
                        )
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            if st.button("Confirm", key=f"confirm_edit_yes_{prov}", use_container_width=True):
                                if new_key:
                                    with st.spinner("Saving..."):
                                        try:
                                            resp = requests.post(
                                                f"{api_url}/v1/keys",
                                                headers=_headers(),
                                                json={"provider": prov, "api_key": new_key},
                                                timeout=30,
                                            )
                                            if resp.ok:
                                                st.session_state[f"confirm_edit_{prov}"] = False
                                                st.rerun()
                                            else:
                                                st.error(resp.json().get("detail", "Failed"))
                                        except requests.RequestException as e:
                                            st.error(f"Error: {e}")
                                else:
                                    st.error("Please enter a key.")
                        with ce2:
                            if st.button("Cancel", key=f"confirm_edit_no_{prov}", use_container_width=True):
                                st.session_state[f"confirm_edit_{prov}"] = False
                                st.rerun()

                    # Remove confirmation
                    if st.session_state.get(f"confirm_remove_{prov}"):
                        st.warning(f"Are you sure you want to remove the **{prov}** key?")
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            if st.button("Yes, remove", key=f"confirm_del_yes_{prov}", use_container_width=True):
                                requests.delete(
                                    f"{api_url}/v1/keys/{prov}",
                                    headers=_headers(),
                                    timeout=5,
                                )
                                st.session_state[f"confirm_remove_{prov}"] = False
                                st.rerun()
                        with cr2:
                            if st.button("Cancel", key=f"confirm_del_no_{prov}", use_container_width=True):
                                st.session_state[f"confirm_remove_{prov}"] = False
                                st.rerun()

                else:
                    # No key set
                    st.markdown(
                        f'### {prov.capitalize()} &nbsp; '
                        f'<span style="background:#D1D5DB;color:#6B7280;padding:3px 10px;'
                        f'border-radius:10px;font-size:12px;font-weight:600;'
                        f'vertical-align:middle;">Not set</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption("No API key configured")
                    new_key = st.text_input(
                        "API Key", type="password", key=f"add_key_{prov}",
                    )
                    if st.button("Save", key=f"save_{prov}", use_container_width=True):
                        if new_key:
                            with st.spinner("Validating & saving..."):
                                try:
                                    resp = requests.post(
                                        f"{api_url}/v1/keys",
                                        headers=_headers(),
                                        json={"provider": prov, "api_key": new_key},
                                        timeout=30,
                                    )
                                    if resp.ok:
                                        st.rerun()
                                    else:
                                        st.error(resp.json().get("detail", "Failed"))
                                except requests.RequestException as e:
                                    st.error(f"Error: {e}")
                        else:
                            st.warning("Please enter an API key.")


# ── Chat Page ────────────────────────────────────────────────────────

def show_chat():
    api_url = st.session_state.api_url

    st.title("BYOK Router Chat")

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("routing"):
                st.caption(f"Routed to **{msg['routing'].get('provider', '')}** / `{msg['routing'].get('model', '')}`")

            _bidi(msg["content"])

            if msg.get("profile"):
                with st.expander("Prompt Profile"):
                    st.json(msg["profile"])

            if msg.get("sources"):
                with st.expander(f"Sources ({len(msg['sources'])})"):
                    for src in msg["sources"]:
                        st.markdown(f"- [{src['title']}]({src['url']})")

            if msg.get("routing"):
                with st.expander("Routing Details"):
                    st.json(msg["routing"])

    # Chat input
    if user_input := st.chat_input("Type your prompt..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            _bidi(user_input)

        with st.chat_message("assistant"):
            contextual_prompt = build_contextual_prompt(
                st.session_state.messages[:-1],
                user_input,
            )

            # Step 1: Profile
            with st.spinner("Profiling prompt..."):
                try:
                    profile_resp = requests.post(
                        f"{api_url}/v1/prompts",
                        headers=_headers(),
                        json={"username": st.session_state.username, "prompt": contextual_prompt},
                        timeout=30,
                    )
                    if not profile_resp.ok:
                        detail = profile_resp.json().get("detail", "")
                        friendly = format_rate_limit_error(detail)
                        if friendly:
                            st.warning(friendly)
                        else:
                            st.error(f"Profiling failed: {detail}")
                        st.stop()
                    profile_data = profile_resp.json()
                except requests.RequestException as e:
                    st.error(f"Profiling failed: {e}")
                    st.stop()

            prompt_id = profile_data["prompt_id"]
            profile_json = profile_data["prompt_profile_json"]

            with st.expander("Prompt Profile"):
                st.json(profile_json)

            # Step 2: Completion
            with st.spinner("Routing and generating response..."):
                try:
                    completion_resp = requests.post(
                        f"{api_url}/v1/completions",
                        headers=_headers(),
                        json={"prompt_id": prompt_id},
                        timeout=60,
                    )
                    if not completion_resp.ok:
                        detail = completion_resp.json().get("detail", "")
                        friendly = format_rate_limit_error(detail)
                        if friendly:
                            st.warning(friendly)
                        else:
                            st.error(f"Completion failed: {detail}")
                        st.stop()
                    completion_data = completion_resp.json()
                except requests.RequestException as e:
                    st.error(f"Completion failed: {e}")
                    st.stop()

            # Model caption
            provider = completion_data.get("provider", "")
            model = completion_data.get("model", "")
            st.caption(f"Routed to **{provider}** / `{model}`")

            # LLM response
            assistant_text = completion_data["text"]
            _bidi(assistant_text)

            # Web sources
            sources = completion_data.get("sources") or []
            if sources:
                with st.expander(f"Sources ({len(sources)})"):
                    for src in sources:
                        st.markdown(f"- [{src['title']}]({src['url']})")

            # Routing details
            route_decision = completion_data.get("route_decision", {})
            routing_info = {
                "provider": completion_data.get("provider"),
                "model": completion_data.get("model"),
                "attempts": completion_data.get("attempts"),
                "reason": route_decision.get("reason"),
                "constraints": route_decision.get("constraints"),
                "candidates": route_decision.get("candidates"),
            }

            with st.expander("Routing Details"):
                st.json(routing_info)

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "profile": profile_json,
                "routing": routing_info,
                "sources": sources if sources else None,
            })


# ── Main ─────────────────────────────────────────────────────────────

if st.session_state.auth_token:
    show_sidebar()
    if st.session_state.page == "API Keys":
        show_keys_page()
    else:
        show_chat()
else:
    show_auth_page()