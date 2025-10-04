from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import re
from bs4 import BeautifulSoup
import subprocess
import tempfile
import os
import time

# Simple in-memory cache for fetched problems
_problem_cache = {}

def home(request):
    """Home page view with links to polls and LeetCode"""
    return render(request, 'home.html')

def leetcode_home(request):
    """LeetCode home page view"""
    return render(request, 'leetcode_home.html')

def _extract_description_before_examples(elem):
    """Extract the description part before examples from an HTML element"""
    try:
        # Get all text content
        full_text = elem.get_text(separator=' ', strip=True)
        
        # Find the first occurrence of "Example" or "Input:"
        example_markers = ['Example 1:', 'Example 1', 'Example:', 'Input:', 'Examples:']
        first_example_pos = len(full_text)
        
        for marker in example_markers:
            pos = full_text.find(marker)
            if pos != -1 and pos < first_example_pos:
                first_example_pos = pos
        
        # If we found an example marker, extract text before it
        if first_example_pos < len(full_text):
            description_text = full_text[:first_example_pos].strip()
            if len(description_text) > 50:  # Make sure it's substantial
                # Convert back to HTML by finding the corresponding HTML elements
                html_parts = []
                for child in elem.children:
                    if hasattr(child, 'get_text'):
                        child_text = child.get_text(separator=' ', strip=True)
                        if child_text and not any(marker in child_text for marker in example_markers):
                            html_parts.append(str(child))
                        elif any(marker in child_text for marker in example_markers):
                            break
                
                if html_parts:
                    return ''.join(html_parts)
                else:
                    return f"<p>{description_text}</p>"
        
        return None
    except Exception:
        return None

def parse_leetcode_content(content):
    """Parse LeetCode HTML content to extract problem details"""
    if not content:
        return {
            'description': 'No description available',
            'examples': [],
            'constraints': []
        }
    
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract description - try multiple selectors
        description = ''
        
        # Try different selectors for description, but exclude examples
        selectors = [
            'div.content__u3I1.question-content__JfgR',
            'div.question-content',
            'div.content',
            'div[class*="content"]',
            'div[class*="question"]',
            'div[class*="problem"]'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Get HTML content to preserve formatting
                html_content = str(elem)
                # Get text content for length check
                text = elem.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Make sure it's substantial content
                    # Check if this content contains examples - if so, try to extract just the description part
                    if 'Example' in text or 'Input:' in text:
                        # Try to extract just the description part before examples
                        description_part = _extract_description_before_examples(elem)
                        if description_part:
                            description = description_part
                        else:
                            description = html_content
                    else:
                        description = html_content
                    break
        
        # If still no description, try to get the entire HTML content
        if not description:
            # Get the entire HTML content
            full_html = str(soup)
            if len(full_html) > 200:
                description = full_html
        
        # Always try to get the complete content, not just the first part
        if description and len(description) < 1000:  # If we have a short description, try to get more
            # Try to get the complete HTML content
            full_html = str(soup)
            if len(full_html) > len(description):
                description = full_html
        
        # If no description found, try to get all substantial text
        if not description:
            # Try to find the main content div and get its HTML
            main_content = soup.find('div', class_='content__u3I1') or soup.find('div', class_='question-content')
            if main_content:
                description = str(main_content)
            else:
                # Fallback to text extraction
                all_text = soup.get_text(separator=' ', strip=True)
                # Split by common separators and find the longest meaningful section
                sections = re.split(r'(?:\n\s*\n|Example|Constraints|Follow-up)', all_text)
                for section in sections:
                    section = section.strip()
                    if len(section) > 100 and not section.startswith('Example') and not section.startswith('Constraints'):
                        description = section
                        break
        
        # Clean up description
        if description:
            # If it's HTML content, clean it up while preserving markup
            if '<' in description and '>' in description:
                # It's HTML content, clean up whitespace but preserve tags
                description = re.sub(r'>\s+<', '><', description)  # Remove whitespace between tags
                description = re.sub(r'\s+', ' ', description)  # Normalize other whitespace
            else:
                # It's plain text, normalize whitespace
                description = re.sub(r'\s+', ' ', description)
                # Remove common LeetCode boilerplate but keep the content
                description = re.sub(r'^Given\s+', '', description)
            
            # Ensure we have the full content by checking for common problem elements
            if not any(keyword in description.lower() for keyword in ['example', 'constraint', 'follow-up', 'note']):
                # If we don't see these keywords, we might have incomplete content
                # Try to get more content
                if '<' in description:
                    # It's HTML, try to get more HTML content
                    main_content = soup.find('div', class_='content__u3I1') or soup.find('div', class_='question-content')
                    if main_content and len(str(main_content)) > len(description):
                        description = str(main_content)
                else:
                    # It's text, try to get more text content
                    all_text = soup.get_text(separator=' ', strip=True)
                    if len(all_text) > len(description):
                        description = all_text  # Remove the 2000 character limit
        
        # Extract examples
        examples = []
        example_elements = soup.find_all('pre')
        for pre in example_elements:
            example_text = pre.get_text().strip()
            if 'Input:' in example_text and 'Output:' in example_text:
                lines = example_text.split('\n')
                input_line = ''
                output_line = ''
                explanation = ''
                
                for line in lines:
                    if line.startswith('Input:'):
                        input_line = line.replace('Input:', '').strip()
                    elif line.startswith('Output:'):
                        output_line = line.replace('Output:', '').strip()
                    elif line.startswith('Explanation:'):
                        explanation = line.replace('Explanation:', '').strip()
                
                if input_line and output_line:
                    examples.append({
                        'input': input_line,
                        'output': output_line,
                        'explanation': explanation
                    })
        
        # Also try to extract examples from the main content if not found in <pre> tags
        if not examples:
            # Look for example patterns in the main content
            main_content = soup.find('div', class_='content__u3I1') or soup.find('div', class_='question-content')
            if main_content:
                example_sections = main_content.find_all(['div', 'section'], string=re.compile(r'Example\s*\d*', re.I))
                for section in example_sections:
                    # Get the parent element that contains the full example
                    parent = section.parent
                    if parent:
                        example_text = parent.get_text().strip()
                        if 'Input:' in example_text and 'Output:' in example_text:
                            lines = example_text.split('\n')
                            input_line = ''
                            output_line = ''
                            explanation = ''
                            
                            for line in lines:
                                if line.startswith('Input:'):
                                    input_line = line.replace('Input:', '').strip()
                                elif line.startswith('Output:'):
                                    output_line = line.replace('Output:', '').strip()
                                elif line.startswith('Explanation:'):
                                    explanation = line.replace('Explanation:', '').strip()
                            
                            if input_line and output_line:
                                examples.append({
                                    'input': input_line,
                                    'output': output_line,
                                    'explanation': explanation
                                })
        
        # If no examples found in <pre> tags, try to find them in the text
        if not examples:
            all_text = soup.get_text(separator=' ', strip=True)
            # Look for example patterns in the text
            example_pattern = r'Example\s*\d*[:\s]*(.*?)(?:Input:|Output:|Explanation:)'
            matches = re.findall(example_pattern, all_text, re.IGNORECASE | re.DOTALL)
            for i, match in enumerate(matches[:5]):  # Increased limit to 5 examples
                if match.strip():
                    examples.append({
                        'input': f'See LeetCode for input details',
                        'output': f'See LeetCode for output details',
                        'explanation': match.strip()  # Remove truncation
                    })
        
        # Also try to extract examples from the HTML content directly
        if not examples:
            # Look for example divs or sections in the HTML
            example_divs = soup.find_all(['div', 'section'], class_=re.compile(r'example', re.I))
            for div in example_divs:
                example_text = div.get_text().strip()
                if example_text and len(example_text) > 20:
                    examples.append({
                        'input': 'See LeetCode for input details',
                        'output': 'See LeetCode for output details',
                        'explanation': example_text
                    })
        
        # Extract constraints
        constraints = []
        constraint_elements = soup.find_all('li')
        for li in constraint_elements:
            text = li.get_text().strip()
            if any(keyword in text.lower() for keyword in ['≤', '≥', 'length', 'range', 'constraint', '1 ≤', '0 ≤', 'n ≤', 'm ≤']):
                constraints.append(text)
        
        # If no constraints found in <li> tags, try to find them in the text
        if not constraints:
            all_text = soup.get_text(separator=' ', strip=True)
            # Look for constraint patterns
            constraint_pattern = r'Constraints?[:\s]*(.*?)(?:Example|Follow-up|Note|$)'
            matches = re.findall(constraint_pattern, all_text, re.IGNORECASE | re.DOTALL)
            if matches:
                constraint_text = matches[0].strip()
                # Split by common constraint separators
                constraint_lines = re.split(r'[•\-\*]', constraint_text)
                for line in constraint_lines:
                    line = line.strip()
                    if line and len(line) > 10:
                        constraints.append(line)
        
        # Also try to extract constraints from HTML content directly
        if not constraints:
            # Look for constraint divs or sections in the HTML
            constraint_divs = soup.find_all(['div', 'section'], class_=re.compile(r'constraint', re.I))
            for div in constraint_divs:
                constraint_text = div.get_text().strip()
                if constraint_text and len(constraint_text) > 20:
                    # Split by common separators
                    lines = re.split(r'[•\-\*]', constraint_text)
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10:
                            constraints.append(line)
        
        # If we still don't have a good description, show raw content
        if not description or len(description) < 100:
            # Try to get HTML content first
            main_content = soup.find('div', class_='content__u3I1') or soup.find('div', class_='question-content')
            if main_content:
                raw_content = str(main_content)
                description = f"Raw HTML content: {raw_content}"
            else:
                # Fallback to text
                raw_content = soup.get_text(separator=' ', strip=True)
                if raw_content:
                    description = f"Raw content: {raw_content}"
        
        return {
            'description': description or 'Problem description not available',
            'examples': examples,
            'constraints': constraints
        }
        
    except Exception as e:
        return {
            'description': f'Error parsing content: {str(e)}',
            'examples': [],
            'constraints': []
        }

def test_html(request):
    """Test HTML rendering"""
    test_data = {
        'title': 'HTML Test',
        'description': '<p>This is a <strong>test</strong> with <em>HTML markup</em> and <code>code blocks</code>.</p><ul><li>List item 1</li><li>List item 2</li></ul>'
    }
    return render(request, 'daily_question.html', {'daily_question': test_data, 'is_real_question': False})

def daily_question(request):
    """LeetCode daily question page view"""
    try:
        # Fetch the real daily question from LeetCode API
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = {
            'query': '''
                query questionOfToday {
                    activeDailyCodingChallengeQuestion {
                        date
                        link
                        question {
                            acRate
                            difficulty
                            frontendQuestionId: questionFrontendId
                            title
                            titleSlug
                            content
                            exampleTestcases
                            codeSnippets {
                                lang
                                code
                            }
                        }
                    }
                }
            '''
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'activeDailyCodingChallengeQuestion' in data['data']:
                question_data = data['data']['activeDailyCodingChallengeQuestion']
                question = question_data['question']
                
                # Parse the content to extract description, examples, and constraints
                content = question.get('content', '')
                parsed_content = parse_leetcode_content(content)
                
                # Get example test cases from the API
                example_testcases = question.get('exampleTestcases', '')
                
                # Extract code snippets
                code_snippets = question.get('codeSnippets', [])
                python_template = ''
                cpp_template = ''
                
                print(f"Daily question code snippets count: {len(code_snippets)}")
                # for snippet in code_snippets:
                #     lang = snippet.get('lang', '')
                #     print(f"Found code snippet in language: {lang}")
                
                # print(f"EXAMPLE TESTCASES: {example_testcases}")

                # Find Python and C++ templates from LeetCode
                for snippet in code_snippets:
                    lang = snippet.get('lang', '').lower()
                    code = snippet.get('code', '')
                    if lang == 'python3' or lang == 'python':
                        python_template = code
                        print(f"Found Python template with {len(code)} characters")
                    elif lang in ['cpp', 'c++', 'cxx', 'cc']:
                        cpp_template = code
                        print(f"Found C++ template with {len(code)} characters")
                
                if not cpp_template:
                    print("No C++ template found in daily question, will create generic one")
                
                # Create a structured daily question data
                daily_question_data = {
                    'title': question.get('title', 'Daily Question'),
                    'difficulty': question.get('difficulty', 'Medium'),
                    'date': question_data.get('date', '2024-12-20'),
                    'ac_rate': question.get('acRate', 0),
                    'frontend_id': question.get('frontendQuestionId', ''),
                    'title_slug': question.get('titleSlug', ''),
                    'link': f"https://leetcode.com{question_data.get('link', '')}",
                    'description': parsed_content['description'] if parsed_content['description'] != 'Problem description not available' else f"<p>This is today's LeetCode daily challenge: <strong>{question.get('title', 'Daily Question')}</strong>. Visit the LeetCode link below to see the full problem description, examples, and constraints.</p><p><em>Test HTML markup: <code>bold</code>, <strong>strong</strong>, <em>italic</em></em></p>",
                    'examples': parsed_content['examples'] if parsed_content['examples'] else [
                        {
                            'input': 'See LeetCode for examples',
                            'output': 'See LeetCode for expected output',
                            'explanation': 'Visit the LeetCode link for detailed examples and explanations.'
                        }
                    ],
                    'constraints': parsed_content['constraints'] if parsed_content['constraints'] else [
                        'Visit LeetCode for full constraints',
                        'This is the official daily challenge'
                    ],
                    'example_testcases': example_testcases,
                    'template': python_template if python_template else f'''def {question.get('titleSlug', 'solution').replace('-', '_')}():
    # Today's LeetCode Daily Challenge: {question.get('title', 'Daily Question')}
    # Difficulty: {question.get('difficulty', 'Medium')}
    # Acceptance Rate: {question.get('acRate', 0)}%
    # Visit: {f"https://leetcode.com{question_data.get('link', '')}"}
    
    # Your code here
    pass

                        # print(f"Found cpp_template snippet in language: {cpp_template}")

# Test your solution on LeetCode!''',
                    'cppTemplate': cpp_template if cpp_template else create_generic_cpp_template(
                        question.get('title', 'Daily Question'),
                        question.get('difficulty', 'Medium'),
                        question.get('frontendQuestionId', '1'),
                        question.get('titleSlug', 'daily-question')
                    ),
                    'hasRealCppTemplate': bool(cpp_template)
                }
                
                context = {
                    'daily_question': daily_question_data,
                    'is_real_question': True,
                    'debug_info': {
                        'content_length': len(content) if content else 0,
                        'parsed_description_length': len(parsed_content['description']) if parsed_content['description'] else 0,
                        'examples_count': len(parsed_content['examples']),
                        'constraints_count': len(parsed_content['constraints']),
                        'raw_content_preview': content[:1000] if content else 'No content',
                        'parsed_content_preview': parsed_content['description'][:1000] if parsed_content['description'] else 'No description',
                        'has_html_tags': '<' in (parsed_content['description'] or ''),
                        'examples_preview': [ex.get('explanation', '')[:200] for ex in parsed_content['examples'][:3]]
                    }
                }
            else:
                raise Exception("Invalid API response structure")
        else:
            raise Exception(f"API request failed with status {response.status_code}")
            
    except Exception as e:
        # Fallback to a default question if API fails
        print(f"Error fetching daily question: {str(e)}")
        daily_question_data = {
        }
        
        context = {
            'daily_question': daily_question_data,
            'is_real_question': False,
            'api_error': str(e)
        }
    
    return render(request, 'daily_question.html', context)

def leetcode(request):
    """LeetCode problems page view"""
    return render(request, 'leetcode.html')

def question_selection(request):
    """Question selection page with LeetCode problems from API"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 50))  # Show 50 questions per page
        skip = (page - 1) * limit
        
        # Get filter parameters
        difficulty = request.GET.get('difficulty', '')
        search_term = request.GET.get('search', '')
        
        # Fetch questions from LeetCode GraphQL API
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Build the GraphQL query to fetch problems (with required parameters)
        query = {
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
                            topicTags {
                                name
                            }
                        }
                    }
                }
            ''',
            'variables': {
                'categorySlug': '',  # Empty string for all problems
                'skip': skip,
                'limit': min(limit, 50),  # Start with smaller limit
                'filters': {}  # Empty filters object
            }
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # print(f"API Response data: {data}")  # Debug log
            
            # Add comprehensive null checks
            if data and isinstance(data, dict) and 'data' in data:
                data_content = data.get('data')
                if data_content and 'problemsetQuestionList' in data_content:
                    problemset_data = data_content.get('problemsetQuestionList')
                    if problemset_data:
                        total_questions = problemset_data.get('total', 0) if isinstance(problemset_data, dict) else 0
                        questions_data = problemset_data.get('questions', []) if isinstance(problemset_data, dict) else []
                        
                        # Format the questions data with null checks
                        questions = []
                        if isinstance(questions_data, list):
                            for q in questions_data:
                                if q and isinstance(q, dict) and not q.get('paidOnly', False):  # Only include free questions
                                    # Safe extraction with defaults
                                    question_id = q.get('frontendQuestionId', '')
                                    title = q.get('title', '')
                                    difficulty = q.get('difficulty', '')
                                    ac_rate = q.get('acRate', 0)
                                    title_slug = q.get('titleSlug', '')
                                    topic_tags = q.get('topicTags', [])
                                    
                                    # Process tags safely
                                    tags = []
                                    if isinstance(topic_tags, list):
                                        tags = [tag.get('name', '') for tag in topic_tags if tag and isinstance(tag, dict)]
                                    
                                    # Only add if we have essential data
                                    if question_id and title:
                                        questions.append({
                                            'id': question_id,
                                            'title': title,
                                            'difficulty': difficulty,
                                            'acceptance_rate': round(float(ac_rate) if ac_rate else 0, 1),
                                            'title_slug': title_slug,
                                            'tags': tags,
                                            'leetcode_url': f"https://leetcode.com/problems/{title_slug}" if title_slug else ''
                                        })
                        
                        # Calculate pagination info
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
            # Debug: Print the error response
            error_text = response.text
            print(f"API Error {response.status_code}: {error_text}")
            raise Exception(f"API request failed with status {response.status_code}: {error_text}")
            
    except Exception as e:
        # Try alternative approach - fetch from problems page
        try:
            print(f"Primary API failed: {str(e)}. Trying alternative approach...")
            questions = fetch_questions_alternative(page, limit, difficulty, search_term)
            
            if questions:  # Only use alternative if we got questions
                context = {
                    'questions': questions,
                    'current_page': page,
                    'total_pages': 1,  # Simplified for alternative approach
                    'total_questions': len(questions),
                    'has_previous': False,
                    'has_next': False,
                    'previous_page': None,
                    'next_page': None,
                    'current_difficulty': difficulty,
                    'current_search': search_term,
                    'limit': limit,
                    'api_error': f"Primary API failed: {str(e)}. Using alternative method."
                }
            else:
                raise Exception("Alternative method returned no questions")
        except Exception as e2:
            print(f"Alternative approach also failed: {str(e2)}")
            # Final fallback to sample questions
            # questions = fetch_questions_scraping()  # Use the expanded sample questions
            questions = []
            
            context = {
                'questions': questions,
                'current_page': 1,
                'total_pages': 1,
                'total_questions': len(questions),
                'has_previous': False,
                'has_next': False,
                'previous_page': None,
                'next_page': None,
                'current_difficulty': difficulty,
                'current_search': search_term,
                'limit': limit,
                'api_error': f"API methods failed. Primary: {str(e)[:100]}..., Alternative: {str(e2)[:100]}..."
            }
    
    return render(request, 'question_selection.html', context)

def fetch_questions_alternative(page, limit, difficulty, search_term):
    """Alternative method to fetch questions when GraphQL API fails"""
    try:
        # Try a different GraphQL endpoint or query
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        # Try with required parameters
        query = {
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
                            frontendQuestionId: questionFrontendId
                            title
                            difficulty
                            acRate
                            paidOnly: isPaidOnly
                            titleSlug
                        }
                    }
                }
            ''',
            'variables': {
                'categorySlug': '',
                'limit': 10,
                'skip': 0,
                'filters': {}
            }
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Alternative API Response: {data}")  # Debug log
            
            # Add comprehensive null checks for alternative API
            if data and isinstance(data, dict) and 'data' in data:
                data_content = data.get('data')
                if data_content and 'problemsetQuestionList' in data_content:
                    problemset_data = data_content.get('problemsetQuestionList')
                    if problemset_data and isinstance(problemset_data, dict):
                        questions_data = problemset_data.get('questions', [])
                        
                        questions = []
                        if isinstance(questions_data, list):
                            for q in questions_data:
                                if q and isinstance(q, dict) and not q.get('paidOnly', False):
                                    # Safe extraction with null checks
                                    question_id = q.get('frontendQuestionId', '')
                                    title = q.get('title', '')
                                    difficulty = q.get('difficulty', '')
                                    ac_rate = q.get('acRate', 0)
                                    title_slug = q.get('titleSlug', '')
                                    topic_tags = q.get('topicTags', [])
                                    
                                    # Process tags safely
                                    tags = []
                                    if isinstance(topic_tags, list):
                                        tags = [tag.get('name', '') for tag in topic_tags if tag and isinstance(tag, dict)]
                                    
                                    # Only add if we have essential data
                                    if question_id and title:
                                        questions.append({
                                            'id': question_id,
                                            'title': title,
                                            'difficulty': difficulty,
                                            'acceptance_rate': round(float(ac_rate) if ac_rate else 0, 1),
                                            'title_slug': title_slug,
                                            'tags': tags,
                                            'leetcode_url': f"https://leetcode.com/problems/{title_slug}" if title_slug else ''
                                        })
                        
                        if questions:  # Only return if we got valid questions
                            return questions
        
        # If that fails, try scraping the problems page
        print("Alternative API failed, falling back to sample questions")
        # return fetch_questions_scraping()
        return []
        
    except Exception as e:
        print(f"Alternative fetch failed: {str(e)}")
        # return fetch_questions_scraping()
        return []

def fetch_problem_from_leetcode_api(question_id):
    """Fetch problem data from LeetCode API dynamically"""
    # Check cache first
    if question_id in _problem_cache:
        print(f"Using cached problem {question_id}")
        return _problem_cache[question_id]
    
    try:
        # Try a more direct approach - use common title slug patterns
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Skip direct approach and go straight to search approach for better reliability
        print(f"Using search approach for problem {question_id}...")
        result = fetch_problem_by_search(question_id)
        if result:
            print(f"Search approach succeeded for problem {question_id}")
        else:
            print(f"Search approach failed for problem {question_id}")
        return result
        
    except Exception as e:
        print(f"Error fetching problem {question_id} from API: {str(e)}")
        return None

def fetch_problem_by_search(question_id):
    """Fallback method to search for problem by ID"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Search in smaller batches for efficiency
        print(f"Searching for problem {question_id} in LeetCode problemset...")
        for skip in range(0, 1000, 50):  # Check first 1000 problems
            find_query = {
                'query': '''
                    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                        problemsetQuestionList: questionList(
                            categorySlug: $categorySlug
                            limit: $limit
                            skip: $skip
                            filters: $filters
                        ) {
                            questions: data {
                                frontendQuestionId: questionFrontendId
                                title
                                titleSlug
                                difficulty
                                acRate
                            }
                        }
                    }
                ''',
                'variables': {
                    'categorySlug': '',
                    'skip': skip,
                    'limit': 50,
                    'filters': {}
                }
            }
            
            response = requests.post(url, json=find_query, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'problemsetQuestionList' in data['data']:
                    questions = data['data']['problemsetQuestionList'].get('questions', [])
                    
                    # Look for our target question ID
                    for q in questions:
                        if q.get('frontendQuestionId') == question_id:
                            # Try to fetch full problem content
                            title_slug = q.get('titleSlug')
                            if title_slug:
                                full_problem = fetch_full_problem_content(title_slug, q, question_id)
                                if full_problem:
                                    # Cache the result
                                    _problem_cache[question_id] = full_problem
                                    return full_problem
                            
                            # Fallback to basic info if full content fetch fails
                            problem = create_problem_from_basic_info(q, question_id)
                            # Cache the result
                            _problem_cache[question_id] = problem
                            return problem
        
        return None
        
    except Exception as e:
        print(f"Error in search fallback for problem {question_id}: {str(e)}")
        return None

def fetch_cpp_template_from_leetcode(question_id, title_slug=None):
    """Fetch C++ code template specifically from LeetCode API"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # If we don't have title_slug, try to find it first
        if not title_slug:
            title_slug = find_title_slug_by_id(question_id)
            if not title_slug:
                print(f"Could not find title_slug for question {question_id}")
                return None
        
        # Query to get C++ code snippet specifically
        detail_query = {
            'query': '''
                query questionContent($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        title
                        difficulty
                        content
                        exampleTestcases
                        codeSnippets {
                            lang
                            code
                        }
                    }
                }
            ''',
            'variables': {
                'titleSlug': title_slug
            }
        }
        
        response = requests.post(url, json=detail_query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'question' in data['data'] and data['data']['question']:
                question_data = data['data']['question']
                
                # Get code snippets and find C++ template
                code_snippets = question_data.get('codeSnippets', [])
                cpp_code = ''
                
                # Try different C++ language identifiers
                cpp_languages = ['cpp', 'c++', 'cxx', 'cc']
                
                for snippet in code_snippets:
                    lang = snippet.get('lang', '').lower()
                    if lang in cpp_languages:
                        cpp_code = snippet.get('code', '')
                        break
                
                if cpp_code:
                    print(f"Successfully fetched C++ template for problem {question_id} ({title_slug})")
                    return {
                        'cpp_template': cpp_code,
                        'title': question_data.get('title', f'Problem {question_id}'),
                        'difficulty': question_data.get('difficulty', 'Medium'),
                        'title_slug': title_slug
                    }
                else:
                    # If no C++ template found, create a generic one based on the problem
                    print(f"No C++ code snippet found for problem {question_id} ({title_slug}), creating generic template")
                    title = question_data.get('title', f'Problem {question_id}')
                    difficulty = question_data.get('difficulty', 'Medium')
                    
                    # Create a generic C++ template
                    generic_template = create_generic_cpp_template(title, difficulty, question_id, title_slug)
                    
                    return {
                        'cpp_template': generic_template,
                        'title': title,
                        'difficulty': difficulty,
                        'title_slug': title_slug,
                        'is_generic': True
                    }
        
        print(f"Failed to fetch C++ template for problem {question_id} ({title_slug}): {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Error fetching C++ template for problem {question_id} ({title_slug}): {str(e)}")
        return None

def create_generic_cpp_template(title, difficulty, question_id, title_slug):
    """Create a generic C++ template when LeetCode doesn't provide one"""
    
    # Common includes based on problem type
    includes = [
        "#include <iostream>",
        "#include <vector>",
        "#include <string>",
        "#include <algorithm>",
        "#include <unordered_map>",
        "#include <unordered_set>",
        "#include <queue>",
        "#include <stack>",
        "#include <climits>"
    ]
    
    # Determine likely includes based on title keywords
    title_lower = title.lower()
    selected_includes = ["#include <iostream>"]
    
    if any(keyword in title_lower for keyword in ['tree', 'binary', 'node']):
        selected_includes.extend(["#include <vector>", "#include <queue>"])
    elif any(keyword in title_lower for keyword in ['array', 'list', 'vector']):
        selected_includes.extend(["#include <vector>", "#include <algorithm>"])
    elif any(keyword in title_lower for keyword in ['string', 'char']):
        selected_includes.extend(["#include <string>", "#include <algorithm>"])
    elif any(keyword in title_lower for keyword in ['hash', 'map', 'set']):
        selected_includes.extend(["#include <unordered_map>", "#include <unordered_set>"])
    elif any(keyword in title_lower for keyword in ['stack', 'queue']):
        selected_includes.extend(["#include <stack>", "#include <queue>"])
    else:
        # Default includes for general problems
        selected_includes.extend(["#include <vector>", "#include <string>", "#include <algorithm>"])
    
    # Remove duplicates and sort
    selected_includes = sorted(list(set(selected_includes)))
    
    # Create the template
    includes_str = "\\n".join(selected_includes)
    template = f"""{includes_str}
using namespace std;

/**
 * Problem {question_id}: {title}
 * Difficulty: {difficulty}
 * LeetCode URL: https://leetcode.com/problems/{title_slug}/
 */

class Solution {{
public:
    // TODO: Implement your solution here
    // Add your method signature and implementation
    
}};

int main() {{
    Solution solution;
    
    // TODO: Add test cases here
    // Example test cases for {title}:
    
    cout << "Testing {title}..." << endl;
    
    return 0;
}}"""
    
    return template

def find_title_slug_by_id(question_id):
    """Find title_slug for a given question ID by searching through LeetCode problems"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/all/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Search in batches to find the question
        for skip in range(0, 1000, 50):  # Check first 1000 problems
            find_query = {
                'query': '''
                    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                        problemsetQuestionList: questionList(
                            categorySlug: $categorySlug
                            limit: $limit
                            skip: $skip
                            filters: $filters
                        ) {
                            questions: data {
                                frontendQuestionId: questionFrontendId
                                title
                                titleSlug
                                difficulty
                            }
                        }
                    }
                ''',
                'variables': {
                    'categorySlug': '',
                    'skip': skip,
                    'limit': 50,
                    'filters': {}
                }
            }
            
            response = requests.post(url, json=find_query, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'problemsetQuestionList' in data['data']:
                    questions = data['data']['problemsetQuestionList'].get('questions', [])
                    
                    # Look for our target question ID
                    for q in questions:
                        if q.get('frontendQuestionId') == question_id:
                            return q.get('titleSlug')
        
        return None
        
    except Exception as e:
        print(f"Error finding title_slug for question {question_id}: {str(e)}")
        return None

def fetch_full_problem_content(title_slug, question_info, question_id):
    """Fetch full problem content using the title slug"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Query to get full problem content
        detail_query = {
            'query': '''
                query questionContent($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        content
                        title
                        difficulty
                        exampleTestcases
                        codeSnippets {
                            lang
                            code
                        }
                    }
                }
            ''',
            'variables': {
                'titleSlug': title_slug
            }
        }
        
        response = requests.post(url, json=detail_query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'question' in data['data'] and data['data']['question']:
                question_data = data['data']['question']
                
                # Parse the content
                content = question_data.get('content', '')
                print(f"Raw content length for problem {question_id}: {len(content)}")
                parsed_content = parse_leetcode_content(content)
                print(f"Parsed description length: {len(parsed_content.get('description', ''))}")
                print(f"Parsed examples count: {len(parsed_content.get('examples', []))}")
                print(f"Parsed constraints count: {len(parsed_content.get('constraints', []))}")
                
                # Get code snippets
                code_snippets = question_data.get('codeSnippets', [])
                python_code = ''
                cpp_code = ''
                
                for snippet in code_snippets:
                    if snippet.get('lang') == 'python3':
                        python_code = snippet.get('code', '')
                    elif snippet.get('lang') == 'cpp':
                        cpp_code = snippet.get('code', '')
                
                # Create full problem data structure
                problem = {
                    'title': question_data.get('title', question_info.get('title', f'Problem {question_id}')),
                    'difficulty': question_data.get('difficulty', question_info.get('difficulty', 'Medium')),
                    'description': parsed_content['description'] if parsed_content['description'] else f"Problem {question_id}: {question_data.get('title', 'Unknown')}",
                    'examples': parsed_content['examples'] if parsed_content['examples'] else [
                        {
                            'input': 'See LeetCode for examples',
                            'output': 'See LeetCode for expected output',
                            'explanation': 'Visit the LeetCode link for detailed examples.'
                        }
                    ],
                    'constraints': parsed_content['constraints'] if parsed_content['constraints'] else [
                        'Visit LeetCode for full constraints'
                    ],
                    'template': python_code if python_code else f'''def solution_{question_id}():
    # Problem {question_id}: {question_data.get('title', 'Unknown')}
    # Your code here
    pass

# Test your solution!''',
                    'cppTemplate': cpp_code if cpp_code else f'''#include <iostream>
using namespace std;

class Solution {{
public:
    // Problem {question_id}: {question_data.get('title', 'Unknown')}
    // Your code here
    
}};

int main() {{
    Solution solution;
    // Test your solution here
    return 0;
}}'''
                }
                
                print(f"Successfully fetched full content for problem {question_id} ({title_slug})")
                return problem
        
        print(f"Failed to fetch full content for problem {question_id} ({title_slug}): {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Error fetching full content for problem {question_id} ({title_slug}): {str(e)}")
        return None

def create_problem_from_basic_info(question_info, question_id):
    """Create a basic problem structure from limited info"""
    title = question_info.get('title', f'Problem {question_id}')
    difficulty = question_info.get('difficulty', 'Medium')
    ac_rate = question_info.get('acRate', 0)
    
    return {
        'title': title,
        'difficulty': difficulty,
        'description': f"<p>This is <strong>{title}</strong> from LeetCode.</p><p>Difficulty: {difficulty}</p><p>Acceptance Rate: {ac_rate}%</p><p>Visit <a href='https://leetcode.com/problems/{question_info.get('titleSlug', '')}' target='_blank'>LeetCode</a> for the full problem description, examples, and constraints.</p>",
        'examples': [
            {
                'input': 'See LeetCode for examples',
                'output': 'See LeetCode for expected output',
                'explanation': 'Visit the LeetCode link for detailed examples and explanations.'
            }
        ],
        'constraints': [
            'Visit LeetCode for full constraints',
            f'This is problem {question_id} from LeetCode'
        ],
        'template': f'''def solution_{question_id}():
    # Problem {question_id}: {title}
    # Difficulty: {difficulty}
    # Acceptance Rate: {ac_rate}%
    # Visit: https://leetcode.com/problems/{question_info.get('titleSlug', '')}
    # Your code here
    pass

# Test your solution!''',
        'cppTemplate': f'''#include <iostream>
using namespace std;

class Solution {{
public:
    // Problem {question_id}: {title}
    // Difficulty: {difficulty}
    // Acceptance Rate: {ac_rate}%
    // Visit: https://leetcode.com/problems/{question_info.get('titleSlug', '')}
    // Your code here
    
}};

int main() {{
    Solution solution;
    // Test your solution here
    return 0;
}}'''
    }

def question_editor(request, question_id=None):

    print(f"IN FUNCTION question_editor")

    """Question editor page for coding problems"""
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
    
    context = {
        'problems': json.dumps(problems),
        'current_problem': problem,
        'current_question_id': question_id,
        'current_title_slug': title_slug,
        'is_daily': is_daily
    }
    return render(request, 'question_editor.html', context)

@csrf_exempt
def fetch_cpp_template(request):
    """API endpoint to fetch C++ template for a specific LeetCode question"""
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

@csrf_exempt
def compile_code(request):
    """Compile and run code using JDoodle API with intelligent simulation fallback"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'cpp')
        # input_data = data.get('input', '')
        
        if not code:
            return JsonResponse({'error': 'No code provided'}, status=400)

        # print(f"Code before")
        # print(f"Code before")

        # Get question_id and title_slug from request if available
        question_id = data.get('question_id', '1')
        title_slug = data.get('title_slug')

        # print(f"Question ID: {question_id}")
        # print(f"Title Slug: {title_slug}")
        # print(f"Code: {code}")
        # print(f"Language: {language}")

        # return JsonResponse({'error': 'Code before: ' + code})

        # Use the working approach from my_django_project
        result = execute_code_jdoodle(code, language, question_id, title_slug)
        return JsonResponse(result)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


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
        # 'cpp': '4',  # C++11 (version 4)
        'cpp': '5',  # C++17 (version 5)
        'python3': '3',  # Python 3.5.1
        'java': '3',  # Java 1.8
        'javascript': '2',  # Node.js 0.10.36
    }
    
    language_code = language_codes.get(language, 'cpp')
    # version_index = version_indices.get(language, '4')
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
    api_data = {
        "clientId": "5a33bce78cbe581c1c432078db8eaa7f",
        "clientSecret": "5d2a91048622680e7dfb7165e5afc9be131986d2257916e16a5f1d50e8567289",
        "script": full_code,
        "language": language_code,
        "versionIndex": version_index
    }
    
    try:
        # Try JDoodle API first
        response = requests.post(
            jdoodle_url,
            json=api_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Debug: Print the full response
            print(f"JDoodle API Response: {result}")
            
            if 'error' in result and result['error']:
                return {
                    'success': False,
                    'error': result['error'],
                    'error_type': 'api_error'
                }
            
            stdout = result.get('output', '')
            stderr = result.get('error', '')
            
            if stderr and 'compilation error' in stderr.lower():
                return {
                    'success': False,
                    'error': stderr,
                    'error_type': 'compilation_error'
                }
            elif stderr:
                return {
                    'success': False,
                    'error': stderr,
                    'error_type': 'runtime_error'
                }
            
            return {
                'success': True,
                'output': stdout,
                'error': stderr,
                'statusCode': 0,
                'memory': result.get('memory', 'N/A'),
                'cpuTime': result.get('cpuTime', 'N/A')
            }
        
        else:
            # Debug: Print the error response
            print(f"JDoodle API Error: Status {response.status_code}, Response: {response.text}")
            # Fallback to simulated execution for demo
            # return execute_code_simulation(code, language, question_id, leetcode_data)
            return None
    
    except requests.exceptions.RequestException as e:
        # Debug: Print the exception
        print(f"JDoodle API Request Exception: {str(e)}")
        # Fallback to simulated execution
        # return execute_code_simulation(code, language, question_id, leetcode_data)
        return None


def fetch_leetcode_data_for_simulation(question_id, title_slug=None):

    print(f"Fetching LeetCode data for simulation: {question_id}")

    """Fetch LeetCode data for simulation fallback"""
    try:
        # Use provided title_slug if available (from daily question data)
        if title_slug:
            print(f"Using provided title_slug: {title_slug}")
        else:
            # Fallback to finding title_slug (for non-daily questions)
            print(f"No title_slug provided, searching for question_id: {question_id}")
            title_slug = find_title_slug_by_id(question_id)
            if not title_slug:
                return None
        
        # Fetch from LeetCode API
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = {
            'query': '''
                query questionContent($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        title
                        difficulty
                        content
                        exampleTestcases
                        codeSnippets {
                            lang
                            code
                        }
                    }
                }
            ''',
            'variables': {
                'titleSlug': title_slug
            }
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'question' in data['data'] and data['data']['question']:
                question_data = data['data']['question']
                
                # Get example test cases
                example_testcases = question_data.get('exampleTestcases', '')
                
                # Get method name from LeetCode code snippets
                method_name = 'solve'  # default
                code_snippets = question_data.get('codeSnippets', [])
                for snippet in code_snippets:
                    if snippet.get('lang') in ['cpp', 'C++']:
                        cpp_code = snippet.get('code', '')
                        detected_method = detect_method_name_from_code(cpp_code)
                        if detected_method != 'solve':
                            method_name = detected_method
                            break
                
                return {
                    'example_testcases': example_testcases,
                    'method_name': method_name,
                    'title': question_data.get('title', ''),
                    'difficulty': question_data.get('difficulty', '')
                }
        
        return None
        
    except Exception as e:
        print(f"Error fetching LeetCode data for simulation: {str(e)}")
        return None

def parse_leetcode_test_cases_for_simulation(leetcode_data):
    """Parse LeetCode test cases for simulation"""
    try:
        example_testcases = leetcode_data.get('example_testcases', '')
        method_name = leetcode_data.get('method_name', 'solve')
        
        # Parse test cases - LeetCode format is just input strings
        lines = example_testcases.strip().split('\n')
        test_cases = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove quotes if present
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                test_cases.append({
                    'input': line,
                    'expected': f'[Expected output for {method_name}]'
                })
        
        return test_cases
        
    except Exception as e:
        print(f"Error parsing LeetCode test cases for simulation: {str(e)}")
        return []

def get_test_cases_for_question(question_id, code=''):
    """Get test cases and execution code for a specific question"""
    test_cases_map = {}
    # If question not found, try to fetch from LeetCode API
    if question_id not in test_cases_map:
        leetcode_test_cases = fetch_test_cases_from_leetcode(question_id)
        if leetcode_test_cases:
            return leetcode_test_cases
        # Fallback to generic test cases if LeetCode API fails
        print(f"Test cases LeetCode API fails")
        # return generate_generic_test_cases_fallback(question_id, code)
        return None
    return test_cases_map.get(question_id, test_cases_map['1'])

def generate_cpp_wrapper_jdoodle(code, question_id='1', title_slug=None):
    """Generate a complete C++ program with test cases for Judge0"""
    
    # Check if code already has main function
    if 'int main(' in code or 'void main(' in code:
        return code
    
    # ALWAYS try to fetch test cases from LeetCode API first (for ALL questions)
    print(f"Generating C++ wrapper for question {question_id}")
    leetcode_wrapper = fetch_and_generate_leetcode_wrapper(code, question_id, title_slug)
    if leetcode_wrapper:
        print(f"Using LeetCode API wrapper for question {question_id}")
        return leetcode_wrapper
    
    # Only fallback to hardcoded test cases if LeetCode API completely fails
    print(f"LeetCode API failed, falling back to hardcoded test cases for question {question_id}")
    test_cases = get_test_cases_for_question(question_id, code)
    
    # Generate wrapper code for Judge0
    wrapper_code = '''#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <algorithm>
#include <sstream>
using namespace std;

''' + code + '''

''' + test_cases['test_data'] + '''

int main() {
    Solution solution;
    int passed = 0;
    int total = ''' + test_cases.get('total_count', 'test_inputs.size()') + ''';
    
    for (int i = 0; i < total; i++) {
        ''' + test_cases['test_execution'] + '''
        
        cout << "Test Case " << (i + 1) << ": ";
        ''' + test_cases['test_output'] + '''
        
        cout << "Expected: ";
        ''' + test_cases['expected_output'] + '''
        
        cout << "Your Output: ";
        ''' + test_cases['actual_output'] + '''
        
        // Check if result is correct
        bool is_correct = (result == expected_outputs[i]);
        if (is_correct) {
            cout << " ✓" << endl;
            passed++;
        } else {
            cout << " ✗" << endl;
        }
        cout << endl;
    }
    
    cout << "Result: " << passed << "/" << total << " test cases passed" << endl;
    return 0;
}
'''
    
    return wrapper_code

def fetch_and_generate_leetcode_wrapper(code, question_id, title_slug=None):

    print(f"Fetching and generating LeetCode wrapper for question {question_id}")

    """Fetch test cases from LeetCode and generate a complete C++ wrapper"""
    try:
        print(f"Attempting to fetch LeetCode test cases for question {question_id}")
        
        # Use provided title_slug if available (from daily question data)
        if title_slug:
            print(f"Using provided title_slug: {title_slug}")
        else:
            # Fallback to finding title_slug (for non-daily questions)
            print(f"No title_slug provided, searching for question_id: {question_id}")
            title_slug = find_title_slug_by_id(question_id)
            if not title_slug:
                print(f"No title_slug found for question {question_id}")
                return None
        
        print(f"Found title_slug: {title_slug}")
        
        # Fetch from LeetCode API
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = {
            'query': '''
                query questionContent($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        title
                        difficulty
                        content
                        exampleTestcases
                        codeSnippets {
                            lang
                            code
                        }
                    }
                }
            ''',
            'variables': {
                'titleSlug': title_slug
            }
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=10)
        
        print(f"LeetCode API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'question' in data['data'] and data['data']['question']:
                question_data = data['data']['question']
                
                # Get example test cases
                example_testcases = question_data.get('exampleTestcases', '')
                print(f"Found example test cases: {example_testcases[:100]}...")
                
                # Get method name from LeetCode code snippets
                method_name = 'solve'  # default
                code_snippets = question_data.get('codeSnippets', [])
                for snippet in code_snippets:
                    if snippet.get('lang') in ['cpp', 'C++']:
                        cpp_code = snippet.get('code', '')
                        detected_method = detect_method_name_from_code(cpp_code)
                        if detected_method != 'solve':
                            method_name = detected_method
                            print(f"Found method name from LeetCode: {method_name}")
                            break
                
                if example_testcases:
                    # Generate a simple, working C++ wrapper
                    wrapper = generate_simple_leetcode_wrapper(code, question_id, example_testcases, method_name)
                    if wrapper:
                        print(f"Successfully generated LeetCode wrapper for question {question_id}")
                        print(f"Wrapper length: {len(wrapper)} characters")
                        # print(f"First 200 characters: {wrapper[:200]}")
                        print(f"All wrapper characters: {wrapper}")
                        return wrapper
                    else:
                        print(f"Failed to generate wrapper for question {question_id}")
                else:
                    print(f"No example test cases found for question {question_id}")
            else:
                print(f"No question data found in API response for question {question_id}")
        else:
            print(f"LeetCode API request failed with status {response.status_code}")
        
        return None
        
    except Exception as e:
        print(f"Error fetching LeetCode wrapper for question {question_id}: {str(e)}")
        return None

def generate_simple_leetcode_wrapper(code, question_id, example_testcases, method_name='solve'):
    """Generate a simple, working C++ wrapper for LeetCode test cases"""
    try:
        print(f"generate_simple_leetcode_wrapper called with method_name: {method_name}")
        
        # Try to detect the complete function signature
        function_signature = detect_function_signature(code, method_name)
        
        # Parse test cases with proper type conversion
        typed_test_cases = parse_typed_test_cases(example_testcases, function_signature)
        
        if not typed_test_cases:
            return None
        
        # Use the enhanced typed wrapper generation
        wrapper_code = generate_typed_cpp_wrapper(code, question_id, function_signature, typed_test_cases)
        
        return wrapper_code
        
    except Exception as e:
        print(f"Error generating simple LeetCode wrapper: {str(e)}")
        return None

def fetch_test_cases_from_leetcode(question_id):

    print(f"Fetching test cases from LeetCode API for question {question_id}")

    """Fetch actual test cases from LeetCode API"""
    try:
        # First, try to find the title_slug for this question_id
        title_slug = find_title_slug_by_id(question_id)
        if not title_slug:
            print(f"Could not find title_slug for question {question_id}")
            return None
        
        # Fetch the full problem details including test cases
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Query to get problem details including example test cases
        query = {
            'query': '''
                query questionContent($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        title
                        difficulty
                        content
                        exampleTestcases
                        codeSnippets {
                            lang
                            code
                        }
                    }
                }
            ''',
            'variables': {
                'titleSlug': title_slug
            }
        }
        
        response = requests.post(url, json=query, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'question' in data['data'] and data['data']['question']:
                question_data = data['data']['question']
                
                # Get example test cases
                example_testcases = question_data.get('exampleTestcases', '')
                
                # Get code snippets to find the method name
                code_snippets = question_data.get('codeSnippets', [])
                method_name = 'solve'  # default
                
                for snippet in code_snippets:
                    if snippet.get('lang') == 'cpp':
                        cpp_code = snippet.get('code', '')
                        detected_method = detect_method_name_from_code(cpp_code)
                        if detected_method != 'solve':
                            method_name = detected_method
                            break
                
                # Parse the example test cases
                if example_testcases:
                    return parse_leetcode_test_cases(example_testcases, method_name, question_id)
        
        print(f"Failed to fetch test cases for question {question_id} ({title_slug})")
        return None
        
    except Exception as e:
        print(f"Error fetching test cases for question {question_id}: {str(e)}")
        return None

def parse_leetcode_test_cases(example_testcases, method_name, question_id):
    """Parse LeetCode example test cases and generate C++ wrapper code"""
    try:
        # Example test cases are usually in a format like:
        # "nums = [2,7,11,15], target = 9\n[0,1]\nnums = [3,2,4], target = 6\n[1,2]"
        
        lines = example_testcases.strip().split('\n')
        test_cases = []
        
        i = 0
        while i < len(lines):
            if i + 1 < len(lines):
                input_line = lines[i].strip()
                output_line = lines[i + 1].strip()
                
                if input_line and output_line:
                    test_cases.append({
                        'input': input_line,
                        'output': output_line
                    })
                i += 2
            else:
                i += 1
        
        if not test_cases:
            return None
        
        # Generate a simple, working C++ test structure
        test_data = f'''// Test cases for Problem {question_id} (fetched from LeetCode)
vector<string> test_cases = {{'''
        
        for i, test_case in enumerate(test_cases):
            # Escape quotes in the input
            escaped_input = test_case['input'].replace('"', '\\"')
            test_data += f'\n    "{escaped_input}"'
            if i < len(test_cases) - 1:
                test_data += ','
        
        test_data += '\n};\n\nvector<string> expected_outputs = {'
        
        for i, test_case in enumerate(test_cases):
            # Escape quotes in the output
            escaped_output = test_case['output'].replace('"', '\\"')
            test_data += f'\n    "{escaped_output}"'
            if i < len(test_cases) - 1:
                test_data += ','
        
        test_data += '\n};'
        
        return {
            'test_data': test_data,
            'total_count': 'test_cases.size()',
            'test_execution': f'// Note: This is a simplified test - actual implementation would need proper parsing of test_cases[i]',
            'test_output': 'cout << "Test case " << (i+1) << ": " << test_cases[i] << endl;',
            'expected_output': 'cout << "Expected: " << expected_outputs[i] << endl;',
            'actual_output': 'cout << "Your output: [implementation needed]";'
        }
        
    except Exception as e:
        print(f"Error parsing test cases: {str(e)}")
        return None

def generate_leetcode_cpp_wrapper(code, question_id, method_name, test_cases_data):
    """Generate a complete C++ wrapper for LeetCode test cases"""
    try:
        # Parse the test cases data
        lines = test_cases_data.strip().split('\n')
        test_cases = []
        
        i = 0
        while i < len(lines):
            if i + 1 < len(lines):
                input_line = lines[i].strip()
                output_line = lines[i + 1].strip()
                
                if input_line and output_line:
                    test_cases.append({
                        'input': input_line,
                        'output': output_line
                    })
                i += 2
            else:
                i += 1
        
        if not test_cases:
            return None
        
        # Generate a complete C++ program
        wrapper_code = f'''#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <algorithm>
#include <sstream>
using namespace std;

{code}

int main() {{
    Solution solution;
    int passed = 0;
    int total = {len(test_cases)};
    
    // Test cases from LeetCode
    vector<string> test_inputs = {{'''
        
        for i, test_case in enumerate(test_cases):
            escaped_input = test_case['input'].replace('"', '\\"')
            wrapper_code += f'\n        "{escaped_input}"'
            if i < len(test_cases) - 1:
                wrapper_code += ','
        
        wrapper_code += '\n    };\n\n    vector<string> expected_outputs = {'
        
        for i, test_case in enumerate(test_cases):
            escaped_output = test_case['output'].replace('"', '\\"')
            wrapper_code += f'\n        "{escaped_output}"'
            if i < len(test_cases) - 1:
                wrapper_code += ','
        
        wrapper_code += f'''
    }};
    
    for (int i = 0; i < total; i++) {{
        cout << "Test Case " << (i + 1) << ": " << test_inputs[i] << endl;
        cout << "Expected: " << expected_outputs[i] << endl;
        cout << "Your Output: [Test execution would go here]" << endl;
        cout << "Note: This is a simplified test runner. For full functionality, proper parsing of inputs is needed." << endl;
        cout << endl;
    }}
    
    cout << "Result: " << total << " test cases displayed (fetched from LeetCode)" << endl;
    return 0;
}}'''
        
        return wrapper_code
        
    except Exception as e:
        print(f"Error generating LeetCode C++ wrapper: {str(e)}")
        return None

# def generate_generic_test_cases_fallback(question_id, code=''):

#     print(f"Generating generic test cases as fallback for question {question_id}")

#     """Generate generic test cases as fallback when LeetCode API fails"""
#     # Try to detect the method name from the code
#     method_name = detect_method_name_from_code(code)
    
#     # Try to detect parameter type from method signature
#     param_type = detect_parameter_type_from_code(code, method_name)
    
#     if param_type == 'string':
#         return {
#             'test_data': f'''// Generic test cases for Problem {question_id}
# vector<string> test_inputs = {{"hello", "leetcode", "a"}};

# vector<string> expected_outputs = {{"holle", "leotcede", "a"}};''',
#             'total_count': 'test_inputs.size()',
#             'test_execution': f'string result = solution.{method_name}(test_inputs[i]);',
#             'test_output': 'cout << "input = \\"" << test_inputs[i] << "\\"" << endl;',
#             'expected_output': 'cout << "\\"" << expected_outputs[i] << "\\"" << endl;',
#             'actual_output': 'cout << "\\"" << result << "\\"";'
#         }
#     elif param_type == 'bool':
#         return {
#             'test_data': f'''// Generic test cases for Problem {question_id}
# vector<bool> test_inputs = {{true, false, true}};

# vector<bool> expected_outputs = {{false, true, false}};''',
#             'total_count': 'test_inputs.size()',
#             'test_execution': f'bool result = solution.{method_name}(test_inputs[i]);',
#             'test_output': 'cout << "input = " << (test_inputs[i] ? "true" : "false") << endl;',
#             'expected_output': 'cout << (expected_outputs[i] ? "true" : "false") << endl;',
#             'actual_output': 'cout << (result ? "true" : "false");'
#         }
#     else:  # Default to int
#         return {
#             'test_data': f'''// Generic test cases for Problem {question_id}
# vector<int> test_inputs = {{1, 2, 3, 4, 5}};

# vector<int> expected_outputs = {{1, 2, 3, 4, 5}};''',
#             'total_count': 'test_inputs.size()',
#             'test_execution': f'int result = solution.{method_name}(test_inputs[i]);',
#             'test_output': 'cout << "input = " << test_inputs[i] << endl;',
#             'expected_output': 'cout << expected_outputs[i] << endl;',
#             'actual_output': 'cout << result;'
#         }

def detect_parameter_type_from_code(code, method_name):
    """Detect the parameter type from method signature"""
    import re
    
    # Look for method signature with the specific method name
    pattern = rf'{method_name}\s*\(\s*(\w+)\s+\w+'
    match = re.search(pattern, code)
    
    if match:
        param_type = match.group(1)
        print(f"Detected parameter type: {param_type}")
        return param_type
    
    # Fallback: look for common patterns
    if 'string' in code and method_name in ['reverseVowels', 'isPalindrome', 'isAnagram', 'wordPattern', 'reverseString']:
        return 'string'
    elif 'bool' in code and method_name in ['isHappy', 'isPalindrome', 'isAnagram']:
        return 'bool'
    else:
        return 'int'  # Default

def search_question_by_id(question_id):
    """Search for a question by ID using LeetCode's problemset API"""
    try:
        url = 'https://leetcode.com/graphql'
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problemset/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Query to search for problems by ID
        query = {
            'query': '''
                query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
                    problemsetQuestionList: questionList(
                        categorySlug: $categorySlug
                        limit: $limit
                        skip: $skip
                        filters: $filters
                    ) {
                        questions: data {
                            questionId
                            title
                            titleSlug
                            difficulty
                        }
                    }
                }
            ''',
            'variables': {
                'categorySlug': '',
                'limit': 50,
                'skip': 0,
                'filters': {}
            }
        }
        
        # Try to find the question by searching through the problemset
        # We'll search in batches since LeetCode limits the results
        for skip in range(0, 1000, 50):  # Search up to 1000 questions
            query['variables']['skip'] = skip
            response = requests.post(url, json=query, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'problemsetQuestionList' in data['data']:
                    questions = data['data']['problemsetQuestionList'].get('questions', [])
                    
                    for question in questions:
                        # Compare both string and integer versions of the question ID
                        if (question.get('questionId') == question_id or 
                            question.get('questionId') == int(question_id) or
                            str(question.get('questionId')) == str(question_id)):
                            title_slug = question.get('titleSlug')
                            print(f"Found question {question_id}: {title_slug}")
                            return title_slug
                    
                    # If we got fewer questions than the limit, we've reached the end
                    if len(questions) < 50:
                        break
        
        print(f"Question {question_id} not found in problemset")
        return None
        
    except Exception as e:
        print(f"Error searching for question {question_id}: {str(e)}")
        return None

def detect_method_name_from_code(code):

    print(f"Detecting method name from code")

    """Detect the method name from C++ code"""
    import re
    
    # Look for method declarations in the Solution class
    # Pattern: return_type methodName(parameters)
    method_patterns = [
        r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{',  # Standard method
        r'(\w+)\s+(\w+)\s*\([^)]*\)\s*;',   # Method declaration
    ]
    
    for pattern in method_patterns:
        matches = re.findall(pattern, code)
        for match in matches:
            return_type, method_name = match
            # Skip constructors, destructors, and common non-solution methods
            if method_name not in ['Solution', '~Solution', 'main', 'cout', 'cin', 'next', 'prev', 'begin', 'end', 'size', 'empty', 'push', 'pop', 'top', 'front', 'back']:
                print(f"Detected method name: {method_name}")
                return method_name
    
    # If no method found, try to find any function-like pattern
    function_pattern = r'(\w+)\s*\([^)]*\)\s*{'
    matches = re.findall(function_pattern, code)
    for match in matches:
        if match not in ['main', 'cout', 'cin', 'if', 'for', 'while', 'next', 'prev', 'begin', 'end', 'size', 'empty', 'push', 'pop', 'top', 'front', 'back']:
            print(f"Detected function name: {match}")
            return match
    
    # Default fallback
    print("No method detected, using default 'solve'")
    return 'solve'

def detect_function_signature(code, method_name):
    """Extract complete function signature including all parameters"""
    import re
    
    print(f"Detecting function signature for method: {method_name}")
    
    # Pattern to match: return_type methodName(type1 param1, type2 param2, ...)
    # This pattern handles various C++ type declarations including references, pointers, and templates
    pattern = rf'(\w+(?:<[^>]*>)?(?:\s*&\s*|\s*\*\s*)?)\s+{method_name}\s*\(\s*([^)]*)\s*\)'
    match = re.search(pattern, code)
    
    if match:
        return_type = match.group(1).strip()
        params_str = match.group(2).strip()
        
        print(f"Found signature: {return_type} {method_name}({params_str})")
        
        # Parse individual parameters
        parameters = []
        if params_str:
            # Split by comma, but be careful with template parameters
            param_parts = []
            current_param = ""
            template_depth = 0
            
            for char in params_str:
                if char == '<':
                    template_depth += 1
                elif char == '>':
                    template_depth -= 1
                elif char == ',' and template_depth == 0:
                    param_parts.append(current_param.strip())
                    current_param = ""
                    continue
                current_param += char
            
            if current_param.strip():
                param_parts.append(current_param.strip())
            
            for param in param_parts:
                if param:
                    # Split type and name - handle complex types
                    # Look for the last word as the parameter name
                    words = param.split()
                    if len(words) >= 2:
                        # Handle cases like "vector<int>& nums" or "const string& s"
                        param_name = words[-1]  # Last word is the parameter name
                        param_type = ' '.join(words[:-1])  # Everything else is the type
                        
                        parameters.append({
                            'type': param_type,
                            'name': param_name
                        })
                        print(f"  Parameter: {param_type} {param_name}")
        
        result = {
            'return_type': return_type,
            'parameters': parameters,
            'method_name': method_name
        }
        
        print(f"Complete signature detected: {result}")
        return result
    
    print(f"No signature found for method: {method_name}")
    return None

def parse_typed_test_cases(example_testcases, function_signature):
    """Parse test cases with proper type conversion based on function signature"""
    print(f"Parsing typed test cases for signature: {function_signature}")
    
    if not function_signature:
        print("No function signature provided, using fallback parsing")
        return parse_fallback_test_cases(example_testcases)
    
    parameters = function_signature['parameters']
    
    # Parse LeetCode test case format
    lines = example_testcases.strip().split('\n')
    test_cases = []
    
    # Handle different test case formats
    if len(parameters) == 1:
        # Single parameter: input-output pairs
        i = 0
        while i < len(lines):
            if i + 1 < len(lines):
                input_line = lines[i].strip()
                output_line = lines[i + 1].strip()
                
                if input_line and output_line:
                    # Parse individual parameters from input string
                    parsed_params = parse_parameters_from_string(input_line, parameters)
                    expected_output = parse_output_value(output_line, function_signature['return_type'])
                    
                    test_cases.append({
                        'input_params': parsed_params,
                        'expected_output': expected_output,
                        'raw_input': input_line,
                        'raw_output': output_line
                    })
                    print(f"  Parsed test case {len(test_cases)}: {parsed_params} -> {expected_output}")
                i += 2
            else:
                i += 1
    else:
        # Multiple parameters: need to group input lines together
        # Format: param1, param2, ..., expected_output
        i = 0
        while i < len(lines):
            # Check if we have enough lines for all parameters + output
            if i + len(parameters) < len(lines):
                # Collect input parameters
                input_lines = []
                for j in range(len(parameters)):
                    input_lines.append(lines[i + j].strip())
                
                # Get expected output
                output_line = lines[i + len(parameters)].strip()
                
                if all(input_lines) and output_line:
                    # Parse parameters from multiple input lines
                    parsed_params = parse_parameters_from_multiple_lines(input_lines, parameters)
                    expected_output = parse_output_value(output_line, function_signature['return_type'])
                    
                    test_cases.append({
                        'input_params': parsed_params,
                        'expected_output': expected_output,
                        'raw_input': '\n'.join(input_lines),
                        'raw_output': output_line
                    })
                    print(f"  Parsed test case {len(test_cases)}: {parsed_params} -> {expected_output}")
                
                i += len(parameters) + 1
            else:
                i += 1
    
    print(f"Successfully parsed {len(test_cases)} test cases")
    return test_cases

def parse_parameters_from_string(input_string, parameters):
    """Parse individual parameters from LeetCode input string"""
    print(f"Parsing parameters from: '{input_string}'")
    parsed = {}
    
    # Handle different input formats
    if '=' in input_string:
        # Format: "nums = [2,7,11,15], target = 9"
        # Need to be more careful with splitting to handle nested brackets
        parts = []
        current_part = ""
        bracket_depth = 0
        
        for char in input_string:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and bracket_depth == 0:
                parts.append(current_part.strip())
                current_part = ""
                continue
            current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Find matching parameter
                for param in parameters:
                    if param['name'] == key:
                        parsed[key] = convert_value_to_type(value, param['type'])
                        print(f"    {key} = {value} -> {parsed[key]} ({param['type']})")
                        break
    else:
        # Format: "[2,7,11,15]\n9" (separate lines) - handle this case
        # For now, try to match parameters by position
        values = [line.strip() for line in input_string.split('\n') if line.strip()]
        for i, param in enumerate(parameters):
            if i < len(values):
                parsed[param['name']] = convert_value_to_type(values[i], param['type'])
                print(f"    {param['name']} = {values[i]} -> {parsed[param['name']]} ({param['type']})")
    
    return parsed

def parse_parameters_from_multiple_lines(input_lines, parameters):
    """Parse parameters from multiple input lines (one per parameter)"""
    print(f"Parsing parameters from multiple lines: {input_lines}")
    parsed = {}
    
    for i, param in enumerate(parameters):
        if i < len(input_lines):
            value_str = input_lines[i].strip()
            parsed[param['name']] = convert_value_to_type(value_str, param['type'])
            print(f"    {param['name']} = {value_str} -> {parsed[param['name']]} ({param['type']})")
    
    return parsed

def convert_value_to_type(value_str, target_type):
    """Convert string value to appropriate type"""
    value_str = value_str.strip()
    print(f"Converting '{value_str}' to type '{target_type}'")
    
    # Handle vector types
    if target_type.startswith('vector<') and target_type.endswith('>'):
        # Parse "[1,2,3]" format
        if value_str.startswith('[') and value_str.endswith(']'):
            inner = value_str[1:-1]
            if inner.strip():
                # Determine inner type
                inner_type = target_type[7:-1]  # Extract type from vector<type>
                if inner_type == 'int':
                    # Handle both "[1,2,3]" and "["1","2","3"]" formats
                    elements = []
                    current_element = ""
                    bracket_depth = 0
                    
                    for char in inner:
                        if char == '[':
                            bracket_depth += 1
                        elif char == ']':
                            bracket_depth -= 1
                        elif char == ',' and bracket_depth == 0:
                            if current_element.strip():
                                elements.append(int(current_element.strip()))
                            current_element = ""
                            continue
                        current_element += char
                    
                    if current_element.strip():
                        elements.append(int(current_element.strip()))
                    
                    return elements
                elif inner_type == 'string':
                    # Handle string vectors - remove quotes from each element
                    elements = []
                    current_element = ""
                    bracket_depth = 0
                    
                    for char in inner:
                        if char == '[':
                            bracket_depth += 1
                        elif char == ']':
                            bracket_depth -= 1
                        elif char == ',' and bracket_depth == 0:
                            if current_element.strip():
                                elements.append(current_element.strip().strip('"'))
                            current_element = ""
                            continue
                        current_element += char
                    
                    if current_element.strip():
                        elements.append(current_element.strip().strip('"'))
                    
                    return elements
                elif inner_type == 'char':
                    # Handle char vectors
                    elements = []
                    current_element = ""
                    bracket_depth = 0
                    
                    for char in inner:
                        if char == '[':
                            bracket_depth += 1
                        elif char == ']':
                            bracket_depth -= 1
                        elif char == ',' and bracket_depth == 0:
                            if current_element.strip():
                                elements.append(current_element.strip().strip('"'))
                            current_element = ""
                            continue
                        current_element += char
                    
                    if current_element.strip():
                        elements.append(current_element.strip().strip('"'))
                    
                    return elements
            else:
                return []  # Empty vector
        return []
    
    # Handle string type
    elif target_type == 'string':
        # Remove quotes
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        return value_str
    
    # Handle int type
    elif target_type == 'int':
        try:
            return int(value_str)
        except ValueError:
            return 0
    
    # Handle bool type
    elif target_type == 'bool':
        return value_str.lower() in ['true', '1']
    
    # Handle pointer types (for now, return as string)
    elif target_type.endswith('*'):
        return value_str
    
    # Handle reference types
    elif target_type.endswith('&'):
        # Remove the & and process the base type
        base_type = target_type[:-1].strip()
        return convert_value_to_type(value_str, base_type)
    
    # Default fallback
    return value_str

def parse_output_value(output_str, return_type):
    """Parse expected output value based on return type"""
    print(f"Parsing output '{output_str}' for return type '{return_type}'")
    return convert_value_to_type(output_str, return_type)

def parse_fallback_test_cases(example_testcases):
    """Fallback parsing when no function signature is available"""
    print("Using fallback test case parsing")
    lines = example_testcases.strip().split('\n')
    test_cases = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Remove quotes if present
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            test_cases.append({
                'input_params': {'input': line},
                'expected_output': '[Expected output would be here]',
                'raw_input': line,
                'raw_output': '[Expected output would be here]'
            })
    
    return test_cases

def generate_typed_cpp_wrapper(code, question_id, function_signature, test_cases):
    """Generate C++ wrapper with proper type handling and enhanced features"""
    print(f"Generating typed C++ wrapper for question {question_id}")
    
    if not function_signature:
        print("No function signature provided, using fallback wrapper generation")
        return generate_fallback_wrapper(code, question_id, test_cases)
    
    method_name = function_signature['method_name']
    return_type = function_signature['return_type']
    parameters = function_signature['parameters']
    
    # Generate parameter declarations
    param_declarations = []
    for param in parameters:
        param_declarations.append(f"{param['type']} {param['name']}")
    
    # Generate test case data with proper types
    test_data = generate_typed_test_data(test_cases, parameters, return_type, method_name)
    
    # Generate includes based on detected types
    includes = generate_necessary_includes(parameters, return_type)
    
    # Generate data structure definitions
    data_structures = generate_data_structures(parameters, return_type)
    
    wrapper_code = f'''{includes}

{data_structures}

{code}

int main() {{
    Solution solution;
    int passed = 0;
    int total = {len(test_cases)};
    
    cout << "=== Test Cases for Problem {question_id} ===" << endl;
    cout << "Method: {method_name}({', '.join(param_declarations)}) -> {return_type}" << endl;
    cout << "Parameters detected: {len(parameters)}" << endl;
    '''
    
    for i, param in enumerate(parameters):
        wrapper_code += f'''    cout << "  {i+1}. {param['type']} {param['name']}" << endl;
    '''
    
    wrapper_code += f'''    cout << endl;
    
    {test_data}
    
    cout << "Result: " << passed << "/" << total << " test cases passed" << endl;
    cout << "Function signature: {return_type} {method_name}({', '.join(param_declarations)})" << endl;
    return 0;
}}'''
    
    return wrapper_code

def generate_necessary_includes(parameters, return_type):
    """Generate necessary #include statements based on detected types"""
    includes = set(['<iostream>', '<vector>', '<string>'])
    
    # Check parameters and return type for additional includes
    all_types = [return_type] + [param['type'] for param in parameters]
    
    for type_str in all_types:
        if 'map' in type_str or 'unordered_map' in type_str:
            includes.add('<map>')
            includes.add('<unordered_map>')
        if 'set' in type_str or 'unordered_set' in type_str:
            includes.add('<set>')
            includes.add('<unordered_set>')
        if 'queue' in type_str or 'priority_queue' in type_str:
            includes.add('<queue>')
        if 'stack' in type_str:
            includes.add('<stack>')
        if 'algorithm' in type_str or 'sort' in type_str or 'find' in type_str:
            includes.add('<algorithm>')
        if 'sstream' in type_str or 'stringstream' in type_str:
            includes.add('<sstream>')
        if 'ListNode' in type_str or 'TreeNode' in type_str:
            # These are custom structures, no additional includes needed
            pass
    
    # Convert to sorted list and format
    include_list = sorted(list(includes))
    return '\n'.join([f'#include {inc}' for inc in include_list]) + '\nusing namespace std;'

def generate_data_structures(parameters, return_type):
    """Generate necessary data structure definitions"""
    all_types = [return_type] + [param['type'] for param in parameters]
    
    structures = []
    
    # Check if ListNode is needed
    if any('ListNode' in type_str for type_str in all_types):
        structures.append('''struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};''')
    
    # Check if TreeNode is needed
    if any('TreeNode' in type_str for type_str in all_types):
        structures.append('''struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};''')
    
    return '\n\n'.join(structures) if structures else ''

def generate_typed_test_data(test_cases, parameters, return_type, method_name):
    """Generate properly typed test case execution code with enhanced features"""
    test_code = ""
    
    for i, test_case in enumerate(test_cases):
        test_code += f'''    // Test Case {i+1}
    cout << "Test Case {i+1}:" << endl;
    '''
        
        # Generate parameter values with proper types and unique variable names
        param_values = []
        for param in parameters:
            param_name = param['name']
            param_type = param['type']
            unique_param_name = f"{param_name}_{i+1}"  # Make variable names unique per test case
            
            if param_name in test_case['input_params']:
                value = test_case['input_params'][param_name]
                
                # Generate proper C++ variable declarations
                if param_type == 'vector<int>' or param_type == 'vector<int>&':
                    test_code += f'    vector<int> {unique_param_name} = {{{", ".join(map(str, value))}}};\n'
                elif param_type == 'vector<string>' or param_type == 'vector<string>&':
                    test_code += f'    vector<string> {unique_param_name} = {{'
                    for j, v in enumerate(value):
                        test_code += f'"{v}"'
                        if j < len(value) - 1:
                            test_code += ', '
                    test_code += f'}};\n'
                elif param_type == 'vector<char>' or param_type == 'vector<char>&':
                    test_code += f'    vector<char> {unique_param_name} = {{'
                    for j, v in enumerate(value):
                        test_code += f"'{v}'"
                        if j < len(value) - 1:
                            test_code += ', '
                    test_code += f'}};\n'
                elif param_type == 'string':
                    test_code += f'    string {unique_param_name} = "{value}";\n'
                elif param_type == 'int':
                    test_code += f'    int {unique_param_name} = {value};\n'
                elif param_type == 'bool':
                    test_code += f'    bool {unique_param_name} = {str(value).lower()};\n'
                elif param_type == 'ListNode*':
                    test_code += f'    // ListNode* {unique_param_name} = createListNode({value});\n'
                    test_code += f'    ListNode* {unique_param_name} = nullptr; // TODO: Implement ListNode creation\n'
                elif param_type == 'TreeNode*':
                    test_code += f'    // TreeNode* {unique_param_name} = createTreeNode({value});\n'
                    test_code += f'    TreeNode* {unique_param_name} = nullptr; // TODO: Implement TreeNode creation\n'
                else:
                    test_code += f'    // {param_type} {unique_param_name} = {value};\n'
                    test_code += f'    // Unsupported type: {param_type}\n'
                
                param_values.append(unique_param_name)
        
        # Generate function call with proper return type handling
        param_list = ', '.join(param_values)
        
        if return_type == 'void':
            test_code += f'    solution.{method_name}({param_list});\n'
            test_code += f'    // void function - no return value to check\n'
        else:
            test_code += f'    {return_type} result_{i+1} = solution.{method_name}({param_list});\n'
        
        # Generate expected output with proper type handling
        expected = test_case['expected_output']
        if return_type != 'void':
            if return_type == 'vector<int>':
                test_code += f'    vector<int> expected_{i+1} = {{{", ".join(map(str, expected))}}};\n'
            elif return_type == 'vector<string>':
                test_code += f'    vector<string> expected_{i+1} = {{'
                for j, v in enumerate(expected):
                    test_code += f'"{v}"'
                    if j < len(expected) - 1:
                        test_code += ', '
                test_code += f'}};\n'
            elif return_type == 'vector<char>':
                test_code += f'    vector<char> expected_{i+1} = {{'
                for j, v in enumerate(expected):
                    test_code += f"'{v}'"
                    if j < len(expected) - 1:
                        test_code += ', '
                test_code += f'}};\n'
            elif return_type == 'string':
                test_code += f'    string expected_{i+1} = "{expected}";\n'
            elif return_type == 'int':
                test_code += f'    int expected_{i+1} = {expected};\n'
            elif return_type == 'bool':
                test_code += f'    bool expected_{i+1} = {str(expected).lower()};\n'
            elif return_type == 'ListNode*':
                test_code += f'    // ListNode* expected_{i+1} = createListNode({expected});\n'
                test_code += f'    ListNode* expected_{i+1} = nullptr; // TODO: Implement ListNode comparison\n'
            elif return_type == 'TreeNode*':
                test_code += f'    // TreeNode* expected_{i+1} = createTreeNode({expected});\n'
                test_code += f'    TreeNode* expected_{i+1} = nullptr; // TODO: Implement TreeNode comparison\n'
            else:
                test_code += f'    // Expected: {expected}\n'
                test_code += f'    // Unsupported return type: {return_type}\n'
        
        # Generate output display with very simple approach
        test_code += '''
    cout << "  Input: ";
    '''
        
        # Print input parameters one by one
        for j, param in enumerate(parameters):
            if param['name'] in test_case['input_params']:
                param_name = param['name']
                unique_param_name = f"{param_name}_{i+1}"
                if j > 0:
                    test_code += 'cout << ", ";'
                if param['type'] == 'string':
                    test_code += f'cout << "{param_name} = \\"" << {unique_param_name} << "\\"";'
                elif param['type'] in ['int', 'bool']:
                    test_code += f'cout << "{param_name} = " << {unique_param_name};'
                else:
                    test_code += f'cout << "{param_name} = [complex type]";'
        
        # Handle expected output properly
        expected_str = str(test_case['expected_output'])
        if expected_str == 'True':
            expected_str = 'true'
        elif expected_str == 'False':
            expected_str = 'false'
        
        test_code += f'''
    cout << endl;
    cout << "  Expected: {expected_str}" << endl;
    cout << "  Your Output: ";
    '''
        
        # Generate result display based on return type
        if return_type == 'void':
            test_code += f'''
    cout << "void (no return value)" << endl;
    '''
        elif return_type == 'vector<int>':
            test_code += f'''
    cout << "[";
    for (int j = 0; j < result_{i+1}.size(); j++) {{
        cout << result_{i+1}[j];
        if (j < result_{i+1}.size() - 1) cout << ",";
    }}
    cout << "]" << endl;
    '''
        elif return_type == 'vector<string>':
            test_code += f'''
    cout << "[";
    for (int j = 0; j < result_{i+1}.size(); j++) {{
        cout << "\\"" << result_{i+1}[j] << "\\"";
        if (j < result_{i+1}.size() - 1) cout << ",";
    }}
    cout << "]" << endl;
    '''
        elif return_type == 'vector<char>':
            test_code += f'''
    cout << "[";
    for (int j = 0; j < result_{i+1}.size(); j++) {{
        cout << "\\"" << result_{i+1}[j] << "\\"";
        if (j < result_{i+1}.size() - 1) cout << ",";
    }}
    cout << "]" << endl;
    '''
        elif return_type == 'string':
            test_code += f'    cout << "\\"" << result_{i+1} << "\\"" << endl;\n'
        elif return_type == 'int':
            test_code += f'    cout << result_{i+1} << endl;\n'
        elif return_type == 'bool':
            test_code += f'    cout << (result_{i+1} ? "true" : "false") << endl;\n'
        elif return_type == 'ListNode*':
            test_code += f'''
    // TODO: Implement ListNode printing
    cout << "ListNode* (not implemented)" << endl;
    '''
        elif return_type == 'TreeNode*':
            test_code += f'''
    // TODO: Implement TreeNode printing
    cout << "TreeNode* (not implemented)" << endl;
    '''
        else:
            test_code += f'    cout << "Unsupported type: {return_type}" << endl;\n'
        
        # Generate result checking
        if return_type == 'void':
            test_code += f'''
    // void function - cannot check result
    cout << "  Note: void function - result cannot be verified" << endl;
    '''
        else:
            test_code += f'''
    bool is_correct_{i+1} = false;
    '''
            
            if return_type == 'vector<int>':
                test_code += f'    is_correct_{i+1} = (result_{i+1} == expected_{i+1});\n'
            elif return_type == 'vector<string>':
                test_code += f'    is_correct_{i+1} = (result_{i+1} == expected_{i+1});\n'
            elif return_type == 'vector<char>':
                test_code += f'    is_correct_{i+1} = (result_{i+1} == expected_{i+1});\n'
            elif return_type in ['string', 'int', 'bool']:
                test_code += f'    is_correct_{i+1} = (result_{i+1} == expected_{i+1});\n'
            elif return_type == 'ListNode*':
                test_code += f'''
    // TODO: Implement ListNode comparison
    is_correct_{i+1} = false; // Not implemented
    '''
            elif return_type == 'TreeNode*':
                test_code += f'''
    // TODO: Implement TreeNode comparison
    is_correct_{i+1} = false; // Not implemented
    '''
            else:
                test_code += f'    is_correct_{i+1} = false; // Unsupported type\n'
            
            test_code += f'''
    if (is_correct_{i+1}) {{
        cout << "  ✓ PASSED" << endl;
        passed++;
    }} else {{
        cout << "  ✗ FAILED" << endl;
    }}
    '''
        
        test_code += f'''
    cout << endl;
    '''
    
    return test_code

def generate_fallback_wrapper(code, question_id, test_cases):
    """Generate a basic wrapper when no function signature is available"""
    print("Generating fallback wrapper")
    
    wrapper_code = f'''#include <iostream>
#include <vector>
#include <string>
using namespace std;

{code}

int main() {{
    Solution solution;
    int total = {len(test_cases)};
    
    cout << "=== Test Cases for Problem {question_id} (Fallback Mode) ===" << endl;
    cout << "Note: Function signature not detected, using basic testing" << endl;
    cout << endl;
    
    for (int i = 0; i < total; i++) {{
        cout << "Test Case " << (i + 1) << ":" << endl;
        cout << "  Input: {test_cases[0]['raw_input'] if test_cases else 'N/A'}" << endl;
        cout << "  Note: Cannot execute without proper signature detection" << endl;
        cout << endl;
    }}
    
    cout << "Result: " << total << " test cases displayed (fallback mode)" << endl;
    return 0;
}}'''
    
    return wrapper_code


