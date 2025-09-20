from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import json
import requests
import re
from bs4 import BeautifulSoup

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
                    'template': f'''def {question.get('titleSlug', 'solution').replace('-', '_')}():
    # Today's LeetCode Daily Challenge: {question.get('title', 'Daily Question')}
    # Difficulty: {question.get('difficulty', 'Medium')}
    # Acceptance Rate: {question.get('acRate', 0)}%
    # Visit: {f"https://leetcode.com{question_data.get('link', '')}"}
    
    # Your code here
    pass

# Test your solution on LeetCode!'''
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
        daily_question_data = {
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'date': '2024-12-20',
            'description': '<p>Given an array of integers <code>nums</code> and an integer <code>target</code>, return indices of the two numbers such that they add up to target.</p><p><strong>Test HTML:</strong> <em>This should be italic</em> and <code>this should be code</code></p>',
            'examples': [
                {
                    'input': 'nums = [2,7,11,15], target = 9',
                    'output': '[0,1]',
                    'explanation': 'Because nums[0] + nums[1] == 9, we return [0, 1].'
                }
            ],
            'constraints': [
                '2 ≤ nums.length ≤ 10⁴',
                '-10⁹ ≤ nums[i] ≤ 10⁹',
                '-10⁹ ≤ target ≤ 10⁹'
            ],
            'template': '''def twoSum(nums, target):
        # Your code here
        pass

# Test cases
print(twoSum([2,7,11,15], 9))  # Expected: [0,1]'''
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

def question_editor(request, question_id=None):
    """Question editor page for coding problems"""
    # Check if this is a daily question request
    is_daily = request.GET.get('daily') == 'true'
    
    # Get question_id from URL parameter if not in path
    if not question_id:
        question_id = request.GET.get('q', '1')
    
    # Define problem data
    problems = {
        '1': {
            'title': 'Two Sum',
            'difficulty': 'Easy',
            'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
            'examples': [
                {
                    'input': 'nums = [2,7,11,15], target = 9',
                    'output': '[0,1]',
                    'explanation': 'Because nums[0] + nums[1] == 9, we return [0, 1].'
                },
                {
                    'input': 'nums = [3,2,4], target = 6',
                    'output': '[1,2]',
                    'explanation': ''
                }
            ],
            'constraints': [
                '2 ≤ nums.length ≤ 10⁴',
                '-10⁹ ≤ nums[i] ≤ 10⁹',
                '-10⁹ ≤ target ≤ 10⁹',
                'Only one valid answer exists.'
            ],
            'template': '''def twoSum(nums, target):
    # Your code here
    pass

# Test cases
print(twoSum([2,7,11,15], 9))  # Expected: [0,1]
print(twoSum([3,2,4], 6))      # Expected: [1,2]'''
        },
        '2': {
            'title': 'Add Two Numbers',
            'difficulty': 'Medium',
            'description': 'You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.',
            'examples': [
                {
                    'input': 'l1 = [2,4,3], l2 = [5,6,4]',
                    'output': '[7,0,8]',
                    'explanation': '342 + 465 = 807.'
                }
            ],
            'constraints': [
                'The number of nodes in each linked list is in the range [1, 100].',
                '0 ≤ Node.val ≤ 9',
                'It is guaranteed that the list represents a number that does not have leading zeros.'
            ],
            'template': '''class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def addTwoNumbers(l1, l2):
    # Your code here
    pass

# Test cases would go here'''
        },
        '3': {
            'title': 'Longest Substring Without Repeating Characters',
            'difficulty': 'Medium',
            'description': 'Given a string s, find the length of the longest substring without repeating characters.',
            'examples': [
                {
                    'input': 's = "abcabcbb"',
                    'output': '3',
                    'explanation': 'The answer is "abc", with the length of 3.'
                },
                {
                    'input': 's = "bbbbb"',
                    'output': '1',
                    'explanation': 'The answer is "b", with the length of 1.'
                }
            ],
            'constraints': [
                '0 ≤ s.length ≤ 5 * 10⁴',
                's consists of English letters, digits, symbols and spaces.'
            ],
            'template': '''def lengthOfLongestSubstring(s):
    # Your code here
    pass

# Test cases
print(lengthOfLongestSubstring("abcabcbb"))  # Expected: 3
print(lengthOfLongestSubstring("bbbbb"))     # Expected: 1'''
        }
    }
    
    
    problem = problems.get(question_id)
    if not problem:
        return HttpResponse("Problem not found", status=404)
    
    context = {
        'problems': problems,
        'current_problem': problem,
        'current_question_id': question_id,
        'is_daily': is_daily
    }
    return render(request, 'question_editor.html', context)
