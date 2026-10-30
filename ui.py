"""Look and feel of the app: styles and small HTML builders.

This file does not import Streamlit, so the pieces can be tested on their own.

Design idea: a fact-checker's desk. Ink-navy and highlighter-yellow on cool newsprint,
verdicts shown as a rubber stamp, and the words that drove the decision marked up
in the article itself with green and red highlighter.
"""
import html
import re

# Written to .streamlit/config.toml. Streamlit reads the theme when it starts.
THEME_TOML = """[theme]
base = "light"
primaryColor = "#10213F"
backgroundColor = "#F2F4F7"
secondaryBackgroundColor = "#E4E9F1"
textColor = "#10213F"
font = "sans serif"

[client]
toolbarMode = "minimal"

[browser]
gatherUsageStats = false
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Bricolage+Grotesque:opsz,wght@12..96,600..800&display=swap');

:root{
  --ink:#10213F; --paper:#FFFFFF; --news:#F2F4F7;
  --hl:#FFD23F; --hl-press:#E8B600;
  --green:#0B6B40; --green-tint:#EAF7EF;
  --red:#B91C1C; --red-tint:#FDEDED;
  --muted:#4A5878; --line:#D3DAE6; --focus:#1D4ED8;
  --display:'Bricolage Grotesque','Nirmala UI','Segoe UI',system-ui,sans-serif;
  --text:'Atkinson Hyperlegible','Segoe UI','Nirmala UI',system-ui,sans-serif;
}

/* ---------- Page ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"]{ background:var(--news); }
.stApp{ font-family:var(--text); color:var(--ink); }
.stApp [data-testid="stHeader"]{ background:transparent; }
.stApp .block-container, .stApp [data-testid="stMainBlockContainer"]{ max-width:100%; width:100%; padding:2.6rem clamp(1rem,3vw,3.5rem) 1.2rem; }
.stApp [data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"]{ gap:.7rem; }
.stApp .st-key-input_panel [data-testid="stVerticalBlock"], .stApp [class*="st-key-result_panel"] [data-testid="stVerticalBlock"]{ gap:.55rem; }
.stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stMarkdownContainer"] li{ font-size:1.06rem; line-height:1.65; }
.stApp [data-testid="stWidgetLabel"] p{ font-size:1.02rem; font-weight:700; color:var(--ink); }
.stApp [data-testid="stCaptionContainer"]{ color:var(--muted); font-size:.95rem; }
.stApp button:focus-visible, .stApp textarea:focus-visible, .stApp input:focus-visible{ outline:3px solid var(--focus); outline-offset:2px; }

/* ---------- Top bar ---------- */
.stApp .brand{ display:flex; align-items:center; gap:.7rem; padding-top:.3rem; }
.stApp .brand-mark{ flex:none; width:2.5rem; height:2.5rem; border-radius:8px; background:var(--hl); border:2px solid var(--ink);
  display:grid; place-items:center; font:800 1.3rem var(--display); color:var(--ink); box-shadow:2px 2px 0 var(--ink); }
.stApp .brand-name{ font:800 1.35rem/1.2 var(--display); color:var(--ink); }

/* ---------- Hero ---------- */
.stApp .hero{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:2rem; align-items:center;
  background:var(--ink); color:#fff; border-radius:16px; padding:1.3rem 2.2rem; margin:.2rem 0 .8rem; }
.stApp .hero .hero-title{ font:800 clamp(1.8rem,3vw,2.7rem)/1.15 var(--display); letter-spacing:-.01em; margin:0 0 .5rem; padding:0; color:#fff; }
.stApp .hero .hero-sub{ font-size:1.02rem; line-height:1.5; color:#D6DEEE; max-width:70ch; margin:0 0 .9rem; }
.stApp .hero .facts{ list-style:none; display:flex; flex-wrap:wrap; gap:.6rem 1.6rem; margin:0; padding:0; }
.stApp .hero .facts li{ display:flex; align-items:center; gap:.55rem; font-weight:700; font-size:1.02rem; color:#fff; margin:0; padding:0; }
.stApp .hero .facts li::before{ content:""; width:.75rem; height:.75rem; background:var(--hl); border-radius:2px; flex:none; }
.stApp .hero .hero-art svg{ width:auto; max-width:100%; height:clamp(110px,17vh,170px); display:block; margin-left:auto; }
@media (max-width:860px){
  .stApp .hero{ grid-template-columns:1fr; padding:1.8rem 1.4rem; }
  .stApp .hero .hero-art{ display:none; }
}

/* ---------- Tabs ---------- */
.stApp div[data-baseweb="tab-list"]{ gap:.3rem; border-bottom:2px solid var(--ink); }
.stApp button[data-baseweb="tab"]{ padding:.8rem 1.15rem; border-radius:10px 10px 0 0; background:transparent; height:auto; }
.stApp button[data-baseweb="tab"] p{ font-size:1.05rem; font-weight:700; color:var(--muted); }
.stApp button[data-baseweb="tab"][aria-selected="true"]{ background:var(--hl); }
.stApp button[data-baseweb="tab"][aria-selected="true"] p{ color:var(--ink); }
.stApp div[data-baseweb="tab-highlight"]{ background:var(--ink); height:4px; }
.stApp div[data-baseweb="tab-border"]{ background:transparent; }

/* ---------- Panels ---------- */
.stApp .st-key-input_panel{ background:var(--paper); border:2px solid var(--ink); border-radius:14px;
  padding:1.1rem 1.4rem 1.3rem; box-shadow:6px 6px 0 var(--ink); }
.stApp [class*="st-key-result_panel"]{ border-radius:14px; padding:1.1rem 1.4rem 1.3rem; border:2px solid var(--ink); background:var(--paper); }
.stApp .st-key-result_panel_real{ background:var(--green-tint); border-color:var(--green); box-shadow:6px 6px 0 var(--green); }
.stApp .st-key-result_panel_fake{ background:var(--red-tint); border-color:var(--red); box-shadow:6px 6px 0 var(--red); }
.stApp .st-key-result_panel_unsure{ background:#FFF6D6; border-color:var(--ink); box-shadow:6px 6px 0 var(--hl-press); }
.stApp .st-key-result_panel_empty{ background:transparent; border:2px dashed var(--muted); box-shadow:none; }

.stApp .step{ display:flex; align-items:center; gap:.75rem; margin:0 0 1.1rem; }
.stApp .step-n{ flex:none; width:2.1rem; height:2.1rem; border-radius:50%; background:var(--ink); color:#fff;
  display:grid; place-items:center; font:800 1.05rem var(--display); }
.stApp .step-t{ font:800 1.55rem/1.2 var(--display); color:var(--ink); }
.stApp .try-label{ font-weight:700; font-size:1.02rem; margin:1.2rem 0 .4rem; }

/* ---------- Inputs ---------- */
.stApp div[data-baseweb="textarea"], .stApp div[data-baseweb="select"] > div, .stApp div[data-baseweb="base-input"]{
  background:#fff; border:2px solid var(--ink); border-radius:8px; }
.stApp div[data-baseweb="textarea"]:focus-within, .stApp div[data-baseweb="select"] > div:focus-within{ box-shadow:0 0 0 3px rgba(29,78,216,.35); }
.stApp textarea{ font-size:1.08rem; line-height:1.7; color:var(--ink); background:transparent; }
.stApp [data-testid="stFileUploaderDropzone"]{ background:#fff; border:2px dashed var(--ink); border-radius:10px; }
.stApp [data-testid="stExpander"] details{ background:#fff; border:1.5px solid var(--line); border-radius:8px; }
.stApp [data-testid="stMetric"]{ background:#fff; border:2px solid var(--ink); border-radius:10px; padding:.8rem 1rem; }

/* ---------- Buttons ---------- */
.stApp .stButton > button, .stApp .stDownloadButton > button,
.stApp [data-testid="stBaseButton-secondary"], .stApp [data-testid="stBaseButton-primary"]{
  background:#fff; color:var(--ink); border:2px solid var(--ink); border-radius:8px; font-weight:700;
  min-height:2.8rem; padding:.4rem 1.1rem; box-shadow:0 3px 0 var(--ink);
  transition:transform .08s ease, box-shadow .08s ease, background-color .08s ease; }
.stApp .stButton > button:hover, .stApp .stDownloadButton > button:hover,
.stApp [data-testid="stBaseButton-secondary"]:hover{ background:#EAF0FB; color:var(--ink); border-color:var(--ink);
  transform:translateY(1px); box-shadow:0 2px 0 var(--ink); }
.stApp .stButton > button:active, .stApp .stDownloadButton > button:active{ transform:translateY(3px); box-shadow:0 0 0 var(--ink); }
.stApp .stButton > button p, .stApp .stDownloadButton > button p{ font-size:1.02rem; font-weight:700; line-height:1.2; color:inherit; margin:0; }

.stApp .st-key-check_btn button, .stApp [data-testid="stBaseButton-primary"]{
  background:var(--hl); color:var(--ink); min-height:3.7rem; border-radius:10px; box-shadow:0 5px 0 var(--ink); }
.stApp .st-key-check_btn button:hover, .stApp [data-testid="stBaseButton-primary"]:hover{
  background:#FFDB63; color:var(--ink); transform:translateY(2px); box-shadow:0 3px 0 var(--ink); }
.stApp .st-key-check_btn button:active, .stApp [data-testid="stBaseButton-primary"]:active{ transform:translateY(5px); box-shadow:0 0 0 var(--ink); }
.stApp .st-key-check_btn button p{ font-size:1.25rem; }
.stApp .st-key-sample1 button, .stApp .st-key-sample2 button, .stApp .st-key-sample3 button{ min-height:2.4rem; padding:.2rem .9rem; box-shadow:0 2px 0 var(--ink); }
.stApp .st-key-sample1 button p, .stApp .st-key-sample2 button p, .stApp .st-key-sample3 button p{ font-size:.95rem; }

/* ---------- Verdict ---------- */
.stApp .stamp{ display:inline-flex; align-items:center; gap:.7rem; padding:.5rem 1.15rem; border:4px solid currentColor;
  outline:2px solid currentColor; outline-offset:3px; border-radius:8px; transform:rotate(-2deg); margin:.5rem .5rem 1.2rem;
  font:800 clamp(1.7rem,3vw,2.3rem)/1.2 var(--display); animation:thump .3s cubic-bezier(.2,.9,.3,1.25) both; }
.stApp .stamp.real{ color:var(--green); }
.stApp .stamp.fake{ color:var(--red); }
.stApp .stamp.unsure{ color:var(--ink); background:var(--hl); }
.stApp .stamp-ico{ font-size:.9em; }
@keyframes thump{ from{ transform:rotate(-9deg) scale(1.4); opacity:0; } 55%{ opacity:1; } to{ transform:rotate(-2deg) scale(1); opacity:1; } }
@media (prefers-reduced-motion:reduce){ .stApp .stamp{ animation:none; } .stApp .stButton > button{ transition:none; } }

.stApp .conf{ display:flex; align-items:baseline; gap:.2rem .9rem; flex-wrap:wrap; margin:0 0 1rem; }
.stApp .conf-n{ font:800 2.7rem/1 var(--display); color:var(--ink); }
.stApp .conf-l{ font-size:1.05rem; color:var(--muted); font-weight:700; }
.stApp .meter{ height:1.05rem; background:#fff; border:2px solid var(--ink); border-radius:999px; overflow:hidden; }
.stApp .meter-fill{ height:100%; background:var(--ink); }
.stApp .meter-fill.real{ background:var(--green); }
.stApp .meter-fill.fake{ background:var(--red); }
.stApp .meter-cap{ margin-top:.5rem; font-size:.98rem; font-weight:700; color:var(--ink); }
.stApp .quote{ border-left:5px solid var(--ink); padding:.1rem 0 .1rem .9rem; color:var(--muted); font-size:1rem; margin:1.1rem 0 0; overflow-wrap:anywhere; }

.stApp .strip{ display:flex; border-top:2px solid var(--ink); border-bottom:2px solid var(--ink); margin:.8rem 0 .9rem; }
.stApp .strip > div{ flex:1; padding:.8rem 1rem; }
.stApp .strip > div + div{ border-left:1.5px solid var(--ink); }
.stApp .strip b{ display:block; font:800 1.9rem/1.1 var(--display); color:var(--ink); }
.stApp .strip span{ font-size:.95rem; color:var(--muted); font-weight:700; }

.stApp .section-title{ font:800 1.2rem/1.35 var(--display); color:var(--ink); margin:0 0 .7rem; }
.stApp .marked{ background:#fff; border:1.5px solid var(--line); border-radius:8px; padding:1rem 1.1rem; font-size:1.06rem; line-height:2;
  max-height:8.5rem; overflow:auto; color:var(--ink); overflow-wrap:anywhere; }
.stApp .marked mark{ color:var(--ink); padding:.05em .22em; border-radius:4px; font-weight:700; }
.stApp .marked mark.m-real{ background:#BDEBD0; box-shadow:inset 0 -3px 0 var(--green); }
.stApp .marked mark.m-fake{ background:#F9C6C6; box-shadow:inset 0 -3px 0 var(--red); }
.stApp .legend{ display:flex; flex-wrap:wrap; gap:.4rem 1.5rem; margin:.8rem 0 1.2rem; font-size:.98rem; font-weight:700; color:var(--ink); }
.stApp .legend span::before{ content:""; display:inline-block; width:1.15rem; height:.8rem; border-radius:3px; margin-right:.5rem; vertical-align:-.05rem; }
.stApp .legend .lg-real::before{ background:#BDEBD0; box-shadow:inset 0 -3px 0 var(--green); }
.stApp .legend .lg-fake::before{ background:#F9C6C6; box-shadow:inset 0 -3px 0 var(--red); }

.stApp .empty{ text-align:center; padding:2.5rem 1rem 2.5rem; }
.stApp .empty-q{ font:800 5.5rem/1 var(--display); color:var(--ink); }
.stApp .empty-t{ font-size:1.15rem; line-height:1.55; color:var(--ink); max-width:30ch; margin:.7rem auto 0; font-weight:700; }
.stApp .note{ background:#FFF6D6; border-left:6px solid var(--hl-press); padding:.85rem 1.1rem; border-radius:6px; color:var(--ink);
  font-size:1rem; line-height:1.45; margin-top:.4rem; }
"""

HERO_ART = """<svg viewBox="0 0 320 270" role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
<g transform="rotate(-5 160 135)">
<rect x="36" y="18" width="248" height="234" rx="8" fill="#FFFFFF"/>
<rect x="58" y="42" width="160" height="16" rx="3" fill="#10213F"/>
<rect x="58" y="66" width="204" height="16" rx="3" fill="#10213F"/>
<rect x="58" y="98" width="100" height="72" rx="4" fill="#D3DAE6"/>
<path d="M66 162 l24 -30 l18 20 l14 -14 l24 24z" fill="#9AA8C2"/>
<rect x="170" y="100" width="92" height="7" rx="3.5" fill="#B7C1D6"/>
<rect x="170" y="114" width="92" height="7" rx="3.5" fill="#B7C1D6"/>
<rect x="170" y="128" width="92" height="7" rx="3.5" fill="#B7C1D6"/>
<rect x="170" y="142" width="64" height="7" rx="3.5" fill="#B7C1D6"/>
<rect x="54" y="186" width="212" height="14" rx="3" fill="#FFD23F"/>
<rect x="58" y="190" width="204" height="6" rx="3" fill="#6B7A99"/>
<rect x="58" y="208" width="204" height="6" rx="3" fill="#B7C1D6"/>
<rect x="54" y="222" width="130" height="14" rx="3" fill="#FFD23F"/>
<rect x="58" y="226" width="122" height="6" rx="3" fill="#6B7A99"/>
</g>
<ellipse cx="214" cy="128" rx="74" ry="44" fill="none" stroke="#FF6B6B" stroke-width="6" stroke-linecap="round" transform="rotate(-10 214 128)" stroke-dasharray="330 40"/>
<path d="M262 56 l14 14 l28 -30" fill="none" stroke="#4ADE80" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


def _flat(markup: str) -> str:
    """One line, no indentation: stops the Markdown parser treating indented HTML as code."""
    return "".join(line.strip() for line in markup.splitlines())


def _esc(text) -> str:
    """Escape text for HTML. The dollar sign is escaped too so it is never read as maths."""
    return html.escape(str(text)).replace("$", "&#36;")


def brand_html(title: str) -> str:
    return _flat(f'<div class="brand"><span class="brand-mark">&#10003;</span><span class="brand-name">{_esc(title)}</span></div>')


def hero_html(headline: str, subtitle: str, facts) -> str:
    items = "".join(f"<li>{_esc(f)}</li>" for f in facts)
    return _flat(
        f'<div class="hero"><div class="hero-text"><h1 class="hero-title">{_esc(headline)}</h1>'
        f'<p class="hero-sub">{_esc(subtitle)}</p><ul class="facts">{items}</ul></div>'
        f'<div class="hero-art">{_flat(HERO_ART)}</div></div>'
    )


def step_html(number: int, text: str) -> str:
    return _flat(f'<div class="step"><span class="step-n">{number}</span><span class="step-t">{_esc(text)}</span></div>')


def verdict_html(kind: str, title: str, confidence: float, leaning: str, conf_label: str,
                 leaning_label: str, p_real: float, prob_label: str) -> str:
    """Stamp + confidence figure + probability meter. `kind` is real, fake or unsure."""
    icon = {"real": "&#10003;", "fake": "&#10007;", "unsure": "?"}[kind]
    width = max(0.0, min(100.0, p_real * 100))
    return _flat(
        f'<div class="stamp {kind}"><span class="stamp-ico">{icon}</span><span>{_esc(title)}</span></div>'
        f'<div class="conf"><span class="conf-n">{confidence:.1f}%</span>'
        f'<span class="conf-l">{_esc(conf_label)} ({_esc(leaning_label)}: {_esc(leaning)})</span></div>'
        f'<div class="meter" role="img" aria-label="{_esc(prob_label)}: {width:.1f}%">'
        f'<div class="meter-fill {kind}" style="width:{width:.1f}%"></div></div>'
        f'<div class="meter-cap">{_esc(prob_label)}: {width:.1f}%</div>'
    )


def quote_html(text: str, limit: int = 110) -> str:
    flat = " ".join(str(text).split())
    if len(flat) > limit:
        flat = flat[:limit].rstrip() + "..."
    return f'<div class="quote">{_esc(flat)}</div>'


def strip_html(items) -> str:
    """A ruled strip of (value, label) pairs."""
    cells = "".join(f"<div><b>{_esc(v)}</b><span>{_esc(l)}</span></div>" for v, l in items)
    return f'<div class="strip">{cells}</div>'


def marked_html(text: str, real_words, fake_words, limit: int = 2500) -> str:
    """The article with the words that pushed toward Real / Fake marked like highlighter pen."""
    real_set = {str(w).lower() for w in real_words}
    fake_set = {str(w).lower() for w in fake_words}
    flat = " ".join(str(text).split())  # no blank lines: they would end the HTML block
    cut = len(flat) > limit
    flat = flat[:limit]
    out = []
    for piece in re.split(r"(\w+)", flat):
        low = piece.lower()
        if low in real_set:
            out.append(f'<mark class="m-real">{_esc(piece)}</mark>')
        elif low in fake_set:
            out.append(f'<mark class="m-fake">{_esc(piece)}</mark>')
        else:
            out.append(_esc(piece))
    if cut:
        out.append("...")
    return f'<div class="marked">{"".join(out)}</div>'


def legend_html(real_label: str, fake_label: str) -> str:
    return _flat(f'<div class="legend"><span class="lg-real">{_esc(real_label)}</span><span class="lg-fake">{_esc(fake_label)}</span></div>')


def section_title_html(text: str) -> str:
    return f'<div class="section-title">{_esc(text)}</div>'


def empty_html(text: str) -> str:
    return _flat(f'<div class="empty"><div class="empty-q">?</div><div class="empty-t">{_esc(text)}</div></div>')


def note_html(text: str) -> str:
    return f'<div class="note">{_esc(text)}</div>'


def label_html(text: str) -> str:
    return f'<div class="try-label">{_esc(text)}</div>'
