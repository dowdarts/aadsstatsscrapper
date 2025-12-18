/**
 * AADS Overlay JavaScript
 * Handles data fetching, display updates, and auto-refresh
 */

// Configuration
const CONFIG = {
    API_ENDPOINT: '/api/stats',
    REFRESH_INTERVAL: 30000, // 30 seconds
    SORT_BY_DEFAULT: 'weighted_3da'
};

// State management
let currentData = null;
let refreshInterval = null;
let isBroadcastMode = false;

// DOM Elements
const elements = {
    leaderboardBody: null,
    totalPlayers: null,
    qualifiedCount: null,
    lastUpdated: null,
    sortSelect: null,
    broadcastToggle: null,
    refreshBtn: null,
    mainContainer: null,
    totalEvents: null,
    qualifyingEvents: null
};

/**
 * Initialize the application
 */
function init() {
    // Cache DOM elements
    cacheElements();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    fetchAndUpdateStats();
    
    // Start auto-refresh
    startAutoRefresh();
    
    console.log('AADS Overlay initialized');
}

/**
 * Cache DOM element references
 */
function cacheElements() {
    elements.leaderboardBody = document.getElementById('leaderboardBody');
    elements.totalPlayers = document.getElementById('totalPlayers');
    elements.qualifiedCount = document.getElementById('qualifiedCount');
    elements.lastUpdated = document.getElementById('lastUpdated');
    elements.sortSelect = document.getElementById('sortBy');
    elements.broadcastToggle = document.getElementById('broadcastToggle');
    elements.refreshBtn = document.getElementById('refreshBtn');
    elements.mainContainer = document.getElementById('mainContainer');
    elements.totalEvents = document.getElementById('totalEvents');
    elements.qualifyingEvents = document.getElementById('qualifyingEvents');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Sort selection change
    if (elements.sortSelect) {
        elements.sortSelect.addEventListener('change', handleSortChange);
    }
    
    // Broadcast mode toggle
    if (elements.broadcastToggle) {
        elements.broadcastToggle.addEventListener('click', toggleBroadcastMode);
    }
    
    // Manual refresh button
    if (elements.refreshBtn) {
        elements.refreshBtn.addEventListener('click', handleManualRefresh);
    }
}

/**
 * Fetch stats from API and update display
 */
async function fetchAndUpdateStats() {
    try {
        const sortBy = elements.sortSelect ? elements.sortSelect.value : CONFIG.SORT_BY_DEFAULT;
        const url = `${CONFIG.API_ENDPOINT}?sort_by=${sortBy}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            currentData = data;
            updateDisplay(data);
        } else {
            console.error('API returned error:', data.error);
            showError('Failed to load data');
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
        showError('Connection error');
    }
}

/**
 * Update the display with new data
 */
function updateDisplay(data) {
    // Update series info
    updateSeriesInfo(data.series_info);
    
    // Update summary stats
    updateSummaryStats(data);
    
    // Update leaderboard table
    updateLeaderboard(data.leaderboard);
    
    // Update last updated timestamp
    updateTimestamp(data.last_updated);
}

/**
 * Update series information
 */
function updateSeriesInfo(seriesInfo) {
    if (seriesInfo && elements.totalEvents && elements.qualifyingEvents) {
        elements.totalEvents.textContent = seriesInfo.total_events || 7;
        elements.qualifyingEvents.textContent = seriesInfo.qualifying_events || 6;
    }
}

/**
 * Update summary statistics
 */
function updateSummaryStats(data) {
    // Total players
    if (elements.totalPlayers) {
        elements.totalPlayers.textContent = data.total_players || 0;
    }
    
    // Qualified count
    if (elements.qualifiedCount) {
        const qualifiedCount = data.leaderboard.filter(p => p.qualified).length;
        elements.qualifiedCount.textContent = qualifiedCount;
    }
}

/**
 * Update leaderboard table
 */
function updateLeaderboard(leaderboard) {
    if (!elements.leaderboardBody) return;
    
    // Clear existing rows
    elements.leaderboardBody.innerHTML = '';
    
    if (!leaderboard || leaderboard.length === 0) {
        showEmptyState();
        return;
    }
    
    // Create rows for each player
    leaderboard.forEach((player, index) => {
        const row = createPlayerRow(player, index + 1);
        elements.leaderboardBody.appendChild(row);
    });
}

/**
 * Create a table row for a player
 */
function createPlayerRow(player, rank) {
    const row = document.createElement('tr');
    
    // Add qualified class if applicable
    if (player.qualified) {
        row.classList.add('qualified');
    }
    
    // Rank
    const rankCell = document.createElement('td');
    rankCell.className = 'rank-col';
    rankCell.innerHTML = createRankBadge(rank);
    row.appendChild(rankCell);
    
    // Player Name
    const nameCell = document.createElement('td');
    nameCell.className = 'player-col';
    const nameDiv = document.createElement('div');
    nameDiv.className = player.qualified ? 'player-name qualified' : 'player-name';
    nameDiv.textContent = player.name;
    nameCell.appendChild(nameDiv);
    row.appendChild(nameCell);
    
    // Events Played
    const eventsCell = document.createElement('td');
    eventsCell.className = 'stat-col';
    eventsCell.textContent = player.events_played ? player.events_played.length : 0;
    row.appendChild(eventsCell);
    
    // 3-Dart Average (highlighted)
    const avgCell = document.createElement('td');
    avgCell.className = 'stat-col highlight';
    avgCell.innerHTML = `<span class="stat-highlight">${formatAverage(player.weighted_3da)}</span>`;
    row.appendChild(avgCell);
    
    // 180s
    const oneEightiesCell = document.createElement('td');
    oneEightiesCell.className = 'stat-col';
    oneEightiesCell.textContent = player.total_180s || 0;
    row.appendChild(oneEightiesCell);
    
    // 140+
    const oneFortyPlusCell = document.createElement('td');
    oneFortyPlusCell.className = 'stat-col';
    oneFortyPlusCell.textContent = player.total_140s || 0;
    row.appendChild(oneFortyPlusCell);
    
    // 100+
    const hundredPlusCell = document.createElement('td');
    hundredPlusCell.className = 'stat-col';
    hundredPlusCell.textContent = player.total_100s || 0;
    row.appendChild(hundredPlusCell);
    
    // High Finish
    const highFinishCell = document.createElement('td');
    highFinishCell.className = 'stat-col';
    highFinishCell.textContent = player.highest_finish || '-';
    row.appendChild(highFinishCell);
    
    // Status
    const statusCell = document.createElement('td');
    statusCell.className = 'status-col';
    statusCell.innerHTML = createStatusBadge(player.qualified);
    row.appendChild(statusCell);
    
    return row;
}

/**
 * Create rank badge HTML
 */
function createRankBadge(rank) {
    let badgeClass = 'rank-badge ';
    
    if (rank === 1) {
        badgeClass += 'top-1';
    } else if (rank === 2) {
        badgeClass += 'top-2';
    } else if (rank === 3) {
        badgeClass += 'top-3';
    } else {
        badgeClass += 'other';
    }
    
    return `<span class="${badgeClass}">${rank}</span>`;
}

/**
 * Create status badge HTML
 */
function createStatusBadge(qualified) {
    if (qualified) {
        return '<span class="status-badge qualified">Qualified</span>';
    }
    return '<span class="status-badge competing">Competing</span>';
}

/**
 * Format average to 2 decimal places
 */
function formatAverage(avg) {
    if (!avg || avg === 0) return '-';
    return Number(avg).toFixed(2);
}

/**
 * Show empty state
 */
function showEmptyState() {
    elements.leaderboardBody.innerHTML = `
        <tr class="loading-row">
            <td colspan="9">
                <p>No player data available yet.</p>
                <p class="text-muted">Add matches to see standings.</p>
            </td>
        </tr>
    `;
}

/**
 * Show error message
 */
function showError(message) {
    if (elements.leaderboardBody) {
        elements.leaderboardBody.innerHTML = `
            <tr class="loading-row">
                <td colspan="9">
                    <p style="color: var(--danger);">⚠️ ${message}</p>
                    <p class="text-muted">Please try refreshing the page.</p>
                </td>
            </tr>
        `;
    }
}

/**
 * Update last updated timestamp
 */
function updateTimestamp(timestamp) {
    if (!elements.lastUpdated) return;
    
    if (!timestamp) {
        elements.lastUpdated.textContent = 'Never';
        return;
    }
    
    try {
        const date = new Date(timestamp);
        elements.lastUpdated.textContent = formatDateTime(date);
    } catch (error) {
        elements.lastUpdated.textContent = 'Unknown';
    }
}

/**
 * Format date and time
 */
function formatDateTime(date) {
    const now = new Date();
    const diff = now - date;
    
    // If less than 1 minute ago
    if (diff < 60000) {
        return 'Just now';
    }
    
    // If less than 1 hour ago
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Otherwise show full date/time
    const options = {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleString('en-US', options);
}

/**
 * Handle sort selection change
 */
function handleSortChange() {
    fetchAndUpdateStats();
}

/**
 * Handle manual refresh button click
 */
function handleManualRefresh() {
    if (elements.refreshBtn) {
        elements.refreshBtn.disabled = true;
        elements.refreshBtn.innerHTML = '<span class="icon">⏳</span> Refreshing...';
    }
    
    fetchAndUpdateStats().finally(() => {
        if (elements.refreshBtn) {
            elements.refreshBtn.disabled = false;
            elements.refreshBtn.innerHTML = '<span class="icon">🔄</span> Refresh';
        }
    });
}

/**
 * Toggle broadcast mode
 */
function toggleBroadcastMode() {
    isBroadcastMode = !isBroadcastMode;
    
    if (isBroadcastMode) {
        elements.mainContainer.classList.add('broadcast-mode');
        elements.broadcastToggle.classList.add('active');
        elements.broadcastToggle.innerHTML = '<span class="icon">📺</span> Exit Broadcast';
    } else {
        elements.mainContainer.classList.remove('broadcast-mode');
        elements.broadcastToggle.classList.remove('active');
        elements.broadcastToggle.innerHTML = '<span class="icon">📺</span> Broadcast Mode';
    }
}

/**
 * Start auto-refresh interval
 */
function startAutoRefresh() {
    // Clear any existing interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Set up new interval
    refreshInterval = setInterval(() => {
        console.log('Auto-refreshing stats...');
        fetchAndUpdateStats();
    }, CONFIG.REFRESH_INTERVAL);
    
    console.log(`Auto-refresh enabled (every ${CONFIG.REFRESH_INTERVAL / 1000} seconds)`);
}

/**
 * Stop auto-refresh interval
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
        console.log('Auto-refresh disabled');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
    setupManagementListeners();
}

// Setup management panel event listeners
function setupManagementListeners() {
    const manageToggle = document.getElementById('manageToggle');
    const singleMatchForm = document.getElementById('singleMatchForm');
    const eventScrapeForm = document.getElementById('eventScrapeForm');
    const setWinnerBtn = document.getElementById('setWinnerBtn');
    const resetDbBtn = document.getElementById('resetDbBtn');
    const winnerEvent = document.getElementById('winnerEvent');
    
    if (manageToggle) {
        manageToggle.addEventListener('click', toggleManagementPanel);
    }
    
    if (singleMatchForm) {
        singleMatchForm.addEventListener('submit', handleSingleMatchScrape);
    }
    
    if (eventScrapeForm) {
        eventScrapeForm.addEventListener('submit', handleEventScrape);
    }
    
    if (setWinnerBtn) {
        setWinnerBtn.addEventListener('click', handleSetWinner);
    }
    
    if (resetDbBtn) {
        resetDbBtn.addEventListener('click', handleResetDatabase);
    }
    
    if (winnerEvent) {
        winnerEvent.addEventListener('change', loadPlayerList);
    }
    
    // Load initial player list
    loadPlayerList();
}

// Toggle management panel
function toggleManagementPanel() {
    const panel = document.getElementById('managementPanel');
    const button = document.getElementById('manageToggle');
    
    if (panel) {
        const isHidden = panel.classList.contains('hidden');
        if (isHidden) {
            panel.classList.remove('hidden');
            button.textContent = '🔼 Hide Management';
        } else {
            panel.classList.add('hidden');
            button.innerHTML = '<span class="icon">⚙️</span> Manage';
        }
    }
}

// Handle single match scraping
async function handleSingleMatchScrape(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const url = formData.get('matchUrl') || document.getElementById('matchUrl').value;
    const eventId = formData.get('eventId') || document.getElementById('eventId').value;
    
    if (!url || !eventId) {
        showStatusMessage('Please fill in all fields', 'error');
        return;
    }
    
    setFormLoading(form, true);
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, event_id: parseInt(eventId) })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatusMessage(`✅ Successfully scraped match! Added ${result.data.length} players.`, 'success');
            form.reset();
            fetchAndUpdateStats(); // Refresh leaderboard
        } else {
            showStatusMessage(`❌ ${result.message}`, 'error');
        }
        
    } catch (error) {
        showStatusMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        setFormLoading(form, false);
    }
}

// Handle event scraping
async function handleEventScrape(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const eventUrl = formData.get('eventUrl') || document.getElementById('eventUrl').value;
    const eventId = formData.get('eventIdBatch') || document.getElementById('eventIdBatch').value;
    
    if (!eventUrl || !eventId) {
        showStatusMessage('Please fill in all fields', 'error');
        return;
    }
    
    setFormLoading(form, true);
    showStatusMessage('🔄 Extracting matches from event page...', 'info');
    
    try {
        const response = await fetch('/api/scrape-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                event_url: eventUrl, 
                event_id: parseInt(eventId) 
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            showStatusMessage(
                `✅ Event scraping complete! Processed ${data.total_matches} matches. ` +
                `Success: ${data.successful}, Failed: ${data.failed}. ` +
                `Players added: ${data.players_added.join(', ')}`, 
                'success'
            );
            
            if (data.errors.length > 0) {
                data.errors.forEach(error => {
                    showStatusMessage(`⚠️ ${error}`, 'warning');
                });
            }
            
            form.reset();
            fetchAndUpdateStats(); // Refresh leaderboard
        } else {
            showStatusMessage(`❌ ${result.message}`, 'error');
        }
        
    } catch (error) {
        showStatusMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        setFormLoading(form, false);
    }
}

// Handle setting event winner
async function handleSetWinner() {
    const eventId = document.getElementById('winnerEvent').value;
    const playerName = document.getElementById('winnerPlayer').value;
    
    if (!eventId || !playerName) {
        showStatusMessage('Please select both event and player', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/set-winner', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                event_id: parseInt(eventId), 
                player_name: playerName 
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatusMessage(`✅ Set ${playerName} as winner of Event ${eventId}`, 'success');
            fetchAndUpdateStats(); // Refresh leaderboard
        } else {
            showStatusMessage(`❌ ${result.message}`, 'error');
        }
        
    } catch (error) {
        showStatusMessage(`❌ Error: ${error.message}`, 'error');
    }
}

// Handle database reset
async function handleResetDatabase() {
    if (!confirm('⚠️ Are you sure you want to reset the database? This will delete ALL data and cannot be undone!')) {
        return;
    }
    
    try {
        const response = await fetch('/api/reset-database', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ confirm: true })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatusMessage('✅ Database reset successfully', 'success');
            fetchAndUpdateStats(); // Refresh leaderboard
            loadPlayerList(); // Refresh player list
        } else {
            showStatusMessage(`❌ ${result.message}`, 'error');
        }
        
    } catch (error) {
        showStatusMessage(`❌ Error: ${error.message}`, 'error');
    }
}

// Load player list for winner selection
async function loadPlayerList() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        
        if (result.success) {
            const playerSelect = document.getElementById('winnerPlayer');
            if (playerSelect) {
                playerSelect.innerHTML = '<option value="">Select Player...</option>';
                
                result.data.forEach(player => {
                    const option = document.createElement('option');
                    option.value = player.name;
                    option.textContent = `${player.name} (${player.weighted_3da.toFixed(2)} avg)`;
                    playerSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading player list:', error);
    }
}

// Show status message
function showStatusMessage(message, type = 'info') {
    const container = document.getElementById('statusMessages');
    if (!container) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `status-message ${type}`;
    messageEl.textContent = message;
    
    container.appendChild(messageEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageEl.parentNode) {
            messageEl.parentNode.removeChild(messageEl);
        }
    }, 5000);
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Set form loading state
function setFormLoading(form, isLoading) {
    if (isLoading) {
        form.classList.add('form-loading');
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.textContent;
            submitBtn.textContent = 'Processing...';
        }
    } else {
        form.classList.remove('form-loading');
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            if (submitBtn.dataset.originalText) {
                submitBtn.textContent = submitBtn.dataset.originalText;
            }
        }
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});

// Export functions for potential external use
window.AADSOverlay = {
    refresh: fetchAndUpdateStats,
    toggleBroadcast: toggleBroadcastMode,
    getCurrentData: () => currentData,
    showStatus: showStatusMessage
};
