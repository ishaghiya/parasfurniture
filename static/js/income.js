// Paras Furniture Income & Client Bill Dynamic JavaScript
document.addEventListener('DOMContentLoaded', function () {
  const itemsContainer = document.getElementById('bill_items_container');
  const btnAddItem = document.getElementById('btn_add_item_row');

  if (!itemsContainer) return;

  function calculateBillTotals() {
    let subtotal = 0.0;
    const rows = itemsContainer.querySelectorAll('.item-row');

    rows.forEach(row => {
      const qty = parseFloat(row.querySelector('.item-qty').value) || 1;
      const price = parseFloat(row.querySelector('.item-price').value) || 0.0;
      const disc = parseFloat(row.querySelector('.item-disc').value) || 0.0;
      const tax = parseFloat(row.querySelector('.item-tax').value) || 0.0;

      const total = Math.max(0.0, (qty * price) - disc + tax);
      row.querySelector('.item-total').value = total.toFixed(2);
      subtotal += total;
    });

    document.getElementById('subtotal_input').value = subtotal.toFixed(2);

    const overallDisc = parseFloat(document.getElementById('overall_discount').value) || 0.0;
    const overallTax = parseFloat(document.getElementById('overall_tax').value) || 0.0;
    const finalBillAmount = Math.max(0.0, subtotal - overallDisc + overallTax);

    document.getElementById('final_bill_amount').value = finalBillAmount.toFixed(2);

    const amountReceived = parseFloat(document.getElementById('amount_received').value) || 0.0;
    const pendingAmount = Math.max(0.0, finalBillAmount - amountReceived);

    document.getElementById('pending_amount').value = pendingAmount.toFixed(2);

    // Auto update status badge preview
    const statusSelect = document.getElementById('payment_status');
    if (statusSelect && !statusSelect.disabled) {
      if (amountReceived >= finalBillAmount && finalBillAmount > 0) {
        statusSelect.value = 'PAID';
      } else if (amountReceived > 0 && amountReceived < finalBillAmount) {
        statusSelect.value = 'PARTIALLY_PAID';
      } else if (amountReceived === 0) {
        statusSelect.value = 'PENDING';
      }
    }
  }

  // Event Listeners for real-time recalculations
  itemsContainer.addEventListener('input', calculateBillTotals);
  document.getElementById('overall_discount').addEventListener('input', calculateBillTotals);
  document.getElementById('overall_tax').addEventListener('input', calculateBillTotals);
  document.getElementById('amount_received').addEventListener('input', calculateBillTotals);

  // Add Item Row
  if (btnAddItem) {
    btnAddItem.addEventListener('click', function () {
      const firstRow = itemsContainer.querySelector('.item-row');
      const newRow = firstRow.cloneNode(true);

      // Clear values
      newRow.querySelectorAll('input').forEach(input => {
        if (input.classList.contains('item-qty')) input.value = 1;
        else if (input.classList.contains('item-total')) input.value = '0.00';
        else input.value = '';
      });

      // Enable delete button on cloned row
      const btnRemove = newRow.querySelector('.btn-remove-row');
      if (btnRemove) {
        btnRemove.addEventListener('click', function () {
          if (itemsContainer.querySelectorAll('.item-row').length > 1) {
            newRow.remove();
            calculateBillTotals();
          }
        });
      }

      itemsContainer.appendChild(newRow);
      calculateBillTotals();
    });
  }

  // Initial calculation
  calculateBillTotals();
});
