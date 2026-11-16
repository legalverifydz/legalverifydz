# -*- coding: utf-8 -*-
"""
ui.py -- LegalVerifyDZ
Interface building blocks: unified SVG icon set, compact visitor
landing page (hero + tabs), the registered user's workspace, and the
plans page with the official packages.

All HTML is built from single-line fragments (no indentation, no blank
lines): multi-line HTML inside st.markdown can be misparsed as a
Markdown code block. Text sizes are set on <div>/<span> with
!important because Streamlit restyles <h1>-<h6> and <p> inside its
Markdown container.
"""

import base64
import html as _html
from datetime import datetime

import streamlit as st

import brand
import ui_text

# ---------------------------------------------------------------
# Icons (24x24 outline, one stroke style)
# ---------------------------------------------------------------
_ICON_PATHS = {
    "landmark": '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "scan": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    "languages": '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "briefcase": '<rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
}


def icon_html(name, size=24, color="#4F8BFF"):
    body = _ICON_PATHS[name]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'width="{s}" height="{s}" fill="none" stroke="{c}" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '{b}</svg>'
    ).format(s=size, c=color, b=body)
    enc = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return '<img src="data:image/svg+xml;base64,{}" width="{}" height="{}" alt="" />'.format(enc, size, size)


# ---------------------------------------------------------------
# CSS (neutral greys so it works on light and dark themes)
# ---------------------------------------------------------------
EXTRA_CSS = """
/* ---------- buttons: primary = brand blue, secondary = outlined ---------- */
div.stButton > button[kind="secondary"],
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background: transparent;
    color: inherit;
    border: 1px solid rgba(127,127,127,0.45);
    box-shadow: none;
}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(37,99,235,0.08);
    border-color: #4F8BFF;
    opacity: 1;
}
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #1D4ED8, #3B82F6);
    color: #FFFFFF;
    border: none;
}

/* ---------- sidebar: language switch ---------- */
.st-key-lang_switch button {
    padding: 4px 0 !important;
    min-height: 34px !important;
    font-size: 13px !important;
    border-radius: 9px !important;
}
.st-key-lang_switch button p { font-size: 13px !important; }

/* ---------- sidebar: navigation (buttons styled as menu items) ---------- */
.st-key-sidebar_nav button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    color: #CBD5E1 !important;
}
.st-key-sidebar_nav button p {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: inherit !important;
}
.st-key-sidebar_nav button:hover {
    background: rgba(255,255,255,0.07) !important;
}
.st-key-sidebar_nav button[kind="primary"],
.st-key-sidebar_nav button[data-testid="stBaseButton-primary"] {
    background: rgba(79,139,255,0.22) !important;
    color: #FFFFFF !important;
    box-shadow: inset 3px 0 0 #4F8BFF !important;
}

/* ---------- sidebar: user and guest cards ---------- */
.lv-side-card {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px; padding: 10px 12px;
}
.lv-avatar {
    flex: 0 0 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: #fff !important; font-weight: 800 !important; font-size: 14px !important;
}
.lv-side-lbl { font-size: 14px !important; color: #94A3B8 !important; margin-bottom: 4px; }
.lv-side-tag { font-size: 15px !important; color: #94A3B8 !important; margin-top: 8px; text-align: center; }
[data-baseweb="tab"] p { font-size: 17px !important; font-weight: 700 !important; }
.lv-side-main { font-size: 15px !important; font-weight: 700 !important; line-height: 1.3; }
.lv-side-sub  { font-size: 13px !important; color: #94A3B8 !important; line-height: 1.4; }

/* ---------- hero ---------- */
.lv-hero {
    position: relative; overflow: hidden;
    border-radius: 24px; margin: -1rem 0 1rem; min-height: 440px;
    display: flex; flex-direction: column; justify-content: center;
    background: linear-gradient(135deg, #0B1F3A 0%, #11385E 55%, #0F4C5C 100%);
    box-shadow: 0 16px 44px rgba(11,31,58,0.30);
}
.lv-hero .hero-bg { position: absolute; inset: 0; pointer-events: none; }
.lv-hero-nav {
    position: relative; z-index: 1;
    display: flex; justify-content: space-between; align-items: center; gap: 16px;
    padding: 30px 56px 0;
}
.lv-hero-nav img { width: 250px; max-width: 60%; }
.lv-hero-grid {
    position: relative; z-index: 1;
    display: grid; grid-template-columns: 1.5fr 1fr; align-items: center;
    gap: 28px; padding: 22px 56px 64px;
}
.lv-hero-badge {
    display: inline-block; padding: 5px 14px; border-radius: 999px;
    background: rgba(125,211,252,0.15); border: 1px solid rgba(125,211,252,0.35);
    color: #BAE6FD !important; font-size: 14px !important; font-weight: 700 !important;
}
.lv-hero-title {
    color: #FFFFFF !important; font-size: 42px !important; font-weight: 800 !important;
    line-height: 1.45 !important; margin: 6px 0 12px;
}
.lv-hero-sub {
    color: #CBD5E1 !important; font-size: 19px !important; line-height: 1.9 !important;
    max-width: 660px;
}
.lv-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.lv-chip {
    padding: 6px 14px; border-radius: 999px; font-size: 14px !important; font-weight: 600 !important;
    color: #E2E8F0 !important; background: rgba(255,255,255,0.09); border: 1px solid rgba(255,255,255,0.16);
}
.lv-hero-visual { display: flex; justify-content: center; transform: scale(1.12); }
@media (max-width: 800px) {
    .lv-hero-nav { padding: 20px 22px 0; }
    .lv-hero-nav .lv-hero-badge { display: none; }
    .lv-hero-grid { grid-template-columns: 1fr; padding: 16px 22px 28px; }
    .lv-hero-visual { display: none; }
    .lv-hero-title { font-size: 28px !important; }
}

/* ---------- compact tiles / cards ---------- */
.lv-tiles {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 14px; margin: 14px 0 20px;
}
.lv-tile {
    display: flex; gap: 12px; align-items: flex-start;
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.22);
    border-radius: 16px; padding: 16px;
}
.lv-ico {
    flex: 0 0 42px; height: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(37,99,235,0.14);
}
.lv-t-title { font-size: 17px !important; font-weight: 700 !important; line-height: 1.4 !important; margin-bottom: 4px; }
.lv-t-desc  { font-size: 15px !important; line-height: 1.8 !important; opacity: 0.82; }

/* ---------- tab content ---------- */
.lv-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin: 10px 0; }
.lv-step {
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.22);
    border-radius: 16px; padding: 18px;
}
.lv-step-n {
    width: 34px; height: 34px; border-radius: 50%; margin-bottom: 10px;
    background: #2563EB; color: #fff !important; font-weight: 800 !important; font-size: 16px !important;
    display: flex; align-items: center; justify-content: center;
}
.lv-report {
    display: grid; grid-template-columns: 220px 1fr; gap: 0;
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.22);
    border-radius: 16px; overflow: hidden; margin: 10px 0 6px;
}
.lv-report-side { padding: 18px; border-inline-end: 1px solid rgba(127,127,127,0.22); background: rgba(127,127,127,0.05); }
.lv-report-main { padding: 6px 18px; }
.lv-rs-k { font-size: 13px !important; opacity: 0.7; margin-top: 10px; }
.lv-rs-v { font-size: 17px !important; font-weight: 700 !important; }
.lv-rs-big { font-size: 40px !important; font-weight: 800 !important; line-height: 1.2 !important; color: #DC2626 !important; }
.lv-meter { height: 8px; border-radius: 999px; background: rgba(127,127,127,0.25); overflow: hidden; margin: 4px 0 6px; }
.lv-meter span { display: block; height: 100%; background: #DC2626; border-radius: 999px; }
.lv-find { padding: 12px 0; border-bottom: 1px dashed rgba(127,127,127,0.28); }
.lv-find:last-child { border-bottom: none; }
.lv-find-t { font-size: 16px !important; font-weight: 700 !important; margin-inline-start: 8px; }
.lv-find-d { font-size: 14px !important; line-height: 1.7 !important; opacity: 0.82; margin-top: 6px; }
.lv-note { font-size: 13px !important; opacity: 0.65; margin-bottom: 8px; }
@media (max-width: 800px) {
    .lv-report { grid-template-columns: 1fr; }
    .lv-report-side { border-inline-end: none; border-bottom: 1px solid rgba(127,127,127,0.22); }
}
.lv-pill {
    display: inline-block; padding: 2px 11px; border-radius: 999px;
    font-weight: 700 !important; font-size: 13px !important;
}
.lv-pill.high { background: #FEE2E2; color: #991B1B !important; }
.lv-pill.med  { background: #FEF9C3; color: #854D0E !important; }
.lv-pill.low  { background: #DCFCE7; color: #166534 !important; }

/* ---------- workspace ---------- */
.lv-ws-head {
    border-radius: 22px; padding: 26px 30px; margin: -1rem 0 1rem;
    background: linear-gradient(135deg, #0B1F3A 0%, #11385E 55%, #0F4C5C 100%);
    box-shadow: 0 12px 34px rgba(11,31,58,0.28);
}
.lv-ws-top { display: flex; align-items: center; gap: 18px; }
.lv-ws-top img { flex: 0 0 64px; }
.lv-ws-hello { color: #FFFFFF !important; font-size: 30px !important; font-weight: 800 !important; line-height: 1.4 !important; }
.lv-ws-sub   { color: #CBD5E1 !important; font-size: 16px !important; margin-top: 4px; }
.lv-ws-pill {
    display: inline-block; margin-top: 14px; padding: 5px 14px; border-radius: 999px;
    background: rgba(125,211,252,0.15); border: 1px solid rgba(125,211,252,0.35);
    color: #BAE6FD !important; font-size: 14px !important; font-weight: 700 !important;
}
.lv-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 14px 0; }
.lv-kpi {
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.22);
    border-radius: 16px; padding: 16px 18px;
}
.lv-kpi-top { display: flex; justify-content: space-between; align-items: center; }
.lv-kpi-lbl { font-size: 14px !important; font-weight: 600 !important; opacity: 0.75; }
.lv-kpi-num { font-size: 36px !important; font-weight: 800 !important; line-height: 1.25 !important; margin: 4px 0 2px; }
.lv-kpi-sub { font-size: 13px !important; opacity: 0.65; }
.lv-card-box {
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.22);
    border-radius: 16px; padding: 18px 20px; margin: 8px 0 14px;
}
.lv-h { font-size: 19px !important; font-weight: 800 !important; margin: 4px 0 12px; }
.lv-stack { display: flex; height: 14px; border-radius: 999px; overflow: hidden; background: rgba(127,127,127,0.22); }
.lv-stack span { display: block; height: 100%; }
.lv-legend { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 12px; font-size: 14px !important; }
.lv-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-inline-end: 6px; }
.lv-row-name { font-size: 15px !important; font-weight: 700 !important; word-break: break-word; }
.lv-row-sub  { font-size: 13px !important; opacity: 0.65; }
.lv-row-date { font-size: 14px !important; opacity: 0.75; }

/* ---------- plans ---------- */
.lv-plan {
    background: rgba(127,127,127,0.07); border: 1px solid rgba(127,127,127,0.25);
    border-radius: 20px; padding: 24px 22px; height: 100%; min-height: 380px;
}
.lv-plan.feat { border: 2px solid #2563EB; box-shadow: 0 10px 30px rgba(37,99,235,0.16); }
.lv-plan-name  { font-size: 22px !important; font-weight: 800 !important; }
.lv-plan-price { font-size: 34px !important; font-weight: 800 !important; margin-top: 10px; line-height: 1.2 !important; }
.lv-plan-unit  { font-size: 14px !important; font-weight: 600 !important; opacity: 0.7; }
.lv-plan-year  { font-size: 13px !important; opacity: 0.7; margin: 2px 0 14px; }
.lv-feat { display: flex; gap: 8px; align-items: flex-start; padding: 6px 0; font-size: 15px !important; line-height: 1.6 !important; }
.lv-ck { color: #16A34A !important; font-weight: 800 !important; }
.lv-tag {
    display: inline-block; font-size: 13px !important; font-weight: 700 !important;
    padding: 2px 11px; border-radius: 999px; margin-bottom: 8px;
    background: rgba(37,99,235,0.15); color: #2563EB !important;
}
.lv-table-wrap { overflow-x: auto; margin: 6px 0 12px; }
.lv-table { width: 100%; border-collapse: collapse; font-size: 14px !important; min-width: 560px; }
.lv-table th, .lv-table td { padding: 10px 12px; border-bottom: 1px solid rgba(127,127,127,0.22); text-align: center; }
.lv-table th { background: rgba(37,99,235,0.12); font-weight: 800 !important; }
.lv-table td:first-child, .lv-table th:first-child { text-align: start; font-weight: 600 !important; }
.lv-table .no { opacity: 0.4; }
"""


# ---------------------------------------------------------------
# helpers
# ---------------------------------------------------------------
def _e(text):
    return _html.escape(str(text))


def _tiles(items, color="#4F8BFF"):
    return '<div class="lv-tiles">' + "".join(
        '<div class="lv-tile"><div class="lv-ico">{i}</div><div>'
        '<div class="lv-t-title">{t}</div><div class="lv-t-desc">{d}</div></div></div>'.format(
            i=icon_html(it["i"], 22, color), t=_e(it["t"]), d=_e(it["d"])
        )
        for it in items
    ) + '</div>'


def initials(name):
    parts = [p for p in str(name).replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def money(n, t):
    return "{:,} {}".format(n, t["currency"])


# ---------------------------------------------------------------
# VISITOR LANDING PAGE  (compact: hero + tiles + tabs)
# ---------------------------------------------------------------
def render_landing(t, go, visual_html, bubbles_html):
    chips = "".join('<span class="lv-chip">{}</span>'.format(_e(c)) for c in t["hero_chips"])
    st.markdown(
        '<style>'
        '.block-container{padding-top:0 !important;padding-left:3rem !important;padding-right:3rem !important;}'
        '.lv-hero{margin:0 -3rem 1.4rem -3rem !important;border-radius:0 0 30px 30px !important;}'
        '@media (max-width:800px){.block-container{padding-left:1rem !important;padding-right:1rem !important;}'
        '.lv-hero{margin:0 -1rem 1rem -1rem !important;min-height:0 !important;}}'
        '</style>'
        '<div class="lv-hero">'
        '<div class="hero-bg"><div class="hero-blob b1"></div><div class="hero-blob b2"></div>'
        '<div class="hero-blob b3"></div>' + bubbles_html + '</div>'
        '<div class="lv-hero-nav">{logo}<span class="lv-hero-badge">{badge}</span></div>'
        '<div class="lv-hero-grid"><div>'
        '<div class="lv-hero-title">{title}</div>'
        '<div class="lv-hero-sub">{sub}</div>'
        '<div class="lv-chips">{chips}</div>'
        '</div><div class="lv-hero-visual">{visual}</div></div></div>'.format(
            logo=brand.horizontal(236, dark=True, align="start"),
            badge=_e(t["hero_badge"]), title=_e(t["hero_title"]),
            sub=_e(t["hero_sub"]), chips=chips, visual=visual_html
        ),
        unsafe_allow_html=True,
    )

    c1, c2, c3, _sp = st.columns([1.2, 1.2, 1, 1.4])
    c1.button(
        t["cta_analyze"], key="cta_analyze_btn", type="primary",
        use_container_width=True, icon=":material/upload_file:",
        on_click=go, args=("analysis",),
    )
    c2.button(
        t["cta_demo"], key="cta_demo_btn", use_container_width=True,
        icon=":material/play_circle:",
        on_click=go, args=("analysis",), kwargs={"auto_demo": True},
    )
    c3.button(
        t["cta_plans"], key="cta_plans_btn", use_container_width=True,
        icon=":material/workspace_premium:",
        on_click=go, args=("plans",),
    )

    st.markdown(_tiles(t["values"]), unsafe_allow_html=True)

    tab_how, tab_sample, tab_who, tab_trust = st.tabs(
        [t["tab_how"], t["tab_sample"], t["tab_who"], t["tab_trust"]]
    )

    with tab_how:
        st.markdown(
            '<div class="lv-steps">' + "".join(
                '<div class="lv-step"><div class="lv-step-n">{n}</div>'
                '<div class="lv-t-title">{t}</div><div class="lv-t-desc">{d}</div></div>'.format(
                    n=i, t=_e(s["t"]), d=_e(s["d"])
                )
                for i, s in enumerate(t["steps"], start=1)
            ) + '</div>',
            unsafe_allow_html=True,
        )

    with tab_sample:
        finds = "".join(
            '<div class="lv-find"><span class="lv-pill {s}">{sl}</span>'
            '<span class="lv-find-t">{t}</span><div class="lv-find-d">{d}</div></div>'.format(
                s=f["s"], sl=_e(f["sl"]), t=_e(f["t"]), d=_e(f["d"])
            )
            for f in t["sample_findings"]
        )
        st.markdown(
            '<div class="lv-report"><div class="lv-report-side">'
            '<div class="lv-rs-k">{tl}</div><div class="lv-rs-v">{tv}</div>'
            '<div class="lv-rs-k">{rl}</div><div class="lv-rs-big">70%</div>'
            '<div class="lv-meter"><span style="width:70%"></span></div>'
            '<div class="lv-rs-v">{lvl}</div>'
            '<div class="lv-rs-k">{cl}</div><div class="lv-rs-v">80%</div>'
            '</div><div class="lv-report-main">{finds}</div></div>'
            '<div class="lv-note">{note}</div>'.format(
                tl=_e(t["sample_type_lbl"]), tv=_e(t["sample_type"]),
                rl=_e(t["sample_risk_lbl"]), lvl=_e(t["sample_risk_level"]),
                cl=_e(t["sample_conf_lbl"]), finds=finds, note=_e(t["sample_note"]),
            ),
            unsafe_allow_html=True,
        )

    with tab_who:
        st.markdown(_tiles(t["who"]), unsafe_allow_html=True)

    with tab_trust:
        st.markdown(_tiles(t["trust"]), unsafe_allow_html=True)


# ---------------------------------------------------------------
# REGISTERED USER WORKSPACE
# ---------------------------------------------------------------
def render_workspace(t, user, rows, go, pending_count=0):
    plan = user.get("Plan") or "Free"
    plan_name = t["plan_names"].get(plan, plan)

    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%Y-%m")
    used_year = sum(1 for r in rows if str(r.get("created_at") or "").startswith(year))
    used_month = sum(1 for r in rows if str(r.get("created_at") or "").startswith(month))
    limit = ui_text.PLAN_LIMITS.get(plan)

    pill = t["ws_plan"].format(plan=plan_name) + "  ·  " + (
        t["ws_usage"].format(used=used_year, limit=limit) if limit
        else t["ws_usage_free"].format(used=used_year)
    )

    st.markdown(
        '<div class="lv-ws-head"><div class="lv-ws-top">{ic}<div>'
        '<div class="lv-ws-hello">{h}</div><div class="lv-ws-sub">{s}</div></div></div>'
        '<span class="lv-ws-pill">{p}</span></div>'.format(
            ic=brand.icon(64, dark=True, align="start"),
            h=_e(t["ws_hello"].format(name=user.get("Name", ""))),
            s=_e(t["ws_sub"]), p=_e(pill),
        ),
        unsafe_allow_html=True,
    )

    b1, b2, b3, _sp = st.columns([1.2, 1.2, 1, 1.6])
    b1.button(
        t["new_analysis"], key="ws_new_btn", type="primary",
        use_container_width=True, icon=":material/upload_file:",
        on_click=go, args=("analysis",),
    )
    b2.button(
        t["view_all"], key="ws_hist_btn", use_container_width=True,
        icon=":material/history:", on_click=go, args=("history",),
    )
    b3.button(
        t["cta_plans"], key="ws_plans_btn", use_container_width=True,
        icon=":material/workspace_premium:", on_click=go, args=("plans",),
    )

    high = sum(1 for r in rows if r.get("risk_level") == "High")
    med = sum(1 for r in rows if r.get("risk_level") == "Moderate")
    low = sum(1 for r in rows if r.get("risk_level") == "Low")
    scores = [r["risk_score"] for r in rows if r.get("risk_score") is not None]
    avg = round(sum(scores) / len(scores)) if scores else None
    if avg is None:
        avg_txt, avg_sub = "-", ""
    else:
        avg_txt = "{}%".format(avg)
        avg_sub = t["risk_low"] if avg < 30 else (t["risk_med"] if avg < 60 else t["risk_high"])

    def kpi(icon, color, label, num, sub):
        return (
            '<div class="lv-kpi"><div class="lv-kpi-top"><span class="lv-kpi-lbl">{l}</span>{i}</div>'
            '<div class="lv-kpi-num">{n}</div><div class="lv-kpi-sub">{s}</div></div>'
        ).format(l=_e(label), i=icon_html(icon, 22, color), n=_e(num), s=_e(sub))

    st.markdown(
        '<div class="lv-kpis">'
        + kpi("file", "#2563EB", t["kpi_total"], len(rows), t["kpi_total_sub"].format(n=used_month))
        + kpi("gauge", "#DC2626", t["kpi_avg"], avg_txt, avg_sub)
        + kpi("alert", "#DC2626", t["kpi_high"], high, t["kpi_high_sub"])
        + kpi("scale", "#7C3AED", t["kpi_lawyer"], pending_count, t["kpi_lawyer_sub"])
        + '</div>',
        unsafe_allow_html=True,
    )

    # risk distribution: one stacked bar + legend
    total = len(rows)
    if total:
        segs = "".join(
            '<span style="width:{w:.1f}%;background:{c};"></span>'.format(w=100.0 * n / total, c=c)
            for n, c in ((high, "#DC2626"), (med, "#F59E0B"), (low, "#16A34A")) if n
        )
    else:
        segs = ""
    legend = "".join(
        '<span><span class="lv-dot" style="background:{c};"></span>{l}: <b>{n}</b></span>'.format(
            c=c, l=_e(l), n=n
        )
        for l, n, c in (
            (t["risk_high"], high, "#DC2626"),
            (t["risk_med"], med, "#F59E0B"),
            (t["risk_low"], low, "#16A34A"),
        )
    )
    st.markdown(
        '<div class="lv-card-box"><div class="lv-h">{h}</div>'
        '<div class="lv-stack">{s}</div><div class="lv-legend">{lg}</div></div>'.format(
            h=_e(t["dist_title"]), s=segs, lg=legend
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lv-h">{}</div>'.format(_e(t["recent"])), unsafe_allow_html=True)

    if not rows:
        st.info(t["no_recent"])
        return

    with st.container(border=True):
        for r in rows[:6]:
            level = r.get("risk_level") or "-"
            cls = {"High": "high", "Moderate": "med", "Low": "low"}.get(level, "low")
            lbl = {"High": t["risk_high"], "Moderate": t["risk_med"], "Low": t["risk_low"]}.get(level, level)
            c_name, c_date, c_risk, c_btn = st.columns([3.2, 1.4, 1.6, 1])
            c_name.markdown(
                '<div class="lv-row-name">{f}</div><div class="lv-row-sub">{ty}</div>'.format(
                    f=_e(r.get("filename") or "Contract"), ty=_e(r.get("contract_type") or "-")
                ),
                unsafe_allow_html=True,
            )
            c_date.markdown(
                '<div class="lv-row-date">{}</div>'.format(_e(str(r.get("created_at") or "")[:10])),
                unsafe_allow_html=True,
            )
            c_risk.markdown(
                '<span class="lv-pill {c}">{l} · {s}%</span>'.format(
                    c=cls, l=_e(lbl),
                    s=_e(r["risk_score"] if r.get("risk_score") is not None else "-"),
                ),
                unsafe_allow_html=True,
            )
            c_btn.button(
                t["open_btn"], key="ws_open_{}".format(r["id"]),
                use_container_width=True,
                on_click=go, args=("history",), kwargs={"history_open_id": r["id"]},
            )


# ---------------------------------------------------------------
# PLANS PAGE (official packages)
# ---------------------------------------------------------------
def render_plans(t, current_plan, authenticated):
    st.markdown('<div class="lv-h" style="font-size:28px !important;">{}</div>'.format(_e(t["plans_title"])), unsafe_allow_html=True)
    st.caption(t["plans_sub"])

    if authenticated and current_plan not in {p["id"] for p in ui_text.PLANS}:
        st.caption(t["plan_free_note"].format(plan=t["plan_names"].get(current_plan, current_plan)))

    cols = st.columns(len(ui_text.PLANS))
    for col, p in zip(cols, ui_text.PLANS):
        pid = p["id"]
        is_current = authenticated and pid == current_plan
        featured = pid == "Professional"
        tag = '<span class="lv-tag">{}</span><br>'.format(_e(t["plan_current"])) if is_current else ""
        feats = "".join(
            '<div class="lv-feat"><span class="lv-ck">✓</span><span>{}</span></div>'.format(_e(f))
            for f in t["plan_feats"][pid]
        )
        with col:
            st.markdown(
                '<div class="lv-plan{ft}">{tag}<div class="lv-plan-name">{n}</div>'
                '<div class="lv-plan-price">{pr} <span class="lv-plan-unit">{u}</span></div>'
                '<div class="lv-plan-year">{y}</div>{f}</div>'.format(
                    ft=" feat" if (featured or is_current) else "", tag=tag,
                    n=_e(pid), pr=_e("{:,}".format(p["monthly"])) + " " + _e(t["currency"]),
                    u=_e(t["per_month"]),
                    y=_e(t["or_yearly"].format(price=money(p["yearly"], t))), f=feats,
                ),
                unsafe_allow_html=True,
            )
            if ui_text.CONTACT_EMAIL:
                st.link_button(
                    t["plan_request"],
                    "mailto:{}?subject={}".format(ui_text.CONTACT_EMAIL, "LegalVerifyDZ - " + pid),
                    use_container_width=True,
                    type="primary" if featured else "secondary",
                )

    if ui_text.CONTACT_EMAIL:
        st.caption(t["plan_contact"].format(email=ui_text.CONTACT_EMAIL))
    else:
        st.caption(t["plan_contact_none"])

    st.markdown('<div class="lv-h" style="margin-top:18px;">{}</div>'.format(_e(t["cmp_title"])), unsafe_allow_html=True)

    def cell(v):
        v = str(v)
        if v == "✓":
            return '<td><span class="lv-ck">✓</span></td>'
        if v == "—":
            return '<td><span class="no">—</span></td>'
        return "<td>{}</td>".format(_e(v))

    head = "".join("<th>{}</th>".format(_e(h)) for h in t["cmp_head"])
    body = "".join(
        "<tr><td>{}</td>{}</tr>".format(_e(r[0]), "".join(cell(v) for v in r[1:]))
        for r in t["cmp_rows"]
    )
    st.markdown(
        '<div class="lv-table-wrap"><table class="lv-table"><thead><tr>{h}</tr></thead>'
        '<tbody>{b}</tbody></table></div>'.format(h=head, b=body),
        unsafe_allow_html=True,
    )
