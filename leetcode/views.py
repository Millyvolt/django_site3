import json
import requests
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from mysite import views as project_views
from django.conf import settings
from .services.leetcode_api import LeetCodeAPI


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'leetcode/home.html')


def daily_question(request: HttpRequest) -> HttpResponse:
    cache_key = "leetcode:daily_question"
    cached = cache.get(cache_key)
    context: dict[str, object]
    if cached:
        context = cached
    else:
        api = LeetCodeAPI()
        api_error: str | None = None
        is_real_question = False
        daily: dict[str, object] = {
            'title': 'Daily Question',
            'date': '',
            'difficulty': 'Medium',
            'ac_rate': None,
            'frontend_id': None,
            'title_slug': '',
            'link': '',
            'description': 'Problem description not available',
            'examples': [],
            'constraints': [],
            'example_testcases': '',
            'template': '',
            'cppTemplate': '',
            'hasRealCppTemplate': False,
        }

        resp = api.fetch_daily_question()
        if resp.ok and resp.data:
            try:
                active = resp.data['data']['activeDailyCodingChallengeQuestion']
                daily['date'] = active.get('date') or ''
                daily['link'] = active.get('link') or ''
                q = active.get('question') or {}
                daily['title'] = q.get('title') or daily['title']
                daily['difficulty'] = q.get('difficulty') or daily['difficulty']
                daily['ac_rate'] = q.get('acRate')
                daily['frontend_id'] = q.get('frontendQuestionId')
                title_slug = q.get('titleSlug') or ''
                daily['title_slug'] = title_slug
                is_real_question = True

                # Enrich with problem details
                if title_slug:
                    details = api.fetch_problem_details(title_slug)
                    if details.ok and details.data:
                        dq = details.data['data']['question']
                        content = dq.get('content') or ''
                        daily['description'] = content
                        samples = dq.get('exampleTestcaseList') or []
                        ex_list = []
                        for s in samples:
                            # Heuristic split; LeetCode gives lines like "Input: ..., Output: ..."
                            ex_list.append({'input': s, 'output': '', 'explanation': ''})
                        daily['examples'] = ex_list
                        daily['example_testcases'] = (dq.get('sampleTestCase') or '')
                        daily['constraints'] = []
                        # Templates
                        cpp = None
                        snippets = dq.get('codeSnippets') or []
                        for sn in snippets:
                            if sn.get('langSlug') == 'cpp':
                                cpp = sn.get('code')
                            if sn.get('langSlug') == 'python3' and not daily['template']:
                                daily['template'] = sn.get('code') or ''
                        if cpp:
                            daily['cppTemplate'] = cpp
                            daily['hasRealCppTemplate'] = True
                        elif daily['template']:
                            daily['cppTemplate'] = daily['template']
            except Exception as exc:  # safety net for unexpected API schema
                api_error = str(exc)
        else:
            api_error = resp.error or 'Failed to fetch daily question'

        context = {
            'daily_question': daily,
            'is_real_question': is_real_question,
            'api_error': api_error,
        }

        cache.set(cache_key, context, timeout=getattr(__import__('django.conf').conf.settings, 'LEETCODE_CACHE_TTL_SECONDS', 300))

    return render(request, 'leetcode/daily_question.html', context)


def question_selection(request: HttpRequest) -> HttpResponse:
    """Question selection page with LeetCode problems from API (same approach as site)."""
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 50))
        skip = (page - 1) * limit

        difficulty = request.GET.get('difficulty', '')
        search_term = request.GET.get('search', '')

        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        filters = {}
        # Difficulty is disabled to match stable behavior in site
        # if difficulty:
        #     filters['difficulty'] = difficulty
        if search_term:
            filters['searchKeywords'] = search_term

        payload = {
            'query': '''
                query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                    problemsetQuestionList: questionList(
                        categorySlug: $categorySlug
                        limit: $limit
                        skip: $skip
                        filters: $filters
                    ) {
                        total: totalNum
                        questions: data {
                            acRate
                            difficulty
                            frontendQuestionId: questionFrontendId
                            paidOnly: isPaidOnly
                            title
                            titleSlug
                            topicTags { name }
                        }
                    }
                }
            ''',
            'variables': {
                'categorySlug': '',
                'skip': skip,
                'limit': min(limit, 50),
                'filters': filters
            }
        }

        timeout = min(getattr(settings, 'LEETCODE_TIMEOUT_SECONDS', 10), 15)
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, dict) and 'data' in data:
                data_content = data.get('data')
                if data_content and 'problemsetQuestionList' in data_content:
                    problemset_data = data_content.get('problemsetQuestionList')
                    if problemset_data:
                        total_questions = problemset_data.get('total', 0) if isinstance(problemset_data, dict) else 0
                        questions_data = problemset_data.get('questions', []) if isinstance(problemset_data, dict) else []

                        questions = []
                        if isinstance(questions_data, list):
                            for q in questions_data:
                                if q and isinstance(q, dict) and not q.get('paidOnly', False):
                                    question_id = q.get('frontendQuestionId', '')
                                    title = q.get('title', '')
                                    q_difficulty = q.get('difficulty', '')
                                    ac_rate = q.get('acRate', 0)
                                    title_slug = q.get('titleSlug', '')
                                    topic_tags = q.get('topicTags', [])
                                    tags = []
                                    if isinstance(topic_tags, list):
                                        tags = [tag.get('name', '') for tag in topic_tags if tag and isinstance(tag, dict)]

                                    if question_id and title:
                                        questions.append({
                                            'id': question_id,
                                            'title': title,
                                            'difficulty': q_difficulty,
                                            'acceptance_rate': round(float(ac_rate) if ac_rate else 0, 1),
                                            'title_slug': title_slug,
                                            'tags': tags,
                                            'leetcode_url': f"https://leetcode.com/problems/{title_slug}" if title_slug else ''
                                        })

                        total_pages = (total_questions + limit - 1) // limit if total_questions > 0 else 1
                        has_previous = page > 1
                        has_next = page < total_pages

                        context = {
                            'questions': questions,
                            'current_page': page,
                            'total_pages': total_pages,
                            'total_questions': total_questions,
                            'has_previous': has_previous,
                            'has_next': has_next,
                            'previous_page': page - 1 if has_previous else None,
                            'next_page': page + 1 if has_next else None,
                            'current_difficulty': difficulty,
                            'current_search': search_term,
                            'limit': limit
                        }
                    else:
                        raise Exception("problemsetQuestionList is None or empty")
                else:
                    raise Exception(f"Missing problemsetQuestionList in data: {data_content}")
            else:
                raise Exception(f"Invalid response structure - missing data field: {data}")
        else:
            error_text = response.text
            raise Exception(f"API request failed with status {response.status_code}: {error_text}")

    except Exception as e:
        try:
            # Reuse site's alternative fallback helper
            questions = project_views.fetch_questions_alternative(page, limit, difficulty, search_term)
            if questions:
                context = {
                    'questions': questions,
                    'current_page': page,
                    'total_pages': 1,
                    'total_questions': len(questions),
                    'has_previous': False,
                    'has_next': False,
                    'previous_page': None,
                    'next_page': None,
                    'current_difficulty': difficulty,
                    'current_search': search_term,
                    'limit': limit,
                    'api_error': f"Primary API failed: {str(e)[:120]}... Using alternative method."
                }
            else:
                raise Exception("Alternative method returned no questions")
        except Exception as e2:
            context = {
                'questions': [],
                'current_page': 1,
                'total_pages': 1,
                'total_questions': 0,
                'has_previous': False,
                'has_next': False,
                'previous_page': None,
                'next_page': None,
                'current_difficulty': difficulty,
                'current_search': search_term,
                'limit': limit,
                'api_error': f"API methods failed. Primary: {str(e)[:100]}..., Alternative: {str(e2)[:100]}..."
            }

    return render(request, 'leetcode/question_selection.html', context)


@login_required
def question_editor(request: HttpRequest, question_id: str | None = None) -> HttpResponse:
    return project_views.question_editor(request, question_id=question_id)


@login_required
@require_http_methods(["POST"])
def compile_code(request: HttpRequest) -> HttpResponse:
    # Basic rate limit: 20 requests per 5 minutes per user
    user_key = f"leetcode:rate:compile:{request.user.id}"
    count = cache.get(user_key, 0)
    if count >= 20:
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Try again later.'}, status=429)
    cache.set(user_key, count + 1, timeout=300)
    return project_views.compile_code(request)


@login_required
@require_http_methods(["POST"])
def fetch_cpp_template(request: HttpRequest) -> HttpResponse:
    # Basic rate limit: 20 requests per 5 minutes per user
    user_key = f"leetcode:rate:cpp:{request.user.id}"
    count = cache.get(user_key, 0)
    if count >= 20:
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Try again later.'}, status=429)
    cache.set(user_key, count + 1, timeout=300)

    try:
        body = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        body = {}

    question_id = str(body.get('question_id') or '').strip()
    title_slug = (body.get('title_slug') or '').strip()

    # Prefer caching by title_slug when available
    cache_key = f"leetcode_cpp_template:{title_slug or question_id}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({
            'success': True,
            'cpp_template': cached['cpp_template'],
            'is_generic': cached.get('is_generic', False),
            'message': cached.get('message', ''),
        })

    api = LeetCodeAPI()
    cpp_code = None
    is_generic = False
    message = ''

    if title_slug:
        cpp_code = api.fetch_cpp_template(title_slug)
    # If no title_slug or API did not return C++ snippet, no lookup fallback here for slug by id to avoid heavy search

    if not cpp_code:
        # Provide a minimal generic C++ template as a fallback
        is_generic = True
        message = 'LeetCode C++ template not available; provided generic template.'
        cpp_code = (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false);\n"
            "    cin.tie(nullptr);\n"
            "    // TODO: implement solution\n"
            "    return 0;\n"
            "}\n"
        )

    cache.set(cache_key, {'cpp_template': cpp_code, 'is_generic': is_generic, 'message': message}, timeout=getattr(__import__('django.conf').conf.settings, 'LEETCODE_CACHE_TTL_SECONDS', 300))

    return JsonResponse({
        'success': True,
        'cpp_template': cpp_code,
        'is_generic': is_generic,
        'message': message,
    })

# Create your views here.
