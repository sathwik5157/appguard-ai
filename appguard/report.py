"""Self-contained, escaped HTML report. No external scripts or assets."""
from html import escape


def make_report(result, explanation=None):
    esc = lambda value: escape(str(value), quote=True)
    rows = ""
    if explanation:
        rows = "<h2>Local SHAP contributions</h2><p>Units: " + esc(explanation["units"]) + ". Presence and absence can both affect the model.</p><table><tr><th>Permission</th><th>Present</th><th>Contribution</th></tr>"
        for row in explanation["contributions"][:15]:
            rows += f"<tr><td>{esc(row['permission'])}</td><td>{esc(row['present'])}</td><td>{row['contribution']:+.5f}</td></tr>"
        rows += "</table>"
    else:
        rows = "<p>Local explanation unavailable.</p>"
    permissions = "".join(f"<li>{esc(p)}</li>" for p in result["permissions"])
    warnings = "".join(f"<p>{esc(w)}</p>" for w in result["warnings"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AppGuard AI analysis</title>
    <style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:24px;color:#17283e;background:#f5f8fc}}h1{{color:#1759bf}}.card{{background:white;padding:24px;border:1px solid #dce5f1;border-radius:16px}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #dce5f1;overflow-wrap:anywhere}}li{{overflow-wrap:anywhere}}</style></head>
    <body><p>APPGUARD AI / PERMISSION INTELLIGENCE</p><h1>Application analysis</h1><p>{esc(result['timestamp'])}</p>
    <div class="card"><h2>{esc(result['classification'])}</h2><p>Model-estimated malware probability: <strong>{result['probability']:.1%}</strong></p><p>Illustrative risk band: {esc(result['risk_category'])}</p></div>
    <p>Model: {esc(result['model'])} · Version: {esc(result['version'])}</p><p>Classification threshold: 0.5. Risk bands: low &lt;0.3, moderate 0.3–&lt;0.7, high ≥0.7. Bands are illustrative, not validated security thresholds. Scores are uncalibrated model estimates.</p>
    {warnings}<h2>Selected permissions ({len(result['permissions'])})</h2><ul>{permissions}</ul>{rows}<hr><p>{esc(result['disclaimer'])}</p><p>Dataset provenance and redistribution license are unverified. Permission-only analysis does not inspect application code or runtime behavior.</p></body></html>"""
