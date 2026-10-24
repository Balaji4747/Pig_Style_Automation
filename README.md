# Pig Style Test Automation

Playwright + pytest test automation for the Pig Style Megaways slot (FEG).

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install
cp .env.example .env            # fill in GAME_URL / PLAYER_TOKEN
```

## Running tests
Select environment with `--env` (`qa` default, or `staging`):
```bash
pytest --env qa -m smoke
pytest --env qa -m functional
pytest --env qa tests/math -m math
pytest --env qa -m regression
pytest --env qa -n auto             # parallel (pytest-xdist)
pytest --env qa --reruns 2          # retry flaky tests
pytest --env qa -m smoke --device "iPhone 13"   # mobile/portrait emulation
```

## Viewing reports
- **HTML report:** open `reports/report.html` in a browser.
- **Allure report:** `allure serve reports/allure-results`
- **Screenshots/video/trace (on failure):** `reports/test-results/`.
  View a trace with:
  ```bash
  playwright show-trace reports/test-results/<test-name>/trace.zip
  ```
- **Logs:** `reports/logs/test_run.log`

## Project docs
See [CLAUDE.md](CLAUDE.md) for architecture, conventions, and current open
items. Source documents (game rules, QA test suite workbook, math file) are
in `Docs/` — do not edit, they are the source of truth for test case IDs
and expected values.
