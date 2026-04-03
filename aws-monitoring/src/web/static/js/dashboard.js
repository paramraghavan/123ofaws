/**
 * Dashboard auto-refresh script.
 * Fetches status every 30 seconds and updates the UI.
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateDashboard();
    // Auto-refresh every 30 seconds
    setInterval(updateDashboard, 30000);
});

function updateDashboard() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update summary cards
            document.getElementById('healthy-count').textContent = data.healthy;
            document.getElementById('degraded-count').textContent = data.degraded;
            document.getElementById('unhealthy-count').textContent = data.unhealthy;
            document.getElementById('unknown-count').textContent = data.unknown;

            // Update last update timestamp
            const timestamp = new Date(data.timestamp);
            const timeStr = timestamp.toLocaleTimeString();
            document.getElementById('last-update').textContent = 'Last updated: ' + timeStr;

            // Update service cards
            if (data.services) {
                updateServiceCards(data.services);
            }
        })
        .catch(error => {
            console.error('Error updating dashboard:', error);
            document.getElementById('last-update').textContent = 'Error updating...';
        });
}

function updateServiceCards(services) {
    const container = document.getElementById('services-container');
    if (!container) return;

    for (const [serviceName, serviceData] of Object.entries(services)) {
        const card = container.querySelector(`[data-service="${serviceName}"]`);
        if (card) {
            updateServiceCard(card, serviceData);
        }
    }
}

function updateServiceCard(card, data) {
    const total = data.count;
    const healthyPct = (data.healthy / total * 100).toFixed(0);
    const degradedPct = (data.degraded / total * 100).toFixed(0);
    const unhealthyPct = (data.unhealthy / total * 100).toFixed(0);
    const unknownPct = (data.unknown / total * 100).toFixed(0);

    // Update progress bar
    const progress = card.querySelector('.progress');
    if (progress) {
        progress.innerHTML = `
            <div class="progress-bar bg-success" style="width: ${healthyPct}%">${data.healthy}</div>
            <div class="progress-bar bg-warning" style="width: ${degradedPct}%">${data.degraded}</div>
            <div class="progress-bar bg-danger" style="width: ${unhealthyPct}%">${data.unhealthy}</div>
            <div class="progress-bar bg-secondary" style="width: ${unknownPct}%">${data.unknown}</div>
        `;
    }

    // Update badges
    const badges = card.querySelectorAll('span.badge');
    if (badges.length >= 4) {
        badges[0].textContent = `${data.healthy} Healthy`;
        badges[1].textContent = `${data.degraded} Degraded`;
        badges[2].textContent = `${data.unhealthy} Unhealthy`;
        badges[3].textContent = `${data.unknown} Unknown`;
    }
}

// Handle errors gracefully
function showError(message) {
    console.error(message);
    document.getElementById('last-update').innerHTML = `<span class="text-danger">${message}</span>`;
}
