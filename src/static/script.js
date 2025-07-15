// Global variabless
let currentUser = null;
let currentSection = 'dashboard';
let currentPage = 1;
let tickets = [];
let categories = [];
let departments = [];

// API Base URL
const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    checkAuthStatus();
    loadDepartments();
}

function setupEventListeners() {
    // Navigation
    document.getElementById('navToggle').addEventListener('click', toggleMobileMenu);
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavigation);
    });

    // Auth tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchAuthTab);
    });

    // Forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    document.getElementById('createTicketForm').addEventListener('submit', handleCreateTicket);

    // Role change in registration
    document.getElementById('regRole').addEventListener('change', handleRoleChange);

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Modal
    document.getElementById('closeModal').addEventListener('click', closeModal);
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('ticketModal');
        if (event.target === modal) {
            closeModal();
        }
    });

    // FAQ search
    document.getElementById('faqSearch').addEventListener('input', debounce(searchFAQs, 300));

    // Status filter
    document.getElementById('statusFilter').addEventListener('change', filterTickets);
}

function toggleMobileMenu() {
    const navMenu = document.getElementById('navMenu');
    navMenu.classList.toggle('show');
}

function handleNavigation(e) {
    e.preventDefault();
    const section = e.target.closest('.nav-link').dataset.section;
    showSection(section);
}

function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.style.display = 'none';
    });

    // Show selected section
    document.getElementById(`${section}-section`).style.display = 'block';

    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    currentSection = section;

    // Load section data
    switch(section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'tickets':
            loadTickets();
            break;
        case 'create-ticket':
            loadCreateTicketForm();
            break;
        case 'faq':
            loadFAQs();
            break;
    }
}

function switchAuthTab(e) {
    const tab = e.target.dataset.tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');

    // Show/hide forms
    if (tab === 'login') {
        document.getElementById('loginForm').style.display = 'flex';
        document.getElementById('registerForm').style.display = 'none';
    } else {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'flex';
    }
}

function handleRoleChange(e) {
    const role = e.target.value;
    const studentIdGroup = document.getElementById('studentIdGroup');
    const departmentGroup = document.getElementById('departmentGroup');

    if (role === 'student') {
        studentIdGroup.style.display = 'block';
        departmentGroup.style.display = 'none';
    } else if (role === 'staff') {
        studentIdGroup.style.display = 'none';
        departmentGroup.style.display = 'block';
    } else {
        studentIdGroup.style.display = 'none';
        departmentGroup.style.display = 'none';
    }
}

// Authentication functions
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showAuthenticatedUI();
            showSection('dashboard');
        } else {
            showLoginUI();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginUI();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = data.user;
            showToast('Login successful!', 'success');
            showAuthenticatedUI();
            showSection('dashboard');
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Login failed. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const formData = {
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        full_name: document.getElementById('regFullName').value,
        role: document.getElementById('regRole').value,
        password: document.getElementById('regPassword').value
    };

    if (formData.role === 'student') {
        formData.student_id = document.getElementById('regStudentId').value;
    } else if (formData.role === 'staff') {
        formData.department_id = parseInt(document.getElementById('regDepartment').value);
    }

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            switchAuthTab({ target: { dataset: { tab: 'login' } } });
            document.getElementById('registerForm').reset();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Registration failed. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        showToast('Logged out successfully', 'success');
        showLoginUI();
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Logout failed', 'error');
    }
}

function showLoginUI() {
    document.getElementById('login-section').style.display = 'flex';
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById('navUser').style.display = 'none';
}

function showAuthenticatedUI() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('navUser').style.display = 'flex';
    document.getElementById('userName').textContent = currentUser.full_name;
    document.getElementById('userRole').textContent = currentUser.role;

    // Hide create ticket link for non-students
    const createTicketLink = document.querySelector('[data-section="create-ticket"]');
    if (currentUser.role !== 'student') {
        createTicketLink.style.display = 'none';
    } else {
        createTicketLink.style.display = 'flex';
    }
}

// Dashboard functions
async function loadDashboard() {
    try {
        showLoading(true);
        
        // Load stats for staff/admin
        if (currentUser.role !== 'student') {
            const statsResponse = await fetch(`${API_BASE}/tickets/stats`, {
                credentials: 'include'
            });
            
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                renderStats(statsData.stats);
            }
        }

        // Load recent tickets
        const ticketsResponse = await fetch(`${API_BASE}/tickets/my-tickets?per_page=5`, {
            credentials: 'include'
        });

        if (ticketsResponse.ok) {
            const ticketsData = await ticketsResponse.json();
            renderRecentTickets(ticketsData.tickets);
        }

    } catch (error) {
        console.error('Dashboard load error:', error);
        showToast('Failed to load dashboard', 'error');
    } finally {
        showLoading(false);
    }
}

function renderStats(stats) {
    const statsGrid = document.getElementById('statsGrid');
    
    if (currentUser.role === 'student') {
        statsGrid.innerHTML = '';
        return;
    }

    const statCards = [
        { title: 'Total Tickets', value: stats.total, icon: 'fas fa-ticket-alt', color: '#667eea' },
        { title: 'Open Tickets', value: stats.open, icon: 'fas fa-folder-open', color: '#17a2b8' },
        { title: 'In Progress', value: stats.in_progress, icon: 'fas fa-clock', color: '#ffc107' },
        { title: 'Resolved', value: stats.resolved, icon: 'fas fa-check-circle', color: '#28a745' }
    ];

    if (stats.average_rating) {
        statCards.push({
            title: 'Avg Rating',
            value: stats.average_rating + '/5',
            icon: 'fas fa-star',
            color: '#fd7e14'
        });
    }

    statsGrid.innerHTML = statCards.map(stat => `
        <div class="stat-card">
            <div class="stat-icon" style="background-color: ${stat.color}">
                <i class="${stat.icon}"></i>
            </div>
            <div class="stat-content">
                <h3>${stat.value}</h3>
                <p>${stat.title}</p>
            </div>
        </div>
    `).join('');
}

function renderRecentTickets(tickets) {
    const container = document.getElementById('recentTicketsList');
    
    if (tickets.length === 0) {
        container.innerHTML = '<p>No recent tickets found.</p>';
        return;
    }

    container.innerHTML = tickets.map(ticket => `
        <div class="ticket-card" onclick="openTicketModal(${ticket.id})" style="border-left-color: ${getPriorityColor(ticket.priority)}">
            <div class="ticket-header">
                <div>
                    <div class="ticket-title">${ticket.title}</div>
                    <div class="ticket-id">${ticket.ticket_id}</div>
                </div>
                <div class="ticket-badges">
                    <span class="badge badge-${ticket.status}">${ticket.status.replace('_', ' ')}</span>
                    <span class="badge badge-${ticket.priority}">${ticket.priority}</span>
                </div>
            </div>
            <div class="ticket-meta">
                <div class="ticket-category">
                    <span>${ticket.category_name}</span>
                </div>
                <div>${formatDate(ticket.created_at)}</div>
            </div>
        </div>
    `).join('');
}

// Tickets functions
async function loadTickets() {
    try {
        showLoading(true);
        const status = document.getElementById('statusFilter').value;
        const url = `${API_BASE}/tickets/my-tickets?page=${currentPage}&per_page=10${status ? `&status=${status}` : ''}`;
        
        const response = await fetch(url, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            tickets = data.tickets;
            renderTickets(data.tickets);
            renderPagination(data.current_page, data.pages, data.total);
        } else {
            showToast('Failed to load tickets', 'error');
        }
    } catch (error) {
        console.error('Tickets load error:', error);
        showToast('Failed to load tickets', 'error');
    } finally {
        showLoading(false);
    }
}

function renderTickets(tickets) {
    const container = document.getElementById('ticketsList');
    
    if (tickets.length === 0) {
        container.innerHTML = '<p>No tickets found.</p>';
        return;
    }

    container.innerHTML = tickets.map(ticket => `
        <div class="ticket-card" onclick="openTicketModal(${ticket.id})" style="border-left-color: ${getPriorityColor(ticket.priority)}">
            <div class="ticket-header">
                <div>
                    <div class="ticket-title">${ticket.title}</div>
                    <div class="ticket-id">${ticket.ticket_id}</div>
                </div>
                <div class="ticket-badges">
                    <span class="badge badge-${ticket.status}">${ticket.status.replace('_', ' ')}</span>
                    <span class="badge badge-${ticket.priority}">${ticket.priority}</span>
                </div>
            </div>
            <div class="ticket-meta">
                <div class="ticket-category">
                    <span>${ticket.category_name} • ${ticket.department_name}</span>
                </div>
                <div>${formatDate(ticket.created_at)}</div>
            </div>
        </div>
    `).join('');
}

function filterTickets() {
    currentPage = 1;
    loadTickets();
}

// Create ticket functions
async function loadCreateTicketForm() {
    try {
        // Load categories
        const categoriesResponse = await fetch(`${API_BASE}/tickets/categories`, {
            credentials: 'include'
        });

        if (categoriesResponse.ok) {
            const categoriesData = await categoriesResponse.json();
            categories = categoriesData.categories;
            
            const categorySelect = document.getElementById('ticketCategory');
            categorySelect.innerHTML = '<option value="">Select Category</option>' +
                categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
        }

        // Load departments
        const departmentsResponse = await fetch(`${API_BASE}/auth/departments`, {
            credentials: 'include'
        });

        if (departmentsResponse.ok) {
            const departmentsData = await departmentsResponse.json();
            departments = departmentsData.departments;
            
            const departmentSelect = document.getElementById('ticketDepartment');
            departmentSelect.innerHTML = '<option value="">Select Department</option>' +
                departments.map(dept => `<option value="${dept.id}">${dept.name}</option>`).join('');
        }

    } catch (error) {
        console.error('Form load error:', error);
        showToast('Failed to load form data', 'error');
    }
}

async function handleCreateTicket(e) {
    e.preventDefault();
    
    const formData = {
        title: document.getElementById('ticketTitle').value,
        description: document.getElementById('ticketDescription').value,
        category_id: parseInt(document.getElementById('ticketCategory').value),
        department_id: parseInt(document.getElementById('ticketDepartment').value),
        priority: document.getElementById('ticketPriority').value
    };

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/tickets/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showToast(`Ticket created successfully! ID: ${data.ticket.ticket_id}`, 'success');
            document.getElementById('createTicketForm').reset();
            showSection('tickets');
        } else {
            showToast(data.error || 'Failed to create ticket', 'error');
        }
    } catch (error) {
        console.error('Create ticket error:', error);
        showToast('Failed to create ticket', 'error');
    } finally {
        showLoading(false);
    }
}

// FAQ functions
async function loadFAQs() {
    try {
        showLoading(true);
        
        // Load categories for FAQ filtering
        const categoriesResponse = await fetch(`${API_BASE}/tickets/categories`, {
            credentials: 'include'
        });

        if (categoriesResponse.ok) {
            const categoriesData = await categoriesResponse.json();
            renderFAQCategories(categoriesData.categories);
        }

        // Load FAQs
        const faqResponse = await fetch(`${API_BASE}/faq/`, {
            credentials: 'include'
        });

        if (faqResponse.ok) {
            const faqData = await faqResponse.json();
            renderFAQs(faqData.faqs);
        }

    } catch (error) {
        console.error('FAQ load error:', error);
        showToast('Failed to load FAQs', 'error');
    } finally {
        showLoading(false);
    }
}

function renderFAQCategories(categories) {
    const container = document.getElementById('faqCategories');
    container.innerHTML = `
        <button class="category-btn active" onclick="filterFAQs('')">All</button>
        ${categories.map(cat => `
            <button class="category-btn" onclick="filterFAQs(${cat.id})">${cat.name}</button>
        `).join('')}
    `;
}

function renderFAQs(faqs) {
    const container = document.getElementById('faqList');
    
    if (faqs.length === 0) {
        container.innerHTML = '<p>No FAQs found.</p>';
        return;
    }

    container.innerHTML = faqs.map(faq => `
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(${faq.id})">
                <span>${faq.question}</span>
                <i class="fas fa-chevron-down"></i>
            </div>
            <div class="faq-answer" id="faq-${faq.id}">
                ${faq.answer}
            </div>
        </div>
    `).join('');
}

function toggleFAQ(faqId) {
    const answer = document.getElementById(`faq-${faqId}`);
    answer.classList.toggle('show');
    
    // Update view count
    fetch(`${API_BASE}/faq/${faqId}`, {
        credentials: 'include'
    });
}

async function searchFAQs() {
    const query = document.getElementById('faqSearch').value;
    
    try {
        const response = await fetch(`${API_BASE}/faq/search?q=${encodeURIComponent(query)}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderFAQs(data.faqs);
        }
    } catch (error) {
        console.error('FAQ search error:', error);
    }
}

async function filterFAQs(categoryId) {
    // Update active category button
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    try {
        const url = categoryId ? `${API_BASE}/faq/?category_id=${categoryId}` : `${API_BASE}/faq/`;
        const response = await fetch(url, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderFAQs(data.faqs);
        }
    } catch (error) {
        console.error('FAQ filter error:', error);
    }
}

// Modal functions
async function openTicketModal(ticketId) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/tickets/${ticketId}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderTicketModal(data.ticket);
            document.getElementById('ticketModal').style.display = 'block';
        } else {
            showToast('Failed to load ticket details', 'error');
        }
    } catch (error) {
        console.error('Ticket modal error:', error);
        showToast('Failed to load ticket details', 'error');
    } finally {
        showLoading(false);
    }
}

function renderTicketModal(ticket) {
    document.getElementById('modalTicketTitle').textContent = ticket.title;
    
    const ticketInfo = document.getElementById('ticketInfo');
    ticketInfo.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div><strong>Ticket ID:</strong> ${ticket.ticket_id}</div>
            <div><strong>Status:</strong> <span class="badge badge-${ticket.status}">${ticket.status.replace('_', ' ')}</span></div>
            <div><strong>Priority:</strong> <span class="badge badge-${ticket.priority}">${ticket.priority}</span></div>
            <div><strong>Category:</strong> ${ticket.category_name}</div>
            <div><strong>Department:</strong> ${ticket.department_name}</div>
            <div><strong>Created:</strong> ${formatDate(ticket.created_at)}</div>
        </div>
        <div style="margin-bottom: 20px;">
            <strong>Description:</strong>
            <p style="margin-top: 10px; padding: 15px; background: #f8f9fa; border-radius: 8px;">${ticket.description}</p>
        </div>
    `;

    // Render responses
    const responsesContainer = document.getElementById('ticketResponses');
    if (ticket.responses && ticket.responses.length > 0) {
        responsesContainer.innerHTML = `
            <h4 style="margin-bottom: 15px;">Responses</h4>
            ${ticket.responses.map(response => `
                <div class="response-item">
                    <div class="response-header">
                        <span class="response-author">${response.responder_name} (${response.responder_role})</span>
                        <span>${formatDate(response.created_at)}</span>
                    </div>
                    <div class="response-message">${response.message}</div>
                </div>
            `).join('')}
        `;
    } else {
        responsesContainer.innerHTML = '<p>No responses yet.</p>';
    }

    // Render response form
    const responseForm = document.getElementById('responseForm');
    responseForm.innerHTML = `
        <h4 style="margin: 20px 0 15px 0;">Add Response</h4>
        <form onsubmit="handleAddResponse(event, ${ticket.id})">
            <div class="form-group">
                <textarea id="responseMessage" rows="4" placeholder="Type your response..." required></textarea>
            </div>
            ${currentUser.role !== 'student' ? `
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="isInternal"> Internal note (not visible to student)
                    </label>
                </div>
            ` : ''}
            <button type="submit" class="btn btn-primary">Send Response</button>
        </form>
    `;

    // Add staff controls
    if (currentUser.role !== 'student') {
        responseForm.innerHTML += `
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                <h4>Staff Actions</h4>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px;">
                    <select onchange="updateTicketStatus(${ticket.id}, this.value)">
                        <option value="">Change Status</option>
                        <option value="open" ${ticket.status === 'open' ? 'selected' : ''}>Open</option>
                        <option value="in_progress" ${ticket.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                        <option value="resolved" ${ticket.status === 'resolved' ? 'selected' : ''}>Resolved</option>
                        <option value="closed" ${ticket.status === 'closed' ? 'selected' : ''}>Closed</option>
                    </select>
                    <select onchange="updateTicketPriority(${ticket.id}, this.value)">
                        <option value="">Change Priority</option>
                        <option value="low" ${ticket.priority === 'low' ? 'selected' : ''}>Low</option>
                        <option value="medium" ${ticket.priority === 'medium' ? 'selected' : ''}>Medium</option>
                        <option value="high" ${ticket.priority === 'high' ? 'selected' : ''}>High</option>
                        <option value="urgent" ${ticket.priority === 'urgent' ? 'selected' : ''}>Urgent</option>
                    </select>
                </div>
            </div>
        `;
    }

    // Add rating form for resolved tickets (students only)
    if (currentUser.role === 'student' && ticket.status === 'resolved' && !ticket.satisfaction_rating) {
        responseForm.innerHTML += `
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e9ecef;">
                <h4>Rate this ticket</h4>
                <div style="margin-top: 15px;">
                    <select onchange="rateTicket(${ticket.id}, this.value)">
                        <option value="">Select Rating</option>
                        <option value="1">1 - Poor</option>
                        <option value="2">2 - Fair</option>
                        <option value="3">3 - Good</option>
                        <option value="4">4 - Very Good</option>
                        <option value="5">5 - Excellent</option>
                    </select>
                </div>
            </div>
        `;
    }
}

async function handleAddResponse(e, ticketId) {
    e.preventDefault();
    
    const message = document.getElementById('responseMessage').value;
    const isInternal = document.getElementById('isInternal')?.checked || false;

    try {
        const response = await fetch(`${API_BASE}/tickets/${ticketId}/respond`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ message, is_internal: isInternal })
        });

        if (response.ok) {
            showToast('Response added successfully', 'success');
            openTicketModal(ticketId); // Refresh modal
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to add response', 'error');
        }
    } catch (error) {
        console.error('Add response error:', error);
        showToast('Failed to add response', 'error');
    }
}

async function updateTicketStatus(ticketId, status) {
    if (!status) return;

    try {
        const response = await fetch(`${API_BASE}/tickets/${ticketId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            showToast('Status updated successfully', 'success');
            openTicketModal(ticketId); // Refresh modal
            if (currentSection === 'tickets') {
                loadTickets(); // Refresh tickets list
            }
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to update status', 'error');
        }
    } catch (error) {
        console.error('Update status error:', error);
        showToast('Failed to update status', 'error');
    }
}

async function updateTicketPriority(ticketId, priority) {
    if (!priority) return;

    try {
        const response = await fetch(`${API_BASE}/tickets/${ticketId}/priority`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ priority })
        });

        if (response.ok) {
            showToast('Priority updated successfully', 'success');
            openTicketModal(ticketId); // Refresh modal
            if (currentSection === 'tickets') {
                loadTickets(); // Refresh tickets list
            }
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to update priority', 'error');
        }
    } catch (error) {
        console.error('Update priority error:', error);
        showToast('Failed to update priority', 'error');
    }
}

async function rateTicket(ticketId, rating) {
    if (!rating) return;

    try {
        const response = await fetch(`${API_BASE}/tickets/${ticketId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ rating: parseInt(rating) })
        });

        if (response.ok) {
            showToast('Rating submitted successfully', 'success');
            openTicketModal(ticketId); // Refresh modal
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to submit rating', 'error');
        }
    } catch (error) {
        console.error('Rate ticket error:', error);
        showToast('Failed to submit rating', 'error');
    }
}

function closeModal() {
    document.getElementById('ticketModal').style.display = 'none';
}

// Utility functions
async function loadDepartments() {
    try {
        const response = await fetch(`${API_BASE}/auth/departments`);
        if (response.ok) {
            const data = await response.json();
            departments = data.departments;
            
            // Populate registration form
            const departmentSelect = document.getElementById('regDepartment');
            if (departmentSelect) {
                departmentSelect.innerHTML = '<option value="">Select Department</option>' +
                    departments.map(dept => `<option value="${dept.id}">${dept.name}</option>`).join('');
            }
        }
    } catch (error) {
        console.error('Load departments error:', error);
    }
}

function renderPagination(currentPage, totalPages, totalItems) {
    const container = document.getElementById('ticketsPagination');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let pagination = '<div class="pagination">';
    
    // Previous button
    pagination += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">Previous</button>`;
    
    // Page numbers
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        pagination += `<button class="${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }
    
    // Next button
    pagination += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">Next</button>`;
    
    pagination += '</div>';
    container.innerHTML = pagination;
}

function changePage(page) {
    currentPage = page;
    loadTickets();
}

function getPriorityColor(priority) {
    const colors = {
        low: '#28a745',
        medium: '#ffc107',
        high: '#fd7e14',
        urgent: '#dc3545'
    };
    return colors[priority] || '#6c757d';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
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


// WebSocket functionality
let socket = null;

function initializeWebSocket() {
    if (!currentUser) return;
    
    socket = io('/', {
        withCredentials: true
    });
    
    socket.on('connect', function() {
        console.log('Connected to WebSocket');
        showToast('Real-time notifications enabled', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket');
        showToast('Real-time notifications disabled', 'warning');
    });
    
    // Listen for new tickets (staff/admin only)
    socket.on('new_ticket', function(data) {
        if (currentUser.role !== 'student') {
            showToast(data.message, 'info');
            playNotificationSound();
            
            // Refresh dashboard if visible
            if (currentSection === 'dashboard') {
                loadDashboard();
            }
            
            // Refresh tickets list if visible
            if (currentSection === 'tickets') {
                loadTickets();
            }
        }
    });
    
    // Listen for ticket updates
    socket.on('ticket_update', function(data) {
        showToast(data.message, 'info');
        playNotificationSound();
        
        // Refresh current section
        if (currentSection === 'dashboard') {
            loadDashboard();
        } else if (currentSection === 'tickets') {
            loadTickets();
        }
        
        // Update modal if open
        const modal = document.getElementById('ticketModal');
        if (modal.style.display === 'block') {
            // Refresh modal content
            openTicketModal(data.ticket.id);
        }
    });
    
    // Listen for new responses
    socket.on('new_response', function(data) {
        showToast(data.message, 'info');
        playNotificationSound();
        
        // Update modal if open and showing the same ticket
        const modal = document.getElementById('ticketModal');
        if (modal.style.display === 'block') {
            openTicketModal(data.ticket.id);
        }
    });
    
    // Listen for ticket assignments (staff only)
    socket.on('ticket_assigned', function(data) {
        if (currentUser.role === 'staff') {
            showToast(data.message, 'success');
            playNotificationSound();
            
            // Refresh dashboard and tickets
            if (currentSection === 'dashboard') {
                loadDashboard();
            } else if (currentSection === 'tickets') {
                loadTickets();
            }
        }
    });
    
    socket.on('error', function(error) {
        console.error('WebSocket error:', error);
    });
}

function disconnectWebSocket() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
}

function joinTicketRoom(ticketId) {
    if (socket) {
        socket.emit('join_ticket_room', { ticket_id: ticketId });
    }
}

function leaveTicketRoom(ticketId) {
    if (socket) {
        socket.emit('leave_ticket_room', { ticket_id: ticketId });
    }
}

function playNotificationSound() {
    // Create a simple notification sound
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.log('Audio notification not available');
    }
}

// Update existing functions to include WebSocket initialization
const originalShowAuthenticatedUI = showAuthenticatedUI;
showAuthenticatedUI = function() {
    originalShowAuthenticatedUI();
    initializeWebSocket();
};

const originalHandleLogout = handleLogout;
handleLogout = async function() {
    disconnectWebSocket();
    await originalHandleLogout();
};

// Update modal functions to join/leave ticket rooms
const originalOpenTicketModal = openTicketModal;
openTicketModal = async function(ticketId) {
    await originalOpenTicketModal(ticketId);
    joinTicketRoom(ticketId);
};

const originalCloseModal = closeModal;
closeModal = function() {
    // Get ticket ID from modal if available
    const ticketInfo = document.getElementById('ticketInfo');
    if (ticketInfo && ticketInfo.innerHTML.includes('Ticket ID:')) {
        // Extract ticket ID and leave room
        const ticketIdMatch = ticketInfo.innerHTML.match(/Ticket ID:<\/strong>\s*(\w+)/);
        if (ticketIdMatch) {
            const ticketId = ticketIdMatch[1];
            // Find the actual ticket ID from current tickets
            const ticket = tickets.find(t => t.ticket_id === ticketId);
            if (ticket) {
                leaveTicketRoom(ticket.id);
            }
        }
    }
    originalCloseModal();
};

document.addEventListener('DOMContentLoaded', function () {
  const whatsappForm = document.getElementById('whatsappForm');
  if (whatsappForm) {
    whatsappForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const to = document.getElementById('to').value;
      const body = document.getElementById('body').value;
      const resultDiv = document.getElementById('whatsappResult');
      resultDiv.textContent = 'Sending...';

      try {
        const response = await fetch('/api/whatsapp/send_whatsapp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ to, body })
        });
        const data = await response.json();
        if (response.ok) {
          resultDiv.textContent = 'Message sent! Check your WhatsApp.';
        } else {
          resultDiv.textContent = 'Error: ' + (data.error || 'Unknown error');
        }
      } catch (err) {
        resultDiv.textContent = 'Error: ' + err.message;
      }
    });
  }
});

