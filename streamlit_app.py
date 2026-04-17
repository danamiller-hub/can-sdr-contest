import streamlit as st
import requests
import re
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
SHEET_ID = "1a-zLRK-4zcC0V2uzK2BGzd32vbllNXFaSB1bu8ZlT5E"
GID      = "954096219"

METRICS = [
    {"key": "signs", "label": "Top Mx Signs", "short": "Signs", "goal": 98,  "color": "#FF3008", "emoji": "✍️"},
    {"key": "mh",    "label": "Top Mx MH",    "short": "MH",    "goal": 171, "color": "#FF9800", "emoji": "📋"},
    {"key": "ms",    "label": "Top Mx MS",     "short": "MS",    "goal": 244, "color": "#448aff", "emoji": "🚀"},
]

WEEKS = ["3/30","4/6","4/13","4/20","4/27","5/4","5/11","5/18","5/25","6/1","6/8","6/15","6/22","6/29"]

END_DATE = datetime(2026, 6, 29, 23, 59, 59)

FALLBACK = {
    "signs": {"actual":[6,14,9,0,0,0,0,0,0,0,0,0,0,0], "plan":[6,8,8,6,9,8,8,7,8,8,8,7,5,2],    "qtdA":29,  "qtdP":22, "qtdPct":131},
    "mh":    {"actual":[23,20,42,0,0,0,0,0,0,0,0,0,0,0],"plan":[11,13,13,11,16,14,14,13,14,15,14,12,9,3],"qtdA":85,  "qtdP":38, "qtdPct":222},
    "ms":    {"actual":[22,63,33,0,0,0,0,0,0,0,0,0,0,0], "plan":[16,19,19,16,22,20,19,18,20,21,19,17,12,5],"qtdA":118, "qtdP":54, "qtdPct":213},
}

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🇨🇦 CAN SDR Top Mx Acceleration",
    page_icon="🇨🇦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auto-refresh every 5 minutes (300 000 ms)
st_autorefresh(interval=300_000, key="autorefresh")

# ═══════════════════════════════════════════════════════════
# GLOBAL STYLES
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* Metric cards */
.metric-card {
    background: #13132b;
    border: 1px solid #25254a;
    border-radius: 18px;
    padding: 22px 22px 16px;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 18px 18px 0 0;
}
.card-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #7777aa;
    margin-bottom: 2px;
}
.card-sublabel {
    font-size: 10px;
    color: #444466;
    margin-bottom: 14px;
}
.card-actual {
    font-size: 52px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -2px;
}
.card-of-goal {
    font-size: 12px;
    color: #7777aa;
    margin-top: 3px;
    margin-bottom: 10px;
}
.pacing-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 14px;
}
.bar-track {
    background: rgba(255,255,255,.07);
    border-radius: 8px;
    height: 7px;
    overflow: hidden;
    margin-bottom: 5px;
}
.bar-fill {
    height: 100%;
    border-radius: 8px;
}
.bar-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #444466;
}

/* Table styling */
.week-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.week-table th {
    padding: 8px 10px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: #7777aa;
    border-bottom: 1px solid #25254a;
    text-align: center;
    white-space: nowrap;
}
.week-table th:first-child, .week-table th:nth-child(2) { text-align: left; }
.week-table td {
    padding: 7px 10px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,.03);
    white-space: nowrap;
}
.week-table td:first-child, .week-table td:nth-child(2) { text-align: left; }
.week-table .cur-col { background: rgba(255,48,8,.06); }
.week-table .cur-hd  { color: #FF3008 !important; }
.week-table .qtd-col { border-left: 1px solid #25254a; }
.week-table .p-hi { color: #00e676; font-weight: 700; }
.week-table .p-md { color: #FFD600; font-weight: 700; }
.week-table .p-lo { color: #FF9800; font-weight: 600; }
.week-table .p-zr { color: #444466; }
.week-table .tr-plan td { color: #555577; }
.week-table .tr-gap td { height: 8px; border: none; }
.week-table .metric-label { font-weight: 700; }

/* Section headers */
.section-header {
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 7px;
}

/* Banner */
.banner {
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 13px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.banner .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

/* Countdown */
.countdown-row {
    display: flex;
    gap: 0;
    align-items: flex-end;
}
.cd-unit { text-align: center; min-width: 56px; }
.cd-num  { font-size: 38px; font-weight: 900; line-height: 1; color: #FF3008; text-shadow: 0 0 20px rgba(255,48,8,.4); }
.cd-lbl  { font-size: 9px; color: #7777aa; text-transform: uppercase; letter-spacing: 1px; }
.cd-sep  { font-size: 30px; font-weight: 900; color: #25254a; padding-bottom: 13px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# DATA FETCH
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=300)   # cache 5 min to match autorefresh
def fetch_sheet_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json&gid={GID}"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    raw = res.text
    match = re.search(r"google\.visualization\.Query\.setResponse\(([\s\S]*)\)", raw)
    if not match:
        raise ValueError("Could not parse gviz response")
    payload = json.loads(match.group(1))
    if payload.get("status") == "error":
        raise ValueError("Sheet returned error")

    rows = payload["table"]["rows"]

    def cell(r, c):
        try:
            v = rows[r]["c"][c]
            if v is None or v.get("v") is None:
                return 0
            return v["v"]
        except (IndexError, KeyError, TypeError):
            return 0

    def week_row(r):
        vals = []
        for i in range(len(WEEKS)):
            v = cell(r, i + 2)
            vals.append(v if isinstance(v, (int, float)) else 0)
        return vals

    def parse_pct(v):
        if isinstance(v, (int, float)):
            return round(v * 100)
        if isinstance(v, str):
            return int(v.replace("%", "").strip()) if v.strip() else 0
        return 0

    return {
        "signs": {"actual": week_row(2), "plan": week_row(3), "qtdA": cell(2,16) or 0, "qtdP": cell(3,16) or 0, "qtdPct": parse_pct(cell(4,16))},
        "mh":    {"actual": week_row(5), "plan": week_row(6), "qtdA": cell(5,16) or 0, "qtdP": cell(6,16) or 0, "qtdPct": parse_pct(cell(7,16))},
        "ms":    {"actual": week_row(8), "plan": week_row(9), "qtdA": cell(8,16) or 0, "qtdP": cell(9,16) or 0, "qtdPct": parse_pct(cell(10,16))},
    }, True


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def pacing_color(p):
    if p >= 100: return "#00e676"
    if p >= 75:  return "#FFD600"
    if p > 0:    return "#FF9800"
    return "#555577"

def pacing_class(p):
    if p >= 100: return "p-hi"
    if p >= 75:  return "p-md"
    if p > 0:    return "p-lo"
    return "p-zr"

def pacing_label(p):
    if p >= 200: return "🔥🔥 Legendary!"
    if p >= 150: return "🔥 On Fire!"
    if p >= 100: return "✅ On Track"
    if p >= 75:  return "⚠️ At Risk"
    if p > 0:    return "🚨 Behind"
    return "—"

def current_week_idx():
    today = datetime.today()
    idx = 0
    for i, w in enumerate(WEEKS):
        m, d = map(int, w.split("/"))
        if datetime(2026, m, d) <= today:
            idx = i
    return idx

def countdown_html():
    diff = END_DATE - datetime.now()
    if diff.total_seconds() <= 0:
        return "<div style='color:#7777aa'>Contest has ended</div>"
    total_secs = int(diff.total_seconds())
    days  = diff.days
    hours = (total_secs % 86400) // 3600
    mins  = (total_secs % 3600)  // 60
    secs  = total_secs % 60
    def unit(val, lbl):
        return f"<div class='cd-unit'><div class='cd-num'>{str(val).zfill(2)}</div><div class='cd-lbl'>{lbl}</div></div>"
    sep = "<span class='cd-sep'>:</span>"
    return f"""
    <div style='text-align:right'>
        <div style='font-size:10px;color:#7777aa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px'>⏱ Contest ends in</div>
        <div class='countdown-row' style='justify-content:flex-end'>
            {unit(days,'Days')}{sep}{unit(hours,'Hrs')}{sep}{unit(mins,'Min')}{sep}{unit(secs,'Sec')}
        </div>
    </div>"""


# ═══════════════════════════════════════════════════════════
# METRIC CARD HTML
# ═══════════════════════════════════════════════════════════
def metric_card_html(m, d):
    pct   = d["qtdPct"]
    color = m["color"]
    pc    = pacing_color(pct)
    prog  = min(d["qtdA"] / m["goal"] * 100, 100)
    lbl   = pacing_label(pct)
    fire  = " 🔥" if pct >= 150 else ""
    return f"""
    <div class="metric-card" style="border-color:{color}33">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color};border-radius:18px 18px 0 0"></div>
        <div class="card-label">{m['emoji']} {m['short']}{fire}</div>
        <div class="card-sublabel">{m['label']} &nbsp;·&nbsp; Goal: {m['goal']}</div>
        <div class="card-actual" style="color:{color}">{d['qtdA']}</div>
        <div class="card-of-goal">of <strong>{m['goal']}</strong> QTD goal</div>
        <span class="pacing-badge" style="background:{pc}1a;color:{pc};border:1px solid {pc}44">
            {lbl}{f" &nbsp; {pct}%" if pct > 0 else ""}
        </span>
        <div class="bar-track">
            <div class="bar-fill" style="width:{prog:.1f}%;background:{color}"></div>
        </div>
        <div class="bar-labels">
            <span>0</span><span>{m['goal']//2}</span><span>{m['goal']}</span>
        </div>
    </div>"""


# ═══════════════════════════════════════════════════════════
# SPARKLINE CHART
# ═══════════════════════════════════════════════════════════
def sparkline_chart(m, d):
    active = [i for i in range(len(WEEKS)) if d["plan"][i] > 0 or d["actual"][i] > 0]
    labels  = [WEEKS[i] for i in active]
    actuals = [d["actual"][i] for i in active]
    plans   = [d["plan"][i]   for i in active]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=actuals,
        name="Actual",
        mode="lines+markers",
        line=dict(color=m["color"], width=2.5),
        fill="tozeroy",
        fillcolor=m["color"] + "22",
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=plans,
        name="Plan",
        mode="lines+markers",
        line=dict(color="rgba(255,255,255,.25)", width=1.5, dash="dot"),
        marker=dict(size=3),
    ))
    fig.update_layout(
        height=130,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=True,
                   tickfont=dict(color="#555577", size=9), zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.05)",
                   tickfont=dict(color="#555577", size=9), zeroline=False),
        hovermode="x unified",
    )
    return fig


# ═══════════════════════════════════════════════════════════
# WEEKLY TABLE HTML
# ═══════════════════════════════════════════════════════════
def weekly_table_html(data):
    cwi = current_week_idx()

    def th(txt, extra=""):
        return f"<th {extra}>{txt}</th>"

    header = "".join([
        th("Metric"), th(""),
        *[th(w, f'class="{"cur-hd cur-col" if i==cwi else ""}"') for i, w in enumerate(WEEKS)],
        th("QTD", 'class="qtd-col"'),
    ])

    def pace_td(v, plan, cwi_flag):
        cur = "cur-col " if cwi_flag else ""
        if v == 0 and plan == 0:
            return f'<td class="{cur}p-zr">—</td>'
        p = round(v / plan * 100) if plan > 0 else (999 if v > 0 else 0)
        return f'<td class="{cur}{pacing_class(p)}">{f"{p}%" if v > 0 else "—"}</td>'

    rows_html = ""
    for mi, m in enumerate(METRICS):
        d = data[m["key"]]
        if mi > 0:
            rows_html += f'<tr class="tr-gap"><td colspan="{len(WEEKS)+3}"></td></tr>'

        # Actual row
        actual_tds = "".join(
            f'<td class="{"cur-col" if i==cwi else ""}">{v or "—"}</td>'
            for i, v in enumerate(d["actual"])
        )
        rows_html += f"""<tr>
            <td class="metric-label" style="color:{m['color']}">{m['emoji']} {m['short']}</td>
            <td style="font-size:10px;letter-spacing:.5px;color:#555577">ACTUAL</td>
            {actual_tds}
            <td class="qtd-col"><strong>{d['qtdA']}</strong></td>
        </tr>"""

        # Plan row
        plan_tds = "".join(
            f'<td class="{"cur-col" if i==cwi else ""}">{v or "—"}</td>'
            for i, v in enumerate(d["plan"])
        )
        rows_html += f"""<tr class="tr-plan">
            <td></td>
            <td style="font-size:10px;letter-spacing:.5px">PLAN</td>
            {plan_tds}
            <td class="qtd-col">{d['qtdP']}</td>
        </tr>"""

        # Pacing row
        pacing_tds = "".join(
            pace_td(d["actual"][i], d["plan"][i], i == cwi)
            for i in range(len(WEEKS))
        )
        qtd_cls = pacing_class(d["qtdPct"])
        rows_html += f"""<tr>
            <td></td>
            <td style="font-size:10px;letter-spacing:.5px;color:#555577">PACING</td>
            {pacing_tds}
            <td class="qtd-col {qtd_cls}"><strong>{f"{d['qtdPct']}%" if d['qtdPct'] > 0 else "—"}</strong></td>
        </tr>"""

    return f"""
    <table class="week-table">
        <thead><tr>{header}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>"""


# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

# --- Fetch data ---
try:
    data, live = fetch_sheet_data()
    status_color = "#00e676"
    status_dot   = "background:#00e676"
    status_msg   = "<strong>Live data</strong> — synced from Google Sheets"
    banner_bg    = "rgba(0,230,118,.06);border:1px solid rgba(0,230,118,.25)"
except Exception as e:
    data  = FALLBACK
    live  = False
    status_color = "#FF9800"
    status_dot   = "background:#FF9800"
    status_msg   = f"⚠️ Using cached data — make sure the sheet is shared publicly. <em style='color:#555577'>({e})</em>"
    banner_bg    = "rgba(255,152,0,.06);border:1px solid rgba(255,152,0,.25)"

# --- Header ---
col_title, col_cd = st.columns([2, 1])
with col_title:
    st.markdown("""
    <div style="padding-top:6px">
        <div style="font-size:28px;font-weight:900;background:linear-gradient(90deg,#FF3008,#FF9800);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
             letter-spacing:-0.5px">
            🇨🇦 CAN Top Mx Acceleration Contest
        </div>
        <div style="color:#7777aa;font-size:13px;margin-top:4px">SDR Q2 2026 &nbsp;·&nbsp; Mar 30 – Jun 29</div>
    </div>""", unsafe_allow_html=True)

with col_cd:
    st.markdown(countdown_html(), unsafe_allow_html=True)

st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

# --- Status banner ---
st.markdown(f"""
<div class="banner" style="background:{banner_bg}">
    <span class="dot" style="{status_dot}"></span>
    <span>{status_msg}</span>
    <span style="margin-left:auto;color:#444466;font-size:11px">
        Last refresh: {datetime.now().strftime('%b %d, %H:%M')} &nbsp;·&nbsp; auto-refreshes every 5 min
    </span>
</div>""", unsafe_allow_html=True)

# --- Metric Cards ---
cols = st.columns(3)
for i, m in enumerate(METRICS):
    with cols[i]:
        st.markdown(metric_card_html(m, data[m["key"]]), unsafe_allow_html=True)
        st.plotly_chart(
            sparkline_chart(m, data[m["key"]]),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"spark_{m['key']}",
        )

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# --- Weekly Breakdown Table ---
st.markdown('<div style="background:#13132b;border:1px solid #25254a;border-radius:18px;padding:24px">', unsafe_allow_html=True)
st.markdown('<div class="section-header">📅 Weekly Breakdown</div>', unsafe_allow_html=True)
st.markdown(weekly_table_html(data), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown(f"""
<div style="text-align:center;padding:20px 0;font-size:11px;color:#444466">
    <a href="https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit" target="_blank"
       style="color:#FF3008;text-decoration:none">View source sheet →</a>
</div>""", unsafe_allow_html=True)
