/**
 * Time Tracker JavaScript - Freelancer Project Management System
 * Handles time tracking functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    initTimeTracker();
});

// Global variables for time tracking
let timerInterval = null;
let startTime = null;
let timerRunning = false;
let currentTimeLogId = null;

// Initialize the time tracker
function initTimeTracker() {
    const timerStartBtn = document.getElementById('startTimerBtn');
    const timerStopBtn = document.getElementById('stopTimerBtn');
    const timerDisplay = document.getElementById('timerDisplay');
    const timerForm = document.getElementById('timerForm');
    
    if (!timerDisplay) return;
    
    // Check if there's an already running timer
    checkForRunningTimer();
    
    // Add event listeners to the timer buttons
    if (timerStartBtn) {
        timerStartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!timerRunning) {
                startTimer();
            }
        });
    }
    
    if (timerStopBtn) {
        timerStopBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (timerRunning) {
                stopTimer();
            }
        });
    }
    
    // Initialize project selection change handler
    const projectSelect = document.getElementById('project_id');
    if (projectSelect) {
        projectSelect.addEventListener('change', function() {
            updateTaskOptions(this.value);
        });
    }
}

// Check if there's a running timer
function checkForRunningTimer() {
    fetch('/api/timer/check')
        .then(response => response.json())
        .then(data => {
            if (data.active_timer) {
                // There's an active timer, let's resume it
                currentTimeLogId = data.active_timer.id;
                startTime = new Date(data.active_timer.start_time);
                timerRunning = true;
                
                // Update UI
                updateTimerUI(true);
                
                // Start the timer interval
                timerInterval = setInterval(updateTimerDisplay, 1000);
                
                // Show notification
                showToast('Timer resumed from a previous session', 'info');
            }
        })
        .catch(error => {
            console.error('Error checking for running timer:', error);
        });
}

// Start the timer
function startTimer() {
    const projectId = document.getElementById('project_id').value;
    const taskId = document.getElementById('task_id')?.value || '';
    
    if (!projectId) {
        showToast('Please select a project', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('project_id', projectId);
    if (taskId) {
        formData.append('task_id', taskId);
    }
    
    // Send start timer request to the server
    fetch('/timer/start', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Timer started successfully
            currentTimeLogId = data.time_log_id;
            startTime = new Date();
            timerRunning = true;
            
            // Update UI
            updateTimerUI(true);
            
            // Start the timer interval
            timerInterval = setInterval(updateTimerDisplay, 1000);
            
            // Show notification
            showToast('Timer started', 'success');
        } else {
            // Show error message
            showToast(data.error || 'Failed to start timer', 'danger');
        }
    })
    .catch(error => {
        console.error('Error starting timer:', error);
        showToast('Error starting timer. Please try again.', 'danger');
    });
}

// Stop the timer
function stopTimer() {
    const formData = new FormData();
    if (currentTimeLogId) {
        formData.append('time_log_id', currentTimeLogId);
    }
    
    // Send stop timer request to the server
    fetch('/timer/stop', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Timer stopped successfully
            clearInterval(timerInterval);
            timerRunning = false;
            
            // Update UI
            updateTimerUI(false);
            
            // Show notification
            showToast(`Timer stopped. Logged ${formatDuration(data.duration)}`, 'success');
            
            // Reset timer state
            currentTimeLogId = null;
            startTime = null;
            
            // Refresh the time logs list if it exists
            const timeLogsList = document.getElementById('timeLogsList');
            if (timeLogsList) {
                // Reload the page to show the new time log
                location.reload();
            }
        } else {
            // Show error message
            showToast(data.error || 'Failed to stop timer', 'danger');
        }
    })
    .catch(error => {
        console.error('Error stopping timer:', error);
        showToast('Error stopping timer. Please try again.', 'danger');
    });
}

// Update the timer display
function updateTimerDisplay() {
    if (!startTime || !timerRunning) return;
    
    const timerDisplay = document.getElementById('timerDisplay');
    if (!timerDisplay) return;
    
    const currentTime = new Date();
    const elapsedMilliseconds = currentTime - startTime;
    
    // Convert to hours, minutes, seconds
    const elapsedSeconds = Math.floor(elapsedMilliseconds / 1000);
    const hours = Math.floor(elapsedSeconds / 3600);
    const minutes = Math.floor((elapsedSeconds % 3600) / 60);
    const seconds = elapsedSeconds % 60;
    
    // Format the display
    timerDisplay.textContent = 
        String(hours).padStart(2, '0') + ':' + 
        String(minutes).padStart(2, '0') + ':' + 
        String(seconds).padStart(2, '0');
    
    // Change color based on duration (just for visual feedback)
    if (hours >= 1) {
        timerDisplay.classList.add('text-warning');
    } else {
        timerDisplay.classList.remove('text-warning');
    }
}

// Update the timer UI based on the timer state
function updateTimerUI(isRunning) {
    const startBtn = document.getElementById('startTimerBtn');
    const stopBtn = document.getElementById('stopTimerBtn');
    const timerDisplay = document.getElementById('timerDisplay');
    const projectSelect = document.getElementById('project_id');
    const taskSelect = document.getElementById('task_id');
    
    if (isRunning) {
        // Timer is running
        startBtn?.classList.add('d-none');
        stopBtn?.classList.remove('d-none');
        timerDisplay?.classList.add('text-success');
        
        // Disable project and task selection while timer is running
        projectSelect?.setAttribute('disabled', 'disabled');
        taskSelect?.setAttribute('disabled', 'disabled');
    } else {
        // Timer is stopped
        startBtn?.classList.remove('d-none');
        stopBtn?.classList.add('d-none');
        timerDisplay?.classList.remove('text-success', 'text-warning');
        timerDisplay?.textContent = '00:00:00';
        
        // Enable project and task selection
        projectSelect?.removeAttribute('disabled');
        taskSelect?.removeAttribute('disabled');
    }
}

// Format duration in seconds to HH:MM:SS format
function formatDuration(seconds) {
    if (!seconds) return '0h 0m 0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${hours}h ${minutes}m ${secs}s`;
}
