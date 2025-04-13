// Main JavaScript file for Freelancer Project Management System

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Handle client selection change for project forms
    const clientSelect = document.getElementById('client_id');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            updateProjectOptions(this.value);
        });
    }
    
    // Handle project selection change for task forms
    const projectSelect = document.getElementById('project_id');
    if (projectSelect) {
        projectSelect.addEventListener('change', function() {
            updateTaskOptions(this.value);
        });
    }
    
    // Set up confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Initialize date pickers with current date/time defaults
    initDateInputs();
    
    // Handle tax calculation for invoices
    const amountInput = document.getElementById('amount');
    const taxRateInput = document.getElementById('tax_rate');
    const taxAmountDisplay = document.getElementById('tax_amount_display');
    const totalAmountDisplay = document.getElementById('total_amount_display');
    
    if (amountInput && taxRateInput && taxAmountDisplay && totalAmountDisplay) {
        const calculateTax = function() {
            const amount = parseFloat(amountInput.value) || 0;
            const taxRate = (parseFloat(taxRateInput.value) || 0) / 100;
            
            const taxAmount = amount * taxRate;
            const totalAmount = amount + taxAmount;
            
            taxAmountDisplay.textContent = taxAmount.toFixed(2);
            totalAmountDisplay.textContent = totalAmount.toFixed(2);
        };
        
        amountInput.addEventListener('input', calculateTax);
        taxRateInput.addEventListener('input', calculateTax);
        
        // Initial calculation
        calculateTax();
    }
    
    // Handle file input styling
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = this.files[0]?.name;
            const label = this.nextElementSibling;
            
            if (fileName) {
                label.textContent = fileName;
            } else {
                label.textContent = 'Choose file';
            }
        });
    });
    
    // Set active navigation item based on current URL
    setActiveNavItem();
});

// Function to update project select options based on selected client
function updateProjectOptions(clientId) {
    if (!clientId) return;
    
    const projectSelect = document.getElementById('project_id');
    if (!projectSelect) return;
    
    // Disable select while loading
    projectSelect.disabled = true;
    
    fetch(`/api/clients/${clientId}/projects`)
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            projectSelect.innerHTML = '';
            
            // Add new options
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.title;
                projectSelect.appendChild(option);
            });
            
            // Re-enable select
            projectSelect.disabled = false;
        })
        .catch(error => {
            console.error('Error fetching projects:', error);
            projectSelect.disabled = false;
        });
}

// Function to update task select options based on selected project
function updateTaskOptions(projectId) {
    if (!projectId) return;
    
    const taskSelect = document.getElementById('task_id');
    if (!taskSelect) return;
    
    // Disable select while loading
    taskSelect.disabled = true;
    
    fetch(`/api/projects/${projectId}/tasks`)
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            taskSelect.innerHTML = '';
            
            // Add new options
            data.tasks.forEach(task => {
                const option = document.createElement('option');
                option.value = task.id;
                option.textContent = task.title;
                taskSelect.appendChild(option);
            });
            
            // Re-enable select
            taskSelect.disabled = false;
        })
        .catch(error => {
            console.error('Error fetching tasks:', error);
            taskSelect.disabled = false;
        });
}

// Function to initialize date inputs with current date/time
function initDateInputs() {
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    const now = new Date();
    
    // Format the date and time for the input
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    const formattedDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
    
    dateTimeInputs.forEach(input => {
        // Only set the value if it's currently empty
        if (!input.value) {
            input.value = formattedDateTime;
        }
    });
}

// Function to set active navigation item
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // Check if the current path starts with the link href (excluding the root path)
        if (href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

// Function to format currency
function formatCurrency(amount, currencySymbol = '$') {
    return currencySymbol + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Function to format date
function formatDate(dateString, includeTime = false) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return date.toLocaleDateString('en-US', options);
}

// Function to show toast notifications
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}
