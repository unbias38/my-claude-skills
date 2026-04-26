# /// script
# requires-python = ">=3.11"
# ///
"""Shared HTML polish helpers for converters.

Used by docx_converter / md_converter / pptx_converter to inject:
- loading="lazy" on all <img> tags
- A sidebar enhancement script that:
    1. Rebuilds sidebar nav with ALL h1/h2/h3 (overrides style_injector's
       restrictive regex which drops Chinese / "1. xxx" style headings).
    2. Adds a search box above the nav.

Why these live here, not in style_injector.py: hard rule #2 says don't modify
upstream style_injector. These are converter-side enhancements layered on top.

Why we override the sidebar nav (not just append): style_injector's regex
filter (`^\\d+\\s` or `^[A-Z]\\s`) drops headings like "1. xxx" (digit+dot+space
- the natural markdown heading style) and pure-Chinese headings (H2/H3 with
no Latin/digit prefix). Appending missing items would yield wrong document
order when matched and unmatched headings interleave. Clearing and rebuilding
in document order is the only correct approach.
"""

import re

# JS that runs after style_injector finishes:
# 1. Rebuild #sidebar-nav from ALL h1/h2/h3 inside .WordSection1 (in document
#    order). Reuses existing IDs assigned by style_injector to keep scroll-spy
#    IntersectionObserver working; assigns th-section-N for new ones.
# 2. Insert a search input above the rebuilt nav.
SIDEBAR_SEARCH_SCRIPT = """
<script>
(function () {
  function rebuildNav(nav) {
    if (nav.getAttribute('data-th-rebuilt') === '1') return;
    var content = document.querySelector('.WordSection1');
    if (!content) return;
    var headers = content.querySelectorAll('h1, h2, h3');
    if (headers.length === 0) return;

    nav.innerHTML = '';
    headers.forEach(function (h, i) {
      if (!h.id) h.id = 'th-section-' + i;
      var link = document.createElement('a');
      link.href = '#' + h.id;
      link.innerText = h.innerText.trim();
      var tag = h.tagName;
      if (tag === 'H2') {
        link.className = 'nav-link level-2';
      } else if (tag === 'H3') {
        link.className = 'nav-link level-3';
      } else {
        link.className = 'nav-link level-1';
        link.style.marginTop = '15px';
        link.style.borderTop = '1px solid #eee';
        link.style.paddingTop = '15px';
      }
      nav.appendChild(link);
    });
    nav.setAttribute('data-th-rebuilt', '1');
  }

  function addSearchBox(nav) {
    if (document.getElementById('th-search')) return;
    var input = document.createElement('input');
    input.id = 'th-search';
    input.type = 'search';
    input.placeholder = '\\u{1F50D} \\u641C\\u5C0B\\u76EE\\u9304\\u2026';
    input.setAttribute('autocomplete', 'off');
    input.style.cssText =
      'display:block;width:calc(100% - 20px);margin:8px 10px 4px;padding:6px 10px;' +
      'border:1px solid #ddd;border-radius:4px;font-size:13px;box-sizing:border-box;' +
      'font-family:inherit;';

    nav.parentNode.insertBefore(input, nav);

    input.addEventListener('input', function () {
      var q = this.value.toLowerCase().trim();
      nav.querySelectorAll('.nav-link').forEach(function (link) {
        var match = !q || link.innerText.toLowerCase().indexOf(q) !== -1;
        link.style.display = match ? '' : 'none';
      });
    });
  }

  function init() {
    var nav = document.getElementById('sidebar-nav');
    if (!nav) return;
    rebuildNav(nav);
    addSearchBox(nav);
  }

  if (document.readyState === 'complete') {
    init();
  } else {
    window.addEventListener('load', init);
  }
})();
</script>
"""


def add_lazy_loading(html: str) -> str:
    """Add loading="lazy" attribute to every <img> tag that doesn't already have it."""
    def repl(m):
        tag = m.group(0)
        if "loading=" in tag.lower():
            return tag
        return tag[:4] + ' loading="lazy"' + tag[4:]
    return re.sub(r"<img\b[^>]*>", repl, html, flags=re.IGNORECASE)
