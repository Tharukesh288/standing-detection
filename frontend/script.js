const standingCount = document.getElementById('standing-count');
const sittingCount = document.getElementById('sitting-count');
const statusBadge = document.getElementById('connection-status');
const videoFeed = document.getElementById('video-feed');
const overcrowdedBanner = document.getElementById('overcrowded-banner');

// Set video feed URL
const BACKEND_URL = 'http://localhost:5000';
videoFeed.src = `${BACKEND_URL}/video_feed`;

// Connect to WebSocket
const socket = io(BACKEND_URL);

socket.on('connect', () => {
    statusBadge.textContent = 'Connected';
    statusBadge.className = 'status connected';
});

socket.on('disconnect', () => {
    statusBadge.textContent = 'Disconnected';
    statusBadge.className = 'status disconnected';
});

// Initialize Chart.js
const ctx = document.getElementById('historyChart').getContext('2d');
const MAX_DATA_POINTS = 30; // Keep roughly 30 ticks of history

const historyChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Time labels
        datasets: [
            {
                label: 'Standing',
                data: [],
                borderColor: '#a3be8c', // Nord Green
                backgroundColor: 'rgba(163, 190, 140, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Sitting',
                data: [],
                borderColor: '#bf616a', // Nord Red
                backgroundColor: 'rgba(191, 97, 106, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 0 // Disable animation for smoother real-time feel
        },
        scales: {
            x: {
                display: false // Hide X axis labels for clean look
            },
            y: {
                beginAtZero: true,
                suggestedMax: 10,
                grid: {
                    color: '#4c566a' // Nord 3
                },
                ticks: {
                    color: '#d8dee9', // Nord text
                    stepSize: 1
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: '#eceff4'
                }
            }
        }
    }
});

socket.on('count_update', (data) => {
    standingCount.textContent = data.standing;
    sittingCount.textContent = data.sitting;
    
    // Update Chart Data
    const now = new Date();
    historyChart.data.labels.push(now.toLocaleTimeString());
    historyChart.data.datasets[0].data.push(data.standing);
    historyChart.data.datasets[1].data.push(data.sitting);
    
    // Maintain maximum data points
    if (historyChart.data.labels.length > MAX_DATA_POINTS) {
        historyChart.data.labels.shift();
        historyChart.data.datasets[0].data.shift();
        historyChart.data.datasets[1].data.shift();
    }
    historyChart.update();
    
    // Handle overcrowded warning
    if (data.overcrowded) {
        overcrowdedBanner.classList.remove('hidden');
    } else {
        overcrowdedBanner.classList.add('hidden');
    }
});

// Manual Trigger Logic
const manualBtn = document.getElementById('manual-trigger-btn');
manualBtn.addEventListener('click', () => {
    socket.emit('manual_trigger');
    
    // Give visual feedback
    const originalText = manualBtn.textContent;
    manualBtn.textContent = 'Trigged!';
    manualBtn.style.backgroundColor = 'var(--nord14)'; // Success green
    manualBtn.style.boxShadow = '0 0 15px rgba(163, 190, 140, 0.4)';
    
    setTimeout(() => {
        manualBtn.textContent = originalText;
        manualBtn.style.backgroundColor = '';
        manualBtn.style.boxShadow = '';
    }, 2000);
});

// Switch Camera Logic
const switchCamBtn = document.getElementById('switch-cam-btn');
switchCamBtn.addEventListener('click', () => {
    fetch(`${BACKEND_URL}/api/switch_camera`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            console.log("Switched camera", data);
            const originalText = switchCamBtn.textContent;
            switchCamBtn.textContent = data.use_stream ? 'ESP32 Cam Active' : 'Laptop Cam Active';
            switchCamBtn.style.backgroundColor = 'var(--nord10)'; // Feedback color
            
            setTimeout(() => {
                switchCamBtn.textContent = originalText;
                switchCamBtn.style.backgroundColor = '';
            }, 2000);
        })
        .catch(err => console.error("Error switching camera", err));
});

// Stats polling logic from Database
const todayEventsEl = document.getElementById('today-events');
const peakStandingEl = document.getElementById('peak-standing');
const lastEventEl = document.getElementById('last-event');

function updateDatabaseStats() {
    fetch(`${BACKEND_URL}/api/stats`)
        .then(res => res.json())
        .then(data => {
            if(todayEventsEl) todayEventsEl.textContent = data.today_events;
            if(peakStandingEl) peakStandingEl.textContent = data.peak_standing;
            if(lastEventEl) lastEventEl.textContent = data.last_event;
        })
        .catch(err => console.error("Could not fetch DB stats", err));
}

// Update stats every 5 seconds
setInterval(updateDatabaseStats, 5000);
updateDatabaseStats(); // Initial call

