/**
 * Dashboard JavaScript - Freelancer Project Management System
 * Handles dashboard charts and statistics visualization
 */

// Function to initialize dashboard charts
function initDashboardCharts(projectStatusData, priorityData) {
    // Project Status Chart (Pie chart)
    if (document.getElementById('projectStatusChart')) {
        const statusCtx = document.getElementById('projectStatusChart').getContext('2d');
        
        const statusColors = {
            'New': '#0dcaf0',           // info
            'In Progress': '#0d6efd',   // primary
            'On Hold': '#ffc107',       // warning
            'Completed': '#198754'      // success
        };
        
        const statusBackgroundColors = [];
        for (let i = 0; i < projectStatusData.labels.length; i++) {
            statusBackgroundColors.push(statusColors[projectStatusData.labels[i]] || '#6c757d');
        }
        
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: projectStatusData.labels,
                datasets: [{
                    data: projectStatusData.values,
                    backgroundColor: statusBackgroundColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f8f9fa'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }
    
    // Fetch recent activity for dashboard updates
    fetchDashboardStats();
    
    // Set up periodic refresh for dashboard data (every 5 minutes)
    setInterval(fetchDashboardStats, 5 * 60 * 1000);
}

// Function to fetch dashboard statistics from API
function fetchDashboardStats() {
    fetch('/api/freelancer/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update dashboard stats if needed
            updateDashboardStatsUI(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard stats:', error);
        });
}

// Function to update dashboard UI with fresh data
function updateDashboardStatsUI(data) {
    // This would update any live elements that need refreshing
    // For now, we'll just leave this as a stub since we're
    // primarily relying on server-side rendering for most elements
    
    // If we had real-time counters, we would update them here
    
    // Example of how we would update a DOM element:
    // const totalEarningsElement = document.getElementById('totalEarnings');
    // if (totalEarningsElement && data.total_earnings) {
    //     totalEarningsElement.textContent = '$' + data.total_earnings.toFixed(2);
    // }
}

// Handle deadline notifications
document.addEventListener('DOMContentLoaded', function() {
    // Check for overdue projects and show notification if needed
    const overdueProjects = document.querySelectorAll('.deadline-overdue');
    if (overdueProjects.length > 0) {
        setTimeout(() => {
            showToast(`You have ${overdueProjects.length} overdue project(s)`, 'danger');
        }, 2000);
    }
    
    // Check for approaching deadlines and show notification if needed
    const approachingDeadlines = document.querySelectorAll('.deadline-approaching');
    if (approachingDeadlines.length > 0) {
        setTimeout(() => {
            showToast(`You have ${approachingDeadlines.length} project(s) due soon`, 'warning');
        }, 3000);
    }
});
