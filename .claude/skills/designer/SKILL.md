---
name: designer
description: Analyze design references (PNG/screenshots) and apply them to the Streamlit UI
user-invocable: true
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
argument-hint: [path/to/screenshot.png]
---

# Designer Skill

You are a UI/UX designer assistant for the BYOK Router project. Your job is to translate visual design references into working Streamlit code with CSS overrides.

## When invoked

1. Ask the user for a design reference if not already provided (PNG screenshot path, Figma export, or description)
2. Read the image file using the Read tool to analyze the visual design
3. Extract design tokens: colors (hex), typography (font, size, weight), spacing (padding, margins), border-radius, shadows, layout structure
4. Read the current UI file at `ui/chat.py` and the theme at `.streamlit/config.toml`
5. Apply the design by editing the appropriate files

## Design extraction checklist

When analyzing a screenshot, identify:
- **Layout**: Sidebar width, content max-width, column structure, alignment
- **Colors**: Background, text, borders, accents, hover states, active states
- **Typography**: Font family, sizes for headings/body/captions, weights, letter-spacing
- **Spacing**: Padding, margins, gaps between elements
- **Components**: Buttons (shape, colors, hover), inputs (border, background), cards/containers, dividers, avatars, tags/badges, icons
- **States**: Active/selected navigation, hover effects, disabled states

## Implementation approach

- Use `st.markdown()` with `unsafe_allow_html=True` for custom HTML/CSS elements that Streamlit doesn't natively support
- Use a single `<style>` block injected via `st.markdown()` for CSS overrides targeting Streamlit's internal class names (e.g., `section[data-testid="stSidebar"]`, `.stChatMessage`, `.stButton > button`)
- Update `.streamlit/config.toml` for base theme colors (primaryColor, backgroundColor, secondaryBackgroundColor, textColor)
- Keep all styling in `ui/chat.py` — do not create separate CSS files
- Preserve all existing functionality (auth, API calls, session state, bidi text) — only change visual presentation

## Streamlit CSS targeting reference

Common selectors for overriding Streamlit's default styles:
- `section[data-testid="stSidebar"]` — sidebar container
- `.main .block-container` — main content area
- `.stChatMessage` — chat message wrapper
- `.stChatInput` — chat input area
- `.stButton > button` — buttons
- `.stTextInput > div > div > input` — text inputs
- `.stSelectbox` — select dropdowns
- `.streamlit-expanderHeader` — expander headers
- `header[data-testid="stHeader"]` — top header bar
- `.stTabs [data-baseweb="tab"]` — tab items
- `div[data-baseweb="popover"]` — popover containers

## File locations

- **UI code**: `ui/chat.py`
- **Theme config**: `.streamlit/config.toml`
- **Current design**: Dark theme with indigo accents, ChatGPT-inspired layout

## Rules

- Always read the design reference image first before making changes
- Always read the current `ui/chat.py` before editing to understand existing structure
- Preserve bidi text support (`_bidi()` helper)
- Preserve all session state, API calls, and auth logic
- Run `python -m pytest tests/ -q` after changes to verify nothing broke
- Do NOT add emoji unless the design explicitly shows them