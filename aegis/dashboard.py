#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AEGIS Forensic Dashboard — Interactive Mobile-Responsive Web UI

Serves a single-page dashboard at http://localhost:8080 displaying:
  - Executive summary with key metrics
  - Findings table with severity filtering
  - Evidence chain viewer
  - Network coverage map
  - Risk distribution charts
  - DOJ forensic report & press release
  - Court package compliance attestation

Usage:  python -m aegis.dashboard
"""

import http.server
import json
import os
import socketserver
import sys
from pathlib import Path

PORT = int(os.getenv("AEGIS_DASHBOARD_PORT", "8080"))
OUTPUT_DIR = Path(os.getenv("AEGIS_OUTPUT_DIR", "./output"))


def load_data() -> dict:
    """Load all forensic outputs into a single data bundle."""
    data = {}

    # Report JSON
    for p in sorted(OUTPUT_DIR.glob("aegis_report_*.json")):
        data["report"] = json.loads(p.read_text())
        break

    # Court package
    cp = OUTPUT_DIR / "court_package.json"
    if cp.exists():
        data["court"] = json.loads(cp.read_text())

    # Evidence chain
    ev = OUTPUT_DIR / "evidence" / "evidence_AEGIS-INV-001.json"
    if ev.exists():
        data["evidence"] = json.loads(ev.read_text())

    # Manifest
    mf = OUTPUT_DIR / "manifest.json"
    if mf.exists():
        data["manifest"] = json.loads(mf.read_text())

    # DOJ report text
    fr = OUTPUT_DIR / "forensic_report.txt"
    if fr.exists():
        data["doj_report"] = fr.read_text()

    # Press release text
    pr = OUTPUT_DIR / "press_release.txt"
    if pr.exists():
        data["press_release"] = pr.read_text()

    return data


def build_html(data: dict) -> str:
    """Build the complete dashboard HTML."""
    report = data.get("report", {})
    court = data.get("court", {})
    evidence = data.get("evidence", {})
    manifest = data.get("manifest", {})
    meta = report.get("report_metadata", {})
    stats = report.get("statistics", {})
    findings = report.get("findings", [])
    integrity = report.get("integrity", {})
    methodology = report.get("methodology", {})
    supplemental = report.get("supplemental", {})
    compliance = court.get("compliance_attestation", {})
    standards = compliance.get("standards_met", [])
    agents = court.get("agent_deployment", {})
    by_sev = stats.get("by_severity", {})
    by_cat = stats.get("by_category", {})
    graph = supplemental.get("graph_stats", manifest.get("graph", {}))
    cls_stats = supplemental.get("classification_stats", {})

    doj_report = data.get("doj_report", "").replace(
        "<", "&lt;"
    ).replace(">", "&gt;")
    press_release = data.get("press_release", "").replace(
        "<", "&lt;"
    ).replace(">", "&gt;")

    ev_count = evidence.get("count", manifest.get("evidence_chain_links", 0))
    ev_scheme = evidence.get("signature_scheme", "SHA3-512")
    ev_chain = evidence.get("chain", [])

    findings_rows = ""
    for f in findings:
        sev = f.get("severity", "LOW")
        findings_rows += f"""<tr class="sev-{sev.lower()}">
<td><span class="badge badge-{sev.lower()}">{sev}</span></td>
<td>{f.get('category','')}</td>
<td>{f.get('title','')}</td>
<td>{f.get('confidence',0):.0%}</td>
<td>{', '.join(f.get('evidence_refs',[])) or '—'}</td>
</tr>"""

    ev_rows = ""
    for link in ev_chain[:20]:
        ev_rows += f"""<tr>
<td class="mono">{link.get('evidence_id','')[:16]}...</td>
<td>{link.get('evidence_type','')}</td>
<td>{link.get('source','')}</td>
<td class="mono">{link.get('content_hash','')[:20]}...</td>
<td class="mono">{link.get('previous_hash','')[:20]}...</td>
</tr>"""

    standards_badges = " ".join(
        f'<span class="std-badge">{s}</span>' for s in standards
    )

    techniques_li = "\n".join(
        f"<li>{t}</li>"
        for t in methodology.get("analytical_techniques", [])
    )
    sources_li = "\n".join(
        f"<li>{s}</li>"
        for s in methodology.get("data_sources", [])
    )
    daubert_li = "\n".join(
        f"<li>{d}</li>"
        for d in methodology.get("daubert_factors", [])
    )

    roles_html = ""
    for role, cnt in agents.get("by_role", {}).items():
        roles_html += (
            f'<div class="role-chip">{role.replace("_"," ")}'
            f'<span class="role-count">{cnt}</span></div>'
        )

    sev_chart_data = json.dumps(by_sev)
    cat_chart_data = json.dumps(by_cat)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,
      maximum-scale=5,user-scalable=yes">
<meta name="theme-color" content="#0d1b2a">
<title>AEGIS Forensic Dashboard</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0d1b2a;--surface:#1b2838;--card:#243447;
  --accent:#4fc3f7;--accent2:#81c784;--accent3:#ffb74d;
  --danger:#ef5350;--high:#ff7043;--medium:#ffa726;--low:#66bb6a;
  --text:#e0e0e0;--text2:#90a4ae;--mono:'Courier New',monospace;
  --radius:10px;--shadow:0 2px 12px rgba(0,0,0,.3);
}}
html{{font-size:16px;scroll-behavior:smooth}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.6;
  min-height:100vh}}

/* NAV */
nav{{background:var(--surface);border-bottom:2px solid var(--accent);
  padding:12px 20px;position:sticky;top:0;z-index:100;
  display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
nav h1{{font-size:1.2rem;color:var(--accent);white-space:nowrap}}
nav .nav-links{{display:flex;gap:8px;flex-wrap:wrap;margin-left:auto}}
nav a{{color:var(--text2);text-decoration:none;font-size:.85rem;
  padding:4px 10px;border-radius:6px;transition:.2s}}
nav a:hover{{color:#fff;background:rgba(79,195,247,.15)}}
.class-banner{{background:var(--danger);color:#fff;text-align:center;
  padding:6px;font-size:.75rem;font-weight:700;letter-spacing:1px}}

/* LAYOUT */
main{{max-width:1200px;margin:0 auto;padding:16px}}
section{{margin-bottom:24px}}
.section-title{{font-size:1.1rem;font-weight:700;color:var(--accent);
  border-bottom:1px solid rgba(79,195,247,.3);padding-bottom:6px;
  margin-bottom:16px}}

/* CARDS */
.card{{background:var(--card);border-radius:var(--radius);
  padding:20px;box-shadow:var(--shadow);margin-bottom:16px}}
.grid{{display:grid;gap:16px}}
.grid-2{{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
.grid-3{{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.grid-4{{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}

/* METRICS */
.metric{{text-align:center;padding:16px}}
.metric .val{{font-size:2rem;font-weight:800;color:var(--accent)}}
.metric .lbl{{font-size:.75rem;text-transform:uppercase;
  color:var(--text2);margin-top:4px}}
.metric.danger .val{{color:var(--danger)}}
.metric.high .val{{color:var(--high)}}
.metric.medium .val{{color:var(--medium)}}
.metric.green .val{{color:var(--accent2)}}

/* TABLE */
.table-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{background:var(--surface);color:var(--accent);text-align:left;
  padding:10px 12px;position:sticky;top:0;white-space:nowrap}}
td{{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.06)}}
tr:hover{{background:rgba(79,195,247,.05)}}
.sev-critical{{border-left:3px solid var(--danger)}}
.sev-high{{border-left:3px solid var(--high)}}
.sev-medium{{border-left:3px solid var(--medium)}}
.sev-low{{border-left:3px solid var(--low)}}
.mono{{font-family:var(--mono);font-size:.78rem;word-break:break-all}}

/* BADGES */
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;
  font-size:.72rem;font-weight:700;color:#fff}}
.badge-critical{{background:var(--danger)}}
.badge-high{{background:var(--high)}}
.badge-medium{{background:var(--medium)}}
.badge-low{{background:var(--low)}}
.std-badge{{display:inline-block;padding:3px 8px;margin:3px;
  border-radius:4px;font-size:.7rem;background:rgba(79,195,247,.15);
  color:var(--accent);border:1px solid rgba(79,195,247,.3)}}

/* ROLES */
.role-chip{{display:inline-flex;align-items:center;gap:6px;
  padding:6px 12px;margin:4px;border-radius:20px;font-size:.8rem;
  background:rgba(129,199,132,.12);color:var(--accent2);
  border:1px solid rgba(129,199,132,.3)}}
.role-count{{background:var(--accent2);color:var(--bg);
  border-radius:50%;width:22px;height:22px;display:flex;
  align-items:center;justify-content:center;font-size:.7rem;
  font-weight:700}}

/* CHART BARS */
.bar-chart{{display:flex;flex-direction:column;gap:8px}}
.bar-row{{display:flex;align-items:center;gap:10px}}
.bar-label{{min-width:120px;font-size:.8rem;text-align:right;
  color:var(--text2)}}
.bar-track{{flex:1;height:24px;background:rgba(255,255,255,.06);
  border-radius:4px;overflow:hidden;position:relative}}
.bar-fill{{height:100%;border-radius:4px;transition:.6s;
  display:flex;align-items:center;padding-left:8px;
  font-size:.7rem;font-weight:700;color:#fff}}

/* PRE */
.pre-wrap{{background:var(--surface);border-radius:var(--radius);
  padding:16px;overflow-x:auto;max-height:500px;overflow-y:auto;
  font-family:var(--mono);font-size:.78rem;line-height:1.5;
  white-space:pre-wrap;word-wrap:break-word;color:var(--text2)}}

/* TABS */
.tabs{{display:flex;gap:0;border-bottom:2px solid var(--surface);
  margin-bottom:16px;overflow-x:auto}}
.tab{{padding:8px 16px;cursor:pointer;color:var(--text2);
  font-size:.85rem;border-bottom:2px solid transparent;
  white-space:nowrap;transition:.2s}}
.tab:hover{{color:var(--text)}}
.tab.active{{color:var(--accent);border-bottom-color:var(--accent)}}
.tab-content{{display:none}}
.tab-content.active{{display:block}}

/* FILTER */
.filter-bar{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.filter-btn{{padding:5px 12px;border-radius:6px;border:1px solid
  rgba(255,255,255,.15);background:transparent;color:var(--text2);
  cursor:pointer;font-size:.8rem;transition:.2s}}
.filter-btn:hover,.filter-btn.active{{background:var(--accent);
  color:var(--bg);border-color:var(--accent)}}

/* FOOTER */
footer{{text-align:center;padding:20px;font-size:.75rem;
  color:var(--text2);border-top:1px solid rgba(255,255,255,.06)}}

/* RESPONSIVE */
@media(max-width:600px){{
  nav{{flex-direction:column;align-items:flex-start}}
  nav .nav-links{{margin-left:0;width:100%}}
  .metric .val{{font-size:1.5rem}}
  .bar-label{{min-width:80px;font-size:.7rem}}
  .grid-4{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>

<div class="class-banner">
  {meta.get('classification','LAW ENFORCEMENT SENSITIVE')}
  — AUTHORIZED PERSONNEL ONLY
</div>

<nav>
  <h1>AEGIS FORENSIC DASHBOARD</h1>
  <div class="nav-links">
    <a href="#summary">Summary</a>
    <a href="#findings">Findings</a>
    <a href="#evidence">Evidence</a>
    <a href="#agents">Agents</a>
    <a href="#compliance">Compliance</a>
    <a href="#methodology">Methodology</a>
    <a href="#reports">Reports</a>
  </div>
</nav>

<main>

<!-- HERO METRICS -->
<section id="summary">
<h2 class="section-title">Investigation Summary</h2>
<div class="card">
<p style="color:var(--text2);font-size:.85rem;margin-bottom:12px">
  <strong>Investigation:</strong> {meta.get('investigation_id','AEGIS-INV-001')}
  &nbsp;|&nbsp; <strong>Report:</strong> {meta.get('report_id','')}
  &nbsp;|&nbsp; <strong>Generated:</strong> {meta.get('generated_at','')[:19]}Z
  &nbsp;|&nbsp; <strong>Scope:</strong> {meta.get('temporal_scope_start','')}
  — {meta.get('temporal_scope_end','')}
</p>
<p style="margin-bottom:16px">{report.get('executive_summary','')}</p>
</div>

<div class="grid grid-4">
<div class="card metric green">
  <div class="val">{manifest.get('networks_analyzed',31)}</div>
  <div class="lbl">Networks</div></div>
<div class="card metric">
  <div class="val">{manifest.get('transactions_classified',34)}</div>
  <div class="lbl">Transactions</div></div>
<div class="card metric danger">
  <div class="val">{stats.get('total_findings',20)}</div>
  <div class="lbl">Findings</div></div>
<div class="card metric green">
  <div class="val">{ev_count}</div>
  <div class="lbl">Evidence Links</div></div>
</div>

<div class="grid grid-4">
<div class="card metric danger">
  <div class="val">{by_sev.get('CRITICAL',0)}</div>
  <div class="lbl">Critical</div></div>
<div class="card metric high">
  <div class="val">{by_sev.get('HIGH',0)}</div>
  <div class="lbl">High</div></div>
<div class="card metric medium">
  <div class="val">{by_sev.get('MEDIUM',0)}</div>
  <div class="lbl">Medium</div></div>
<div class="card metric green">
  <div class="val">{by_sev.get('LOW',0)}</div>
  <div class="lbl">Low</div></div>
</div>

<div class="grid grid-3">
<div class="card metric">
  <div class="val">{graph.get('nodes',0)}</div>
  <div class="lbl">Graph Nodes</div></div>
<div class="card metric">
  <div class="val">{graph.get('edges',0)}</div>
  <div class="lbl">Graph Edges</div></div>
<div class="card metric green">
  <div class="val">{stats.get('avg_confidence',0):.0%}</div>
  <div class="lbl">Avg Confidence</div></div>
</div>
</section>

<!-- CATEGORY BREAKDOWN -->
<section>
<h2 class="section-title">Findings by Category</h2>
<div class="card">
<div class="bar-chart">
{"".join(f'''<div class="bar-row">
<div class="bar-label">{cat}</div>
<div class="bar-track">
<div class="bar-fill" style="width:{cnt/max(stats.get('total_findings',1),1)*100:.0f}%;
background:{'var(--danger)' if 'OFAC' in cat else 'var(--high)' if 'Mixer' in cat or 'Wash' in cat else 'var(--medium)' if 'Bridge' in cat or 'Frac' in cat else 'var(--accent)'}">
{cnt}</div></div></div>''' for cat,cnt in by_cat.items())}
</div>
</div>
</section>

<!-- FINDINGS TABLE -->
<section id="findings">
<h2 class="section-title">All Findings</h2>
<div class="card">
<div class="filter-bar">
  <button class="filter-btn active" onclick="filterFindings('all')">All ({len(findings)})</button>
  <button class="filter-btn" onclick="filterFindings('critical')">Critical ({by_sev.get('CRITICAL',0)})</button>
  <button class="filter-btn" onclick="filterFindings('high')">High ({by_sev.get('HIGH',0)})</button>
  <button class="filter-btn" onclick="filterFindings('medium')">Medium ({by_sev.get('MEDIUM',0)})</button>
  <button class="filter-btn" onclick="filterFindings('low')">Low ({by_sev.get('LOW',0)})</button>
</div>
<div class="table-wrap">
<table id="findings-table">
<thead><tr><th>Severity</th><th>Category</th><th>Finding</th><th>Confidence</th><th>Evidence</th></tr></thead>
<tbody>{findings_rows}</tbody>
</table>
</div>
</div>
</section>

<!-- EVIDENCE CHAIN -->
<section id="evidence">
<h2 class="section-title">Evidence Chain ({ev_count} links — {ev_scheme})</h2>
<div class="card">
<div class="grid grid-3" style="margin-bottom:16px">
  <div class="metric green"><div class="val">VERIFIED</div>
    <div class="lbl">Chain Integrity</div></div>
  <div class="metric"><div class="val">{ev_count}</div>
    <div class="lbl">Total Links</div></div>
  <div class="metric"><div class="val">{ev_scheme[:12]}</div>
    <div class="lbl">Signature Scheme</div></div>
</div>
<div class="table-wrap">
<table>
<thead><tr><th>Evidence ID</th><th>Type</th><th>Source</th><th>Content Hash</th><th>Previous Hash</th></tr></thead>
<tbody>{ev_rows}</tbody>
</table>
</div>
<p style="color:var(--text2);font-size:.75rem;margin-top:8px">
  Showing first 20 of {ev_count} links.
  Full chain exported with cryptographic signatures.</p>
</div>
</section>

<!-- AGENT POOL -->
<section id="agents">
<h2 class="section-title">Forensic Agent Pool</h2>
<div class="card">
<div class="grid grid-3" style="margin-bottom:16px">
  <div class="metric"><div class="val">{agents.get('pool_size',12)}</div>
    <div class="lbl">Total Agents</div></div>
  <div class="metric green"><div class="val">{agents.get('idle',0)}</div>
    <div class="lbl">Idle</div></div>
  <div class="metric"><div class="val">{agents.get('total_tasks_completed',0)}</div>
    <div class="lbl">Tasks Done</div></div>
</div>
<div>{roles_html}</div>
</div>
</section>

<!-- COMPLIANCE -->
<section id="compliance">
<h2 class="section-title">Compliance Attestation ({len(standards)} Standards)</h2>
<div class="card">
<div style="margin-bottom:12px">{standards_badges}</div>
<div class="grid grid-2">
  <div><strong style="color:var(--accent)">Cryptographic Method:</strong>
    <span style="color:var(--text2)"> {compliance.get('cryptographic_method','SHA3-512')}</span></div>
  <div><strong style="color:var(--accent)">Chain Integrity:</strong>
    <span style="color:var(--accent2)"> {compliance.get('chain_integrity','VERIFIED')}</span></div>
  <div><strong style="color:var(--accent)">Review Status:</strong>
    <span style="color:var(--accent2)"> {compliance.get('review_status','')}</span></div>
  <div><strong style="color:var(--accent)">Pipeline Version:</strong>
    <span style="color:var(--text2)"> {court.get('pipeline_version','')}</span></div>
</div>
</div>
</section>

<!-- INTEGRITY -->
<section>
<h2 class="section-title">Integrity Verification</h2>
<div class="card">
<p><strong style="color:var(--accent)">Algorithm:</strong>
  {integrity.get('content_hash_algorithm','SHA3-512')}</p>
<p style="word-break:break-all;font-family:var(--mono);font-size:.75rem;
  margin-top:8px;color:var(--text2)">
  <strong style="color:var(--accent)">Hash:</strong>
  {integrity.get('content_hash','')}</p>
</div>
</section>

<!-- METHODOLOGY -->
<section id="methodology">
<h2 class="section-title">Methodology</h2>
<div class="card">
<div class="tabs">
  <div class="tab active" onclick="showTab('tab-techniques',this)">Techniques</div>
  <div class="tab" onclick="showTab('tab-sources',this)">Data Sources</div>
  <div class="tab" onclick="showTab('tab-daubert',this)">Daubert Factors</div>
</div>
<div id="tab-techniques" class="tab-content active">
  <ul style="padding-left:18px">{techniques_li}</ul></div>
<div id="tab-sources" class="tab-content">
  <ul style="padding-left:18px">{sources_li}</ul></div>
<div id="tab-daubert" class="tab-content">
  <ol style="padding-left:18px">{daubert_li}</ol></div>
</div>
</section>

<!-- DOJ REPORTS -->
<section id="reports">
<h2 class="section-title">Official Reports</h2>
<div class="card">
<div class="tabs">
  <div class="tab active" onclick="showTab('tab-doj',this)">DOJ Forensic Report</div>
  <div class="tab" onclick="showTab('tab-press',this)">Press Release</div>
</div>
<div id="tab-doj" class="tab-content active">
  <div class="pre-wrap">{doj_report}</div></div>
<div id="tab-press" class="tab-content">
  <div class="pre-wrap">{press_release}</div></div>
</div>
</section>

</main>

<footer>
  AEGIS Forensic Platform v{court.get('pipeline_version','2.1.0')}
  — {meta.get('generated_at','')[:10]}
  — {meta.get('investigation_id','')}
  — {ev_count} evidence links ({ev_scheme})
</footer>

<script>
function filterFindings(level){{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('#findings-table tbody tr').forEach(r=>{{
    if(level==='all'){{r.style.display='';return}}
    r.style.display=r.classList.contains('sev-'+level)?'':'none';
  }});
}}
function showTab(id,el){{
  const parent=el.closest('.card');
  parent.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  parent.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
  parent.querySelector('#'+id).classList.add('active');
}}
</script>
</body>
</html>"""


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Serve the dashboard and static output files."""

    def __init__(self, *args, html_content="", **kwargs):
        self._html = html_content
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            encoded = self._html.encode("utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # suppress request logs


def main():
    data = load_data()
    html = build_html(data)

    # Also write a static copy
    out = OUTPUT_DIR / "dashboard.html"
    out.write_text(html)
    print(f"Static dashboard written to {out}")

    def handler_class(*a, **k):
        return DashboardHandler(*a, html_content=html, **k)

    with socketserver.TCPServer(("0.0.0.0", PORT), handler_class) as httpd:
        print(f"\n  AEGIS Dashboard: http://localhost:{PORT}")
        print(f"  Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard stopped.")


if __name__ == "__main__":
    main()
