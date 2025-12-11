// API Configuration
const API_KEY = localStorage.getItem('apiKey') || 'your-api-key-change-this';
const API_BASE = window.location.origin;

// Auth headers
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
    };
}

// Check authentication on page load
if (!localStorage.getItem('authToken') && !window.location.pathname.includes('login')) {
    window.location.href = '/login';
}

// Global state
let currentTab = 'dashboard';
let allTransactions = [];
let allUsers = [];
let updateIntervals = [];

// =========================
// Utility Functions
// =========================
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
}

function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

function showNotification(message, type = 'info') {
    // Simple notification - can be enhanced
    alert(message);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// =========================
// API Functions
// =========================
async function apiCall(endpoint, options = {}) {
    try {
        const headers = getHeaders();
        
        // Check if we have required auth headers
        const token = localStorage.getItem('authToken');
        if (!token && endpoint !== '/login' && endpoint !== '/status') {
            console.warn('No auth token found, redirecting to login');
            window.location.href = '/login';
            return null;
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: headers
        });

        if (response.status === 401) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.message || 'Authentication required';
            
            // Clear token and redirect to login
            localStorage.removeItem('authToken');
            localStorage.removeItem('username');
            
            // Show error message before redirect
            if (errorMsg.includes('expired') || errorMsg.includes('invalid')) {
                alert('Your session has expired. Please login again.');
            }
            
            window.location.href = '/login';
            return null;
        }

        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error('API Error:', error);
        return { ok: false, error: error.message };
    }
}

// =========================
// Dashboard Functions
// =========================
async function loadSystemStatus() {
    const result = await apiCall('/status');
    if (!result || !result.ok) return;

    const { components, storage, temperature } = result.data;

    // Update status badges
    document.getElementById('internetStatus').textContent = components.internet ? 'Connected' : 'Offline';
    document.getElementById('internetStatus').style.color = components.internet ? 'var(--success)' : 'var(--danger)';

    document.getElementById('firebaseStatus').textContent = components.firebase ? 'Connected' : 'Offline';
    document.getElementById('firebaseStatus').style.color = components.firebase ? 'var(--success)' : 'var(--warning)';

    document.getElementById('rfidStatus').textContent = components.rfid_readers ? 'Online' : 'Offline';
    document.getElementById('rfidStatus').style.color = components.rfid_readers ? 'var(--success)' : 'var(--danger)';

    document.getElementById('storageStatus').textContent = `${storage.tx_dir_gb} / ${storage.cap_gb} GB`;
    document.getElementById('storageStatus').style.color = 
        storage.tx_dir_gb > storage.cap_gb * 0.8 ? 'var(--warning)' : 'var(--success)';

    // Update temperature
    const tempElement = document.getElementById('temperatureStatus');
    if (temperature && temperature.cpu_celsius !== null) {
        const temp = temperature.cpu_celsius;
        tempElement.textContent = `${temp}°C`;
        // Color coding: green (<60°C), yellow (60-75°C), red (>75°C)
        if (temp < 60) {
            tempElement.style.color = 'var(--success)';
        } else if (temp < 75) {
            tempElement.style.color = 'var(--warning)';
        } else {
            tempElement.style.color = 'var(--danger)';
        }
    } else {
        tempElement.textContent = 'N/A';
        tempElement.style.color = '#666';
    }
}

async function loadTodayStats() {
    const result = await apiCall('/get_today_stats');
    if (!result || !result.ok) return;

    const stats = result.data;
    document.getElementById('totalScans').textContent = stats.total || 0;
    document.getElementById('grantedScans').textContent = stats.granted || 0;
    document.getElementById('deniedScans').textContent = stats.denied || 0;
    document.getElementById('blockedScans').textContent = stats.blocked || 0;
}

// Pagination state for live transactions
let currentPage = 1;
let itemsPerPage = 25;
let allLiveTransactions = [];

async function loadLiveTransactions() {
    const result = await apiCall('/get_transactions?limit=200');
    if (!result || !result.ok) return;

    allLiveTransactions = result.data;
    displayLiveTransactionsPage();
}

function displayLiveTransactionsPage() {
    const tbody = document.getElementById('liveTransactions');
    
    if (allLiveTransactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No transactions yet</td></tr>';
        document.getElementById('livePaginationControls').style.display = 'none';
        return;
    }

    // Calculate pagination
    const totalPages = Math.ceil(allLiveTransactions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageTransactions = allLiveTransactions.slice(startIndex, endIndex);

    // Render transactions
    tbody.innerHTML = pageTransactions.map(tx => {
        const statusClass = tx.status === 'Access Granted' ? 'status-granted' :
                          tx.status === 'Blocked' ? 'status-blocked' : 'status-denied';
        return `
            <tr>
                <td>${formatTime(tx.timestamp)}</td>
                <td>${tx.name}</td>
                <td>${tx.card}</td>
                <td>Reader ${tx.reader}</td>
                <td><span class="status-badge-table ${statusClass}">${tx.status}</span></td>
            </tr>
        `;
    }).join('');

    // Update pagination controls
    document.getElementById('livePaginationControls').style.display = 'flex';
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages} (${allLiveTransactions.length} total)`;
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
}

function initDashboard() {
    loadSystemStatus();
    loadTodayStats();
    loadLiveTransactions();

    // Pagination controls
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            displayLiveTransactionsPage();
        }
    });

    document.getElementById('nextPageBtn').addEventListener('click', () => {
        const totalPages = Math.ceil(allLiveTransactions.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            displayLiveTransactionsPage();
        }
    });

    document.getElementById('itemsPerPage').addEventListener('change', (e) => {
        itemsPerPage = parseInt(e.target.value);
        currentPage = 1; // Reset to first page
        displayLiveTransactionsPage();
    });

    // Auto-refresh every 5 seconds
    updateIntervals.push(setInterval(() => {
        const oldLength = allLiveTransactions.length;
        loadLiveTransactions().then(() => {
            // If new transactions arrived and we're on page 1, stay on page 1
            // Otherwise maintain current page
            if (currentPage === 1 || allLiveTransactions.length !== oldLength) {
                displayLiveTransactionsPage();
            }
        });
    }, 5000));
    updateIntervals.push(setInterval(loadTodayStats, 10000));
    updateIntervals.push(setInterval(loadSystemStatus, 30000));
}

// =========================
// Transactions Functions
// =========================
async function loadAllTransactions(limit = 50) {
    const result = await apiCall(`/get_transactions?limit=${limit}`);
    if (!result || !result.ok) return;

    allTransactions = result.data;
    renderTransactions(allTransactions);
}

function renderTransactions(transactions) {
    const tbody = document.getElementById('transactionsTable');

    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No transactions found</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const statusClass = tx.status === 'Access Granted' ? 'status-granted' :
                          tx.status === 'Blocked' ? 'status-blocked' : 'status-denied';
        return `
            <tr>
                <td>${formatTimestamp(tx.timestamp)}</td>
                <td>${tx.name}</td>
                <td>${tx.card}</td>
                <td>Reader ${tx.reader}</td>
                <td><span class="status-badge-table ${statusClass}">${tx.status}</span></td>
            </tr>
        `;
    }).join('');
}

function filterTransactions(searchTerm) {
    const filtered = allTransactions.filter(tx => 
        tx.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tx.card.includes(searchTerm)
    );
    renderTransactions(filtered);
}

function initTransactions() {
    loadAllTransactions();

    document.getElementById('txLimit').addEventListener('change', (e) => {
        loadAllTransactions(e.target.value);
    });

    document.getElementById('txSearch').addEventListener('input', 
        debounce((e) => filterTransactions(e.target.value), 300)
    );

    document.getElementById('downloadCsvBtn').addEventListener('click', downloadCsv);
}

async function downloadCsv() {
    const result = await apiCall('/download_transactions_csv');
    if (!result || !result.ok) {
        showNotification('Failed to generate CSV', 'error');
        return;
    }

    // Create blob and download
    const csvContent = result.data.csv;
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// =========================
// Users Functions
// =========================
async function loadUsers() {
    const result = await apiCall('/get_users');
    if (!result || !result.ok) return;

    allUsers = result.data;
    renderUsers(allUsers);
}

function renderUsers(users) {
    const tbody = document.getElementById('usersTable');

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No users found</td></tr>';
        return;
    }

    tbody.innerHTML = users.map(user => {
        const statusBadge = user.blocked ? 
            '<span class="badge-blocked">BLOCKED</span>' : 
            '<span class="badge-active">ACTIVE</span>';
        
        const privacyBadge = user.privacy_protected ?
            '<span class="badge-privacy">🔒 PROTECTED</span>' :
            '<span class="badge-normal">📝 LOGGING</span>';
        
        const blockBtn = user.blocked ?
            `<button class="action-btn btn-success" onclick="unblockUser('${user.card_number}')">Unblock</button>` :
            `<button class="action-btn btn-warning" onclick="blockUser('${user.card_number}')">Block</button>`;
        
        const privacyBtn = user.privacy_protected ?
            `<button class="action-btn btn-secondary" onclick="togglePrivacy('${user.card_number}', '${user.name}', false)">Disable Privacy</button>` :
            `<button class="action-btn btn-primary" onclick="togglePrivacy('${user.card_number}', '${user.name}', true)">Enable Privacy</button>`;

        return `
            <tr>
                <td>${user.name}</td>
                <td>${user.card_number}</td>
                <td>${user.id}</td>
                <td>${statusBadge}</td>
                <td>${privacyBadge}</td>
                <td>
                    ${privacyBtn}
                    ${blockBtn}
                    <button class="action-btn btn-danger" onclick="deleteUser('${user.card_number}', '${user.name}')">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterUsers(searchTerm) {
    const filtered = allUsers.filter(user => 
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.card_number.includes(searchTerm) ||
        user.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderUsers(filtered);
}

function initUsers() {
    loadUsers();

    document.getElementById('userSearch').addEventListener('input',
        debounce((e) => filterUsers(e.target.value), 300)
    );

    document.getElementById('addUserBtn').addEventListener('click', () => {
        document.getElementById('addUserModal').classList.add('show');
    });

    document.getElementById('addUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addUser();
    });
    
    document.getElementById('privacyForm').addEventListener('submit', confirmPrivacyToggle);
}

async function addUser() {
    const userData = {
        name: document.getElementById('newUserName').value,
        card_number: document.getElementById('newUserCard').value,
        id: document.getElementById('newUserId').value,
        ref_id: document.getElementById('newUserRefId').value || ''
    };

    const result = await apiCall('/add_user', {
        method: 'POST',
        body: JSON.stringify(userData)
    });

    if (result && result.ok) {
        showNotification('User added successfully', 'success');
        closeModal();
        document.getElementById('addUserForm').reset();
        loadUsers();
    } else {
        showNotification(result?.data?.message || 'Failed to add user', 'error');
    }
}

async function blockUser(cardNumber) {
    if (!confirm('Are you sure you want to block this user?')) return;

    const result = await apiCall('/block_user', {
        method: 'POST',
        body: JSON.stringify({ card_number: cardNumber })
    });

    if (result && result.ok) {
        showNotification('User blocked successfully', 'success');
        loadUsers();
    } else {
        showNotification('Failed to block user', 'error');
    }
}

async function unblockUser(cardNumber) {
    const result = await apiCall('/unblock_user', {
        method: 'POST',
        body: JSON.stringify({ card_number: cardNumber })
    });

    if (result && result.ok) {
        showNotification('User unblocked successfully', 'success');
        loadUsers();
    } else {
        showNotification('Failed to unblock user', 'error');
    }
}

async function deleteUser(cardNumber, name) {
    if (!confirm(`Are you sure you want to delete user "${name}"?`)) return;

    const result = await apiCall('/delete_user', {
        method: 'POST',
        body: JSON.stringify({ card_number: cardNumber })
    });

    if (result && result.ok) {
        showNotification('User deleted successfully', 'success');
        loadUsers();
    } else {
        showNotification('Failed to delete user', 'error');
    }
}

// =========================
// Advanced Analytics Functions
// =========================
let currentAnalyticsMode = 'all';
let currentAnalyticsPeriod = 30;

function initAnalytics() {
    // Mode switcher
    document.getElementById('analyticsMode').addEventListener('change', (e) => {
        currentAnalyticsMode = e.target.value;
        if (currentAnalyticsMode === 'all') {
            document.getElementById('systemAnalytics').style.display = 'block';
            document.getElementById('userAnalytics').style.display = 'none';
            loadSystemAnalytics();
        } else {
            document.getElementById('systemAnalytics').style.display = 'none';
            document.getElementById('userAnalytics').style.display = 'block';
        }
    });
    
    // Period selector
    document.getElementById('analyticsPeriod').addEventListener('change', (e) => {
        currentAnalyticsPeriod = parseInt(e.target.value);
        if (currentAnalyticsMode === 'all') {
            loadSystemAnalytics();
        }
    });
    
    // Refresh button
    document.getElementById('refreshAnalyticsBtn').addEventListener('click', () => {
        if (currentAnalyticsMode === 'all') {
            loadSystemAnalytics();
        }
    });
    
    // User report search
    document.getElementById('userReportSearchBtn').addEventListener('click', generateUserReport);
    document.getElementById('userReportSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') generateUserReport();
    });
    
    // Load initial data
    loadSystemAnalytics();
}

async function loadSystemAnalytics() {
    const result = await apiCall(`/get_analytics?days=${currentAnalyticsPeriod}`);
    if (!result || !result.ok) {
        showNotification('Failed to load analytics', 'error');
        return;
    }
    
    const analytics = result.data.analytics;
    
    // Update summary cards
    document.getElementById('analyticsTotal').textContent = analytics.total_transactions;
    
    const successRate = analytics.total_transactions > 0 
        ? ((analytics.status_breakdown.granted / analytics.total_transactions) * 100).toFixed(1)
        : 0;
    document.getElementById('analyticsSuccessRate').textContent = successRate + '%';
    
    document.getElementById('analyticsUniqueUsers').textContent = analytics.unique_users;
    
    const avgPerDay = (analytics.total_transactions / analytics.period_days).toFixed(1);
    document.getElementById('analyticsAvgPerDay').textContent = avgPerDay;
    
    // Render charts
    renderHourlyChart(analytics.hourly_distribution);
    renderStatusChart(analytics.status_breakdown);
    renderReaderChart(analytics.reader_breakdown);
    renderDailyChart(analytics.daily_distribution);
    
    // Update top users table
    renderTopUsersTable(analytics.top_users);
    
    // Update insights
    document.getElementById('insightPeakHour').textContent = formatHour(analytics.peak_hour);
    document.getElementById('insightPeakDay').textContent = analytics.peak_day || 'N/A';
    document.getElementById('insightBusiestReader').textContent = `Reader ${analytics.busiest_reader}`;
}

function renderHourlyChart(hourlyData) {
    const container = document.getElementById('hourlyChart');
    const maxValue = Math.max(...Object.values(hourlyData), 1);
    
    let html = '<div class="bar-chart">';
    for (let hour = 0; hour < 24; hour++) {
        const value = hourlyData[hour.toString()] || 0;
        const heightPercent = (value / maxValue) * 100;
        html += `
            <div class="bar-item">
                <div class="bar" style="height: ${heightPercent}%">
                    ${value > 0 ? `<span class="bar-value">${value}</span>` : ''}
                </div>
                <div class="bar-label">${hour}h</div>
            </div>
        `;
    }
    html += '</div>';
    container.innerHTML = html;
}

function renderStatusChart(statusData) {
    const container = document.getElementById('statusChart');
    const total = statusData.granted + statusData.denied + statusData.blocked || 1;
    
    const html = `
        <div class="pie-chart">
            <div class="pie-segments">
                <div class="pie-segment">
                    <div class="pie-slice" style="background: #4CAF50;">${statusData.granted}</div>
                    <div class="bar-label">Granted</div>
                </div>
                <div class="pie-segment">
                    <div class="pie-slice" style="background: #f44336;">${statusData.denied}</div>
                    <div class="bar-label">Denied</div>
                </div>
                <div class="pie-segment">
                    <div class="pie-slice" style="background: #FF9800;">${statusData.blocked}</div>
                    <div class="bar-label">Blocked</div>
                </div>
            </div>
            <div class="pie-legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #4CAF50;"></div>
                    <span>Granted: ${((statusData.granted/total)*100).toFixed(1)}%</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f44336;"></div>
                    <span>Denied: ${((statusData.denied/total)*100).toFixed(1)}%</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF9800;"></div>
                    <span>Blocked: ${((statusData.blocked/total)*100).toFixed(1)}%</span>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderReaderChart(readerData) {
    const container = document.getElementById('readerChart');
    const maxValue = Math.max(readerData[1], readerData[2], readerData[3], 1);
    
    const html = `
        <div class="bar-chart">
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[1]/maxValue)*100}%; background: linear-gradient(to top, #2196F3, #64B5F6);">
                    ${readerData[1] > 0 ? `<span class="bar-value">${readerData[1]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 1</div>
            </div>
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[2]/maxValue)*100}%; background: linear-gradient(to top, #4CAF50, #81C784);">
                    ${readerData[2] > 0 ? `<span class="bar-value">${readerData[2]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 2</div>
            </div>
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[3]/maxValue)*100}%; background: linear-gradient(to top, #FF9800, #FFB74D);">
                    ${readerData[3] > 0 ? `<span class="bar-value">${readerData[3]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 3</div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderDailyChart(dailyData) {
    const container = document.getElementById('dailyChart');
    
    // Sort days and take last 14 days
    const sortedDays = Object.keys(dailyData).sort().slice(-14);
    const maxValue = Math.max(...sortedDays.map(day => dailyData[day]), 1);
    
    if (sortedDays.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">No data available</p>';
        return;
    }
    
    let html = '<div class="bar-chart">';
    sortedDays.forEach(day => {
        const value = dailyData[day];
        const heightPercent = (value / maxValue) * 100;
        const label = day.substring(5); // MM-DD format
        html += `
            <div class="bar-item">
                <div class="bar" style="height: ${heightPercent}%">
                    ${value > 0 ? `<span class="bar-value">${value}</span>` : ''}
                </div>
                <div class="bar-label">${label}</div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

function renderTopUsersTable(topUsers) {
    const tbody = document.getElementById('topUsersTable');
    
    if (!topUsers || topUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = topUsers.map((user, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${user.name}</td>
            <td>${user.card}</td>
            <td><strong>${user.count}</strong></td>
            <td>
                <button class="action-btn btn-primary" onclick="viewUserReport('${user.card}')">View Report</button>
            </td>
        </tr>
    `).join('');
}

async function generateUserReport() {
    const searchTerm = document.getElementById('userReportSearch').value.trim();
    if (!searchTerm) {
        showNotification('Please enter a name or card number', 'error');
        return;
    }
    
    // Find user
    const usersResult = await apiCall('/get_users');
    if (!usersResult?.ok) {
        showNotification('Failed to load users', 'error');
        return;
    }
    
    const users = usersResult.data;
    const user = users.find(u => 
        u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.card_number === searchTerm
    );
    
    if (!user) {
        showNotification('User not found', 'error');
        return;
    }
    
    await viewUserReport(user.card_number);
}

async function viewUserReport(cardNumber) {
    // Switch to user mode if not already
    if (currentAnalyticsMode !== 'user') {
        document.getElementById('analyticsMode').value = 'user';
        document.getElementById('systemAnalytics').style.display = 'none';
        document.getElementById('userAnalytics').style.display = 'block';
        currentAnalyticsMode = 'user';
    }
    
    const result = await apiCall(`/get_user_report?card=${cardNumber}&days=${currentAnalyticsPeriod}`);
    if (!result || !result.ok) {
        showNotification(result?.data?.message || 'Failed to load user report', 'error');
        return;
    }
    
    const report = result.data.report;
    
    // Show results, hide empty state
    document.getElementById('userReportResults').style.display = 'block';
    document.getElementById('userReportEmpty').style.display = 'none';
    
    // Update user info
    const statusBadge = report.user.blocked ? 
        '<span class="badge-blocked">BLOCKED</span>' : 
        '<span class="badge-active">ACTIVE</span>';
    
    document.getElementById('userReportInfo').innerHTML = `
        <div class="user-info-item">
            <label>Name</label>
            <div class="value">${report.user.name}</div>
        </div>
        <div class="user-info-item">
            <label>Card Number</label>
            <div class="value">${report.user.card}</div>
        </div>
        <div class="user-info-item">
            <label>User ID</label>
            <div class="value">${report.user.id}</div>
        </div>
        <div class="user-info-item">
            <label>Status</label>
            <div class="value">${statusBadge}</div>
        </div>
    `;
    
    // Update summary
    document.getElementById('userTotalAccess').textContent = report.summary.total_accesses;
    document.getElementById('userGranted').textContent = report.summary.granted;
    document.getElementById('userDenied').textContent = report.summary.denied;
    document.getElementById('userAvgPerDay').textContent = report.summary.avg_per_day;
    
    // Render charts
    renderUserHourlyChart(report.hourly_pattern);
    renderUserReaderChart(report.reader_usage);
    
    // Update patterns
    document.getElementById('userFavoriteHour').textContent = formatHour(report.patterns.favorite_hour);
    document.getElementById('userMostUsedReader').textContent = `Reader ${report.patterns.most_used_reader}`;
    document.getElementById('userFirstAccess').textContent = report.patterns.first_access 
        ? formatTimestamp(report.patterns.first_access) : 'N/A';
    document.getElementById('userLastAccess').textContent = report.patterns.last_access 
        ? formatTimestamp(report.patterns.last_access) : 'N/A';
    
    // Render timeline
    renderUserTimeline(report.timeline);
}

function renderUserHourlyChart(hourlyData) {
    const container = document.getElementById('userHourlyChart');
    const maxValue = Math.max(...Object.values(hourlyData), 1);
    
    let html = '<div class="bar-chart">';
    for (let hour = 0; hour < 24; hour++) {
        const value = hourlyData[hour.toString()] || 0;
        const heightPercent = (value / maxValue) * 100;
        html += `
            <div class="bar-item">
                <div class="bar" style="height: ${heightPercent}%">
                    ${value > 0 ? `<span class="bar-value">${value}</span>` : ''}
                </div>
                <div class="bar-label">${hour}h</div>
            </div>
        `;
    }
    html += '</div>';
    container.innerHTML = html;
}

function renderUserReaderChart(readerData) {
    const container = document.getElementById('userReaderChart');
    const maxValue = Math.max(readerData[1], readerData[2], readerData[3], 1);
    
    const html = `
        <div class="bar-chart">
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[1]/maxValue)*100}%; background: linear-gradient(to top, #2196F3, #64B5F6);">
                    ${readerData[1] > 0 ? `<span class="bar-value">${readerData[1]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 1</div>
            </div>
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[2]/maxValue)*100}%; background: linear-gradient(to top, #4CAF50, #81C784);">
                    ${readerData[2] > 0 ? `<span class="bar-value">${readerData[2]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 2</div>
            </div>
            <div class="bar-item">
                <div class="bar" style="height: ${(readerData[3]/maxValue)*100}%; background: linear-gradient(to top, #FF9800, #FFB74D);">
                    ${readerData[3] > 0 ? `<span class="bar-value">${readerData[3]}</span>` : ''}
                </div>
                <div class="bar-label">Reader 3</div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderUserTimeline(timeline) {
    const tbody = document.getElementById('userTimelineTable');
    
    if (!timeline || timeline.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">No activity in selected period</td></tr>';
        return;
    }
    
    tbody.innerHTML = timeline.map(tx => {
        const statusClass = tx.status === 'Access Granted' ? 'status-granted' :
                          tx.status === 'Blocked' ? 'status-blocked' : 'status-denied';
        return `
            <tr>
                <td>${formatTimestamp(tx.timestamp)}</td>
                <td>Reader ${tx.reader}</td>
                <td><span class="status-badge-table ${statusClass}">${tx.status}</span></td>
            </tr>
        `;
    }).join('');
}

function formatHour(hour) {
    const h = hour % 12 || 12;
    const ampm = hour < 12 ? 'AM' : 'PM';
    return `${h}:00 ${ampm}`;
}

// Make viewUserReport global for onclick handlers
window.viewUserReport = viewUserReport;

// =========================
// Relay Control
// =========================
async function controlRelay(relayNum, action) {
    const result = await apiCall('/relay', {
        method: 'POST',
        body: JSON.stringify({
            relay: relayNum,
            action: action
        })
    });

    if (result && result.ok) {
        showNotification(`Relay ${relayNum}: ${action}`, 'success');
    } else {
        showNotification('Relay control failed', 'error');
    }
}

// =========================
// Configuration Management
// =========================
let currentConfig = null;

async function loadConfiguration() {
    const result = await apiCall('/get_config');
    if (!result || !result.ok) {
        showNotification('Failed to load configuration', 'error');
        return;
    }

    currentConfig = result.data.config;
    displayConfiguration(currentConfig);
}

function displayConfiguration(config) {
    // Set reader bit selections
    document.getElementById('reader1Bits').value = config.wiegand_bits.reader_1;
    document.getElementById('reader2Bits').value = config.wiegand_bits.reader_2;
    document.getElementById('reader3Bits').value = config.wiegand_bits.reader_3;

    // Display current values
    document.querySelector('#reader1Status .current-bits').textContent = config.wiegand_bits.reader_1;
    document.querySelector('#reader2Status .current-bits').textContent = config.wiegand_bits.reader_2;
    document.querySelector('#reader3Status .current-bits').textContent = config.wiegand_bits.reader_3;

    // Duplicate prevention & tracking
    document.getElementById('scanDelay').value = config.scan_delay_seconds;
    document.getElementById('entryExitEnabled').checked = config.entry_exit_tracking.enabled;
    document.getElementById('entryExitGap').value = config.entry_exit_tracking.min_gap_seconds;
    
    // Show/hide entry/exit gap setting based on enabled state
    const gapGroup = document.getElementById('entryExitGapGroup');
    if (config.entry_exit_tracking.enabled) {
        gapGroup.style.display = 'block';
    } else {
        gapGroup.style.display = 'none';
    }
    
    // Entity configuration
    document.getElementById('entityId').value = config.entity_id || 'default_entity';
    
    // Advanced RFID settings
    document.getElementById('wiegandTimeout').value = config.wiegand_timeout_ms;
    
    // Basic Auth setting
    document.getElementById('basicAuthEnabled').checked = config.basic_auth_enabled !== false; // Default to true if not set
}

function initConfiguration() {
    loadConfiguration();
    loadSystemTime();
    startBrowserTimeClock();

    document.getElementById('configForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveConfiguration();
    });

    document.getElementById('resetConfigBtn').addEventListener('click', () => {
        if (currentConfig) {
            displayConfiguration(currentConfig);
        }
    });
    
    // Entry/Exit toggle handler
    document.getElementById('entryExitEnabled').addEventListener('change', (e) => {
        const gapGroup = document.getElementById('entryExitGapGroup');
        if (e.target.checked) {
            gapGroup.style.display = 'block';
        } else {
            gapGroup.style.display = 'none';
        }
    });
    
    // Save Tracking Settings button
    document.getElementById('saveTrackingBtn').addEventListener('click', async () => {
        await saveTrackingSettings();
    });
    
    // Save Entity ID button
    document.getElementById('saveEntityBtn').addEventListener('click', async () => {
        await saveEntitySettings();
    });
    
    // Security form handler
    document.getElementById('securityForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateSecuritySettings();
    });
    
    // Time configuration handlers
    document.getElementById('syncWithPcBtn').addEventListener('click', async () => {
        await syncWithPcTime();
    });
    
    document.getElementById('enableNtpBtn').addEventListener('click', async () => {
        await enableNtpSync();
    });
    
    document.getElementById('refreshTimeBtn').addEventListener('click', async () => {
        await loadSystemTime();
    });
    
    document.getElementById('setManualTimeBtn').addEventListener('click', async () => {
        await setManualTime();
    });
    
    // Save Authentication Settings button
    document.getElementById('saveAuthSettingsBtn').addEventListener('click', async () => {
        await saveAuthSettings();
    });
}

async function saveTrackingSettings() {
    // Preserve all existing config
    const newConfig = {
        ...currentConfig,
        scan_delay_seconds: parseInt(document.getElementById('scanDelay').value),
        entry_exit_tracking: {
            enabled: document.getElementById('entryExitEnabled').checked,
            min_gap_seconds: parseInt(document.getElementById('entryExitGap').value)
        }
    };

    const saveBtn = document.getElementById('saveTrackingBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Saving...</span>';

    const result = await apiCall('/update_config', {
        method: 'POST',
        body: JSON.stringify({ config: newConfig })
    });

    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;

    if (result && result.ok) {
        showNotification('Tracking settings saved successfully!', 'success');
        currentConfig = newConfig;
    } else {
        showNotification(result?.data?.message || 'Failed to save tracking settings', 'error');
    }
}

async function saveEntitySettings() {
    // Preserve all existing config
    const newConfig = {
        ...currentConfig,
        entity_id: document.getElementById('entityId').value.trim() || 'default_entity'
    };

    const saveBtn = document.getElementById('saveEntityBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Saving...</span>';

    const result = await apiCall('/update_config', {
        method: 'POST',
        body: JSON.stringify({ config: newConfig })
    });

    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;

    if (result && result.ok) {
        showNotification('Entity ID saved successfully!', 'success');
        currentConfig = newConfig;
    } else {
        showNotification(result?.data?.message || 'Failed to save entity ID', 'error');
    }
}

async function saveConfiguration() {
    // Check authentication before attempting save
    const token = localStorage.getItem('authToken');
    const apiKey = localStorage.getItem('apiKey') || API_KEY;
    
    if (!token) {
        showNotification('Please login first', 'error');
        window.location.href = '/login';
        return;
    }
    
    if (!apiKey || apiKey === 'your-api-key-change-this') {
        showNotification('API key not configured. Please set it in localStorage or use the setup page.', 'error');
        return;
    }
    
    // Preserve existing config and only update changed fields
    const newConfig = {
        ...currentConfig,  // Preserve all existing settings
        wiegand_bits: {
            reader_1: parseInt(document.getElementById('reader1Bits').value),
            reader_2: parseInt(document.getElementById('reader2Bits').value),
            reader_3: parseInt(document.getElementById('reader3Bits').value)
        },
        wiegand_timeout_ms: parseInt(document.getElementById('wiegandTimeout').value),
        scan_delay_seconds: parseInt(document.getElementById('scanDelay').value),
        entry_exit_tracking: {
            enabled: document.getElementById('entryExitEnabled').checked,
            min_gap_seconds: parseInt(document.getElementById('entryExitGap').value)
        },
        entity_id: document.getElementById('entityId').value.trim() || 'default_entity'
    };

    const saveBtn = document.getElementById('saveConfigBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Saving...</span>';

    const result = await apiCall('/update_config', {
        method: 'POST',
        body: JSON.stringify({ config: newConfig })
    });

    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;

    if (result && result.ok) {
        showNotification(result.data.message || 'Configuration saved successfully', 'success');
        currentConfig = newConfig;
        displayConfiguration(newConfig);
    } else {
        const errorMsg = result?.data?.message || result?.error || 'Failed to save configuration';
        console.error('Save configuration error:', errorMsg, result);
        showNotification(errorMsg, 'error');
        
        // If authentication error, suggest re-login
        if (errorMsg.includes('Authentication') || errorMsg.includes('expired') || errorMsg.includes('invalid')) {
            setTimeout(() => {
                if (confirm('Authentication error. Would you like to login again?')) {
                    window.location.href = '/login';
                }
            }, 1000);
        }
    }
}

async function updateSecuritySettings() {
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const newApiKey = document.getElementById('newApiKey').value;
    
    // Validate passwords match if provided
    if (newPassword && newPassword !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    // Check if at least one field is provided
    if (!newPassword && !newApiKey) {
        showNotification('Please enter a new password or API key', 'error');
        return;
    }
    
    // Confirm security change
    if (!confirm('Are you sure you want to update security settings? You will need to update your saved credentials.')) {
        return;
    }
    
    const updateBtn = document.getElementById('updateSecurityBtn');
    const originalText = updateBtn.innerHTML;
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<span>Updating...</span>';
    
    const data = {};
    if (newPassword) data.new_password = newPassword;
    if (newApiKey) data.new_api_key = newApiKey;
    
    const result = await apiCall('/update_security', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    updateBtn.disabled = false;
    updateBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        showNotification(result.data.message || 'Security settings updated!', 'success');
        
        // Clear form
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
        document.getElementById('newApiKey').value = '';
        
        // If API key changed, show reminder
        if (newApiKey) {
            setTimeout(() => {
                alert('IMPORTANT: Update your API key in localStorage!\n\n1. Press F12\n2. Console tab\n3. Run: setApiKey(\'' + newApiKey + '\')');
            }, 500);
        }
    } else {
        showNotification(result?.data?.message || 'Failed to update security settings', 'error');
    }
}

async function saveAuthSettings() {
    // Check authentication before attempting save
    const token = localStorage.getItem('authToken');
    const apiKey = localStorage.getItem('apiKey') || API_KEY;
    
    if (!token) {
        showNotification('Please login first', 'error');
        window.location.href = '/login';
        return;
    }
    
    if (!apiKey || apiKey === 'your-api-key-change-this') {
        showNotification('API key not configured. Please set it in localStorage or use the setup page.', 'error');
        return;
    }
    
    if (!currentConfig) {
        showNotification('Configuration not loaded. Please refresh the page.', 'error');
        return;
    }
    
    const basicAuthEnabled = document.getElementById('basicAuthEnabled').checked;
    
    const newConfig = {
        ...currentConfig,
        basic_auth_enabled: basicAuthEnabled
    };
    
    const saveBtn = document.getElementById('saveAuthSettingsBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Saving...</span>';
    
    const result = await apiCall('/update_config', {
        method: 'POST',
        body: JSON.stringify({ config: newConfig })
    });
    
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        const status = basicAuthEnabled ? 'enabled' : 'disabled';
        showNotification(`Basic HTTP authentication ${status} successfully!`, 'success');
        currentConfig = newConfig;
    } else {
        const errorMsg = result?.data?.message || result?.error || 'Failed to save authentication settings';
        console.error('Save auth settings error:', errorMsg, result);
        showNotification(errorMsg, 'error');
        
        // If authentication error, suggest re-login
        if (errorMsg.includes('Authentication') || errorMsg.includes('expired') || errorMsg.includes('invalid')) {
            setTimeout(() => {
                if (confirm('Authentication error. Would you like to login again?')) {
                    window.location.href = '/login';
                }
            }, 1000);
        }
    }
}

// Make it global for onclick handlers
window.controlRelay = controlRelay;
window.blockUser = blockUser;
window.unblockUser = unblockUser;
window.deleteUser = deleteUser;

// =========================
// Tab Navigation
// =========================
function switchTab(tabName) {
    // Clear intervals
    updateIntervals.forEach(interval => clearInterval(interval));
    updateIntervals = [];

    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active from nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    currentTab = tabName;

    // Initialize tab content
    switch(tabName) {
        case 'dashboard':
            initDashboard();
            break;
        case 'transactions':
            initTransactions();
            break;
        case 'users':
            initUsers();
            break;
        case 'analytics':
            initAnalytics();
            break;
        case 'config':
            initConfiguration();
            break;
    }
}

// =========================
// Privacy Protection Functions
// =========================
let pendingPrivacyChange = null;

function togglePrivacy(cardNumber, name, enable) {
    // Store pending change
    pendingPrivacyChange = { cardNumber, name, enable };
    
    // Update modal
    document.getElementById('privacyUserName').textContent = name;
    document.getElementById('privacyUserCard').textContent = cardNumber;
    document.getElementById('privacyAction').textContent = enable ? 
        'Enable Privacy Protection (transactions will NOT be logged)' :
        'Disable Privacy Protection (transactions will be logged normally)';
    
    // Clear password field
    document.getElementById('privacyPassword').value = '';
    
    // Show modal
    document.getElementById('privacyModal').classList.add('show');
}

async function confirmPrivacyToggle(e) {
    e.preventDefault();
    
    if (!pendingPrivacyChange) return;
    
    const password = document.getElementById('privacyPassword').value;
    const confirmBtn = document.getElementById('confirmPrivacyBtn');
    const originalText = confirmBtn.innerHTML;
    
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span>Confirming...</span>';
    
    const result = await apiCall('/toggle_privacy', {
        method: 'POST',
        body: JSON.stringify({
            card_number: pendingPrivacyChange.cardNumber,
            password: password,
            enable: pendingPrivacyChange.enable
        })
    });
    
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        showNotification(result.data.message || 'Privacy setting updated', 'success');
        closePrivacyModal();
        loadUsers();  // Refresh user list
    } else {
        showNotification(result?.data?.message || 'Failed to update privacy setting', 'error');
    }
}

function closePrivacyModal() {
    document.getElementById('privacyModal').classList.remove('show');
    pendingPrivacyChange = null;
}

window.togglePrivacy = togglePrivacy;
window.closePrivacyModal = closePrivacyModal;

// =========================
// Modal Functions
// =========================
function closeModal() {
    document.getElementById('addUserModal').classList.remove('show');
}

window.closeModal = closeModal;

// =========================
// Logout
// =========================
async function logout() {
    await apiCall('/logout', { method: 'POST' });
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    window.location.href = '/login';
}

// =========================
// Initialization
// =========================
document.addEventListener('DOMContentLoaded', () => {
    // Set username display
    const username = localStorage.getItem('username') || 'Admin';
    const userDisplay = document.getElementById('userDisplay');
    if (userDisplay) {
        userDisplay.textContent = `Logged in as ${username}`;
    }

    // Tab navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.getAttribute('data-tab');
            switchTab(tab);
        });
    });

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Close modal on outside click
    document.getElementById('addUserModal').addEventListener('click', (e) => {
        if (e.target.id === 'addUserModal') {
            closeModal();
        }
    });
    
    document.getElementById('privacyModal').addEventListener('click', (e) => {
        if (e.target.id === 'privacyModal') {
            closePrivacyModal();
        }
    });

    // Initialize first tab
    switchTab('dashboard');
});

// Handle page visibility for auto-refresh
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Clear intervals when page is hidden
        updateIntervals.forEach(interval => clearInterval(interval));
        updateIntervals = [];
    } else {
        // Restart intervals when page is visible
        if (currentTab === 'dashboard') {
            initDashboard();
        }
    }
});

// =========================
// Time Management Functions
// =========================
let browserTimeInterval = null;
let systemTimeData = null;

async function loadSystemTime() {
    const result = await apiCall('/get_system_time');
    if (!result || !result.ok) {
        showNotification('Failed to load system time', 'error');
        return;
    }
    
    systemTimeData = result.data;
    
    // Update system time display
    const systemTime = new Date(systemTimeData.timestamp * 1000);
    document.getElementById('systemTimeDisplay').textContent = formatTimeHHMMSS(systemTime);
    document.getElementById('systemTimezone').textContent = `Timezone: ${systemTimeData.timezone}`;
    
    // Check time difference
    checkTimeDifference();
}

function startBrowserTimeClock() {
    // Clear existing interval if any
    if (browserTimeInterval) {
        clearInterval(browserTimeInterval);
    }
    
    // Update browser time immediately
    updateBrowserTime();
    
    // Update every second
    browserTimeInterval = setInterval(() => {
        updateBrowserTime();
        
        // Also update system time display if we have the data
        if (systemTimeData) {
            const systemTime = new Date(systemTimeData.timestamp * 1000);
            systemTime.setSeconds(systemTime.getSeconds() + Math.floor((Date.now() - (systemTimeData.timestamp * 1000)) / 1000));
            document.getElementById('systemTimeDisplay').textContent = formatTimeHHMMSS(systemTime);
        }
    }, 1000);
}

function updateBrowserTime() {
    const now = new Date();
    document.getElementById('browserTimeDisplay').textContent = formatTimeHHMMSS(now);
    
    // Get timezone offset
    const offset = -now.getTimezoneOffset();
    const offsetHours = Math.floor(Math.abs(offset) / 60);
    const offsetMinutes = Math.abs(offset) % 60;
    const offsetSign = offset >= 0 ? '+' : '-';
    const offsetString = `${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`;
    
    document.getElementById('browserTimezone').textContent = `Timezone: UTC${offsetString}`;
}

function formatTimeHHMMSS(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

function checkTimeDifference() {
    if (!systemTimeData) return;
    
    const systemTimestamp = systemTimeData.timestamp;
    const browserTimestamp = Math.floor(Date.now() / 1000);
    const differenceSeconds = Math.abs(browserTimestamp - systemTimestamp);
    
    const alertDiv = document.getElementById('timeDifferenceAlert');
    const differenceSpan = document.getElementById('timeDifference');
    
    // Show alert if difference is more than 10 seconds
    if (differenceSeconds > 10) {
        const minutes = Math.floor(differenceSeconds / 60);
        const seconds = differenceSeconds % 60;
        
        let differenceText = '';
        if (minutes > 0) {
            differenceText = `${minutes} minute${minutes > 1 ? 's' : ''} ${seconds} second${seconds !== 1 ? 's' : ''}`;
        } else {
            differenceText = `${seconds} second${seconds !== 1 ? 's' : ''}`;
        }
        
        differenceSpan.textContent = differenceText;
        alertDiv.style.display = 'block';
    } else {
        alertDiv.style.display = 'none';
    }
}

async function syncWithPcTime() {
    if (!confirm('This will set the system time to match your PC\'s current time. Continue?')) {
        return;
    }
    
    const syncBtn = document.getElementById('syncWithPcBtn');
    const originalText = syncBtn.innerHTML;
    syncBtn.disabled = true;
    syncBtn.innerHTML = '<span>Syncing...</span>';
    
    // Get current browser timestamp
    const browserTimestamp = Math.floor(Date.now() / 1000);
    
    const result = await apiCall('/set_system_time', {
        method: 'POST',
        body: JSON.stringify({ timestamp: browserTimestamp })
    });
    
    syncBtn.disabled = false;
    syncBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        showNotification('System time synchronized with your PC!', 'success');
        setTimeout(() => loadSystemTime(), 1000);
    } else {
        showNotification(result?.data?.message || 'Failed to sync time. Check sudo permissions.', 'error');
    }
}

async function enableNtpSync() {
    if (!confirm('This will enable automatic NTP time synchronization. The system will sync time from internet time servers. Continue?')) {
        return;
    }
    
    const ntpBtn = document.getElementById('enableNtpBtn');
    const originalText = ntpBtn.innerHTML;
    ntpBtn.disabled = true;
    ntpBtn.innerHTML = '<span>Enabling...</span>';
    
    const result = await apiCall('/enable_ntp', {
        method: 'POST',
        body: JSON.stringify({ enable: true })
    });
    
    ntpBtn.disabled = false;
    ntpBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        showNotification('NTP time synchronization enabled!', 'success');
        setTimeout(() => loadSystemTime(), 2000);
    } else {
        showNotification(result?.data?.message || 'Failed to enable NTP. Check sudo permissions.', 'error');
    }
}

async function setManualTime() {
    const manualTimeInput = document.getElementById('manualTimeInput');
    const timeValue = manualTimeInput.value;
    
    if (!timeValue) {
        showNotification('Please select a date and time', 'error');
        return;
    }
    
    if (!confirm(`Set system time to ${timeValue}?`)) {
        return;
    }
    
    const setBtn = document.getElementById('setManualTimeBtn');
    const originalText = setBtn.innerHTML;
    setBtn.disabled = true;
    setBtn.innerHTML = '<span>Setting...</span>';
    
    // Convert datetime-local input to timestamp
    const selectedDate = new Date(timeValue);
    const timestamp = Math.floor(selectedDate.getTime() / 1000);
    
    const result = await apiCall('/set_system_time', {
        method: 'POST',
        body: JSON.stringify({ timestamp: timestamp })
    });
    
    setBtn.disabled = false;
    setBtn.innerHTML = originalText;
    
    if (result && result.ok) {
        showNotification('System time set successfully!', 'success');
        manualTimeInput.value = '';
        setTimeout(() => loadSystemTime(), 1000);
    } else {
        showNotification(result?.data?.message || 'Failed to set time. Check sudo permissions.', 'error');
    }
}

