// --- DOM Element References ---
const analyzeBtn = document.getElementById('analyze-btn');
const repoUrlInput = document.getElementById('repo-url');
const statusMessage = document.getElementById('status-message');
const loadingSpinner = document.getElementById('loading-spinner');
const chatInput = document.getElementById('chat-input');
const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');

// Views
const initialView = document.getElementById('initial-view');
const chatView = document.getElementById('chat-view');
const thinkingIndicator = document.getElementById('thinking-indicator');

const BACKEND_URL = 'http://127.0.0.1:8000';

// ---- Event Listeners ----
analyzeBtn.addEventListener('click', handleAnalyzeRepo);
chatForm.addEventListener('submit', handleSendMessage);

// ---- Functions ----

async function handleAnalyzeRepo() {
    const url = repoUrlInput.value.trim();
    if (!url) {
        statusMessage.textContent = 'Please enter a valid GitHub URL.';
        return;
    }

    statusMessage.textContent = 'Analyzing repository... This may take a few minutes for larger repos.';
    analyzeBtn.disabled = true;
    repoUrlInput.disabled = true;

    try {
        const response = await fetch(`${BACKEND_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to analyze repository.');
        }

        // Switch to the main chat view
        initialView.classList.add('hidden');
        chatView.classList.remove('hidden');
        addMessageToChat('AI', 'Repository analyzed. You can now ask questions about the code.');

    } catch (error) {
        console.error('Error analyzing repo:', error);
        statusMessage.textContent = `Error: ${error.message}`;
    } finally {
        analyzeBtn.disabled = false;
        repoUrlInput.disabled = false;
    }
}

async function handleSendMessage(event) {
    event.preventDefault();
    const question = chatInput.value.trim();
    if (!question) return;

    addMessageToChat('You', question);
    chatInput.value = '';
    
    // Show the "thinking" indicator
    thinkingIndicator.classList.remove('hidden');
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch(`${BACKEND_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'An error occurred.');
        }

        const result = await response.json();
        // Hide the indicator and add the AI's real message
        thinkingIndicator.classList.add('hidden');
        addMessageToChat('AI', result.answer);

    } catch (error) {
        console.error('Error sending message:', error);
        thinkingIndicator.classList.add('hidden');
        addMessageToChat('AI', `Sorry, I encountered an error: ${error.message}`);
    }
}

function addMessageToChat(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    
    if (sender === 'AI') {
        messageElement.classList.add('ai-message');
        // Use marked.parse() to convert markdown to HTML
        messageElement.innerHTML = marked.parse(message);
    } else {
        messageElement.classList.add('user-message');
        messageElement.textContent = message;
    }
    
    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the bottom
}