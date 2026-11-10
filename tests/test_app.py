from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / "models/model.joblib").exists(), reason="Local trained artifacts required")


@pytest.mark.parametrize("page", ["Overview", "Analyze", "Model evidence", "Project notes"])
def test_pages(page):
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception


def test_analysis_journey():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("Analyze").run()
    next(b for b in app.button if b.label == "Run analysis").click().run()
    assert "Select at least" in app.error[0].value
    app.multiselect[0].set_value(["INTERNET", "READ_SMS", "SEND_SMS"]).run()
    next(b for b in app.button if b.label == "Run analysis").click().run()
    assert not app.exception
    assert "analysis" in app.session_state
    assert app.session_state.analysis[1] is not None
    app.multiselect[0].set_value(["INTERNET"]).run()
    assert any("Permissions changed" in msg.value for msg in app.info)
    next(b for b in app.button if b.label == "Compare with analyzed pattern").click().run()
    assert not app.exception
