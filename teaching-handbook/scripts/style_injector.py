# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "beautifulsoup4",
# ]
# ///
import os
from bs4 import BeautifulSoup
import re

def inject_styles_and_nav(input_file, output_file, layout_mode="sidebar", page_title="教學手冊", sidebar_title="教學手冊導航"):
    print(f"Reading {input_file} for layout: {layout_mode}...")
    
    # Try different encodings
    content = None
    encodings = ['utf-8', 'big5', 'cp950']
    
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"Successfully read file with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        print("Failed to read file with known encodings.")
        return

    soup = BeautifulSoup(content, 'html.parser')

    # --- CSS Injection (Sidebar Layout) ---
    style_content = """
    /* Reset & Base */
    body {
        margin: 0;
        padding: 0;
        background-color: #f5f7f9;
        font-family: "Microsoft JhengHei", "Segoe UI", sans-serif;
        display: flex;
        min-height: 100vh;
        overflow-x: hidden; 
    }
    
    body.sidebar-collapsed {
        /* When collapsed, we can allow more fluid width */
    }

    *, *:before, *:after {
        box-sizing: border-box;
    }

    /* Sidebar Container */
    #sidebar-container {
        width: 280px;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        background-color: #fff;
        border-right: 1px solid #e0e0e0;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        transition: width 0.3s ease;
        box-shadow: 2px 0 5px rgba(0,0,0,0.02);
    }
    
    #sidebar-container.collapsed {
        width: 60px;
    }

    /* Toggle Button */
    #sidebar-header {
        border-bottom: 1px solid #eee;
        background-color: #fafafa;
    }

    #sidebar-toggle {
        padding: 10px 15px;
        cursor: pointer;
        text-align: right;
        color: #5f6368;
        font-weight: bold;
        font-size: 18px;
        background: transparent;
        border: none;
        width: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        height: 40px;
    }
    
    #sidebar-container.collapsed #sidebar-toggle {
        justify-content: center;
        padding: 0;
    }

    /* Controls Area (Font Size) */
    #sidebar-controls {
        padding: 10px 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #fff;
    }
    
    #sidebar-container.collapsed #sidebar-controls {
        display: none;
    }
    
    .control-btn {
        background-color: #f1f3f4;
        border: 1px solid #dadce0;
        border-radius: 4px;
        color: #3c4043;
        font-size: 14px;
        cursor: pointer;
        padding: 4px 10px;
        font-family: inherit;
    }
    
    .control-btn:hover {
        background-color: #e8eaed;
        color: #202124;
    }
    
    .control-label {
        font-size: 12px;
        color: #5f6368;
        margin-right: 5px;
    }

    /* Sidebar Content Wrapper */
    #sidebar-content {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        transition: opacity 0.2s;
        scrollbar-width: thin;
    }
    
    #sidebar-container.collapsed #sidebar-content {
        display: none;
        opacity: 0;
    }

    #sidebar-title {
        font-size: 18px;
        font-weight: bold;
        color: #1a73e8;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid #f1f3f4;
        font-family: "Microsoft JhengHei", sans-serif;
        white-space: nowrap;
    }

    /* Sidebar Links */
    .nav-link {
        display: block;
        padding: 10px 15px;
        margin-bottom: 5px;
        color: #444;
        text-decoration: none;
        border-radius: 8px;
        font-size: 14px;
        transition: all 0.2s;
        line-height: 1.4;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .nav-link:hover {
        background-color: #f1f3f4;
        color: #1a73e8;
        padding-left: 20px;
    }
    
    .nav-link.active {
        background-color: #e8f0fe;
        color: #1967d2;
        font-weight: bold;
    }
    
    .nav-link.level-2 { margin-left: 0px; font-weight: 500;}
    .nav-link.level-3 { margin-left: 15px; font-size: 13px; color: #666; }

    /* Main Content Area */
    .WordSection1 {
        margin-left: 280px; 
        width: calc(100% - 280px);
        max-width: 1200px; 
        margin-right: auto; 
        padding: 60px 80px;
        background-color: #fff;
        min-height: 100vh;
        box-shadow: -5px 0 15px rgba(0,0,0,0.02);
        transition: margin-left 0.3s ease, width 0.3s ease;
        
        /* 
           Defaults:
           We set a base zoom for "Proportional Enlargement".
           Standard browser zoom logic.
        */
        zoom: 1.15; 
    }
    
    body.sidebar-collapsed .WordSection1 {
        margin-left: 60px;
        width: calc(100% - 60px);
        max-width: 1400px; 
    }
    
    html {
        scroll-behavior: smooth;
    }
    
    @media (max-width: 900px) {
        #sidebar-container {
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }
        
        #sidebar-container.mobile-active {
            transform: translateX(0);
        }
        
        .WordSection1 {
            margin-left: 0;
            width: 100%;
            padding: 20px;
            zoom: 1.0; /* Reset zoom on mobile to prevent overflow issues */
        }
        
        #sidebar-controls {
            display: none; /* Hide controls on mobile if sidebar hidden */
        }
    }

    /* Code Block Copy Button */
    pre {
        position: relative;
    }
    .copy-btn {
        position: absolute;
        top: 5px;
        right: 5px;
        background-color: #eee;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        opacity: 0.8;
        transition: all 0.2s;
        z-index: 10;
        font-family: inherit;
    }
    .copy-btn:hover {
        opacity: 1;
        background-color: #d0d0d0;
    }
    """
    
    if layout_mode == "scroll":
        style_content += """
        /* Scroll Snap Additions */
        html {
            scroll-snap-type: y mandatory;
        }
        
        .snap-section {
            scroll-snap-align: start;
            /* Using min-height instead of fixed height allows longer content to scroll naturally 
               if it exceeds viewport, but still snaps to top */
            min-height: 100vh;
            padding-top: 80px; /* Space for fixed header/sidebar-toggle if needed */
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            position: relative;
            
            /* Visual separation */
            border-bottom: 1px dashed #e0e0e0;
        }
        /* Ensure sidebar stays fixed even in snap mode */
        #sidebar-container {
            z-index: 2000;
        }
        """
    
    style_tag = soup.new_tag('style')
    style_tag.string = style_content
    if soup.head:
        soup.head.append(style_tag)
    else:
        head = soup.new_tag('head')
        soup.insert(0, head)
        head.append(style_tag)

    # --- Content Chunking (Scroll Mode) ---
    if layout_mode == "scroll" and soup.body:
        # We need to wrap content between headers into <div class="snap-section">
        new_body = soup.new_tag("body")
        # Copy attributes if any? Usually body has none for converted doc
        
        current_section = soup.new_tag("div", **{"class": "snap-section"})
        new_body.append(current_section)
        
        # Iterate over a copy of contents
        children = list(soup.body.contents)
        for child in children:
            if child.name in ['h1', 'h2']:
                # Close current section, start new one
                # Note: Only if current section has content to avoid empty top sections?
                # Actually, H1/H2 should START the section.
                
                # If current_section is valid and has children, we leave it.
                # If it's the very first empty one, we just append to it (the "Cover")?
                # A common pattern: Start new section for every H1/H2.
                
                if len(current_section.contents) > 0:
                   current_section = soup.new_tag("div", **{"class": "snap-section"})
                   new_body.append(current_section)
                
                current_section.append(child)
            else:
                current_section.append(child)
        
        # Replace old body with new body structure
        soup.body.replace_with(new_body)

    # --- HTML Injection (Sidebar) ---
    nav_html = f"""
    <div id="sidebar-container">
        <div id="sidebar-header">
            <button id="sidebar-toggle" title="切換側邊欄">
                <span>&lt;&lt;</span>
            </button>
        </div>
        
        <div id="sidebar-controls">
            <span class="control-label">字體:</span>
            <button class="control-btn" id="font-decrease" title="縮小">A-</button>
            <button class="control-btn" id="font-reset" title="重置">100%</button>
            <button class="control-btn" id="font-increase" title="放大">A+</button>
        </div>

        <div id="sidebar-content">
            <div id="sidebar-title">{page_title}<br><span style="font-size:12px;color:#666">{sidebar_title}</span></div>
            <div id="sidebar-nav">
                <!-- Links injected by JS -->
            </div>
        </div>
    </div>
    """
    nav_soup = BeautifulSoup(nav_html, 'html.parser')
    if soup.body:
        soup.body.insert(0, nav_soup)

    # --- JS Injection ---
    script_content = """
    document.addEventListener("DOMContentLoaded", function() {
        const navContainer = document.getElementById('sidebar-nav');
        const headers = document.querySelectorAll('h1, h2, h3');
        const sidebar = document.getElementById('sidebar-container');
        const toggleBtn = document.getElementById('sidebar-toggle');
        const toggleIcon = toggleBtn.querySelector('span');
        
        // Font Zoom Logic
        let currentZoom = 1.15; // Matches CSS default
        const contentArea = document.querySelector('.WordSection1');
        const btnInc = document.getElementById('font-increase');
        const btnDec = document.getElementById('font-decrease');
        const btnReset = document.getElementById('font-reset');

        function updateZoom() {
            if(contentArea) {
                contentArea.style.zoom = currentZoom;
                btnReset.innerText = Math.round(currentZoom * 100) + "%";
            }
        }

        if(btnInc) {
            btnInc.addEventListener('click', () => {
                currentZoom += 0.05;
                updateZoom();
            });
        }
        if(btnDec) {
            btnDec.addEventListener('click', () => {
                currentZoom = Math.max(0.8, currentZoom - 0.05);
                updateZoom();
            });
        }
        if(btnReset) {
            btnReset.addEventListener('click', () => {
                currentZoom = 1.15; // Reset to our "Enhanced" default
                updateZoom();
            });
        }
        
        // Initial label update
        if(btnReset) btnReset.innerText = "115%";


        // Sidebar Toggle Logic
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            document.body.classList.toggle('sidebar-collapsed');
            
            if (sidebar.classList.contains('collapsed')) {
                toggleIcon.innerHTML = "&gt;&gt;";
                toggleBtn.title = "展開側邊欄";
            } else {
                toggleIcon.innerHTML = "&lt;&lt;";
                toggleBtn.title = "收起側邊欄";
            }
        });

        // Generate Nav Links
        headers.forEach((header, index) => {
            const text = header.innerText.trim();
            const match = text.match(/^(\\d+(\\.\\d+)?)(\\s|$)/) || text.match(/^[A-Z](\\s|$)/);
            
           if (match || header.tagName === 'H1') {
                const sectionId = 'section-' + index;
                header.id = sectionId;

                const link = document.createElement('a');
                link.href = '#' + sectionId;
                link.innerText = text; 
                
                if (header.tagName === 'H2') {
                    link.className = 'nav-link level-2';
                } else if (header.tagName === 'H3') {
                    link.className = 'nav-link level-3';
                } else {
                    link.className = 'nav-link level-1';
                    link.style.marginTop = "15px";
                    link.style.borderTop = "1px solid #eee";
                    link.style.paddingTop = "15px";
                }
                
                navContainer.appendChild(link);
            }
        });
        
        // Highlight active link
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.getAttribute('id');
                    document.querySelectorAll('.nav-link').forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === '#' + id) {
                            link.classList.add('active');
                            if (!sidebar.classList.contains('collapsed')) {
                                link.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                            }
                        }
                    });
                }
            });
        }, observerOptions);

        headers.forEach(header => {
            observer.observe(header);
        });

        // Copy Button Logic (for code blocks detected as tables)
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            // Heuristic 1: Tables with exactly one cell are likely code blocks in this conversion
            const tds = table.querySelectorAll('td');
            if (tds.length !== 1) return;
            
            const td = tds[0];
            const textContent = td.innerText.trim();
            
            // Heuristic 2: Filter out known non-code tables
            // e.g. "Execution Steps" usually starts with bold text
            const firstChild = td.firstElementChild;
            const hasStrongStart = firstChild && (firstChild.tagName === 'STRONG' || firstChild.querySelector('strong'));
            if (hasStrongStart && (textContent.includes('執行步驟') || textContent.includes('Step'))) {
                return; 
            }

            // Heuristic 3 (Optional): Check for code-like patterns if needed, 
            // but for now, the single-cell + exclusion logic covers most
            
            // Add relative positioning to the cell so the button stays inside
            td.style.position = 'relative';
            
            // Create button
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.innerText = '複製';
            
            // Append to the td (code container)
            td.appendChild(btn);
            
            btn.addEventListener('click', () => {
                let textToCopy = '';
                // Since this doc usually represents lines as <p> tags inside the td
                const paragraphs = td.querySelectorAll('p');
                
                if (paragraphs.length > 0) {
                    // Extract text from each p and join with newline
                    textToCopy = Array.from(paragraphs)
                        .map(p => {
                            // Text inside p, we want to maintain spaces but trim end-of-line whitespace if desired
                            // For code, preserving spaces is generally safer.
                            // But usually, innerText of a <p> is just its content.
                            return p.innerText;
                        })
                        .join('\\n');
                } else {
                    // Fallback for non-paragraph structure (e.g. if it's just text or text nodes)
                    const clone = td.cloneNode(true);
                    const cloneBtn = clone.querySelector('.copy-btn');
                    if(cloneBtn) cloneBtn.remove();
                    textToCopy = clone.innerText;
                }
                
                // Copy API
                navigator.clipboard.writeText(textToCopy).then(() => {
                    btn.innerText = '已複製!';
                    setTimeout(() => {
                        btn.innerText = '複製';
                    }, 2000);
                }).catch(err => {
                    console.error('Copy failed:', err);
                    alert('複製失敗，請手動複製');
                });
            });
        });

        // Copy Button Logic (for <pre> blocks)
        const pres = document.querySelectorAll('pre');
        pres.forEach(pre => {
            // Check if it already has a button (avoid duplicate if run multiple times)
            if (pre.querySelector('.copy-btn')) return;

            pre.style.position = 'relative';
            
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.innerText = '複製';
            
            pre.appendChild(btn);
            
            btn.addEventListener('click', () => {
                // For pre, text is direct or in code
                let textToCopy = pre.innerText.replace('複製', '').trim(); 
                // Simple cleanup if button text is caught, but since button is child, innerText includes it.
                // Better: Clone and remove button
                const clone = pre.cloneNode(true);
                const cloneBtn = clone.querySelector('.copy-btn');
                if(cloneBtn) cloneBtn.remove();
                textToCopy = clone.innerText;

                navigator.clipboard.writeText(textToCopy).then(() => {
                    btn.innerText = '已複製!';
                    setTimeout(() => {
                        btn.innerText = '複製';
                    }, 2000);
                }).catch(err => {
                    console.error('Copy failed:', err);
                    alert('複製失敗，請手動複製');
                });
            });
        });
    });
    """
    
    script_tag = soup.new_tag('script')
    script_tag.string = script_content
    if soup.body:
        soup.body.append(script_tag)

    # --- Output ---
    # --- Content Fixes (Status Colors) ---
    final_html = str(soup)
    target_string = "選項輸入這三個：🔴 待處理、🔴 處理中、🔴 已修復"
    replacement_string = "選項輸入這三個：🔴 待處理、🟡 處理中、🟢 已修復"
    if target_string in final_html:
        final_html = final_html.replace(target_string, replacement_string)
        print("Auto-fixed status colors.")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Generated {output_file}")
