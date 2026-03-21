"""
Custom Visual Generation -- Generate self-contained HTML files for
lines flagged as needing a custom visual.
"""
from utils.claude_client import call_claude
import re
import os


VISUAL_PROMPT = """Generate a self-contained HTML file for this visual element in a finance documentary:

DESCRIPTION: {description}

STYLE REQUIREMENTS:
- Dark background: #1B2A4A or #111827
- Clean sans-serif font (system-ui or Inter)
- Accent colors: #C0392B for emphasis, #27AE60 for positive, #3498DB for neutral
- Professional, cinematic look suitable for YouTube documentary
- 16:9 aspect ratio (1920x1080 viewport)
- All text legible at 1080p
- If data is included, add source citation at bottom

Return ONLY the complete HTML file. No markdown wrapping, no explanation."""


def generate_custom_visuals(annotated_script: str, output_dir: str) -> list[str]:
    """Find CUSTOM VISUAL NEEDED flags and generate HTML files."""
    os.makedirs(output_dir, exist_ok=True)

    pattern = r'\[CUSTOM VISUAL NEEDED: (.+?)\]'
    matches = re.findall(pattern, annotated_script)

    generated_files = []
    for i, description in enumerate(matches[:3]):
        response = call_claude(
            VISUAL_PROMPT.format(description=description),
            model="sonnet",
            max_tokens=8192
        )

        html = response.strip()
        if html.startswith('```html'):
            html = html[7:]
        if html.startswith('```'):
            html = html[3:]
        if html.endswith('```'):
            html = html[:-3]

        filename = f"custom_visual_{i+1}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(html.strip())

        generated_files.append(filepath)

    return generated_files
