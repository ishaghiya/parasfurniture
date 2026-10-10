// Paras Furniture Dashboard JavaScript Engine
document.addEventListener('DOMContentLoaded', function () {
  let charts = {};

  // Utility Indian Currency Formatter
  function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(amount || 0);
  }

  // Toggle Custom Date Inputs
  const datePresetSelect = document.getElementById('filter_date_preset');
  datePresetSelect.addEventListener('change', function () {
    const customContainers = document.querySelectorAll('.custom-date-container');
    if (this.value === 'custom') {
      customContainers.forEach(el => el.classList.remove('d-none'));
    } else {
      customContainers.forEach(el => el.classList.add('d-none'));
    }
  });

  // Fetch Dashboard Data via AJAX
  function loadDashboardData() {
    const filters = {
      date_preset: document.getElementById('filter_date_preset').value,
      custom_start: document.getElementById('filter_custom_start').value,
      custom_end: document.getElementById('filter_custom_end').value,
      location: document.getElementById('filter_location').value,
      furniture_category_id: document.getElementById('filter_furniture_cat').value,
      expense_category_id: document.getElementById('filter_expense_cat').value
    };

    fetch('/api/dashboard/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters)
    })
      .then(response => response.json())
      .then(data => {
        updateKPIs(data.kpis);
        updateCharts(data.charts);
      })
      .catch(err => console.error('Error fetching dashboard analytics:', err));
  }

  // Update KPI Cards
  function updateKPIs(kpis) {
    document.getElementById('kpi_total_income').textContent = formatINR(kpis.total_income);
    document.getElementById('kpi_num_bills').textContent = `${kpis.num_bills} Bills (${kpis.num_customers} Clients)`;
    
    document.getElementById('kpi_total_expense').textContent = formatINR(kpis.total_expense);
    document.getElementById('kpi_highest_exp_cat').textContent = `Highest: ${kpis.highest_exp_category}`;
    
    document.getElementById('kpi_net_profit').textContent = formatINR(kpis.net_profit);
    document.getElementById('kpi_profit_margin').textContent = `Margin: ${kpis.profit_margin}%`;
    
    document.getElementById('kpi_pending_amount').textContent = formatINR(kpis.pending_amount);
    document.getElementById('kpi_amount_received').textContent = `Received: ${formatINR(kpis.amount_received)}`;

    document.getElementById('kpi_units_sold').textContent = `${kpis.total_units_sold} Units`;
    document.getElementById('kpi_most_sold_item').textContent = kpis.most_sold_item;
    document.getElementById('kpi_top_location').textContent = kpis.top_location;
    document.getElementById('kpi_top_customer').textContent = kpis.top_customer;
    document.getElementById('kpi_avg_bill_value').textContent = formatINR(kpis.avg_bill_value);
  }

  // Render or Destroy/Update Chart.js Charts
  function updateCharts(cData) {
    // 1. Income vs Expense Trend
    renderChart('chart_income_vs_expense', 'bar', {
      labels: cData.months,
      datasets: [
        { label: 'Income (₹)', data: cData.income_series, backgroundColor: '#16a34a' },
        { label: 'Expense (₹)', data: cData.expense_series, backgroundColor: '#dc2626' }
      ]
    });

    // 2. Expense Category Distribution
    renderChart('chart_expense_categories', 'doughnut', {
      labels: cData.exp_cat_labels,
      datasets: [{
        data: cData.exp_cat_values,
        backgroundColor: ['#b45309', '#0284c7', '#16a34a', '#d97706', '#dc2626', '#8b5cf6', '#ec4899', '#64748b']
      }]
    });

    // 3. Furniture Item Revenue
    renderChart('chart_furniture_revenue', 'bar', {
      labels: cData.items_labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: cData.items_revenue,
        backgroundColor: '#b45309'
      }]
    });

    // 4. Furniture Quantity Sold
    renderChart('chart_furniture_qty', 'bar', {
      labels: cData.items_labels,
      datasets: [{
        label: 'Units Sold',
        data: cData.items_qty,
        backgroundColor: '#0284c7'
      }]
    });

    // 5. Revenue by Location
    renderChart('chart_revenue_location', 'bar', {
      labels: cData.location_labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: cData.location_revenue,
        backgroundColor: '#1e293b'
      }]
    });

    // 6. Revenue by Customer
    renderChart('chart_revenue_customer', 'bar', {
      labels: cData.customer_labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: cData.customer_revenue,
        backgroundColor: '#16a34a'
      }]
    });

    // 7. Monthly Profit Trend
    renderChart('chart_monthly_profit', 'line', {
      labels: cData.months,
      datasets: [{
        label: 'Net Profit (₹)',
        data: cData.profit_series,
        borderColor: '#b45309',
        backgroundColor: 'rgba(180, 83, 9, 0.1)',
        fill: true,
        tension: 0.3
      }]
    });

    // 8. Payment Status Breakdown
    renderChart('chart_payment_status', 'pie', {
      labels: ['Paid', 'Partially Paid', 'Pending', 'Overdue'],
      datasets: [{
        data: [
          cData.payment_status.PAID || 0,
          cData.payment_status.PARTIALLY_PAID || 0,
          cData.payment_status.PENDING || 0,
          cData.payment_status.OVERDUE || 0
        ],
        backgroundColor: ['#16a34a', '#d97706', '#dc2626', '#7f1d1d']
      }]
    });

    // 9. Payment Method
    renderChart('chart_payment_method', 'doughnut', {
      labels: cData.payment_method.labels,
      datasets: [{
        data: cData.payment_method.values,
        backgroundColor: ['#0284c7', '#16a34a', '#b45309', '#8b5cf6', '#64748b']
      }]
    });
  }

  function renderChart(canvasId, type, dataConfig) {
    if (charts[canvasId]) {
      charts[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
      type: type,
      data: dataConfig,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // Filter Buttons
  document.getElementById('btn_apply_filters').addEventListener('click', loadDashboardData);
  document.getElementById('btn_reset_filters').addEventListener('click', function () {
    document.getElementById('filter_date_preset').value = 'this_year';
    document.getElementById('filter_custom_start').value = '';
    document.getElementById('filter_custom_end').value = '';
    document.getElementById('filter_location').value = '';
    document.getElementById('filter_furniture_cat').value = '';
    document.getElementById('filter_expense_cat').value = '';
    document.querySelectorAll('.custom-date-container').forEach(el => el.classList.add('d-none'));
    loadDashboardData();
  });

  // Initial Load
  loadDashboardData();
});
