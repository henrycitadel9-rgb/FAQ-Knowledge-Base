// Retrieval Chat JavaScript

async function sendMessage(message) {
    try {
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        return { answer: 'Sorry, there was an error processing your request.', source: '', confidence: 0 };
    }
}

function escapeHtml(value) {
    if (typeof value !== 'string') {
        return '';
    }
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function addMessage(content, isUser = false) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function buildMatchMeta(match) {
    const metaParts = [];
    if (Array.isArray(match.matched_terms) && match.matched_terms.length) {
        metaParts.push(`Matched on: ${escapeHtml(match.matched_terms.join(', '))}`);
    }
    if (match.source) {
        metaParts.push(`Source: ${escapeHtml(match.source)}`);
    }
    return metaParts.join(' • ');
}

function buildOptionButtons(matches) {
    return matches.map((match, index) => {
        const meta = buildMatchMeta(match);
        return `
            <button class="chat-option-btn" data-question="${escapeHtml(match.question)}">
                <span class="chat-option-kicker">Option ${index + 1}</span>
                <span class="chat-option-title">${escapeHtml(match.question)}</span>
                ${meta ? `<span class="chat-option-meta">${meta}</span>` : ''}
            </button>
        `;
    }).join('');
}

function buildRetrievalResponseHtml(response) {
    let responseHtml = `<p>${escapeHtml(response.answer)}</p>`;

    if (response.response_type === 'multiple' && Array.isArray(response.matches)) {
        responseHtml += `<div class="chat-options">${buildOptionButtons(response.matches)}</div>`;
    } else if (response.source) {
        responseHtml += `<p class="source">Source: ${escapeHtml(response.source)}</p>`;
    }

    if (response.confidence < 0.5) {
        responseHtml += `<p class="low-confidence">This answer may not be accurate.</p>`;
    }

    return responseHtml;
}

function showTyping() {
    const messagesDiv = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing';
    typingDiv.id = 'typing-indicator';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<p>Thinking...</p>';
    
    typingDiv.appendChild(contentDiv);
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTyping() {
    const typingDiv = document.getElementById('typing-indicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

async function handleOptionSelect(question) {
    const input = document.getElementById('message-input');
    input.value = question;
    await handleSend();
}

async function handleSend() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(`<p>${message}</p>`, true);
    input.value = '';
    
    // Show typing indicator
    showTyping();
    
    // Get response
    const response = await sendMessage(message);
    hideTyping();
    
    // Add bot response
    addMessage(buildRetrievalResponseHtml(response));
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('send-btn').addEventListener('click', handleSend);
    document.getElementById('message-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });
    document.getElementById('chat-messages').addEventListener('click', function(e) {
        const optionButton = e.target.closest('.chat-option-btn');
        if (!optionButton) {
            return;
        }
        handleOptionSelect(optionButton.dataset.question);
    });
});
