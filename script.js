const state = {
  dashboard: null,
  selectedChartType: 'bar',
  charts: {},
  currentUser: null,
};

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function setSection(sectionName) {
  document.querySelectorAll('.dashboard-section').forEach((section) => {
    section.classList.toggle('active', section.id === `${sectionName}-section`);
  });
  document.querySelectorAll('.nav-link').forEach((button) => {
    button.classList.toggle('active', button.dataset.section === sectionName);
  });
  const titleMap = {
    overview: 'Overview',
    transactions: 'Transactions',
    goals: 'Goals',
    targets: 'Targets',
    insights: 'Insights',
    literacy: 'Learning',
    profile: 'Profile',
  };
  const pageTitle = document.getElementById('page-title');
  if (pageTitle) pageTitle.textContent = titleMap[sectionName] || 'Dashboard';
}

function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '₹0';
  return currency.format(Number(value));
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('hidden');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('hidden');
}

function fetchData(url, options = {}) {
  return fetch(url, {
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || 'Request failed');
    }
    return data;
  });
}

function applyTheme(theme) {
  const dark = theme === 'dark';
  document.body.classList.toggle('dark-mode', dark);
  localStorage.setItem('smartlife-theme', theme);
  const toggleText = document.querySelector('#theme-toggle span');
  if (toggleText) toggleText.textContent = dark ? 'Light mode' : 'Dark mode';
  const toggleIcon = document.querySelector('#theme-toggle i');
  if (toggleIcon) {
    toggleIcon.className = dark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
  }
}

function toggleTheme() {
  const currentTheme = localStorage.getItem('smartlife-theme') || 'light';
  applyTheme(currentTheme === 'light' ? 'dark' : 'light');
}

function updateDashboardView() {
  if (!state.dashboard) return;
  const { metrics, coach, user, insights, upi, lessons } = state.dashboard;

  const userBadge = document.getElementById('user-badge');
  if (userBadge) userBadge.textContent = user?.name || 'User';

  document.getElementById('total-income').textContent = formatCurrency(metrics.total_income || 0);
  document.getElementById('total-expenses').textContent = formatCurrency(metrics.total_expenses || 0);
  document.getElementById('total-savings').textContent = formatCurrency(metrics.total_savings || 0);
  document.getElementById('savings-rate').textContent = `${metrics.savings_rate || 0}%`;
  document.getElementById('safe-to-spend').textContent = formatCurrency(metrics.safe_to_spend || 0);
  document.getElementById('safe-spend-text').textContent = 'Based on remaining monthly budget and remaining days.';

  const healthStatus = document.getElementById('health-status');
  const healthScore = document.getElementById('health-score');
  const healthDescription = document.getElementById('health-description');
  const scoreRing = document.getElementById('score-ring');
  if (healthStatus) {
    healthStatus.textContent = metrics.status || 'Needs Attention';
    healthStatus.className = 'chip';
    if (metrics.status === 'Excellent') healthStatus.classList.add('success');
    else if (metrics.status === 'Good') healthStatus.classList.add('success');
    else if (metrics.status === 'Fair') healthStatus.classList.add('warning');
    else healthStatus.classList.add('danger');
  }
  if (healthScore) healthScore.textContent = `${metrics.health_score || 0}/100`;
  if (healthDescription) {
    const narrative = metrics.health_score >= 80 ? 'Strong budgeting and saving habits.' : metrics.health_score >= 65 ? 'Healthy progress with room to improve.' : metrics.health_score >= 50 ? 'Your habits are fair but can be improved.' : 'Your spending is high relative to income; focus on reducing unnecessary costs.';
    healthDescription.textContent = narrative;
  }
  if (scoreRing) {
    const degree = (metrics.health_score / 100) * 360;
    scoreRing.style.background = `conic-gradient(var(--primary) ${degree}deg, rgba(95, 78, 247, 0.14) 0deg 360deg)`;
  }

  const coachMessage = document.getElementById('coach-message');
  if (coachMessage) coachMessage.textContent = coach || 'Start tracking your spending to get guidance.';

  renderTransactionsTable();
  renderGoals();
  renderTargets();
  renderInsights(insights || []);
  renderUPI(upi || {});
  renderLessons(lessons || []);
  renderCharts();
}

function renderTransactionsTable() {
  const tableBody = document.getElementById('transactions-table-body');
  if (!tableBody) return;
  const transactions = state.dashboard?.transactions || [];
  tableBody.innerHTML = '';

  if (!transactions.length) {
    tableBody.innerHTML = '<tr><td colspan="7" class="muted">No transactions yet. Add your first income or expense to get started.</td></tr>';
    return;
  }

  transactions.forEach((transaction) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${new Date(transaction.date).toLocaleDateString()}</td>
      <td><span class="transaction-type ${transaction.type}">${transaction.type}</span></td>
      <td>${transaction.category}</td>
      <td>${transaction.payment}</td>
      <td>${transaction.note || '-'}</td>
      <td class="${transaction.type === 'income' ? 'green' : 'red'}">${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}</td>
      <td>
        <div class="row-actions">
          <button class="icon-btn" data-action="edit-transaction" data-id="${transaction.id}" title="Edit"><i class="fa-solid fa-pen"></i></button>
          <button class="icon-btn delete" data-action="delete-transaction" data-id="${transaction.id}" title="Delete"><i class="fa-solid fa-trash"></i></button>
        </div>
      </td>
    `;
    tableBody.appendChild(row);
  });
}

function renderGoals() {
  const grid = document.getElementById('goals-grid');
  if (!grid) return;
  const goals = state.dashboard?.goals || [];
  grid.innerHTML = '';

  if (!goals.length) {
    grid.innerHTML = '<div class="panel-card"><p class="muted">No savings goals yet. Create one to start planning for your next milestone.</p></div>';
    return;
  }

  goals.forEach((goal) => {
    const card = document.createElement('div');
    card.className = 'goal-card';
    const progress = Math.min((goal.saved / goal.amount) * 100, 100);
    card.innerHTML = `
      <div class="goal-header">
        <h4>${goal.name}</h4>
        <span class="chip ${progress >= 100 ? 'success' : 'warning'}">${Math.round(progress)}%</span>
      </div>
      <p>Target: ${formatCurrency(goal.amount)}</p>
      <p>Saved: ${formatCurrency(goal.saved)}</p>
      <p>Remaining: ${formatCurrency(goal.remaining || 0)}</p>
      <div class="progress-track"><div class="progress-fill" style="width: ${progress}%"></div></div>
      <div class="value-line">
        <span>Target date</span>
        <strong>${new Date(goal.target_date).toLocaleDateString()}</strong>
      </div>
      <div class="row-actions" style="margin-top:14px;">
        <button class="icon-btn" data-action="edit-goal" data-id="${goal.id}"><i class="fa-solid fa-pen"></i></button>
        <button class="icon-btn delete" data-action="delete-goal" data-id="${goal.id}"><i class="fa-solid fa-trash"></i></button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderTargets() {
  const grid = document.getElementById('targets-grid');
  if (!grid) return;
  const target = state.dashboard?.targets || {};
  const metrics = state.dashboard?.metrics || {};
  const rows = [
    { label: 'Income target', value: target.income_target || 0, current: metrics.total_income || 0, unit: 'Income' },
    { label: 'Expense limit', value: target.expense_target || 0, current: metrics.total_expenses || 0, unit: 'Spent' },
    { label: 'Savings target', value: target.savings_target || 0, current: metrics.total_savings || 0, unit: 'Saved' },
    { label: 'Food budget', value: target.food_target || 0, current: state.dashboard?.food_spend || 0, unit: 'Food' },
  ];

  grid.innerHTML = rows.map((row) => {
    const pct = row.value > 0 ? Math.min((row.current / row.value) * 100, 100) : 0;
    const over = row.current > row.value && row.label !== 'Income target' && row.label !== 'Savings target';
    return `
      <div class="target-card">
        <div class="target-header">
          <h4>${row.label}</h4>
          <span class="chip ${over ? 'danger' : 'success'}">${Math.round(pct)}%</span>
        </div>
        <p>Target: ${formatCurrency(row.value)}</p>
        <p>Current: ${formatCurrency(row.current)}</p>
        <p>Remaining: ${formatCurrency(Math.max(row.value - row.current, 0))}</p>
        ${over ? '<p class="warning-text">Warning: target exceeded.</p>' : '<p class="muted">On track.</p>'}
        <div class="progress-track"><div class="progress-fill" style="width: ${pct}%"></div></div>
      </div>
    `;
  }).join('');
}

function renderInsights(insights) {
  const grid = document.getElementById('insights-grid');
  if (!grid) return;
  if (!insights.length) {
    grid.innerHTML = '<div class="insight-card"><p class="muted">Insight data will appear as soon as transactions are recorded.</p></div>';
    return;
  }
  grid.innerHTML = insights.map((insight) => `
    <div class="insight-card">
      <h4>Smart insight</h4>
      <p>${insight}</p>
    </div>
  `).join('');
}

function renderUPI(upiStats) {
  const grid = document.getElementById('upi-grid');
  if (!grid) return;
  const entries = [
    ['Google Pay', upiStats['Google Pay'] || 0],
    ['PhonePe', upiStats['PhonePe'] || 0],
    ['Paytm', upiStats['Paytm'] || 0],
    ['BHIM UPI', upiStats['BHIM UPI'] || 0],
  ];
  grid.innerHTML = entries.map(([name, count]) => `
    <div class="upi-card">
      <h4>${name}</h4>
      <p>${count} transaction${count === 1 ? '' : 's'}</p>
    </div>
  `).join('');
}

function renderLessons(lessons) {
  const grid = document.getElementById('lessons-grid');
  if (!grid) return;
  grid.innerHTML = lessons.map((lesson) => `
    <div class="lesson-card">
      <h4>${lesson.topic}</h4>
      <p><strong>Explanation:</strong> ${lesson.explanation}</p>
      <p><strong>Example:</strong> ${lesson.example}</p>
      <p><strong>Tip:</strong> ${lesson.tip}</p>
    </div>
  `).join('');
}

function buildChartConfig(type, labels, datasets) {
  return {
    type,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
      },
      scales: type === 'doughnut' || type === 'bar' ? { y: { beginAtZero: true } } : { y: { beginAtZero: true } },
    },
  };
}

function renderCharts() {
  const finance = state.dashboard?.analytics || {};
  const incomeExpense = finance.income_vs_expense || { labels: [], values: [] };
  const category = finance.expense_category || { labels: [], values: [] };
  const monthly = finance.monthly || { labels: [], income: [], expense: [] };
  const savingsTrend = finance.savings_trend || { labels: [], values: [] };

  const chartOptions = {
    bar: {
      type: 'bar',
      data: {
        labels: incomeExpense.labels,
        datasets: [
          { label: 'Income', data: incomeExpense.values, backgroundColor: 'rgba(18,183,106,0.75)' },
          { label: 'Expenses', data: incomeExpense.values, backgroundColor: 'rgba(239,68,68,0.75)' },
        ],
      },
    },
  };

  if (state.charts.incomeExpense) state.charts.incomeExpense.destroy();
  state.charts.incomeExpense = new Chart(document.getElementById('incomeExpenseChart'), buildChartConfig(state.selectedChartType, incomeExpense.labels, [
    {
      label: 'Income / Expenses',
      data: incomeExpense.values,
      backgroundColor: ['#22c55e', '#ef4444'],
      borderColor: ['#16a34a', '#dc2626'],
      borderWidth: 1,
    },
  ]));

  if (state.charts.category) state.charts.category.destroy();
  state.charts.category = new Chart(document.getElementById('categoryChart'), buildChartConfig('doughnut', category.labels, [{
    data: category.values,
    backgroundColor: ['#5f4ef7', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#10b981', '#f97316'],
  }]));

  if (state.charts.monthly) state.charts.monthly.destroy();
  state.charts.monthly = new Chart(document.getElementById('monthlyChart'), buildChartConfig('line', monthly.labels, [
    { label: 'Income', data: monthly.income, borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.12)', fill: false },
    { label: 'Expenses', data: monthly.expense, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.12)', fill: false },
  ]));

  if (state.charts.savings) state.charts.savings.destroy();
  state.charts.savings = new Chart(document.getElementById('savingsChart'), buildChartConfig('line', savingsTrend.labels, [{
    label: 'Savings trend', data: savingsTrend.values, borderColor: '#5f4ef7', backgroundColor: 'rgba(95,78,247,0.12)', fill: true,
  }]));
}

async function loadDashboard() {
  try {
    const data = await fetchData('/api/dashboard');
    state.dashboard = data;
    updateDashboardView();
  } catch (error) {
    console.error(error);
    showToast(error.message || 'Unable to load dashboard.', 'error');
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const result = await fetchData('/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast(result.message || 'Login successful.', 'success');
    window.location.href = result.redirect || '/dashboard';
  } catch (error) {
    showToast(error.message || 'Invalid email or password.', 'error');
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const result = await fetchData('/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast(result.message || 'Account created successfully.', 'success');
    window.location.href = result.redirect || '/dashboard';
  } catch (error) {
    showToast(error.message || 'Unable to create account.', 'error');
  }
}

async function handleTransactionSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const result = await fetchData('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast(result.message || 'Transaction added successfully.', 'success');
    closeModal('transaction-modal');
    form.reset();
    await loadDashboard();
  } catch (error) {
    showToast(error.message || 'Unable to add transaction.', 'error');
  }
}

async function handleGoalSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const result = await fetchData('/api/goals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast(result.message || 'Goal created successfully.', 'success');
    closeModal('goal-modal');
    form.reset();
    await loadDashboard();
  } catch (error) {
    showToast(error.message || 'Unable to create goal.', 'error');
  }
}

async function handleProfileSubmit(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById('profile-name').value,
    email: document.getElementById('profile-email').value,
    user_type: document.getElementById('profile-user-type').value,
    bio: document.getElementById('profile-bio').value,
  };
  try {
    const result = await fetchData('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    showToast(result.message || 'Profile updated successfully.', 'success');
    await loadDashboard();
  } catch (error) {
    showToast(error.message || 'Unable to update profile.', 'error');
  }
}

async function deleteTransaction(id) {
  try {
    const result = await fetchData(`/api/transactions/${id}`, {
      method: 'DELETE',
    });
    showToast(result.message || 'Transaction deleted.', 'success');
    await loadDashboard();
  } catch (error) {
    showToast(error.message || 'Unable to delete transaction.', 'error');
  }
}

async function deleteGoal(id) {
  try {
    const result = await fetchData(`/api/goals/${id}`, {
      method: 'DELETE',
    });
    showToast(result.message || 'Goal deleted.', 'success');
    await loadDashboard();
  } catch (error) {
    showToast(error.message || 'Unable to delete goal.', 'error');
  }
}

async function logoutUser() {
  try {
    await fetchData('/api/logout', { method: 'POST' });
    window.location.href = '/login';
  } catch (error) {
    window.location.href = '/login';
  }
}

function bindGlobalEvents() {
  document.querySelectorAll('.nav-link').forEach((button) => {
    button.addEventListener('click', () => setSection(button.dataset.section));
  });

  document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });

  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  document.getElementById('categoryChart')?.addEventListener('click', () => setSection('insights'));

  document.getElementById('logout-btn')?.addEventListener('click', logoutUser);
  document.getElementById('add-transaction-btn')?.addEventListener('click', () => openModal('transaction-modal'));
  document.getElementById('add-goal-btn')?.addEventListener('click', () => openModal('goal-modal'));

  document.querySelectorAll('[data-close]').forEach((button) => {
    button.addEventListener('click', () => closeModal(button.dataset.close));
  });

  document.getElementById('login-form')?.addEventListener('submit', handleLoginSubmit);
  document.getElementById('register-form')?.addEventListener('submit', handleRegisterSubmit);
  document.getElementById('transaction-form')?.addEventListener('submit', handleTransactionSubmit);
  document.getElementById('goal-form')?.addEventListener('submit', handleGoalSubmit);
  document.getElementById('profile-form')?.addEventListener('submit', handleProfileSubmit);

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-action]');
    if (!button) return;
    const id = Number(button.dataset.id);
    const action = button.dataset.action;
    if (action === 'delete-transaction') deleteTransaction(id);
    if (action === 'delete-goal') deleteGoal(id);
  });

  document.querySelectorAll('.chart-type').forEach((button) => {
    button.addEventListener('click', () => {
      state.selectedChartType = button.dataset.chart;
      document.querySelectorAll('.chart-type').forEach((node) => node.classList.toggle('active', node === button));
      renderCharts();
    });
  });

  const filterType = document.getElementById('filter-type');
  const filterCategory = document.getElementById('filter-category');
  const filterPayment = document.getElementById('filter-payment');
  const search = document.getElementById('transaction-search');

  if (search) {
    search.addEventListener('input', async () => {
      await refreshTransactionList();
    });
  }
  [filterType, filterCategory, filterPayment].forEach((input) => {
    input?.addEventListener('change', refreshTransactionList);
  });
}

async function refreshTransactionList() {
  const query = new URLSearchParams();
  const type = document.getElementById('filter-type')?.value || '';
  const category = document.getElementById('filter-category')?.value || '';
  const payment = document.getElementById('filter-payment')?.value || '';
  const search = document.getElementById('transaction-search')?.value || '';

  if (type) query.set('type', type);
  if (category) query.set('category', category);
  if (payment) query.set('payment', payment);
  if (search) query.set('search', search);

  try {
    const data = await fetchData(`/api/transactions?${query.toString()}`);
    state.dashboard.transactions = data.transactions || [];
    renderTransactionsTable();
  } catch (error) {
    showToast(error.message || 'Unable to load filtered transactions.', 'error');
  }
}

async function populateProfileForm() {
  try {
    const result = await fetchData('/api/profile');
    const user = result.user;
    document.getElementById('profile-name').value = user.name || '';
    document.getElementById('profile-email').value = user.email || '';
    document.getElementById('profile-user-type').value = user.user_type || 'Other';
    document.getElementById('profile-bio').value = user.bio || '';
  } catch (error) {
    console.error(error);
  }
}

async function bootApp() {
  const preferredTheme = localStorage.getItem('smartlife-theme') || 'light';
  applyTheme(preferredTheme);

  bindGlobalEvents();

  const protectedPage = window.location.pathname.includes('/dashboard');
  if (protectedPage) {
    await loadDashboard();
    await populateProfileForm();
    return;
  }

  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLoginSubmit);
  }
}

document.addEventListener('DOMContentLoaded', bootApp);
