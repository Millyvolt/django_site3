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
from polls.models import UserCodeSubmission, UserProfile


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
    """Question editor page for coding problems"""
    print(f"IN FUNCTION question_editor")
    
    # Check if this is a daily question request
    is_daily = request.GET.get('daily') == 'true'
    
    # Get question_id from URL parameter if not in path
    if not question_id:
        question_id = request.GET.get('q', '1')
    
    # Get title_slug from URL parameter if available
    title_slug = request.GET.get('slug', None)
    
    # Define problem data
    problems = {}
    problem = problems.get(question_id)
    if not problem:
        # Try to fetch the problem dynamically from LeetCode API
        print(f"Problem {question_id} not found in hardcoded list, fetching from LeetCode API...")
        problem = fetch_problem_from_leetcode_api(question_id)
        if not problem:
            print(f"Failed to fetch problem {question_id} from API, creating fallback...")
            # Create a basic fallback problem
            problem = {
                'title': f'Problem {question_id}',
                'difficulty': 'Medium',
                'description': f'<p>This is LeetCode problem {question_id}. The full problem details could not be loaded from the API.</p><p>Please visit <a href="https://leetcode.com/problemset/all/" target="_blank">LeetCode</a> to see the complete problem description.</p>',
                'examples': [
                    {
                        'input': 'See LeetCode for examples',
                        'output': 'See LeetCode for expected output',
                        'explanation': 'Visit LeetCode for detailed examples and explanations.'
                    }
                ],
                'constraints': [
                    'Visit LeetCode for full constraints',
                    f'This is problem {question_id} from LeetCode'
                ],
                'template': f'''def solution_{question_id}():
    # Problem {question_id} from LeetCode
    # Your code here
    pass

# Test your solution!''',
                'cppTemplate': f'''#include <iostream>
using namespace std;

class Solution {{
public:
    // Problem {question_id} from LeetCode
    // Your code here
    
}};

int main() {{
    Solution solution;
    // Test your solution here
    return 0;
}}'''
            }
        
        # Add the fetched/created problem to the problems dictionary so JavaScript can find it
        problems[question_id] = problem
    
    # Load user's saved code if they're logged in
    user_code = ""
    if request.user.is_authenticated:
        try:
            user_submission = UserCodeSubmission.objects.get(
                user=request.user, 
                question_id=question_id
            )
            user_code = user_submission.code
            # Override the template with user's saved code
            problem['template'] = user_code
            problem['cppTemplate'] = user_code
        except UserCodeSubmission.DoesNotExist:
            # No saved code found, use default template
            pass
    
    # Get user profile for avatar display
    user_profile = None
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'problems': json.dumps(problems),
        'current_problem': problem,
        'current_question_id': question_id,
        'current_title_slug': title_slug,
        'is_daily': is_daily,
        'user_code': user_code,
        'user_profile': user_profile
    }
    return render(request, 'leetcode/editor.html', context)


@login_required
@require_http_methods(["POST"])
def compile_code(request: HttpRequest) -> HttpResponse:
    """Compile and run code using JDoodle API with intelligent simulation fallback"""
    # Basic rate limit: 20 requests per 5 minutes per user
    user_key = f"leetcode:rate:compile:{request.user.id}"
    count = cache.get(user_key, 0)
    if count >= 20:
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Try again later.'}, status=429)
    cache.set(user_key, count + 1, timeout=300)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'cpp')
        
        if not code:
            return JsonResponse({'error': 'No code provided'}, status=400)

        # Get question_id and title_slug from request if available
        question_id = data.get('question_id', '1')
        title_slug = data.get('title_slug')

        # Use the working approach from my_django_project
        result = execute_code_jdoodle(code, language, question_id, title_slug)
        
        # Save user's code if they're logged in
        if request.user.is_authenticated and code.strip():
            try:
                user_submission, created = UserCodeSubmission.objects.get_or_create(
                    user=request.user,
                    question_id=question_id,
                    defaults={
                        'code': code,
                        'language': language
                    }
                )
                if not created:
                    # Update existing submission
                    user_submission.code = code
                    user_submission.language = language
                    user_submission.save()
            except Exception as e:
                # Log error but don't fail the compilation
                print(f"Error saving user code: {e}")
        
        return JsonResponse(result)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def fetch_cpp_template(request: HttpRequest) -> HttpResponse:
    """API endpoint to fetch C++ template for a specific LeetCode question"""
    # Basic rate limit: 20 requests per 5 minutes per user
    user_key = f"leetcode:rate:cpp:{request.user.id}"
    count = cache.get(user_key, 0)
    if count >= 20:
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Try again later.'}, status=429)
    cache.set(user_key, count + 1, timeout=300)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id', '')
        title_slug = data.get('title_slug', None)
        
        if not question_id:
            return JsonResponse({'error': 'No question_id provided'}, status=400)
        
        # Fetch C++ template from LeetCode
        result = fetch_cpp_template_from_leetcode(question_id, title_slug)
        
        if result:
            response_data = {
                'success': True,
                'cpp_template': result['cpp_template'],
                'title': result['title'],
                'difficulty': result['difficulty'],
                'title_slug': result['title_slug']
            }
            
            # Add information about whether this is a generic template
            if result.get('is_generic'):
                response_data['is_generic'] = True
                response_data['message'] = 'LeetCode did not provide a C++ template, so a generic template was created'
            
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': f'Could not fetch C++ template for question {question_id}'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"])
def save_user_code(request: HttpRequest) -> HttpResponse:
    """Save user's code without compiling it"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'cpp')
        question_id = data.get('question_id', '1')
        
        if not code.strip():
            return JsonResponse({'error': 'No code provided'}, status=400)
        
        # Save user's code
        user_submission, created = UserCodeSubmission.objects.get_or_create(
            user=request.user,
            question_id=question_id,
            defaults={
                'code': code,
                'language': language
            }
        )
        if not created:
            # Update existing submission
            user_submission.code = code
            user_submission.language = language
            user_submission.save()
        
        return JsonResponse({'success': True, 'message': 'Code saved successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

# Problem cache for dynamic fetching
_problem_cache = {}

def fetch_problem_from_leetcode_api(question_id):
    """Fetch problem data from LeetCode API dynamically"""
    # Check cache first
    if question_id in _problem_cache:
        print(f"Using cached problem {question_id}")
        return _problem_cache[question_id]
    
    try:
        api = LeetCodeAPI()
        # Try to fetch by question ID first
        problem_data = api.fetch_problem_by_id(question_id)
        
        if problem_data:
            problem = {
                'title': problem_data.get('title', f'Problem {question_id}'),
                'difficulty': problem_data.get('difficulty', 'Medium'),
                'description': problem_data.get('content', f'Problem {question_id} from LeetCode'),
                'examples': problem_data.get('exampleTestcaseList', []),
                'constraints': problem_data.get('constraints', []),
                'template': problem_data.get('codeSnippets', {}).get('python3', ''),
                'cppTemplate': problem_data.get('codeSnippets', {}).get('cpp', ''),
                'title_slug': problem_data.get('titleSlug', '')
            }
            
            # Cache the result
            _problem_cache[question_id] = problem
            return problem
    except Exception as e:
        print(f"Error fetching problem {question_id}: {e}")
    
    return None

def fetch_cpp_template_from_leetcode(question_id, title_slug=None):
    """Fetch C++ code template specifically from LeetCode API"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try to get title_slug if not provided
        if not title_slug:
            # This is a simplified approach - in practice you might want to cache question_id -> title_slug mapping
            pass
        
        if title_slug:
            query = {
                'query': '''
                    query questionContent($titleSlug: String!) {
                        question(titleSlug: $titleSlug) {
                            content
                            title
                            difficulty
                            codeSnippets {
                                langSlug
                                code
                            }
                            exampleTestcaseList
                        }
                    }
                ''',
                'variables': {
                    'titleSlug': title_slug
                }
            }
        else:
            # Fallback query without title_slug
            query = {
                'query': '''
                    query {
                        problemsetQuestionList: questionList(
                            categorySlug: ""
                            limit: 1
                            skip: 0
                            filters: {}
                        ) {
                            data {
                                title
                                titleSlug
                                difficulty
                                content
                                codeSnippets {
                                    langSlug
                                    code
                                }
                                exampleTestcaseList
                            }
                        }
                    }
                '''
            }
        
        response = requests.post(url, json=query, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if title_slug and 'data' in data and 'question' in data['data']:
                question_data = data['data']['question']
                cpp_code = None
                
                # Find C++ code snippet
                for snippet in question_data.get('codeSnippets', []):
                    if snippet.get('langSlug') == 'cpp':
                        cpp_code = snippet.get('code')
                        break
                
                if cpp_code:
                    return {
                        'cpp_template': cpp_code,
                        'title': question_data.get('title', ''),
                        'difficulty': question_data.get('difficulty', ''),
                        'title_slug': title_slug,
                        'is_generic': False
                    }
            
            # If no C++ template found, create a generic one
            return {
                'cpp_template': f'''#include <iostream>
#include <vector>
#include <string>
using namespace std;

class Solution {{
public:
    // Problem {question_id} solution
    // TODO: Implement your solution here
}};

int main() {{
    Solution solution;
    // Test your solution here
    return 0;
}}''',
                'title': f'Problem {question_id}',
                'difficulty': 'Medium',
                'title_slug': title_slug or '',
                'is_generic': True
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching C++ template: {e}")
        return None

def execute_code_jdoodle(code, language, question_id='1', title_slug=None):
    """Execute code using JDoodle API (more reliable than Judge0)"""
    
    # JDoodle language codes and version indices
    language_codes = {
        'cpp': 'cpp',
        'python3': 'python3',
        'java': 'java',
        'javascript': 'nodejs',
    }
    
    # Version indices for different language versions
    version_indices = {
        'cpp': '5',  # C++17 (version 5)
        'python3': '3',  # Python 3.5.1
        'java': '3',  # Java 1.8
        'javascript': '2',  # Node.js 0.10.36
    }
    
    language_code = language_codes.get(language, 'cpp')
    version_index = version_indices.get(language, '5')
    
    # Prepare the code for submission
    leetcode_data = None
    if language == 'cpp':
        # Try to get LeetCode API data first
        leetcode_data = fetch_leetcode_data_for_simulation(question_id, title_slug)
        
        # Wrap C++ code with test cases
        full_code = generate_cpp_wrapper_jdoodle(code, question_id, title_slug)
        print(f"Generated wrapper for question {question_id}, length: {len(full_code)}")
        print(f"First 200 chars: {full_code[:200]}")
    else:
        full_code = code
    
    # JDoodle API endpoint
    jdoodle_url = "https://api.jdoodle.com/v1/execute"
    
    # JDoodle API data with your actual credentials
    jdoodle_data = {
        "clientId": getattr(settings, 'JDOODLE_CLIENT_ID', ''),
        "clientSecret": getattr(settings, 'JDOODLE_CLIENT_SECRET', ''),
        "script": full_code,
        "language": language_code,
        "versionIndex": version_index,
        "stdin": ""
    }
    
    try:
        response = requests.post(jdoodle_url, json=jdoodle_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'output' in result:
                return {
                    'success': True,
                    'output': result['output'],
                    'memory': result.get('memory', ''),
                    'cpuTime': result.get('cpuTime', '')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error from JDoodle'),
                    'error_type': 'api_error'
                }
        else:
            return {
                'success': False,
                'error': f'JDoodle API returned status {response.status_code}',
                'error_type': 'api_error'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Execution timeout - code took too long to run',
            'error_type': 'timeout_error'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Execution error: {str(e)}',
            'error_type': 'runtime_error'
        }

def fetch_leetcode_data_for_simulation(question_id, title_slug=None):
    """Fetch LeetCode data for simulation fallback"""
    try:
        # This is a simplified version - you might want to implement full LeetCode API integration
        return {
            'title': f'Problem {question_id}',
            'testcases': [
                {'input': 'Test input', 'expected': 'Expected output'}
            ]
        }
    except Exception as e:
        print(f"Error fetching LeetCode data: {e}")
        return None

def generate_cpp_wrapper_jdoodle(code, question_id='1', title_slug=None):
    """Generate a complete C++ program with test cases for JDoodle"""
    
    # Check if code already has main function
    if 'int main(' in code or 'void main(' in code:
        return code
    
    # Get LeetCode data for test cases
    leetcode_data = fetch_leetcode_data_for_simulation(question_id, title_slug)
    
    # Create a wrapper with basic test structure
    wrapper = f'''{code}

int main() {{
    // Basic test for Problem {question_id}
    std::cout << "Testing Problem {question_id}" << std::endl;
    
    // Add your test cases here
    // Example:
    // Solution solution;
    // auto result = solution.someFunction(test_input);
    // std::cout << "Result: " << result << std::endl;
    
    std::cout << "Test completed" << std::endl;
    return 0;
}}'''
    
    return wrapper

# Create your views here.
