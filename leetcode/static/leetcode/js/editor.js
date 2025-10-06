/* LeetCode Editor JavaScript */

// Check if we have daily question data from sessionStorage
let dailyQuestionData = null;
try {
    const stored = sessionStorage.getItem('dailyQuestionData');
    if (stored) {
        dailyQuestionData = JSON.parse(stored);
        // Clear the stored data after reading
        sessionStorage.removeItem('dailyQuestionData');
    }
} catch (e) {
    console.log('No daily question data found');
}

// Current language and question tracking
let currentLanguage = 'cpp';
let currentTheme = 'default';

// Problem data from Django - will be injected by template
let problemsData = window.TEMPLATE_DATA ? window.TEMPLATE_DATA.problems : {};
let currentQuestionId = window.TEMPLATE_DATA ? window.TEMPLATE_DATA.currentQuestionId : '';
let currentTitleSlug = window.TEMPLATE_DATA ? window.TEMPLATE_DATA.currentTitleSlug : '';

// URL constants
const LEETCODE_FETCH_CPP_TEMPLATE_URL = window.TEMPLATE_DATA ? window.TEMPLATE_DATA.fetchCppTemplateUrl : '';
const LEETCODE_COMPILE_URL = window.TEMPLATE_DATA ? window.TEMPLATE_DATA.compileUrl : '';

// Initialize CodeMirror
let codeEditor = null;
let outputPanel = null;
let statusIndicator = null;

// Initialize CodeMirror
function initializeCodeMirror() {
    const editorElement = document.getElementById('codeEditor');
    const initialContent = editorElement.textContent;
    
    // Clear the div content
    editorElement.innerHTML = '';
    
    // Initialize CodeMirror
    codeEditor = CodeMirror(editorElement, {
        value: initialContent,
        mode: getCodeMirrorMode(currentLanguage),
        theme: getCodeMirrorTheme(currentTheme),
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        lineWrapping: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        highlightSelectionMatches: {showToken: /\w/},
        scrollbarStyle: "native",
        extraKeys: {
            "Ctrl-Space": "autocomplete",
            "Ctrl-/": "toggleComment",
            "Ctrl-Enter": function(cm) {
                // Add a new line and indent
                cm.replaceSelection("\n");
                cm.execCommand("indentAuto");
            },
            "Tab": function(cm) {
                if (cm.getMode().name === "null") {
                    cm.execCommand("insertTab");
                } else {
                    if (cm.somethingSelected()) {
                        cm.execCommand("indentMore");
                    } else {
                        cm.execCommand("insertSoftTab");
                    }
                }
            }
        }
    });
    
    // Register custom commands
    codeEditor.setOption("extraKeys", {
        ...codeEditor.getOption("extraKeys"),
        "Ctrl-/": function(cm) {
            toggleComment(cm);
        }
    });
}

// Get CodeMirror mode for language
function getCodeMirrorMode(language) {
    const modeMap = {
        'cpp': 'text/x-c++src',
        'python3': 'python',
        'python': 'python',
        'java': 'text/x-java',
        'javascript': 'javascript'
    };
    return modeMap[language] || 'text/plain';
}

// Get CodeMirror theme
function getCodeMirrorTheme(theme) {
    const themeMap = {
        'default': 'default',
        'monokai': 'monokai',
        'material': 'material',
        'dracula': 'dracula'
    };
    return themeMap[theme] || 'default';
}

// Change theme function
function changeTheme() {
    const themeSelect = document.getElementById('themeSelect');
    currentTheme = themeSelect.value;
    
    if (codeEditor) {
        codeEditor.setOption('theme', getCodeMirrorTheme(currentTheme));
    }
}

// Custom comment toggle function
function toggleComment(cm) {
    const ranges = cm.listSelections();
    const commentTokens = getCommentTokens(cm.getMode().name);
    
    // If no selection, toggle comment on current line
    if (ranges.length === 1 && ranges[0].empty()) {
        const line = cm.getCursor().line;
        const lineText = cm.getLine(line);
        const startOfLine = { line: line, ch: 0 };
        const endOfLine = { line: line, ch: lineText.length };
        
        if (isLineCommented(lineText, commentTokens)) {
            // Uncomment the line
            uncommentLine(cm, startOfLine, endOfLine, commentTokens);
        } else {
            // Comment the line
            commentLine(cm, startOfLine, endOfLine, commentTokens);
        }
    } else {
        // Handle multiple selections or multiline selection
        for (let i = ranges.length - 1; i >= 0; i--) {
            const range = ranges[i];
            const start = range.from();
            const end = range.to();
            
            if (range.empty()) {
                // Single cursor - toggle current line
                const line = start.line;
                const lineText = cm.getLine(line);
                const lineStart = { line: line, ch: 0 };
                const lineEnd = { line: line, ch: lineText.length };
                
                if (isLineCommented(lineText, commentTokens)) {
                    uncommentLine(cm, lineStart, lineEnd, commentTokens);
                } else {
                    commentLine(cm, lineStart, lineEnd, commentTokens);
                }
            } else {
                // Selection - check if all lines are commented
                const allCommented = areAllLinesCommented(cm, start, end, commentTokens);
                
                if (allCommented) {
                    // Uncomment all lines in selection
                    uncommentLines(cm, start, end, commentTokens);
                } else {
                    // Comment all lines in selection
                    commentLines(cm, start, end, commentTokens);
                }
            }
        }
    }
}

// Get comment tokens for different languages
function getCommentTokens(modeName) {
    const tokens = {
        'clike': { single: '//', multiStart: '/*', multiEnd: '*/' },
        'cpp': { single: '//', multiStart: '/*', multiEnd: '*/' },
        'java': { single: '//', multiStart: '/*', multiEnd: '*/' },
        'javascript': { single: '//', multiStart: '/*', multiEnd: '*/' },
        'python': { single: '#', multiStart: null, multiEnd: null },
        'default': { single: '//', multiStart: '/*', multiEnd: '*/' }
    };
    
    return tokens[modeName] || tokens['default'];
}

// Check if a line is commented
function isLineCommented(lineText, tokens) {
    const trimmed = lineText.trim();
    return trimmed.startsWith(tokens.single) || 
           (tokens.multiStart && trimmed.startsWith(tokens.multiStart));
}

// Check if all lines in selection are commented
function areAllLinesCommented(cm, start, end, tokens) {
    const startLine = Math.min(start.line, end.line);
    const endLine = Math.max(start.line, end.line);
    
    for (let line = startLine; line <= endLine; line++) {
        const lineText = cm.getLine(line);
        if (lineText.trim() && !isLineCommented(lineText, tokens)) {
            return false;
        }
    }
    return true;
}

// Comment a single line
function commentLine(cm, start, end, tokens) {
    const lineText = cm.getLine(start.line);
    const indent = lineText.match(/^\s*/)[0];
    const content = lineText.substring(indent.length);
    
    cm.replaceRange(
        indent + tokens.single + ' ' + content,
        start,
        end
    );
}

// Uncomment a single line
function uncommentLine(cm, start, end, tokens) {
    const lineText = cm.getLine(start.line);
    const trimmed = lineText.trim();
    
    if (trimmed.startsWith(tokens.single)) {
        // Remove single line comment
        const commentIndex = lineText.indexOf(tokens.single);
        const beforeComment = lineText.substring(0, commentIndex);
        const afterComment = lineText.substring(commentIndex + tokens.single.length);
        
        // Remove extra space after comment token if present
        const cleanedAfter = afterComment.startsWith(' ') ? afterComment.substring(1) : afterComment;
        
        cm.replaceRange(
            beforeComment + cleanedAfter,
            start,
            end
        );
    } else if (tokens.multiStart && trimmed.startsWith(tokens.multiStart)) {
        // Remove multi-line comment start
        const startIndex = lineText.indexOf(tokens.multiStart);
        const endIndex = lineText.indexOf(tokens.multiEnd);
        
        if (endIndex !== -1) {
            // Single line multi-line comment
            const beforeStart = lineText.substring(0, startIndex);
            const afterEnd = lineText.substring(endIndex + tokens.multiEnd.length);
            cm.replaceRange(beforeStart + afterEnd, start, end);
        }
    }
}

// Comment multiple lines
function commentLines(cm, start, end, tokens) {
    const startLine = Math.min(start.line, end.line);
    const endLine = Math.max(start.line, end.line);
    
    for (let line = startLine; line <= endLine; line++) {
        const lineText = cm.getLine(line);
        if (lineText.trim()) {
            const indent = lineText.match(/^\s*/)[0];
            const content = lineText.substring(indent.length);
            
            cm.replaceRange(
                indent + tokens.single + ' ' + content,
                { line: line, ch: 0 },
                { line: line, ch: lineText.length }
            );
        }
    }
}

// Uncomment multiple lines
function uncommentLines(cm, start, end, tokens) {
    const startLine = Math.min(start.line, end.line);
    const endLine = Math.max(start.line, end.line);
    
    for (let line = startLine; line <= endLine; line++) {
        const lineText = cm.getLine(line);
        if (lineText.trim()) {
            uncommentLine(cm, 
                { line: line, ch: 0 }, 
                { line: line, ch: lineText.length }, 
                tokens
            );
        }
    }
}

// Check if device is mobile
function isMobileDevice() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Auto-apply mobile styles on mobile devices
function applyMobileStyles() {
    if (isMobileDevice()) {
        document.body.classList.add('mobile-device');
        // Ensure output panel is visible
        const outputPanel = document.getElementById('outputPanel');
        if (outputPanel) {
            outputPanel.style.display = 'block';
            outputPanel.style.visibility = 'visible';
        }
    }
}

// Initialize with current question
function initializeEditor() {
    // Apply mobile styles if needed
    applyMobileStyles();
    
    // Initialize CodeMirror first
    initializeCodeMirror();
    
    // If we have daily question data, load it instead
    if (dailyQuestionData) {
        currentQuestionId = dailyQuestionData.frontend_id || '1'; // Use actual daily question ID
        currentTitleSlug = dailyQuestionData.title_slug || '';
        loadQuestion(currentQuestionId);
    } else {
        loadQuestion(currentQuestionId);
    }
}

// Handle window resize (orientation changes on mobile)
window.addEventListener('resize', function() {
    applyMobileStyles();
    if (codeEditor) {
        setTimeout(() => {
            codeEditor.refresh();
        }, 100);
    }
});

function switchQuestion(questionId) {
    currentQuestionId = questionId;
    loadQuestion(questionId);
    
    // Update active button
    document.querySelectorAll('.question-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

function loadQuestion(questionId) {
    let problem;
    
    // Check if we have daily question data
    if (dailyQuestionData && (questionId === dailyQuestionData.frontend_id || questionId === '1')) {
        problem = {
            title: dailyQuestionData.title,
            difficulty: dailyQuestionData.difficulty,
            description: dailyQuestionData.description,
            examples: dailyQuestionData.examples,
            constraints: dailyQuestionData.constraints,
            template: dailyQuestionData.template,
            cppTemplate: dailyQuestionData.cppTemplate || dailyQuestionData.template
        };
        
        // Update header to show it's a daily question
        document.getElementById('problem-title').textContent = dailyQuestionData.title + ' (Daily Challenge)';
    } else {
        problem = problemsData[questionId];
    }
    
    if (!problem) return;
    
    // Update header (title already set for daily questions)
    if (!dailyQuestionData || (questionId !== dailyQuestionData.frontend_id && questionId !== '1')) {
        document.getElementById('problem-title').textContent = problem.title;
    }
    const difficultyBadge = document.getElementById('difficulty-badge');
    difficultyBadge.textContent = problem.difficulty;
    difficultyBadge.className = `difficulty-badge difficulty-${problem.difficulty.toLowerCase()}`;
    
    // Update problem description (handle HTML content)
    const descriptionElement = document.getElementById('problem-description');
    if (problem.description.includes('<')) {
        descriptionElement.innerHTML = problem.description;
    } else {
        descriptionElement.textContent = problem.description;
    }
    
    // Update examples
    const examplesHtml = problem.examples.map((example, index) => `
        <div class="example">
            <strong>Example ${index + 1}:</strong>
            <pre><strong>Input:</strong> ${example.input}
<strong>Output:</strong> ${example.output}
${example.explanation ? `<strong>Explanation:</strong> ${example.explanation}` : ''}</pre>
        </div>
    `).join('');
    document.getElementById('problem-examples').innerHTML = examplesHtml;
    
    // Update constraints
    const constraintsHtml = problem.constraints.map(constraint => `<li>${constraint}</li>`).join('');
    document.getElementById('problem-constraints').innerHTML = constraintsHtml;
    
    // Update code editor with appropriate template based on current language
    if (codeEditor) {
        if (currentLanguage === 'cpp' && problem.cppTemplate) {
            codeEditor.setValue(problem.cppTemplate);
        } else {
            codeEditor.setValue(problem.template);
        }
    }
    
    // If current language is C++ and we don't have a proper C++ template, fetch it from LeetCode
    if (currentLanguage === 'cpp' && (!problem.cppTemplate || problem.cppTemplate.includes('// Your code here'))) {
        fetchCppTemplateFromLeetCode(questionId);
    }
    
    // Reset output
    outputPanel.innerHTML = '<div>Output will appear here...</div>';
    outputPanel.className = 'output-panel';
    statusIndicator.textContent = 'Ready to code';
}

function changeLanguage() {
    const languageSelect = document.getElementById('languageSelect');
    currentLanguage = languageSelect.value;
    console.log('Language changed to:', currentLanguage);
    
    // Update CodeMirror mode
    if (codeEditor) {
        codeEditor.setOption('mode', getCodeMirrorMode(currentLanguage));
    }
    
    // Check if we have daily question data
    let problem;
    if (dailyQuestionData && (currentQuestionId === dailyQuestionData.frontend_id || currentQuestionId === '1')) {
        problem = {
            title: dailyQuestionData.title,
            difficulty: dailyQuestionData.difficulty,
            description: dailyQuestionData.description,
            examples: dailyQuestionData.examples,
            constraints: dailyQuestionData.constraints,
            template: dailyQuestionData.template,
            cppTemplate: dailyQuestionData.cppTemplate || dailyQuestionData.template
        };
    } else {
        problem = problemsData[currentQuestionId];
    }
    
    if (problem) {
        updateCodeTemplate(problem);
    }
    
    // If switching to C++ and we don't have a C++ template, try to fetch it from LeetCode
    if (currentLanguage === 'cpp' && problem && (!problem.cppTemplate || problem.cppTemplate.includes('// Your code here'))) {
        fetchCppTemplateFromLeetCode(currentQuestionId);
    }
}

function fetchCppTemplateFromLeetCode(questionId, titleSlug = null) {
    console.log(`Fetching C++ template for question ${questionId} from LeetCode...`);
    statusIndicator.textContent = 'Fetching C++ template from LeetCode...';
    statusIndicator.className = 'status running';
    
    const requestData = {
        question_id: questionId
    };
    
    // Use title_slug if available for more efficient fetching
    if (titleSlug || currentTitleSlug || (dailyQuestionData && dailyQuestionData.title_slug)) {
        requestData.title_slug = titleSlug || currentTitleSlug || dailyQuestionData.title_slug;
    }
    
    fetch(LEETCODE_FETCH_CPP_TEMPLATE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('Successfully fetched C++ template from LeetCode');
            
            // Update the problem data with the fetched C++ template
            if (problemsData[questionId]) {
                problemsData[questionId].cppTemplate = result.cpp_template;
            }
            
            // If current language is C++, update the editor
            if (currentLanguage === 'cpp' && codeEditor) {
                codeEditor.setValue(result.cpp_template);
            }
            
            // Show appropriate success message
            if (result.is_generic) {
                statusIndicator.textContent = 'Generic C++ template created (LeetCode template not available)';
                console.log('Generic template created:', result.message);
            } else {
                statusIndicator.textContent = 'C++ template loaded from LeetCode';
            }
            statusIndicator.className = 'status success';
            
            // Reset status after 4 seconds (longer for generic template message)
            setTimeout(() => {
                statusIndicator.textContent = 'Ready to code';
                statusIndicator.className = '';
            }, 4000);
        } else {
            console.log('Failed to fetch C++ template:', result.error);
            statusIndicator.textContent = 'Could not fetch C++ template from LeetCode';
            statusIndicator.className = 'status error';
            
            // Reset status after 3 seconds
            setTimeout(() => {
                statusIndicator.textContent = 'Ready to code';
                statusIndicator.className = '';
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error fetching C++ template:', error);
        statusIndicator.textContent = 'Error fetching C++ template';
        statusIndicator.className = 'status error';
        
        // Reset status after 3 seconds
        setTimeout(() => {
            statusIndicator.textContent = 'Ready to code';
            statusIndicator.className = '';
        }, 3000);
    });
}

function updateCodeTemplate(problem) {
    if (codeEditor) {
        if (currentLanguage === 'cpp' && problem.cppTemplate && !problem.cppTemplate.includes('// Your code here')) {
            codeEditor.setValue(problem.cppTemplate);
        } else {
            codeEditor.setValue(problem.template);
        }
    }
}

function runCode() {
    const code = codeEditor ? codeEditor.getValue() : '';
    const language = document.getElementById('languageSelect').value;
    console.log('Running code with language:', language);
    console.log('Code preview:', code.substring(0, 200) + '...');
    const input = '';
    
    if (!code.trim()) {
        outputPanel.innerHTML = '<div style="color: #e74c3c;">Please enter some code to run</div>';
        outputPanel.className = 'output-panel error has-content';
        return;
    }
    
    statusIndicator.textContent = 'Running...';
    statusIndicator.className = 'status running';
    
    // Make AJAX request to compile endpoint
    fetch(LEETCODE_COMPILE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            code: code,
            language: language,
            input: input,
            question_id: currentQuestionId,
            title_slug: dailyQuestionData ? dailyQuestionData.title_slug : currentTitleSlug
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            let output = '';
            if (result.output) {
                output += `<div style="color: #27ae60;"><strong>Output:</strong><br><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; white-space: pre-wrap;">${result.output}</pre></div>`;
            }
            if (result.memory || result.cpuTime) {
                output += `<div style="color: #7f8c8d; font-size: 0.9em;"><strong>Stats:</strong> Memory: ${result.memory || 'N/A'}, CPU Time: ${result.cpuTime || 'N/A'}</div>`;
            }
            outputPanel.innerHTML = output || '<div>Code executed successfully (no output)</div>';
            outputPanel.className = 'output-panel success has-content';
            statusIndicator.textContent = 'Success';
            statusIndicator.className = 'status success';
        } else {
            let errorMessage = result.error;
            if (result.error_type === 'compilation_error') {
                errorMessage = `<strong>Compilation Error:</strong><br>${result.error}`;
            } else if (result.error_type === 'runtime_error') {
                errorMessage = `<strong>Runtime Error:</strong><br>${result.error}`;
            } else if (result.error_type === 'api_error') {
                errorMessage = `<strong>API Error:</strong><br>${result.error}`;
            }
            outputPanel.innerHTML = `<div style="color: #e74c3c;">${errorMessage}</div>`;
            outputPanel.className = 'output-panel error has-content';
            statusIndicator.textContent = 'Error';
            statusIndicator.className = 'status error';
        }
    })
    .catch(error => {
        outputPanel.innerHTML = `<div style="color: #e74c3c;"><strong>Network Error:</strong> ${error.message}</div>`;
        outputPanel.className = 'output-panel error has-content';
        statusIndicator.textContent = 'Error';
        statusIndicator.className = 'status error';
    });
}

function simulateCodeExecution(code) {
    // Simple simulation - in reality, this would be handled by a backend
    if (code.includes('twoSum')) {
        return '[0,1]\n[1,2]';
    } else if (code.includes('addTwoNumbers')) {
        return '[7,0,8]';
    } else if (code.includes('lengthOfLongestSubstring')) {
        return '3\n1';
    }
    return 'Code executed successfully';
}

function simulateSubmission(code) {
    // Simulate test case results
    const testCases = {
        '1': { // Two Sum
            passed: code.includes('return') && code.includes('['),
            time: Math.floor(Math.random() * 50) + 20,
            memory: (Math.random() * 2 + 1).toFixed(1),
            error: 'Expected [0,1] but got [1,0]'
        },
        '2': { // Add Two Numbers
            passed: code.includes('ListNode') && code.includes('return'),
            time: Math.floor(Math.random() * 100) + 30,
            memory: (Math.random() * 3 + 2).toFixed(1),
            error: 'Expected [7,0,8] but got [8,0,7]'
        },
        '3': { // Longest Substring
            passed: code.includes('return') && code.includes('max'),
            time: Math.floor(Math.random() * 80) + 25,
            memory: (Math.random() * 2.5 + 1.5).toFixed(1),
            error: 'Expected 3 but got 2'
        }
    };
    
    return testCases[currentQuestionId] || { passed: false, error: 'Unknown problem' };
}

function toggleMobileView() {
    const body = document.body;
    const mobileBtn = document.getElementById('mobileBtn');
    const isMobileMode = body.classList.contains('mobile-mode');
    
    if (isMobileMode) {
        // Exit mobile mode
        body.classList.remove('mobile-mode');
        mobileBtn.innerHTML = '📱 Mobile';
        mobileBtn.title = 'Switch to Mobile View';
    } else {
        // Enter mobile mode
        body.classList.add('mobile-mode');
        mobileBtn.innerHTML = '💻 Desktop';
        mobileBtn.title = 'Switch to Desktop View';
    }
    
    // Refresh CodeMirror to ensure proper scrolling in mobile mode
    if (codeEditor) {
        setTimeout(() => {
            codeEditor.refresh();
            codeEditor.focus();
        }, 100);
    }
}

function toggleFullscreen() {
    const mainContainer = document.querySelector('.main-container');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const isFullscreen = mainContainer.classList.contains('fullscreen-mode');
    
    if (isFullscreen) {
        // Exit fullscreen
        mainContainer.classList.remove('fullscreen-mode');
        fullscreenBtn.innerHTML = '⛶ Full Screen';
        fullscreenBtn.title = 'Enter Full Screen';
    } else {
        // Enter fullscreen
        mainContainer.classList.add('fullscreen-mode');
        fullscreenBtn.innerHTML = '⛷ Exit Full Screen';
        fullscreenBtn.title = 'Exit Full Screen';
    }
}

function toggleOutputPanel() {
    const outputPanel = document.getElementById('outputPanel');
    const outputBtn = document.getElementById('outputToggleBtn');
    const isHidden = outputPanel.classList.contains('hidden');
    const isCollapsed = outputPanel.classList.contains('collapsed');
    
    if (isHidden) {
        // Show output panel
        outputPanel.classList.remove('hidden');
        outputBtn.innerHTML = '📋 Hide Output';
        outputBtn.title = 'Hide Output Panel';
    } else if (isCollapsed) {
        // Expand output panel
        outputPanel.classList.remove('collapsed');
        outputBtn.innerHTML = '📋 Hide Output';
        outputBtn.title = 'Hide Output Panel';
    } else {
        // Collapse output panel
        outputPanel.classList.add('collapsed');
        outputBtn.innerHTML = '📋 Show Output';
        outputBtn.title = 'Show Output Panel';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    outputPanel = document.getElementById('outputPanel');
    statusIndicator = document.getElementById('status');
    
    // Initialize editor
    initializeEditor();
});
