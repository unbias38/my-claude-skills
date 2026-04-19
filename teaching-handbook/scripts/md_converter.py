
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown",
#     "beautifulsoup4",
# ]
# ///
import markdown
import os
import argparse
from style_injector import inject_styles_and_nav

def convert_md_to_html(md_path, output_filename, title="Doc"):
    print(f"Converting {md_path} to {output_filename}...")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Convert MD to HTML
    # Enable common extensions for tables, fenced code, etc.
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    
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
    </body>
    </html>
    """
    
    temp_file = "temp_md.html"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    # Inject Styles and Nav
    inject_styles_and_nav(temp_file, output_filename, layout_mode="sidebar", page_title=title, sidebar_title="導航")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
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
