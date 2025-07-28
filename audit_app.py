from audit import run_audit, export_to_notion, annotate_screenshot
import streamlit as st

st.set_page_config(page_title="Web Usability Auditor", layout="wide")
st.title("🌐 Web Usability & Accessibility Auditor")

url = st.text_input("🔗 Website URL", "https://example.com")
run_btn = st.button("🚀 Run Audit")

if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'screenshot' not in st.session_state:
    st.session_state['screenshot'] = None

if run_btn and url:
    with st.spinner("Auditing the site..."):
        try:
            results, screenshot = run_audit(url)
            st.session_state['results'] = results
            st.session_state['screenshot'] = screenshot
            st.success("✅ Audit complete!")
        except Exception as e:
            st.error(f"Error: {e}")

results = st.session_state.get('results')
screenshot = st.session_state.get('screenshot')

if results and screenshot:
    st.subheader("🖼️ Annotated Screenshot")
    img = annotate_screenshot(screenshot, results)
    st.image(img, caption="Red highlights = issues", use_column_width=True)

    st.subheader("📋 Audit Results (JSON)")
    st.json(results)

    st.subheader("📤 Export to Notion")
    with st.expander("Export Settings"):
        notion_token = st.text_input("🔑 Notion Token", type="password")
        database_id = st.text_input("📂 Notion Database ID")
        if st.button("Export Results to Notion"):
            if notion_token and database_id:
                try:
                    export_to_notion(results, notion_token, database_id)
                    st.success("📬 Exported to Notion!")
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.warning("Please enter both Notion token and database ID.")
