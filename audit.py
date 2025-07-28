"""
Web Usability & Accessibility Auditor

Features:
- Paste a URL and run a full audit (WCAG + Nielsen heuristics)
- Highlights issues directly on a screenshot
- Export results to Google Sheets or Notion

Setup:
1. Install dependencies:
   pip install streamlit playwright pillow requests openai beautifulsoup4 gspread google-auth notion-client
   playwright install
2. Set your OpenAI API key:
   export OPENAI_API_KEY=sk-...
3. For Google Sheets export:
   - Create a Google Service Account, download the JSON credentials
   - Share your Google Sheet with the service account email
4. For Notion export:
   - Create a Notion integration and get the token
   - Share your database with the integration

Run:
   streamlit run audit.py
"""
import sys
import json
import os
import re
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
import openai
import streamlit as st
import tempfile
import gspread
from google.oauth2.service_account import Credentials
from notion_client import Client as NotionClient

WCAG_CONTRAST_RATIO = 4.5
NIELSEN_HEURISTICS = [
    "Visibility of system status",
    "Match between system and the real world",
    "User control and freedom",
    "Consistency and standards",
    "Error prevention",
    "Recognition rather than recall",
    "Flexibility and efficiency of use",
    "Aesthetic and minimalist design",
    "Help users recognize, diagnose, and recover from errors",
    "Help and documentation"
]

def get_html_and_screenshot(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="load")
        page.wait_for_timeout(3000)  # Add this after page.goto(...)
        html = page.content()
        screenshot = page.screenshot(full_page=True)
        # Get positions of images missing alt text
        img_positions = []
        for img in page.query_selector_all("img"):
            alt = img.get_attribute("alt")
            if not alt or not alt.strip():
                bbox = img.bounding_box()
                if bbox:
                    img_positions.append(bbox)
        # Get positions of elements with bad color contrast (inline styles only)
        contrast_positions = []
        for el in page.query_selector_all("*[style]"):
            style = el.get_attribute("style")
            color, bg = extract_inline_styles(style)
            rgb_color = parse_color(color)
            rgb_bg = parse_color(bg) or (255,255,255)
            if rgb_color and rgb_bg:
                ratio = contrast_ratio(rgb_color, rgb_bg)
                if ratio < WCAG_CONTRAST_RATIO:
                    bbox = el.bounding_box()
                    if bbox:
                        contrast_positions.append((bbox, color, bg, ratio))
        browser.close()
    return html, screenshot, img_positions, contrast_positions

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

def luminance(rgb):
    def channel(c):
        c = c/255.0
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    r, g, b = rgb
    return 0.2126*channel(r) + 0.7152*channel(g) + 0.0722*channel(b)

def contrast_ratio(rgb1, rgb2):
    l1 = luminance(rgb1)
    l2 = luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def extract_inline_styles(style):
    color = bg = None
    if style:
        color_match = re.search(r'color:\s*([^;]+);?', style)
        bg_match = re.search(r'background(?:-color)?:\s*([^;]+);?', style)
        if color_match:
            color = color_match.group(1)
        if bg_match:
            bg = bg_match.group(1)
    return color, bg

def parse_color(val):
    if not val:
        return None
    val = val.strip()
    if val.startswith('#'):
        return hex_to_rgb(val)
    elif val.startswith('rgb'):
        nums = [int(float(x)) for x in re.findall(r'[\d.]+', val)]
        return tuple(nums[:3])
    return None

def wcag_checks(html, url, img_positions, contrast_positions):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    # 1. Missing alt text
    img_idx = 0
    for img in soup.find_all('img'):
        alt = img.get('alt')
        if not alt or not alt.strip():
            bbox = img_positions[img_idx] if img_idx < len(img_positions) else None
            el_id = img.get('id')
            el_class = img.get('class')
            el_info = str(img)[:100]
            if el_id:
                el_info += f" | id={el_id}"
            if el_class:
                el_info += f" | class={' '.join(el_class) if isinstance(el_class, list) else el_class}"
            results.append({
                "type": "WCAG",
                "rule": "Images must have alt text",
                "severity": 3,
                "element": el_info,
                "suggestion": "Add descriptive alt text to this image.",
                "bbox": bbox
            })
            img_idx += 1
    # 2. Color contrast (inline styles only)
    for i, (bbox, color, bg, ratio) in enumerate(contrast_positions):
        # Try to find the matching element in soup for id/class
        el = None
        for candidate in soup.find_all(style=True):
            style = candidate.get('style')
            if style and color in style and (not bg or bg in style):
                el = candidate
                break
        el_id = el.get('id') if el else None
        el_class = el.get('class') if el else None
        el_info = f"color: {color}, background: {bg}"
        if el_id:
            el_info += f" | id={el_id}"
        if el_class:
            el_info += f" | class={' '.join(el_class) if isinstance(el_class, list) else el_class}"
        results.append({
            "type": "WCAG",
            "rule": "Text must have sufficient color contrast",
            "severity": 4 if ratio < 3 else 2,
            "element": el_info,
            "suggestion": f"Increase contrast between text color {color} and background {bg} (ratio: {ratio:.2f}).",
            "bbox": bbox
        })
    return results

def gpt4_heuristics_analysis(html, url):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""You are an expert UX auditor. Given the following HTML from {url}, analyze it for each of Nielsen's 10 usability heuristics. For each heuristic, provide:
- 1-2 observations (if any issues found)
- A suggestion for improvement (or say 'No issues found' if none)
- A severity rating (1=minor, 4=critical; use 1 if no issues)
Output as a JSON list of 10 objects (one per heuristic), each with: type (\"Heuristic\"), rule (heuristic), severity, element/area (if known), suggestion.
Always output a list of 10 objects, even if no issues are found.

HTML:
{html[:8000]}"""
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.2
    )
    try:
        text = response['choices'][0]['message']['content']
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
        else:
            return []
    except Exception as e:
        print("GPT-4 error:", e)
        return []

def run_audit(url):
    html, screenshot, img_positions, contrast_positions = get_html_and_screenshot(url)
    wcag = wcag_checks(html, url, img_positions, contrast_positions)
    heuristics = gpt4_heuristics_analysis(html, url)
    results = wcag + heuristics
    return results, screenshot

def annotate_screenshot(screenshot_bytes, results):
    img = Image.open(BytesIO(screenshot_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    for r in results:
        bbox = r.get("bbox")
        if bbox:
            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            draw.rectangle([x, y, x+w, y+h], outline="red", width=4)
    return img

def export_to_google_sheets(results, sheet_url, creds_json_path):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(creds_json_path, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.add_worksheet(title="Audit Results", rows=str(len(results)+1), cols="10")
    headers = ["type", "rule", "severity", "element", "suggestion"]
    worksheet.append_row(headers)
    for r in results:
        worksheet.append_row([r.get("type"), r.get("rule"), r.get("severity"), r.get("element"), r.get("suggestion")])
    return True

def export_to_notion(results, notion_token, database_id):
    notion = NotionClient(auth=notion_token)
    for r in results:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Type": {"title": [{"text": {"content": r.get("type", "")}}]},
                "Rule": {"rich_text": [{"text": {"content": r.get("rule", "")}}]},
                "Severity": {"number": r.get("severity", 1)},
                "Element": {"rich_text": [{"text": {"content": r.get("element", "")}}]},
                "Suggestion": {"rich_text": [{"text": {"content": r.get("suggestion", "")}}]}
            }
        )
    return True




