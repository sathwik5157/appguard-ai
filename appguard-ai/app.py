"""AppGuard AI interactive portfolio application."""
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from appguard.inference import load_artifacts, predict, explain, parse_permissions, DISCLAIMER
from appguard.report import make_report

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="AppGuard AI · Permission intelligence", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp {background:radial-gradient(ellipse at 85% 0%,#123047 0%,#0b1220 48%);}
[data-testid="stSidebar"] {background:#0d1728;border-right:1px solid #203149;}
.block-container {max-width:1280px;padding-top:2.5rem;padding-bottom:3rem;}
h1 {font-weight:750!important;letter-spacing:-.045em!important;}
h2,h3 {letter-spacing:-.025em!important;}
[data-testid="stMetric"] {background:#111f32;border:1px solid #253951;border-radius:14px;padding:18px;}
[data-testid="stMetricLabel"] p {white-space:normal!important;overflow:visible!important;}
[data-testid="stMetricValue"] {white-space:normal!important;overflow-wrap:anywhere;}
@media(max-width:900px) {
  [data-testid="stHorizontalBlock"] {flex-wrap:wrap!important;}
  [data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important;min-width:0!important;}
}
.eyebrow {color:#4dd9d0;font-size:12px;letter-spacing:.18em;font-weight:700;margin-bottom:18px;}
.hero {padding:28px 0 32px;max-width:800px;}
.hero h1 {font-size:clamp(2.5rem,5vw,4.5rem);line-height:1.05;margin:0 0 20px;}
.hero p {color:#b3c4da;font-size:18px;line-height:1.7;}
.step {background:#111e30;border:1px solid #253951;padding:24px;border-radius:14px;min-height:160px;}
.step small {color:#4dd9d0;font-weight:700;letter-spacing:.1em;}
.step p {color:#aabbd1;line-height:1.6;}
.footnote {color:#8da1bb;font-size:12px;margin-top:36px;}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def artifacts():
    return load_artifacts()


@st.cache_data(show_spinner=False)
def local_explanation(permissions, version):
    bundle, _ = artifacts()
    return explain(list(permissions), bundle)


try:
    bundle, evidence = artifacts()
except (FileNotFoundError, ValueError) as error:
    st.title("AppGuard AI")
    st.error(f"Model artifacts unavailable: {error}")
    st.code("python train_model.py --data Combined.xlsx")
    st.stop()

with st.sidebar:
    st.markdown("## ◈ AppGuard AI")
    st.caption("PERMISSION INTELLIGENCE")
    page = st.radio("Workspace", ["Overview", "Analyze", "Model evidence", "Project notes"], key="page")
    st.divider()
    st.caption("ACTIVE MODEL")
    st.write(evidence["selected_model"])
    st.caption(bundle["version"])
    st.caption("Local inference · No API keys")
    st.info("Research prototype. Permission patterns are signals, not proof of malware.")


def chart(fig, height=340):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial", color="#c9d8eb"), height=height, margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig, width="stretch")


def go_analyze():
    st.session_state.page = "Analyze"


def attribution_plot(explanation):
    table = pd.DataFrame(explanation["contributions"][:12]).iloc[::-1]
    table["feature"] = table.permission.map(lambda name: name.rsplit(".", 1)[-1]) + table.present.map({True: " · present", False: " · absent"})
    fig = go.Figure(go.Bar(x=table.contribution, y=table.feature, orientation="h",
                          marker_color=["#ff857f" if v > 0 else "#47d7cb" for v in table.contribution]))
    fig.update_layout(xaxis_title=f"Contribution to malware score ({explanation['units']})")
    chart(fig, 460)
    with st.expander("Full contribution table"):
        st.dataframe(pd.DataFrame(explanation["contributions"]), width="stretch", hide_index=True)
    st.caption(f"Baseline: {explanation['base_value']:.4f} → explained output: {explanation['output_value']:.4f} {explanation['units']}. All feature contributions, including those not shown, sum to the difference.")


if page == "Overview":
    st.markdown('<div class="eyebrow">EXPLAINABLE MACHINE LEARNING / ANDROID</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero"><h1>Understand the risk<br>behind the permissions.</h1><p>Explore how an Android app’s permission pattern influences a machine-learning model. Inspect the prediction, challenge it with a what-if scenario, and examine the evidence behind it.</p></div>', unsafe_allow_html=True)
    st.button("Analyze a permission pattern →", type="primary", on_click=go_analyze)
    st.write("")
    cols = st.columns(4)
    for col, label, value in zip(cols, ["Apps in supplied dataset", "Permission features", "Held-out test F1", "Pattern overlap across splits"],
                                  [f"{evidence['dataset']['rows']:,}", str(len(bundle["features"])), f"{evidence['test']['f1']:.1%}", "0"]):
        col.metric(label, value)
    st.write("")
    for col, number, title, body in zip(st.columns(3), ["01 / INPUT", "02 / INFERENCE", "03 / EVIDENCE"],
        ["Describe the app", "Inspect its signals", "Question the result"],
        ["Select permissions or paste a permission list. Every input maps to the model’s actual feature schema.",
         "Run the trained classifier and see which present or absent permissions move its score.",
         "Compare a modified permission set and review held-out metrics, data quality, and limitations."]):
        col.markdown(f'<div class="step"><small>{number}</small><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
    st.markdown("### Built to be inspected")
    st.write("Four baselines and candidate models. Separate training, validation and test sets. Matching permission patterns stay in one split, even when their labels disagree. The selected model is refitted on training and validation data before final testing.")
    st.caption(DISCLAIMER)

elif page == "Analyze":
    st.markdown('<div class="eyebrow">ANALYSIS WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Inspect a permission pattern")
    st.write("Only select permissions actually requested by the app. Unselected permissions are encoded as absent.")
    with st.expander("Paste a permission list"):
        text = st.text_area("One permission per line, or separated by commas", placeholder="android.permission.INTERNET\nandroid.permission.ACCESS_NETWORK_STATE")
        if st.button("Import permissions"):
            known, unknown = parse_permissions(text, bundle["features"])
            st.session_state.permissions = known
            st.session_state.import_unknown = unknown
        if st.session_state.get("import_unknown"):
            st.warning("Not in this model’s schema; excluded: " + ", ".join(st.session_state.import_unknown))
    selected = st.multiselect("Requested permissions", bundle["features"], key="permissions", placeholder="Search permissions…")
    st.caption(f"{len(selected)} selected · {len(bundle['features'])} available · This tool does not extract or scan APK files.")
    if st.button("Run analysis", type="primary"):
        try:
            result = predict(selected, bundle)
            with st.spinner("Calculating feature contributions…"):
                try:
                    explanation = local_explanation(tuple(sorted(selected)), bundle["version"])
                    error = None
                except Exception as exc:
                    explanation, error = None, f"Local explanation unavailable: {type(exc).__name__}. Prediction remains available."
            st.session_state.analysis = (result, explanation, error)
        except ValueError as exc:
            st.error(str(exc))
    if "analysis" in st.session_state:
        result, explanation, explanation_error = st.session_state.analysis
        if set(selected) != set(result["permissions"]):
            st.info("Permissions changed. Run analysis again to update the result below.")
        st.divider()
        st.subheader("Application assessment")
        a, b, c = st.columns(3)
        a.metric("Model-estimated malware probability", f"{result['probability']:.1%}")
        b.metric("Pattern classification", result["classification"])
        c.metric("Illustrative risk band", result["risk_category"])
        left, right = st.columns([1, 1.4])
        with left:
            chart(go.Figure(go.Indicator(mode="gauge+number", value=result["probability"] * 100,
                number={"suffix": "%"}, gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#5cbcff"},
                "steps": [{"range": [0, 30], "color": "#163e40"}, {"range": [30, 70], "color": "#594b2b"}, {"range": [70, 100], "color": "#582e3b"}]})), 280)
            st.caption("Classification uses a 50% threshold. Risk bands use 30% and 70% and are illustrative. Probability estimates are not post-hoc calibrated.")
            for warning in result["warnings"]:
                st.warning(warning)
        with right:
            st.markdown("#### What influenced this result?")
            if explanation:
                attribution_plot(explanation)
                st.caption("Coral increases the malware score; teal decreases it. SHAP describes this model’s associations, not causation or security advice.")
            else:
                st.warning(explanation_error)
        st.info(DISCLAIMER)
        html = make_report(result, explanation)
        one, two = st.columns(2)
        one.download_button("Download analysis report", html, "appguard-analysis.html", "text/html")
        two.download_button("Download analysis JSON", json.dumps({"result": result, "explanation": explanation}, indent=2), "appguard-analysis.json", "application/json")
        with st.expander("What-if comparison · change the permission set"):
            st.write("Explore model sensitivity. A lower score does not establish that an app became safer.")
            variant = st.multiselect("Alternative permissions", bundle["features"], default=result["permissions"], key="variant_" + "_".join(result["permissions"]))
            if st.button("Compare with analyzed pattern"):
                try:
                    other = predict(variant, bundle)
                    st.metric("Alternative model score", f"{other['probability']:.1%}", f"{(other['probability'] - result['probability']) * 100:+.1f} percentage points", delta_color="off")
                    for warning in other["warnings"]:
                        st.warning(warning)
                    st.write("Added:", ", ".join(sorted(set(variant) - set(result["permissions"]))) or "None")
                    st.write("Removed:", ", ".join(sorted(set(result["permissions"]) - set(variant))) or "None")
                except ValueError as exc:
                    st.error(str(exc))

elif page == "Model evidence":
    st.markdown('<div class="eyebrow">EVALUATION / FIXED SEED 42</div>', unsafe_allow_html=True)
    st.title("Evidence behind the model")
    st.write(f"Selected model: **{evidence['selected_model']}**. {evidence['selection_rule']}")
    for col, key in zip(st.columns(4), ["accuracy", "precision", "recall", "f1"]):
        col.metric("Test " + key.title(), f"{evidence['test'][key]:.2%}")
    ci = evidence["test_group_bootstrap_95_ci"]
    st.caption(f"Test F1 95% group-bootstrap interval: {ci['f1'][0]:.1%}–{ci['f1'][1]:.1%}. 500 resamples of test permission-pattern groups. This captures test-sample variability, not all sources of uncertainty.")
    tabs = st.tabs(["Performance", "Data audit", "Global signals"])
    with tabs[0]:
        st.subheader("Validation comparison")
        comparison = pd.DataFrame(evidence["validation_comparison"]).T.drop(columns="confusion_matrix").astype(float)
        st.dataframe(comparison.style.format("{:.3f}"), width="stretch")
        st.caption("Candidate selection uses validation F1 only. The final test results above are for the selected model refitted on train + validation.")
        left, right = st.columns(2)
        with left:
            st.markdown("#### Held-out confusion matrix")
            fig = px.imshow(evidence["test"]["confusion_matrix"], x=["Benign", "Malware"], y=["Benign", "Malware"], text_auto=True, color_continuous_scale="Teal", labels={"x": "Predicted", "y": "Actual", "color": "Apps"})
            chart(fig)
        with right:
            st.markdown("#### ROC curve")
            fig = go.Figure(go.Scatter(x=evidence["roc"]["fpr"], y=evidence["roc"]["tpr"], name="Selected model", line_color="#4dd9d0"))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line_dash="dash", name="Chance"))
            fig.update_layout(xaxis_title="False positive rate", yaxis_title="True positive rate")
            chart(fig)
        a, b, c = st.columns(3)
        a.metric("Test ROC-AUC", f"{evidence['test']['roc_auc']:.3f}")
        b.metric("Test average precision", f"{evidence['test']['average_precision']:.3f}")
        c.metric("Test Brier score · lower is better", f"{evidence['test']['brier_score']:.3f}")
        st.markdown("#### Probability reliability")
        fig = go.Figure(go.Scatter(x=evidence["calibration"]["predicted"], y=evidence["calibration"]["observed"], mode="lines+markers", name="Test bins", line_color="#4dd9d0"))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Ideal", mode="lines", line_dash="dash"))
        fig.update_layout(xaxis_title="Mean predicted probability", yaxis_title="Observed malware fraction", xaxis_range=[0, 1], yaxis_range=[0, 1])
        chart(fig)
        st.caption("Ten equal-width bins; empty bins omitted. This is a reliability diagnostic, not a calibration step.")
        with st.expander("Test baseline and precision–recall curve"):
            st.json(evidence["test_baseline"])
            fig = px.line(x=evidence["pr"]["recall"], y=evidence["pr"]["precision"], labels={"x": "Recall", "y": "Precision"})
            chart(fig)
    with tabs[1]:
        audit = evidence["dataset"]
        st.write("Source: **Instructor-created Combined.xlsx**, supplied by the project owner. Original collection method, dates, label verification, and redistribution permission have not been established.")
        st.dataframe(pd.DataFrame(evidence["split"]).T, width="stretch")
        a, b, c = st.columns(3)
        a.metric("Distinct permission patterns", f"{audit['unique_patterns']:,}")
        b.metric("Patterns with conflicting labels", str(audit["conflicting_patterns"]))
        c.metric("Constant columns in full dataset", str(len(audit["constant_features"])))
        st.write("Identical permission patterns stay in the same split. Conflicting labels are retained, since permissions alone cannot resolve them. App identifiers and labels never enter the feature matrix. All 195 permission columns remain in the schema; constant columns provide no learned discrimination.")
        chart(px.bar(x=list(audit["class_counts"]), y=list(audit["class_counts"].values()), labels={"x": "Dataset label", "y": "Apps"}, color_discrete_sequence=["#4dd9d0"]))
        st.caption("Dataset SHA-256: " + audit["sha256"])
        st.download_button("Download evaluation evidence", json.dumps(evidence, indent=2), "metrics.json", "application/json")
    with tabs[2]:
        top = pd.Series(evidence["global_importance"]).head(20).iloc[::-1]
        chart(px.bar(x=top.values, y=top.index, orientation="h", labels={"x": evidence["global_importance_method"], "y": ""}, color_discrete_sequence=["#4dd9d0"]), 600)
        st.caption("Global model importance is not an explanation of an individual prediction. Correlated features can share or distort importance. Use the Analyze workspace for local SHAP contributions.")

else:
    st.markdown('<div class="eyebrow">MODEL CARD / PROJECT NOTES</div>', unsafe_allow_html=True)
    st.title("A transparent research prototype")
    st.markdown("""### What this project demonstrates
An end-to-end ML workflow: data validation, leakage-aware splitting, baseline comparison, model selection, held-out evaluation, explainable inference, interactive analysis, and downloadable reports.

### How a prediction works
Every known permission becomes a binary feature in a fixed order. The trained classifier maps that vector to a malware-class probability. A threshold of 0.5 determines the pattern classification. SHAP compares the model output with a background sample of development data and allocates the difference across features. Both present and absent permissions can contribute.

### What the model cannot establish
- It does not inspect code, network behavior, APK signatures, or runtime activity.
- A benign app can request sensitive permissions; malware can request very few.
- Matching permission patterns sometimes have opposite labels in this dataset.
- Random group splitting does not test future malware families or unseen collection sources.
- Model scores are uncalibrated estimates and depend on the dataset’s class balance.
- The original data collection, labeling procedure, dates, and sharing rights remain unverified.

### Reproduce and review
Run `python train_model.py --data Combined.xlsx`, then `python -m pytest`.
The saved split manifest and test predictions support independent auditing. No previous research accuracy is presented as a reproduced result.

### Technology
Python · pandas · scikit-learn · SHAP · Streamlit · Plotly · pytest
""")
    st.code("python -m streamlit run app.py", language="bash")
    st.caption("Instructor-created dataset, as reported by the project owner. Obtain permission before redistributing the workbook or trained artifacts.")

st.markdown('<div class="footnote">APPGUARD AI · Research prototype · Permission patterns, explained.</div>', unsafe_allow_html=True)
