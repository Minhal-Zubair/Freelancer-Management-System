/**
 * Calendar JavaScript - Freelancer Project Management System
 * Handles calendar visualization and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
});

function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    
    if (!calendarEl) return;
    
    // Get events data from the HTML (passed from Flask)
    const eventsData = JSON.parse(calendarEl.dataset.events || '[]');
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listMonth'
        },
        themeSystem: 'bootstrap5',
        events: eventsData,
        eventClick: handleEventClick,
        eventDidMount: function(info) {
            // Add status-specific styling
            if (info.event.extendedProps.status) {
                // Apply different styles based on status
                if (info.event.extendedProps.status === 'Completed') {
                    info.el.style.opacity = '0.7';
                }
                
                if (info.event.extendedProps.status === 'Overdue') {
                    info.el.style.borderLeft = '3px solid #dc3545';
                }
            }
            
            // Enable tooltips on calendar events
            const tooltip = new bootstrap.Tooltip(info.el, {
                title: getTooltipContent(info.event),
                placement: 'top',
                trigger: 'hover',
                container: 'body',
                html: true
            });
        },
        height: 'auto',
        firstDay: 1, // Start week on Monday
        weekNumbers: true,
        weekText: 'W',
        dayMaxEvents: true, // Allow "more" link when too many events
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '09:00',
            endTime: '18:00'
        }
    });
    
    calendar.render();
    
    // Handle calendar view buttons
    document.querySelectorAll('.btn-calendar-view').forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            calendar.changeView(view);
            
            // Update active button state
            document.querySelectorAll('.btn-calendar-view').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
}

function handleEventClick(info) {
    const eventType = info.event.extendedProps.type;
    const eventId = info.event.extendedProps.id;
    
    // Redirect to appropriate page based on event type
    if (eventType === 'project') {
        window.location.href = `/projects/${eventId}`;
    } else if (eventType === 'task') {
        const projectId = info.event.extendedProps.project_id;
        window.location.href = `/projects/${projectId}#task-${eventId}`;
    } else if (eventType === 'invoice') {
        window.location.href = `/invoices/${eventId}`;
    }
}

function getTooltipContent(event) {
    const type = event.extendedProps.type;
    const status = event.extendedProps.status;
    
    let statusBadge = '';
    if (status) {
        let badgeClass = 'bg-secondary';
        
        if (type === 'project') {
            if (status === 'New') badgeClass = 'bg-info';
            else if (status === 'In Progress') badgeClass = 'bg-primary';
            else if (status === 'On Hold') badgeClass = 'bg-warning text-dark';
            else if (status === 'Completed') badgeClass = 'bg-success';
        } else if (type === 'task') {
            if (status === 'Not Started') badgeClass = 'bg-secondary';
            else if (status === 'In Progress') badgeClass = 'bg-primary';
            else if (status === 'Completed') badgeClass = 'bg-success';
            else if (status === 'Blocked') badgeClass = 'bg-danger';
        } else if (type === 'invoice') {
            if (status === 'Draft') badgeClass = 'bg-secondary';
            else if (status === 'Sent') badgeClass = 'bg-primary';
            else if (status === 'Paid') badgeClass = 'bg-success';
            else if (status === 'Overdue') badgeClass = 'bg-danger';
        }
        
        statusBadge = `<span class="badge ${badgeClass}">${status}</span>`;
    }
    
    return `
        <div>
            <div><strong>${event.title}</strong></div>
            <div>Date: ${new Date(event.start).toLocaleDateString()}</div>
            <div>${statusBadge}</div>
        </div>
    `;
}
