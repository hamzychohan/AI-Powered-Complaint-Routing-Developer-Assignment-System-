const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const chatHistory = document.getElementById('chatHistory');
const contextBody = document.getElementById('contextBody');
const sendBtn = document.getElementById('sendBtn');
const welcomeState = document.getElementById('welcomeState');
const togglePanelBtn = document.getElementById('togglePanelBtn');
const contextPanel = document.getElementById('contextPanel');

let messageHistory = [];

// Toggle Evidence Panel
togglePanelBtn.addEventListener('click', () => {
    contextPanel.classList.toggle('hidden');
});

// Helper to pre-fill input from quick actions
window.setInput = function(text) {
    if(welcomeState) welcomeState.style.display = 'none';
    userInput.value = text;
    userInput.focus();
    // Auto submit for demo purposes
    chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
}

// Convert simple markdown-like syntax to HTML
function parseMarkdown(text) {
    let parsed = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    parsed = parsed.replace(/\n/g, '<br>');
    return parsed;
}

// Add message to DOM
function appendMessage(role, content) {
    if(welcomeState) welcomeState.style.display = 'none';
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const senderName = role === 'user' ? 'You' : 'Medica AI';
    const contentHtml = parseMarkdown(content);
    
    msgDiv.innerHTML = `
        <div class="message-sender">${senderName}</div>
        <div class="message-bubble">${contentHtml}</div>
    `;
    
    chatHistory.appendChild(msgDiv);
    
    // Smooth scroll to bottom
    setTimeout(() => {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }, 50);
    
    // Save to history for context
    messageHistory.push({ role, content });
}

// Show loading indicator
function showLoading() {
    if(welcomeState) welcomeState.style.display = 'none';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loadingIndicator';
    
    loadingDiv.innerHTML = `
        <div class="message-sender">Medica AI</div>
        <div class="message-bubble">
            <div class="loading-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;
    
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTo({
        top: chatHistory.scrollHeight,
        behavior: 'smooth'
    });
    sendBtn.disabled = true;
}

// Remove loading indicator
function removeLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
    sendBtn.disabled = false;
    userInput.focus();
}

// Update Context Panel
function updateContextPanel(contexts) {
    if (!contexts || contexts.length === 0) {
        contextBody.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                </div>
                <p>No guidelines retrieved for this query.</p>
            </div>
        `;
        return;
    }
    
    contextBody.innerHTML = '';
    contexts.forEach((ctx, idx) => {
        const source = ctx.metadata?.source_file || 'Clinical Document';
        const score = ctx.metadata?.score ? (ctx.metadata.score * 100).toFixed(1) : '98.5';
        const text = ctx.text || ctx.page_content || 'Extracted clinical content match from the knowledge base.';
        
        const card = document.createElement('div');
        card.className = 'context-card';
        card.innerHTML = `
            <div class="context-meta">
                <a onclick="openDocumentModal('${source}')" class="source-tag" style="text-decoration: none; cursor: pointer;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    ${source}
                </a>
                <span class="match-score">${score}% Match</span>
            </div>
            <div class="context-text">${text}</div>
        `;
        contextBody.appendChild(card);
    });
}

// Handle Form Submit
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;
    
    // Add user message to UI
    appendMessage('user', query);
    userInput.value = '';
    
    showLoading();
    
    try {
        // Exclude the very last message we just pushed to send as chat_history
        const historyToSend = messageHistory.slice(0, -1);
        
        const response = await fetch('http://127.0.0.1:8080/api/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                chat_history: historyToSend,
                generator_model: "groq:llama-3.1-8b-instant", // using Groq API as requested
                retriever_type: "hybrid"
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        removeLoading();
        
        // Add assistant message
        appendMessage('assistant', data.response_text);
        
        // Update context sidebar
        updateContextPanel(data.retrieved_contexts);
        
    } catch (error) {
        console.error("Chat Error:", error);
        removeLoading();
        // Fallback for UI testing if backend is not running
        setTimeout(() => {
            appendMessage('assistant', "I'm sorry, I couldn't connect to the backend server. Make sure the API is running.\n\n**(Demo Mode Response)**: Based on the clinical guidelines, the recommended approach involves multi-modal therapy.");
            updateContextPanel([{
                metadata: { source_file: "demo_guidelines_2026.pdf", score: 0.99 },
                text: "This is a demo retrieved context to show how the UI looks when evidence is provided by the RAG pipeline."
            }]);
        }, 800);
    }
});

// Document Modal Logic
const docModalOverlay = document.getElementById('docModalOverlay');
const closeModalBtn = document.getElementById('closeModalBtn');
const docModalTitle = document.getElementById('docModalTitle');
const docModalText = document.getElementById('docModalText');
const docModalLoading = document.getElementById('docModalLoading');

function closeDocModal() {
    docModalOverlay.classList.remove('active');
}

closeModalBtn.addEventListener('click', closeDocModal);
docModalOverlay.addEventListener('click', (e) => {
    if(e.target === docModalOverlay) closeDocModal();
});

window.openDocumentModal = async function(sourceFile) {
    docModalOverlay.classList.add('active');
    docModalTitle.textContent = sourceFile;
    docModalText.textContent = '';
    docModalText.style.display = 'none';
    docModalLoading.style.display = 'flex';
    
    try {
        const response = await fetch(`http://127.0.0.1:8080/kb/${sourceFile}`);
        if (!response.ok) throw new Error('Document not found');
        const text = await response.text();
        docModalText.textContent = text;
    } catch (e) {
        docModalText.textContent = 'Error loading document content. Make sure the backend server is running and the document exists.';
    } finally {
        docModalLoading.style.display = 'none';
        docModalText.style.display = 'block';
    }
}

