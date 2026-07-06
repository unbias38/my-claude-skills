
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown",
#     "beautifulsoup4",
# ]
# ///
import markdown
import os
import sys
import argparse
import tempfile
try:
    from style_injector import inject_styles_and_nav
    from _polish import SIDEBAR_SEARCH_SCRIPT, add_lazy_loading
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from style_injector import inject_styles_and_nav
    from _polish import SIDEBAR_SEARCH_SCRIPT, add_lazy_loading

def convert_md_to_html(md_path, output_filename, title="Doc"):
    print(f"Converting {md_path} to {output_filename}...")

    if not os.path.exists(md_path):
        print(f"Error: Input file '{md_path}' not found.")
        sys.exit(1)

    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Convert MD to HTML
    # Enable common extensions for tables, fenced code, etc.
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])

    # Local addition: lazy-load all images
    html_content = add_lazy_loading(html_content)

    # Wrap in WordSection1 to match styles
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
    <meta charset="utf-8">
    <title>{title}</title>
    </head>
    <body>
    <div class="WordSection1">
    {html_content}
    </div>
    {SIDEBAR_SEARCH_SCRIPT}
    </body>
    </html>
    """
    
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False
    ) as f:
        temp_file = f.name
        f.write(full_html)

    try:
        # Inject Styles and Nav
        inject_styles_and_nav(temp_file, output_filename, layout_mode="sidebar", page_title=title, sidebar_title="導航")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    if not os.path.exists(output_filename):
        print("Error: style injection failed, no output produced.")
        sys.exit(1)

    print(f"Done! Created {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to input .md file")
    parser.add_argument("output_file", nargs="?", help="Path to output .html file (optional)")
    parser.add_argument("--title", default="Document", help="Page Title")
    args = parser.parse_args()

    output_path = args.output_file
    if not output_path:
        base_name = os.path.splitext(args.input_file)[0]
        output_path = f"{base_name}.html"

    convert_md_to_html(args.input_file, output_path, title=args.title)
