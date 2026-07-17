// AI Chat JavaScript

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function sendMessage(message) {
    try {
        const response = await fetch('/api/chat/ai-message', {
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

function buildOptionButtons(matches) {
    return matches.map((match, index) => {
        const metaParts = [];
        if (Array.isArray(match.matched_terms) && match.matched_terms.length) {
            metaParts.push(`Matched on: ${escapeHtml(match.matched_terms.join(', '))}`);
        }
        if (match.source) {
            metaParts.push(`Source: ${escapeHtml(match.source)}`);
        }
        const meta = metaParts.join(' • ');
        return `
            <button class="chat-option-btn" data-question="${escapeHtml(match.question)}">
                <span class="chat-option-kicker">Option ${index + 1}</span>
                <span class="chat-option-title">${escapeHtml(match.question)}</span>
                ${meta ? `<span class="chat-option-meta">${meta}</span>` : ''}
            </button>
        `;
    }).join('');
}

function buildAiResponseHtml(response) {
    let responseHtml = `<p>${escapeHtml(response.answer)}</p>`;

    if (response.response_type === 'disambiguation' && Array.isArray(response.matches)) {
        responseHtml += `<div class="chat-options">${buildOptionButtons(response.matches)}</div>`;
    } else if (response.source) {
        responseHtml += `<p class="source">Source: ${escapeHtml(response.source)}</p>`;
    }

    if (response.confidence < 0.5) {
        responseHtml += `<p class="low-confidence">I may need a more specific dataset-backed question to answer this accurately.</p>`;
    }

    return responseHtml;
}

async function handleOptionSelect(question) {
    const input = document.getElementById('message-input');
    input.value = question;
    await handleSend();
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

function clearChat() {
    const messagesDiv = document.getElementById('chat-messages');
    const firstMessage = messagesDiv.firstElementChild;
    messagesDiv.innerHTML = '';
    if (firstMessage) {
        messagesDiv.appendChild(firstMessage);
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await transcribeAudio(audioBlob);
            
            // Stop all tracks to release microphone
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        const voiceBtn = document.getElementById('voice-btn');
        voiceBtn.textContent = '⏹️';
        voiceBtn.title = 'Stop Recording';
        voiceBtn.classList.add('recording');
        
        // Show recording indicator
        showRecordingIndicator();
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Could not access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        const voiceBtn = document.getElementById('voice-btn');
        voiceBtn.textContent = '🎤';
        voiceBtn.title = 'Voice Input';
        voiceBtn.classList.remove('recording');
        
        // Hide recording indicator
        hideRecordingIndicator();
    }
}

function showRecordingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message user-message recording';
    indicatorDiv.id = 'recording-indicator';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<p>🎤 Listening... Click stop when finished.</p>';

    indicatorDiv.appendChild(contentDiv);
    messagesDiv.appendChild(indicatorDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideRecordingIndicator() {
    const indicator = document.getElementById('recording-indicator');
    if (indicator) {
        indicator.remove();
    }
}

async function transcribeAudio(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.wav');

        const response = await fetch('/api/chat/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Set the transcribed text in the input field
        document.getElementById('message-input').value = data.text;
        
        // Optionally auto-send the message
        // handleSend();
        
    } catch (error) {
        console.error('Error transcribing audio:', error);
        alert('Failed to transcribe audio. Please try again or type your message.');
    }
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
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
    addMessage(buildAiResponseHtml(response));

    // Removed automatic clearing - now user-controlled via Clear Chat button
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('send-btn').addEventListener('click', handleSend);
    const voiceButton = document.getElementById('voice-btn');
    if (voiceButton) {
        voiceButton.addEventListener('click', toggleRecording);
    }
    document.getElementById('clear-btn').addEventListener('click', clearChat);
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
