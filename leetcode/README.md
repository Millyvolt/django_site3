LeetCode App

This app encapsulates LeetCode-related functionality for the site.

URLs (namespace: leetcode)
- leetcode:home → /leetcode-home/
- leetcode:question_selection → /pick-question/
- leetcode:question_editor → /editor/
- leetcode:daily_question → /daily-question/
- leetcode:compile_code (POST) → /compile/
- leetcode:fetch_cpp_template (POST) → /fetch-cpp-template/

Environment (defaults)
- LEETCODE_GRAPHQL_URL: https://leetcode.com/graphql
- LEETCODE_REFERER: https://leetcode.com
- LEETCODE_TIMEOUT_SECONDS: 15
- LEETCODE_RETRY_COUNT: 2
- LEETCODE_CACHE_TTL_SECONDS: 300
- LEETCODE_ENABLED: true

Development
- Templates: leetcode/templates/leetcode/
- Static: leetcode/static/leetcode/
- Service client: leetcode/services/leetcode_api.py

