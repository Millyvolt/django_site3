from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from django.conf import settings


@dataclass
class LeetCodeResponse:
    ok: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LeetCodeAPI:
    def __init__(self) -> None:
        self.base_url = settings.LEETCODE_GRAPHQL_URL
        self.timeout = settings.LEETCODE_TIMEOUT_SECONDS
        self.retries = settings.LEETCODE_RETRY_COUNT
        self.headers = {
            "Content-Type": "application/json",
            "Referer": settings.LEETCODE_REFERER,
        }

    def _post(self, payload: Dict[str, Any]) -> LeetCodeResponse:
        last_error: Optional[str] = None
        for _ in range(max(1, self.retries + 1)):
            try:
                response = requests.post(self.base_url, data=json.dumps(payload), headers=self.headers, timeout=self.timeout)
                if 200 <= response.status_code < 300:
                    return LeetCodeResponse(ok=True, status_code=response.status_code, data=response.json())
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            except Exception as exc:  # requests exceptions
                last_error = str(exc)
        return LeetCodeResponse(ok=False, status_code=500, error=last_error or "Unknown error")

    def fetch_daily_question(self) -> LeetCodeResponse:
        query = """
        query questionOfToday { activeDailyCodingChallengeQuestion { date link question { frontendQuestionId: questionFrontendId title titleSlug difficulty acRate } } }
        """
        return self._post({"query": query, "variables": {}})

    def fetch_problem_details(self, title_slug: str) -> LeetCodeResponse:
        query = """
        query questionData($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            content
            difficulty
            sampleTestCase
            exampleTestcaseList
            codeSnippets { lang langSlug code }
            acRate
          }
        }
        """
        return self._post({"query": query, "variables": {"titleSlug": title_slug}})

    def fetch_cpp_template(self, title_slug: str) -> Optional[str]:
        resp = self.fetch_problem_details(title_slug)
        if not resp.ok or not resp.data:
            return None
        snippets = (resp.data.get("data", {}).get("question", {}) or {}).get("codeSnippets", [])
        for snippet in snippets:
            if snippet.get("langSlug") == "cpp":
                return snippet.get("code")
        return None

    def fetch_problemset(self, search: str = "", difficulty: Optional[str] = None, skip: int = 0, limit: int = 20) -> LeetCodeResponse:
        # LeetCode problemset query v2 (public GraphQL)
        query = """
        query problemsetQuestionList($categorySlug: String, $skip: Int, $limit: Int, $filters: QuestionFilterInput) {
          problemsetQuestionListV2(categorySlug: $categorySlug, skip: $skip, limit: $limit, filters: $filters) {
            questions {
              questionFrontendId
              title
              titleSlug
              difficulty
              acRate
            }
          }
        }
        """
        # Many LeetCode schemas change filter inputs frequently; pass no filters and filter client-side for stability
        filters: Optional[Dict[str, Any]] = None
        variables = {
            "categorySlug": "all",
            "skip": skip,
            "limit": limit,
            "filters": filters,
        }
        return self._post({"query": query, "variables": variables})


