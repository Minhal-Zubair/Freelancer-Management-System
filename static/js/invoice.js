/**
 * Invoice JavaScript - Freelancer Project Management System
 * Handles invoice creation and management
 */

document.addEventListener('DOMContentLoaded', function() {
    initInvoiceForm();
});

// Initialize invoice form functionality
function initInvoiceForm() {
    // Set up the client selection change handler
    const clientSelect = document.getElementById('client_id');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            updateProjectOptions(this.value);
        });
    }
    
    // Set up invoice calculations
    const amountInput = document.getElementById('amount');
    const taxRateInput = document.getElementById('tax_rate');
    
    if (amountInput && taxRateInput) {
        // Calculate on amount change
        amountInput.addEventListener('input', calculateInvoiceTotal);
        
        // Calculate on tax rate change
        taxRateInput.addEventListener('input', calculateInvoiceTotal);
        
        // Initial calculation
        calculateInvoiceTotal();
    }
    
    // Handle invoice status change
    const statusSelect = document.getElementById('status');
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            togglePaymentFields(this.value);
        });
        
        // Initial check
        togglePaymentFields(statusSelect.value);
    }
    
    // Initialize datepicker for invoice dates
    flatpickrInit();
}

// Calculate invoice total from amount and tax rate
function calculateInvoiceTotal() {
    const amountInput = document.getElementById('amount');
    const taxRateInput = document.getElementById('tax_rate');
    const taxAmountDisplay = document.getElementById('tax_amount_display');
    const totalAmountDisplay = document.getElementById('total_amount_display');
    
    if (!amountInput || !taxRateInput || !taxAmountDisplay || !totalAmountDisplay) return;
    
    const amount = parseFloat(amountInput.value) || 0;
    const taxRate = (parseFloat(taxRateInput.value) || 0) / 100;
    
    const taxAmount = amount * taxRate;
    const totalAmount = amount + taxAmount;
    
    // Update the displayed values
    taxAmountDisplay.textContent = taxAmount.toFixed(2);
    totalAmountDisplay.textContent = totalAmount.toFixed(2);
}

// Toggle payment-related fields based on invoice status
function togglePaymentFields(status) {
    const paymentMethodField = document.getElementById('payment_method_container');
    const transactionIdField = document.getElementById('transaction_id_container');
    const paymentDateField = document.getElementById('payment_date_container');
    
    if (!paymentMethodField || !transactionIdField || !paymentDateField) return;
    
    // Show payment fields only if status is 'Paid'
    if (status === 'Paid') {
        paymentMethodField.classList.remove('d-none');
        transactionIdField.classList.remove('d-none');
        paymentDateField.classList.remove('d-none');
    } else {
        paymentMethodField.classList.add('d-none');
        transactionIdField.classList.add('d-none');
        paymentDateField.classList.add('d-none');
    }
}

// Initialize flatpickr date pickers if available
function flatpickrInit() {
    if (typeof flatpickr !== 'undefined') {
        // Initialize date pickers
        flatpickr('.datepicker', {
            dateFormat: 'Y-m-d',
            defaultDate: 'today'
        });
        
        flatpickr('.datetimepicker', {
            dateFormat: 'Y-m-d H:i',
            enableTime: true,
            time_24hr: true,
            defaultDate: 'today'
        });
    }
}

// Generate a PDF version of the invoice
function generateInvoicePDF(invoiceId) {
    // In a real implementation, this would call a backend endpoint
    // to generate a PDF and return it for download
    
    // For now, we'll just simulate this with a notification
    showToast('Generating PDF invoice...', 'info');
    
    // Redirect to a PDF download endpoint
    window.location.href = `/invoices/${invoiceId}/pdf`;
}

// Send invoice by email
function sendInvoiceEmail(invoiceId) {
    const formData = new FormData();
    formData.append('invoice_id', invoiceId);
    
    // Show loading indicator
    showToast('Sending invoice by email...', 'info');
    
    // Send the request to the server
    fetch(`/invoices/${invoiceId}/send`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Invoice sent successfully!', 'success');
            
            // Update the status badge if needed
            const statusBadge = document.querySelector('.invoice-status-badge');
            if (statusBadge && data.new_status) {
                statusBadge.textContent = data.new_status;
                
                // Update badge class
                statusBadge.className = 'badge invoice-status-badge';
                
                if (data.new_status === 'Sent') {
                    statusBadge.classList.add('bg-primary');
                } else if (data.new_status === 'Paid') {
                    statusBadge.classList.add('bg-success');
                } else if (data.new_status === 'Overdue') {
                    statusBadge.classList.add('bg-danger');
                } else {
                    statusBadge.classList.add('bg-secondary');
                }
            }
        } else {
            showToast(data.error || 'Failed to send invoice', 'danger');
        }
    })
    .catch(error => {
        console.error('Error sending invoice:', error);
        showToast('Error sending invoice. Please try again.', 'danger');
    });
}

// Mark invoice as paid
function markInvoiceAsPaid(invoiceId) {
    const formData = new FormData();
    formData.append('invoice_id', invoiceId);
    
    // Send the request to the server
    fetch(`/invoices/${invoiceId}/mark-paid`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Invoice marked as paid!', 'success');
            
            // Reload the page to update the UI
            location.reload();
        } else {
            showToast(data.error || 'Failed to update invoice', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating invoice:', error);
        showToast('Error updating invoice. Please try again.', 'danger');
    });
}
