/**
 * Voice Recording and Speech-to-Text Module
 * Uses Web Speech API for browser-based STT
 */

const API_BASE_URL = 'http://localhost:8000';

// Voice State
let isRecording = false;
let recognition = null;
let synthesis = window.speechSynthesis;
let ws = null; // WebSocket connection
let mediaRecorder = null;
let audioChunks = [];
let currentRecipe = null;
let cookingSession = null;


// Initialize Voice Module
document.addEventListener('DOMContentLoaded', () => {
    initVoiceRecognition();
    initWebSocket();
});

// WebSocket Connection
function initWebSocket() {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) return;
    
    ws = new WebSocket('ws://localhost:8000/api/voice/ws');
    
    ws.onopen = () => {
        // Send auth
        ws.send(JSON.stringify({ token: authToken }));
        updateVoiceStatus('WebSocket connected - Real-time voice ready', 'success');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connected') {
            updateVoiceStatus('Voice AI connected', 'success');
        } else if (data.type === 'transcript') {
            updateVoiceStatus(`Heard: ${data.text}`, 'success');
            // Trigger recipe extraction
            handleFinalTranscript(data.text);
        } else if (data.type === 'recipe_data') {
            displayRecipeData(data);
            speakText(data.message || 'Recipe processed');
        } else if (data.type === 'tts_audio') {
            // Play TTS audio blob
            const audio = new Audio(`data:audio/mp3;base64,${data.audio_data}`);
            audio.play();
        } else if (data.type === 'cooking_step') {
            updateCookingStepUI(data);
            speakText(data.message);
        } else if (data.type === 'error') {
            updateVoiceStatus(data.message, 'error');
        }
    };
    
    ws.onclose = () => {
        updateVoiceStatus('WebSocket disconnected', 'error');
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateVoiceStatus('WebSocket error', 'error');
    };
}


function initVoiceRecognition() {
    // Check browser support for Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser');
        updateVoiceStatus('Speech recognition not supported', 'error');
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isRecording = true;
        updateVoiceStatus('Listening...', 'recording');
        updateRecordingUI(true);
    };
    
    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
        
        updateTranscriptDisplay(transcript);
        
        if (event.results[0].isFinal) {
            handleFinalTranscript(transcript);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        updateVoiceStatus(`Error: ${event.error}`, 'error');
        isRecording = false;
        updateRecordingUI(false);
    };
    
    recognition.onend = () => {
        isRecording = false;
        updateRecordingUI(false);
        if (isRecording) {
            // Restart if still recording
            recognition.start();
        }
    };
}

// Toggle Voice Recording - WebSocket Audio
async function toggleVoiceRecording() {
    const authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        showNotification('Please login first', 'error');
        return;
    }
    
    try {
        if (isRecording) {
            // Stop both SpeechRecognition and MediaRecorder
            if (recognition) recognition.stop();
            if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
            if (ws) ws.send(JSON.stringify({ type: "stop_recording" }));
            
            isRecording = false;
            updateVoiceStatus('Stopped', 'idle');
            updateRecordingUI(false);
        } else {
            // Request mic permission first
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Stop test stream
            
            // Start SpeechRecognition for live feedback
            if (recognition) {
                recognition.start();
            }
            
            // Start MediaRecorder for backend if WS connected
            if (ws && ws.readyState === WebSocket.OPEN) {
                const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioData = await blobToBase64(audioBlob);
                    ws.send(JSON.stringify({
                        type: "audio",
                        audio_data: audioData
                    }));
                    audioStream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start(1000); // Send chunks every second
                ws.send(JSON.stringify({ type: "start_recording" }));
            } else {
                showNotification('Backend not available - using browser speech only', 'warning');
            }
            
            isRecording = true;
            updateVoiceStatus('Listening... Speak now!', 'recording');
            updateRecordingUI(true);
        }
    } catch (error) {
        console.error('Mic access error:', error);
        updateVoiceStatus('Microphone permission denied', 'error');
        showNotification('Please allow microphone access and refresh', 'error');
    }
}

// Helper function
function blobToBase64(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = () => {
            const base64data = reader.result.split(',')[1];
            resolve(base64data);
        }
    });
}


// Handle Final Transcript
// WebSocket handles all responses - this is now for transcript mode only
async function handleFinalTranscript(transcript) {
    updateVoiceStatus('Processing transcript via WebSocket...', 'processing');
    if (ws) {
        ws.send(JSON.stringify({
            type: "transcript",
            text: transcript
        }));
    }
}


// Display Extracted Recipe Data
function displayRecipeData(data) {
    const container = document.getElementById('voiceRecipeData');
    if (!container) return;
    
    const recipe = data.recipe || {};
    const missingFields = data.missing_fields || [];
    const questions = data.follow_up_questions || [];
    
    container.innerHTML = `
        <div class="voice-recipe-result">
            <h3>Extracted Recipe</h3>
            <div class="recipe-field">
                <strong>Title:</strong> ${recipe.title || 'Not detected'}
            </div>
            <div class="recipe-field">
                <strong>Cuisine:</strong> ${recipe.cuisine || 'Not detected'}
            </div>
            <div class="recipe-field">
                <strong>Category:</strong> ${recipe.category || 'Not detected'}
            </div>
            <div class="recipe-field">
                <strong>Difficulty:</strong> ${recipe.difficulty || 'Not detected'}
            </div>
            <div class="recipe-field">
                <strong>Prep Time:</strong> ${recipe.prep_time || 0} min
            </div>
            <div class="recipe-field">
                <strong>Cook Time:</strong> ${recipe.cook_time || 0} min
            </div>
            <div class="recipe-field">
                <strong>Servings:</strong> ${recipe.servings || 4}
            </div>
            <div class="recipe-field">
                <strong>Ingredients:</strong> ${recipe.ingredients ? recipe.ingredients.length : 0} items
            </div>
            <div class="recipe-field">
                <strong>Instructions:</strong> ${recipe.instructions ? recipe.instructions.length : 0} steps
            </div>
            
            ${missingFields.length > 0 ? `
                <div class="missing-fields">
                    <h4>Missing Information:</h4>
                    <ul>
                        ${missingFields.map(f => `<li>${formatFieldName(f)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${questions.length > 0 ? `
                <div class="follow-up-questions">
                    <h4>Follow-up Questions:</h4>
                    <ul>
                        ${questions.map(q => `<li>${q}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <button class="btn-save-recipe" onclick="saveVoiceRecipe()">
                <i class="fas fa-save"></i> Save Recipe
            </button>
        </div>
    `;
    
    // Store current recipe data
    window.currentVoiceRecipe = recipe;
}

function formatFieldName(field) {
    return field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Save Voice Recipe
async function saveVoiceRecipe() {
    const recipe = window.currentVoiceRecipe;
    if (!recipe) {
        showNotification('No recipe to save', 'error');
        return;
    }
    
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
        showNotification('Please login to save recipe', 'error');
        return;
    }
    
    try {
        // Generate final structured recipe
        const response = await fetch(`${API_BASE_URL}/api/voice/ai/generate-recipe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ recipe_data: recipe })
        });
        
        const result = await response.json();
        
        if (result.type === 'recipe_generated') {
            // Save to database
            const saveResponse = await fetch(`${API_BASE_URL}/api/recipes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(result.recipe)
            });
            
            if (saveResponse.ok) {
                showNotification('Recipe saved successfully!', 'success');
                document.getElementById('voiceRecipeData').innerHTML = '';
                speakText('Your recipe has been saved successfully!');
            } else {
                showNotification('Error saving recipe', 'error');
            }
        }
    } catch (error) {
        console.error('Error saving recipe:', error);
        showNotification('Error saving recipe', 'error');
    }
}

// Text-to-Speech
function speakText(text) {
    if (!synthesis) {
        console.warn('Text-to-speech not supported');
        return;
    }
    
    // Cancel any ongoing speech
    synthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    
    synthesis.speak(utterance);
}

// Stop Speaking
function stopSpeaking() {
    if (synthesis) {
        synthesis.cancel();
    }
}

// Update Voice Status Display
function updateVoiceStatus(message, status) {
    const statusEl = document.getElementById('voiceStatus');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `voice-status voice-status-${status}`;
    }
}

// Update Recording UI
function updateRecordingUI(recording) {
    const recordBtn = document.getElementById('voiceRecordBtn');
    const recordingIndicator = document.getElementById('recordingIndicator');
    
    if (recordBtn) {
        if (recording) {
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        } else {
            recordBtn.classList.remove('recording');
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Voice';
        }
    }
    
    if (recordingIndicator) {
        recordingIndicator.style.display = recording ? 'block' : 'none';
    }
}

// Update Transcript Display
function updateTranscriptDisplay(transcript) {
    const transcriptEl = document.getElementById('voiceTranscript');
    if (transcriptEl) {
        transcriptEl.textContent = transcript;
    }
}

// Guided Cooking Mode
async function startGuidedCooking(recipeId) {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
        showNotification('Please login to start cooking', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/voice/cooking/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ recipe_id: recipeId })
        });
        
        const result = await response.json();
        
        if (result.type === 'cooking_started') {
            cookingSession = {
                session_id: result.session_id,
                current_step: result.current_step,
                total_steps: result.total_steps,
                recipe_id: recipeId
            };
            
            // Show cooking mode UI
            showCookingModeUI(result);
            
            // Speak first step
            speakText(result.message);
        } else {
            showNotification(result.message || 'Error starting cooking mode', 'error');
        }
    } catch (error) {
        console.error('Error starting cooking:', error);
        showNotification('Error starting cooking mode', 'error');
    }
}

// Handle Cooking Voice Commands
async function handleCookingCommand(command) {
    if (!cookingSession) {
        speakText('No active cooking session. Please start cooking a recipe first.');
        return;
    }
    
    const authToken = localStorage.getItem('auth_token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/voice/command?command=${encodeURIComponent(command)}&session_id=${cookingSession.session_id}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.type === 'cooking_step') {
            cookingSession.current_step = result.current_step;
            
            // Update UI
            updateCookingStepUI(result);
            
            // Speak the step
            speakText(result.message);
            
            if (result.is_complete) {
                speakText('Congratulations! You have completed all the steps. Enjoy your meal!');
            }
        }
    } catch (error) {
        console.error('Error handling command:', error);
    }
}

// Show Cooking Mode UI
function showCookingModeUI(data) {
    const container = document.getElementById('cookingModeContainer');
    if (!container) return;
    
    container.innerHTML = `
        <div class="cooking-mode">
            <div class="cooking-header">
                <h2>🍳 Guided Cooking Mode</h2>
                <button class="btn-end-cooking" onclick="endCookingSession()">
                    <i class="fas fa-times"></i> End
                </button>
            </div>
            <div class="cooking-progress">
                <div class="progress-text">
                    Step <span id="currentStep">${data.current_step}</span> 
                    of <span id="totalSteps">${data.total_steps}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(data.current_step / data.total_steps) * 100}%"></div>
                </div>
            </div>
            <div class="cooking-instruction" id="cookingInstruction">
                ${data.message}
            </div>
            <div class="cooking-commands">
                <p>Say a command:</p>
                <div class="command-buttons">
                    <button onclick="handleCookingCommand('next')"><i class="fas fa-forward"></i> Next</button>
                    <button onclick="handleCookingCommand('repeat')"><i class="fas fa-redo"></i> Repeat</button>
                    <button onclick="handleCookingCommand('previous')"><i class="fas fa-backward"></i> Previous</button>
                    <button onclick="handleCookingCommand('help')"><i class="fas fa-question"></i> Help</button>
            </div>
                </div>
            <div class="voice-input">
                <button class="btn-voice" id="voiceRecordBtn" onclick="toggleVoiceRecording()">
                    <i class="fas fa-microphone"></i> Voice Command
                </button>
            </div>
        </div>
    `;
    
    container.style.display = 'block';
}

// Update Cooking Step UI
function updateCookingStepUI(data) {
    const currentStepEl = document.getElementById('currentStep');
    const totalStepsEl = document.getElementById('totalSteps');
    const instructionEl = document.getElementById('cookingInstruction');
    const progressFill = document.querySelector('.progress-fill');
    
    if (currentStepEl) currentStepEl.textContent = data.current_step;
    if (totalStepsEl) totalStepsEl.textContent = data.total_steps;
    if (instructionEl) instructionEl.textContent = data.message;
    if (progressFill) {
        progressFill.style.width = `${(data.current_step / data.total_steps) * 100}%`;
    }
}

// End Cooking Session
function endCookingSession() {
    if (cookingSession) {
        cookingSession = null;
        const container = document.getElementById('cookingModeContainer');
        if (container) {
            container.style.display = 'none';
            container.innerHTML = '';
        }
        stopSpeaking();
        showNotification('Cooking session ended', 'info');
    }
}

// Export functions to window
window.VoiceModule = {
    toggleVoiceRecording,
    speakText,
    stopSpeaking,
    startGuidedCooking,
    handleCookingCommand,
    endCookingSession,
    saveVoiceRecipe
};

