// Task JavaScript

async function loadTasks() {
    try {
        const response = await fetch('/tasks/');
        const data = await response.json();
        // Display tasks
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

document.addEventListener('DOMContentLoaded', loadTasks);
