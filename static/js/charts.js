/**
 * Charts JavaScript - Freelancer Project Management System
 * Handles data visualization and charting functions
 */

// Function to initialize charts for reports page
function initReportCharts(chartType, chartData) {
    // Make sure we have the chart container
    const chartContainer = document.getElementById('reportChart');
    if (!chartContainer) return;
    
    // Clear any existing chart
    Chart.getChart(chartContainer)?.destroy();
    
    // Create context for the chart
    const ctx = chartContainer.getContext('2d');
    
    // Prepare data for the chart
    const labels = chartData.labels || [];
    const values = chartData.values || [];
    
    // Choose chart configuration based on type
    let chartConfig;
    
    switch (chartType) {
        case 'earnings':
            chartConfig = createEarningsChart(labels, values);
            break;
        case 'projects':
            chartConfig = createProjectsChart(labels, values);
            break;
        case 'clients':
            chartConfig = createClientsChart(labels, values);
            break;
        case 'time':
            chartConfig = createTimeChart(labels, values);
            break;
        default:
            chartConfig = createDefaultChart(labels, values);
    }
    
    // Create the chart
    new Chart(ctx, chartConfig);
}

// Function to create earnings chart config
function createEarningsChart(labels, values) {
    return {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Earnings ($)',
                data: values,
                backgroundColor: 'rgba(40, 167, 69, 0.6)',
                borderColor: '#28a745',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + context.raw.toFixed(2);
                        }
                    }
                }
            }
        }
    };
}

// Function to create projects chart config
function createProjectsChart(labels, values) {
    const backgroundColors = [
        'rgba(13, 202, 240, 0.6)', // info
        'rgba(13, 110, 253, 0.6)', // primary
        'rgba(255, 193, 7, 0.6)',  // warning
        'rgba(25, 135, 84, 0.6)'   // success
    ];
    
    const borderColors = [
        '#0dcaf0', // info
        '#0d6efd', // primary
        '#ffc107', // warning
        '#198754'  // success
    ];
    
    return {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderColor: borderColors.slice(0, labels.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
}

// Function to create clients chart config
function createClientsChart(labels, values) {
    return {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue by Client ($)',
                data: values,
                backgroundColor: 'rgba(13, 110, 253, 0.6)',
                borderColor: '#0d6efd',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + context.raw.toFixed(2);
                        }
                    }
                }
            }
        }
    };
}

// Function to create time chart config
function createTimeChart(labels, values) {
    return {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Hours Logged',
                data: values,
                backgroundColor: 'rgba(13, 202, 240, 0.2)',
                borderColor: '#0dcaf0',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' hrs';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.raw.toFixed(1) + ' hours';
                        }
                    }
                }
            }
        }
    };
}

// Default chart configuration
function createDefaultChart(labels, values) {
    return {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Values',
                data: values,
                backgroundColor: 'rgba(13, 110, 253, 0.6)',
                borderColor: '#0d6efd',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    };
}

// Function to create a small chart (for dashboard widgets)
function createMiniChart(elementId, chartType, labels, values, colors) {
    const chartElement = document.getElementById(elementId);
    if (!chartElement) return;
    
    // Create default colors if not provided
    if (!colors) {
        colors = {
            backgroundColor: 'rgba(13, 110, 253, 0.6)',
            borderColor: '#0d6efd'
        };
    }
    
    const ctx = chartElement.getContext('2d');
    
    const chartConfig = {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: Array.isArray(colors.backgroundColor) ? 
                    colors.backgroundColor : [colors.backgroundColor],
                borderColor: Array.isArray(colors.borderColor) ? 
                    colors.borderColor : colors.borderColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    beginAtZero: true
                }
            }
        }
    };
    
    return new Chart(ctx, chartConfig);
}
