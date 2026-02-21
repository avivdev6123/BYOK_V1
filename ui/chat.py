"""
BYOK Router Chat UI — Streamlit POC

A chat interface that calls the FastAPI backend to:
1. Profile prompts via POST /v1/prompts
2. Route + execute via POST /v1/completions
3. Display conversation history with routing metadata
"""

import requests
import streamlit as st

st.set_page_config(page_title="BYOK Router Chat", layout="wide")
st.title("BYOK Router Chat")

PROVIDER_ACCOUNT_URLS = {
    "gemini": "https://aistudio.google.com/apikey",
    "openai": "https://platform.openai.com/account/billing",
    "anthropic": "https://console.anthropic.com/settings/billing",
}


def format_rate_limit_error(detail: str) -> str | None:
    """If the error is a rate limit / quota issue, return a user-friendly message."""
    detail_lower = detail.lower()
    if "429" not in detail_lower and "quota" not in detail_lower and "rate" not in detail_lower:
        return None

    for provider, url in PROVIDER_ACCOUNT_URLS.items():
        if provider in detail_lower:
            return (
                f"The **{provider}** API has reached its usage limit. "
                f"Please upgrade your plan in the provider's account management: "
                f"[{provider} account]({url})"
            )

    return "An API provider has reached its usage limit. Please check your provider account and upgrade your plan."


def build_contextual_prompt(messages: list[dict], new_input: str) -> str:
    """Prepend conversation history to the new prompt so the LLM sees context."""
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

# --- Sidebar configuration ---
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("Byok URL", value="http://127.0.0.1:8000")
    username = st.text_input("Username", value="demo")
    st.divider()
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Render existing messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("routing"):
            st.caption(f"Routed to **{msg['routing'].get('provider', '')}** / `{msg['routing'].get('model', '')}`")

        st.markdown(msg["content"])

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

# --- Chat input ---
if user_input := st.chat_input("Type your prompt..."):
    # Display and store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # Step 1: Profile the prompt
        # Build prompt with conversation context
        contextual_prompt = build_contextual_prompt(
            st.session_state.messages[:-1],  # exclude the just-added user msg
            user_input,
        )

        with st.spinner("Profiling prompt..."):
            try:
                profile_resp = requests.post(
                    f"{api_url}/v1/prompts",
                    json={"username": username, "prompt": contextual_prompt},
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

        # Step 2: Route + execute completion
        with st.spinner("Routing and generating response..."):
            try:
                completion_resp = requests.post(
                    f"{api_url}/v1/completions",
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

        # Show which model was selected
        provider = completion_data.get("provider", "")
        model = completion_data.get("model", "")
        st.caption(f"Routed to **{provider}** / `{model}`")

        # Display the LLM response
        assistant_text = completion_data["text"]
        st.markdown(assistant_text)

        # Display web sources if present
        sources = completion_data.get("sources") or []
        if sources:
            with st.expander(f"Sources ({len(sources)})"):
                for src in sources:
                    st.markdown(f"- [{src['title']}]({src['url']})")

        # Build routing metadata for display
        route_decision = completion_data.get("route_decision", {})
        selected = route_decision.get("selected", {})
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

        # Store assistant message with metadata
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "profile": profile_json,
            "routing": routing_info,
            "sources": sources if sources else None,
        })
