import pytest
from contextlib import contextmanager

try:
    from pytest_html import extras
except Exception:
    extras = None

@contextmanager
def _noop_context():
    yield

@pytest.fixture
def step(request):
    """Context manager fixture to record named steps for the current test."""
    if not hasattr(request.node, '_steps'):
        request.node._steps = []

    @contextmanager
    def _step(name: str):
        request.node._steps.append({'name': name, 'status': 'RUNNING'})
        try:
            yield
            request.node._steps[-1]['status'] = 'PASSED'
        except Exception:
            request.node._steps[-1]['status'] = 'FAILED'
            raise

    return _step

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # attach recorded steps as HTML to the test report if pytest-html is available
    outcome = yield
    rep = outcome.get_result()
    if rep.when == 'call':
        steps = getattr(item, '_steps', [])
        if steps and extras is not None:
            html_lines = [
                "<div class='steps'>",
                "<style>",
                ".steps{font-family:Helvetica,Arial,sans-serif;margin:6px 0}",
                ".step{padding:6px;margin:4px 0;border-radius:4px;font-size:13px}",
                ".step.passed{background:#e6ffea;color:#006400;border:1px solid #b6f0c8}",
                ".step.failed{background:#ffecec;color:#8b0000;border:1px solid #f2b3b3}",
                ".step.running{background:#f0f0f0;color:#333;border:1px solid #ddd}",
                "</style>",
            ]
            for s in steps:
                status = s.get('status', 'RUNNING').lower()
                name = s.get('name', '')
                html_lines.append(f"<div class='step {status}'><strong>{name}</strong> — {s.get('status')}</div>")
            html_lines.append("</div>")
            extra_html = ''.join(html_lines)
            rep.extra = getattr(rep, 'extra', []) + [extras.html(extra_html)]

# Optional: add environment info to pytest-html report
def pytest_configure(config):
    try:
        from datetime import datetime
        if hasattr(config, '_metadata'):
            config._metadata['Test Run Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config._metadata['Environment'] = 'POS Automation'
    except Exception:
        pass

# Auto-save the shared HTML logger at end of test session
@pytest.fixture(scope="session", autouse=True)
def _save_html_logger():
    yield
    try:
        from Scripts.POS_Workspace.RTLPOSFlow.Component.report import logger as _shared_logger
        _shared_logger.save()
        print(f"Report saved to {_shared_logger.report_path}")
    except Exception as e:
        print(f"Could not save shared logger: {e}")
