
****Virtual environment****

        To create a virtual environment, decide upon a directory where you want to place it, and run the venv module as a script with the directory path:
python -m venv tutorial-env

    То асtivate on Windows, run:
tutorial-env\Scripts\activate

    To deactivate a virtual environment, type in terminal:

deactivate


****Requirements****

    Creating requirements.txt

pip freeze > requirements.txt

    Installing dependensies

pip install -r requirements.txt


***To Do:***
- check reset password via email functionality
- static files attach to amvera data storage
- newer C++ version (check that 17 using)
- Linux


Uvicorn
Option 1: Using the Python script
python run_uvicorn.py
Option 3: Direct Uvicorn command
uvicorn mysite.asgi:application --host 127.0.0.1 --port 8000 --reload

Uvicorn doesnt working with django debug toolbar

admin   1q2w

***Ideas for site:***
- russian version of site
- coworking pages (private or not)
- users making new polls

****LeetCode App Extraction Plan (2025-10-06)****

- **Goal**: Move all LeetCode-related functionality into a dedicated Django app `leetcode`, while keeping global authentication, authorization, and functionality/network tests under the main site.

- **App structure**:
  - `leetcode/apps.py`, `leetcode/urls.py`, `leetcode/views.py`, `leetcode/services/leetcode_api.py`, `leetcode/utils/`.
  - Templates live in: `leetcode/templates/leetcode/` (app-local, namespaced).
  - Static assets in: `leetcode/static/leetcode/`.

- **URLs (namespaced `leetcode:`)**:
  - `home` → `/leetcode-home/`
  - `pick_question` → `/pick-question/`
  - `editor` → `/editor/`
  - `daily_question` → `/daily-question/`
  - POST: `compile` → `/compile/`, `fetch_cpp_template` → `/fetch-cpp-template/`

- **Templates** (extend global `base.html`):
  - `home.html`, `question_selection.html`, `editor.html`, `daily_question.html` in `leetcode/templates/leetcode/`.

- **Services and rules**:
  - Use LeetCode GraphQL API for problem data and question-specific test cases (no hard-coded tests).
  - Add timeouts, retries, caching (short TTL), and basic rate limiting.

- **Ownership**:
  - Global: auth, user profiles, functionality/network tests, base layout, feature flags, monitoring.
  - App: LeetCode views, API integrations, templates, static, optional persistence for submissions/logs.

- **Migration/compatibility**:
  - Update Home button to `url 'leetcode:home'`.
  - Redirect legacy project-level paths to new `leetcode:` routes.

- **Config**:
  - Env vars: `LEETCODE_GRAPHQL_URL`, `LEETCODE_TIMEOUT_SECONDS`, `LEETCODE_RETRY_COUNT`, `LEETCODE_CACHE_TTL_SECONDS`.
  - Ensure `TEMPLATES.OPTIONS.APP_DIRS = True`.

- **Testing**:
  - Unit tests for views/services; integration tests for Home → LeetCode → Pick → Editor → Run.

- **Decision**:
  - Templates location confirmed: `leetcode/templates/leetcode/` (preferred for encapsulation and portability).