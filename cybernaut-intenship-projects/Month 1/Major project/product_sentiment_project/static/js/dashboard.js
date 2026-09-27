/**
 * Sentiment-IQ — Product Sentiment Intelligence Dashboard Logic
 */

const API_BASE = '';
let pieChartInstance = null;
let lineChartInstance = null;
let barChartInstance = null;

let currentProductId = null;
let currentProductName = '';
let currentReviews = [];
let activeReviewFilter = 'all';

// DOM Elements
const analyzeBtn = document.getElementById('analyzeBtn');
const productInput = document.getElementById('productInput');
const sourceSelect = document.getElementById('sourceSelect');
const mockToggle = document.getElementById('mockToggle');
const statusEl = document.getElementById('status');
const productListEl = document.getElementById('productList');
const productCountBadge = document.getElementById('productCountBadge');
const dashboardEl = document.getElementById('dashboard');

const productTitleEl = document.getElementById('productTitle');
const productMetaEl = document.getElementById('productMeta');
const productSourceTag = document.getElementById('productSourceTag');
const productHealthTag = document.getElementById('productHealthTag');

const exportCsvBtn = document.getElementById('exportCsvBtn');
const deleteProductBtn = document.getElementById('deleteProductBtn');

const reviewSearchInput = document.getElementById('reviewSearchInput');
const reviewsCountBadge = document.getElementById('reviewsCountBadge');
const reviewsListEl = document.getElementById('reviewsList');
const toastContainer = document.getElementById('toastContainer');

// Palette Constants
const PALETTE = {
  positive: '#10B981',
  neutral: '#F59E0B',
  negative: '#F43F5E',
  primary: '#6366F1',
  cyan: '#06B6D4',
  textSub: '#94A3B8',
  bgInput: '#1E293B',
  border: 'rgba(255, 255, 255, 0.08)'
};

// Global Chart Defaults
Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.color = '#94A3B8';

// Initialization & Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  analyzeBtn.addEventListener('click', analyzeProduct);
  productInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') analyzeProduct();
  });

  // Preset Chips
  document.querySelectorAll('.chip-preset').forEach(chip => {
    chip.addEventListener('click', () => {
      productInput.value = chip.dataset.query;
      analyzeProduct();
    });
  });

  // Filter Tabs
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeReviewFilter = tab.dataset.filter;
      renderFilteredReviews();
    });
  });

  // Review Search
  reviewSearchInput.addEventListener('input', renderFilteredReviews);

  // Actions
  exportCsvBtn.addEventListener('click', exportReviewsToCsv);
  deleteProductBtn.addEventListener('click', deleteCurrentProduct);

  // Load existing products on load
  loadProducts();
});

// Analyze Product Endpoint Call
async function analyzeProduct() {
  const productName = productInput.value.trim();
  if (!productName) {
    showToast('Please enter a product name first.', 'error');
    return;
  }

  setLoadingState(true);
  statusEl.textContent = 'Analyzing reviews & calculating sentiment...';

  try {
    const res = await fetch(`${API_BASE}/api/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productName,
        source: sourceSelect.value,
        use_mock: mockToggle.checked
      })
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data.message || data.error || 'Failed to analyze product.';
      showToast(msg, 'error');
      statusEl.textContent = msg;
      return;
    }

    showToast(`Successfully analyzed ${data.reviews_added} reviews for ${data.product_name}!`, 'success');
    statusEl.textContent = `Added ${data.reviews_added} reviews.`;
    productInput.value = '';

    await loadProducts();
    await loadAnalytics(data.product_id, data.product_name);
  } catch (err) {
    showToast(`Request error: ${err.message}`, 'error');
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(isLoading) {
  analyzeBtn.disabled = isLoading;
  if (isLoading) {
    analyzeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
  } else {
    analyzeBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Analyze Sentiment';
  }
}

// Load Tracked Products
async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    const products = await res.json();

    productListEl.innerHTML = '';
    productCountBadge.textContent = products.length;

    if (products.length === 0) {
      productListEl.innerHTML = `
        <div class="empty-tracked">
          <i class="fa-solid fa-box-open"></i>
          <p>No products tracked yet. Search a product above to pull reviews!</p>
        </div>
      `;
      dashboardEl.classList.add('hidden');
      return;
    }

    products.forEach(p => {
      const chip = document.createElement('div');
      chip.className = `product-chip${p.id === currentProductId ? ' active' : ''}`;
      chip.innerHTML = `
        <i class="fa-solid fa-cube"></i>
        <span>${escapeHtml(p.name)}</span>
        <span class="product-chip-source">${escapeHtml(p.source)}</span>
      `;

      chip.addEventListener('click', () => {
        document.querySelectorAll('.product-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        loadAnalytics(p.id, p.name);
      });

      productListEl.appendChild(chip);
    });

    // If no product selected, select first
    if (!currentProductId && products.length > 0) {
      loadAnalytics(products[0].id, products[0].name);
    }
  } catch (err) {
    console.error('Failed to load products:', err);
  }
}

// Load Analytics & Reviews for Selected Product
async function loadAnalytics(productId, productName) {
  currentProductId = productId;
  currentProductName = productName;

  try {
    const [analyticsRes, reviewsRes] = await Promise.all([
      fetch(`${API_BASE}/api/analytics/${productId}`),
      fetch(`${API_BASE}/api/reviews/${productId}`)
    ]);

    if (!analyticsRes.ok || !reviewsRes.ok) {
      showToast('Error loading analytics for this product.', 'error');
      return;
    }

    const analytics = await analyticsRes.json();
    currentReviews = await reviewsRes.json();

    // Show Dashboard
    dashboardEl.classList.remove('hidden');

    // Hero Info
    productTitleEl.textContent = productName || 'Product';
    productMetaEl.innerHTML = `<i class="fa-solid fa-comments"></i> ${analytics.total_reviews} reviews analyzed • Real-time sentiment metrics`;

    // Render KPI & Health Status
    renderKPIs(analytics);

    // Render Charts
    renderPieChart(analytics.sentiment_distribution);
    renderLineChart(analytics.trend);
    renderBarChart(analytics.word_frequency);

    // Render Reviews
    renderFilteredReviews();

    // Refresh active state in product list
    document.querySelectorAll('.product-chip').forEach(chip => {
      if (chip.textContent.includes(productName)) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
  } catch (err) {
    showToast(`Failed to load data: ${err.message}`, 'error');
  }
}

// KPI calculation
function renderKPIs(analytics) {
  const dist = analytics.sentiment_distribution || {};
  const total = analytics.total_reviews || 0;

  const posCount = dist.positive || 0;
  const neuCount = dist.neutral || 0;
  const negCount = dist.negative || 0;

  const posPct = total ? Math.round((posCount / total) * 100) : 0;
  const neuPct = total ? Math.round((neuCount / total) * 100) : 0;
  const negPct = total ? Math.round((negCount / total) * 100) : 0;

  const avgScore = analytics.average_score || 0;

  // Sentiment Index Display
  document.getElementById('avgScore').textContent = (avgScore >= 0 ? '+' : '') + avgScore.toFixed(2);
  
  const scoreInterpEl = document.getElementById('scoreInterpretation');
  if (avgScore >= 0.25) {
    scoreInterpEl.textContent = '★ Excellent Sentiment';
    scoreInterpEl.className = 'kpi-status-text pos-color';
    productHealthTag.className = 'health-tag positive';
    productHealthTag.innerHTML = '<i class="fa-solid fa-shield-halved"></i> High Favorable Score';
  } else if (avgScore <= -0.05) {
    scoreInterpEl.textContent = '⚠ Negative / Concerns';
    scoreInterpEl.className = 'kpi-status-text neg-color';
    productHealthTag.className = 'health-tag negative';
    productHealthTag.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Cautionary Feedback';
  } else {
    scoreInterpEl.textContent = '⚖ Mixed Feedback';
    scoreInterpEl.className = 'kpi-status-text neu-color';
    productHealthTag.className = 'health-tag neutral';
    productHealthTag.innerHTML = '<i class="fa-solid fa-scale-balanced"></i> Balanced Sentiment';
  }

  // Positive KPI
  document.getElementById('positivePct').textContent = `${posPct}%`;
  document.getElementById('positiveCount').textContent = `(${posCount})`;
  document.getElementById('positiveBar').style.width = `${posPct}%`;

  // Neutral KPI
  document.getElementById('neutralPct').textContent = `${neuPct}%`;
  document.getElementById('neutralCount').textContent = `(${neuCount})`;
  document.getElementById('neutralBar').style.width = `${neuPct}%`;

  // Negative KPI
  document.getElementById('negativePct').textContent = `${negPct}%`;
  document.getElementById('negativeCount').textContent = `(${negCount})`;
  document.getElementById('negativeBar').style.width = `${negPct}%`;
}

// Chart 1: Doughnut Chart
function renderPieChart(distribution) {
  const ctx = document.getElementById('pieChart').getContext('2d');
  const labels = ['Positive', 'Neutral', 'Negative'];
  const values = [
    distribution.positive || 0,
    distribution.neutral || 0,
    distribution.negative || 0
  ];

  if (pieChartInstance) pieChartInstance.destroy();

  pieChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: [PALETTE.positive, PALETTE.neutral, PALETTE.negative],
        borderColor: '#0F172A',
        borderWidth: 3,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 16,
            font: { size: 12, weight: '600' }
          }
        },
        tooltip: {
          backgroundColor: '#1E293B',
          titleColor: '#F8FAFC',
          bodyColor: '#94A3B8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12
        }
      },
      cutout: '70%'
    }
  });
}

// Chart 2: Line Area Chart
function renderLineChart(trend) {
  const ctx = document.getElementById('lineChart').getContext('2d');
  const months = trend.map(t => t.month);

  const posGrad = ctx.createLinearGradient(0, 0, 0, 200);
  posGrad.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
  posGrad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

  const negGrad = ctx.createLinearGradient(0, 0, 0, 200);
  negGrad.addColorStop(0, 'rgba(244, 63, 94, 0.35)');
  negGrad.addColorStop(1, 'rgba(244, 63, 94, 0.0)');

  if (lineChartInstance) lineChartInstance.destroy();

  lineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Positive',
          data: trend.map(t => t.positive || 0),
          borderColor: PALETTE.positive,
          backgroundColor: posGrad,
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: 'Negative',
          data: trend.map(t => t.negative || 0),
          borderColor: PALETTE.negative,
          backgroundColor: negGrad,
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: 'Neutral',
          data: trend.map(t => t.neutral || 0),
          borderColor: PALETTE.neutral,
          backgroundColor: 'transparent',
          borderDash: [4, 4],
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { usePointStyle: true, font: { size: 12 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// Chart 3: Horizontal Bar Chart for Keywords
function renderBarChart(wordFreq) {
  const ctx = document.getElementById('barChart').getContext('2d');
  const top = (wordFreq || []).slice(0, 8);

  const barGrad = ctx.createLinearGradient(0, 0, 300, 0);
  barGrad.addColorStop(0, PALETTE.primary);
  barGrad.addColorStop(1, PALETTE.cyan);

  if (barChartInstance) barChartInstance.destroy();

  barChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(w => w.word),
      datasets: [{
        label: 'Mentions',
        data: top.map(w => w.count),
        backgroundColor: barGrad,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        y: {
          grid: { display: false }
        }
      }
    }
  });
}

// Render Reviews List with Filters & Search
function renderFilteredReviews() {
  const searchQuery = reviewSearchInput.value.toLowerCase().trim();

  let filtered = currentReviews.filter(r => {
    // Filter tab check
    if (activeReviewFilter !== 'all' && r.sentiment !== activeReviewFilter) {
      return false;
    }
    // Search query check
    if (searchQuery && !r.text.toLowerCase().includes(searchQuery)) {
      return false;
    }
    return true;
  });

  reviewsCountBadge.textContent = `${filtered.length} of ${currentReviews.length} reviews`;
  reviewsListEl.innerHTML = '';

  if (filtered.length === 0) {
    reviewsListEl.innerHTML = `
      <div style="text-align: center; color: var(--text-sub); padding: 40px 0;">
        <i class="fa-solid fa-filter-circle-xmark" style="font-size: 28px; margin-bottom: 10px;"></i>
        <p>No customer reviews match your selected filter.</p>
      </div>
    `;
    return;
  }

  // Sort newest first
  filtered.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));

  filtered.forEach(r => {
    const card = document.createElement('div');
    card.className = `review-card ${r.sentiment}`;

    const starsHtml = r.rating 
      ? '★'.repeat(Math.round(r.rating)) + '☆'.repeat(5 - Math.round(r.rating)) 
      : '★ ★ ★ ★ ★';

    const scoreDisplay = (r.score >= 0 ? '+' : '') + Number(r.score).toFixed(2);

    card.innerHTML = `
      <div class="review-card-top">
        <span class="review-badge ${r.sentiment}">
          <i class="fa-solid ${r.sentiment === 'positive' ? 'fa-thumbs-up' : r.sentiment === 'negative' ? 'fa-thumbs-down' : 'fa-minus'}"></i>
          ${r.sentiment}
        </span>
        <div class="review-score-meta">
          <span class="star-rating">${starsHtml}</span>
          <span>Score: <strong>${scoreDisplay}</strong></span>
        </div>
      </div>
      <div class="review-text-content">
        ${escapeHtml(r.text)}
      </div>
      <div class="review-card-footer">
        <span><i class="fa-regular fa-calendar"></i> ${r.date || 'Recent'}</span>
        <span>•</span>
        <span><i class="fa-solid fa-check-circle"></i> Verified Buyer</span>
      </div>
    `;

    reviewsListEl.appendChild(card);
  });
}

// Export Reviews as CSV
function exportReviewsToCsv() {
  if (!currentReviews || currentReviews.length === 0) {
    showToast('No reviews to export.', 'error');
    return;
  }

  let csvContent = 'data:text/csv;charset=utf-8,ID,Sentiment,Score,Rating,Date,Text\n';
  currentReviews.forEach((r, idx) => {
    const safeText = `"${r.text.replace(/"/g, '""')}"`;
    csvContent += `${idx + 1},${r.sentiment},${r.score},${r.rating || ''},${r.date || ''},${safeText}\n`;
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `${currentProductName.replace(/\s+/g, '_')}_sentiment_reviews.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast(`Exported ${currentReviews.length} reviews to CSV!`, 'success');
}

// Delete Current Product
async function deleteCurrentProduct() {
  if (!currentProductId) return;

  if (!confirm(`Are you sure you want to delete "${currentProductName}" and all its sentiment data?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/products/${currentProductId}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      showToast(`Deleted ${currentProductName}`, 'success');
      currentProductId = null;
      currentProductName = '';
      currentReviews = [];
      dashboardEl.classList.add('hidden');
      await loadProducts();
    } else {
      showToast('Failed to delete product.', 'error');
    }
  } catch (err) {
    showToast(`Delete failed: ${err.message}`, 'error');
  }
}

// Helper: Show Toast Notification
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
    <span>${escapeHtml(message)}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, match => {
    const escapeMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return escapeMap[match];
  });
}
