let pendingProductRow = null;
let productPreviewData = null;
let pendingSocietyRowTarget = null;
let societyPreviewData = null;
let rowCounter = 0;
let voluntaryAllMembers = [];
let voluntaryFiltered = [];
let pendingVoluntaryRow = null;
const voluntarySelections = {};

const _originalError = console.error;
console.error = (...args) => {
  if (typeof args[0] === "string" && args[0].includes("message channel closed")) return;
  _originalError.apply(console, args);
};

function money(value, prefix = "PHP ") {
  return `${prefix}${Number(value || 0).toLocaleString("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function nextRowKey() {
  rowCounter += 1;
  return `row_${Date.now()}_${rowCounter}`;
}

function addRow(type = "expense", options = {}) {
  document.getElementById("empty-row")?.remove();
  const rowKey = nextRowKey();
  const row = document.createElement("tr");
  row.className = "entry-row border-b border-gray-50 align-top";
  row.dataset.type = type;
  row.dataset.rowKey = rowKey;
  row.innerHTML = buildRowHTML(type, rowKey, options);
  document.getElementById("entries-body").appendChild(row);
  lucide.createIcons();
  renderReceiptGallery();
  updateTotals();
}

function buildRowHTML(type, rowKey, options = {}) {
  const isIncome = type === "income";
  const dateValue = options.date || "";
  const categoryValue = options.category || "";

  const typeBadge = isIncome
    ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-bold bg-green-100 text-green-700">
         <i data-lucide="trending-up" class="w-3 h-3"></i> Income
       </span>`
    : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-bold bg-red-100 text-red-700">
         <i data-lucide="trending-down" class="w-3 h-3"></i> Expense
       </span>`;

  const hiddenFields = isIncome
    ? `
      <div class="mt-1.5">
        <select name="income_source[]" class="select select-bordered select-xs w-full bg-gray-50 income-source-select" onchange="handleIncomeSourceChange(this)">
          <option value="other">Other Income</option>
          <option value="society">Society Fee</option>
          <option value="product">Product Sale</option>
          <option value="voluntary">Voluntary Funds</option>
        </select>
      </div>
      <input type="hidden" name="society_academic_year[]" class="society-ay-input" value="" />
      <input type="hidden" name="product_id[]" class="product-id-input" value="" />
      <input type="hidden" name="variant_id[]" class="variant-id-input" value="" />
    `
    : `
      <input type="hidden" name="income_source[]" value="" />
      <input type="hidden" name="society_academic_year[]" value="" />
      <input type="hidden" name="product_id[]" value="" />
      <input type="hidden" name="variant_id[]" value="" />
    `;

  const amountCells = isIncome
    ? `<td class="px-2 py-2">
         <input type="number" step="0.01" name="amount[]" placeholder="0.00" class="input input-bordered input-xs w-full bg-gray-50 amount-input" oninput="updateTotals()" required />
       </td>
       <td class="px-2 py-2 text-center text-gray-200">-</td>`
    : `<td class="px-2 py-2 text-center text-gray-200">-</td>
       <td class="px-2 py-2">
         <input type="number" step="0.01" name="amount[]" placeholder="0.00" class="input input-bordered input-xs w-full bg-gray-50 amount-input" oninput="updateTotals()" required />
       </td>`;

  return `
    <td class="px-2 py-2 w-28">
      ${typeBadge}
      <input type="hidden" name="entry_type[]" value="${type}" />
      <input type="hidden" name="row_key[]" value="${rowKey}" />
      ${hiddenFields}
    </td>
    <td class="px-2 py-2">
      <input type="date" name="date[]" value="${dateValue}" class="input input-xs w-full bg-gray-50 date-input" oninput="renderReceiptGallery()" required />
    </td>
    <td class="px-2 py-2">
      <input type="text" name="category[]" value="${categoryValue}" class="input input-xs w-full bg-gray-50 category-input" oninput="renderReceiptGallery()" placeholder="${isIncome ? "e.g. Membership Fee, Product Sale" : "e.g. Supplies, Event Expense"}" required />
    </td>
    <td class="px-2 py-2">
      <input type="text" name="description[]" class="input input-xs w-full bg-gray-50 description-input" oninput="renderReceiptGallery()" placeholder="${isIncome ? "Describe the income source" : "Describe the expense details"}" required />
    </td>
    <td class="px-2 py-2 text-center">
      <input type="number" name="quantity[]" min="1" value="1" class="input input-bordered input-xs w-20 text-center qty-input bg-gray-50" oninput="handleQtyChange(this)" />
    </td>
    <td class="px-2 py-2 text-center">
      <input type="number" name="unit_price[]" step="0.01" value="0" class="input input-bordered input-xs w-24 text-center unit-price-input bg-gray-50" oninput="handleUnitPriceChange(this)" />
    </td>
    <td class="px-2 py-2">
      <label class="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-gray-200 bg-gray-50 px-2 py-2 text-xs text-gray-500 hover:border-blue-300 hover:text-blue-600 transition-colors">
        <i data-lucide="image-plus" class="w-3.5 h-3.5 shrink-0"></i>
        <span class="receipt-label inline-block max-w-18 truncate text-center">Attach</span>
        <input type="file" accept="image/*" name="receipt_image__${rowKey}" class="hidden receipt-input" onchange="handleReceiptChange(this)" />
      </label>
    </td>
    ${amountCells}
    <td class="px-2 py-2">
      <div class="flex justify-end gap-1">
        <button type="button" onclick="addSubRow(this)" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-blue-600 hover:bg-blue-50" title="Add subrow with same category">
          <i data-lucide="indent-increase" class="w-4 h-4"></i>
        </button>
        <button type="button" onclick="addRow('income')" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-green-600 hover:bg-green-50" title="Add income to bottom">
          <i data-lucide="plus-circle" class="w-4 h-4"></i>
        </button>
        <button type="button" onclick="addRow('expense')" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-red-600 hover:bg-red-50" title="Add expense to bottom">
          <i data-lucide="minus-circle" class="w-4 h-4"></i>
        </button>
        <button type="button" onclick="removeRow(this)" class="inline-flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 hover:text-red-600" title="Remove row">
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      </div>
    </td>
  `;
}

function restoreEmptyState() {
  document.getElementById("entries-body").innerHTML = `
    <tr id="empty-row">
      <td colspan="10" class="px-4 py-8 text-center text-sm text-gray-400">
        <div class="flex flex-col items-center gap-2">
          <i data-lucide="inbox" class="w-8 h-8 text-gray-300"></i>
          <span>No entries yet. Add an income or expense row to get started.</span>
          <div class="flex items-center gap-2 pt-2">
            <button type="button" onclick="addRow('income')" class="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-green-50 text-green-700 hover:bg-green-100 transition-colors">
              <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
              Add Income
            </button>
            <button type="button" onclick="addRow('expense')" class="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-red-50 text-red-700 hover:bg-red-100 transition-colors">
              <i data-lucide="minus-circle" class="w-3.5 h-3.5"></i>
              Add Expense
            </button>
          </div>
        </div>
      </td>
    </tr>
  `;
  lucide.createIcons();
}

function removeRow(btn) {
  btn.closest("tr").remove();
  if (!document.querySelector(".entry-row")) restoreEmptyState();
  renderReceiptGallery();
  updateTotals();
}

function addSubRow(btn) {
  const currentRow = btn.closest("tr");
  const type = currentRow.dataset.type || "expense";
  const date = currentRow.querySelector(".date-input")?.value || "";
  const category = currentRow.querySelector(".category-input")?.value || "";
  addRow(type, { date, category });
}

function handleReceiptChange(input) {
  const row = input.closest("tr");
  const label = row.querySelector(".receipt-label");
  const file = input.files?.[0];
  if (!file) {
    label.textContent = "Attach";
    renderReceiptGallery();
    return;
  }
  label.textContent = file.name.length > 10 ? `${file.name.slice(0, 10)}...` : file.name;
  renderReceiptGallery();
}

function deleteReceipt(rowKey) {
  const row = document.querySelector(`.entry-row[data-row-key="${rowKey}"]`);
  if (!row) return;
  const input = row.querySelector(".receipt-input");
  const label = row.querySelector(".receipt-label");
  if (input) input.value = "";
  if (label) label.textContent = "Attach";
  renderReceiptGallery();
}

function openReceiptPreviewModal(rowKey) {
  const row = document.querySelector(`.entry-row[data-row-key="${rowKey}"]`);
  if (!row) return;
  const input = row.querySelector(".receipt-input");
  const file = input?.files?.[0];
  if (!file) return;
  const category = row.querySelector(".category-input")?.value || "Receipt Preview";
  const description = row.querySelector(".description-input")?.value || "";
  const date = row.querySelector(".date-input")?.value || "";
  const imageUrl = URL.createObjectURL(file);
  document.getElementById("receipt-modal-title").textContent = category;
  document.getElementById("receipt-modal-description").textContent = description;
  document.getElementById("receipt-modal-date").textContent = date;
  document.getElementById("receipt-modal-image").src = imageUrl;
  document.getElementById("receipt-preview-modal").showModal();
}

function closeReceiptPreviewModal() {
  const modal = document.getElementById("receipt-preview-modal");
  const image = document.getElementById("receipt-modal-image");
  image.removeAttribute("src");
  modal.close();
}

function renderReceiptGallery() {
  const gallery = document.getElementById("receipt-gallery");
  const cards = [];
  document.querySelectorAll(".entry-row").forEach((row, index) => {
    const input = row.querySelector(".receipt-input");
    const file = input?.files?.[0];
    if (!file) return;
    const rowKey = row.dataset.rowKey;
    const category = row.querySelector(".category-input")?.value || "Uncategorized";
    const description = row.querySelector(".description-input")?.value || "No description";
    const date = row.querySelector(".date-input")?.value || "No date";
    const objectUrl = URL.createObjectURL(file);
    cards.push(`
      <div class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <button type="button" onclick="openReceiptPreviewModal('${rowKey}')" class="block w-full text-left">
          <img src="${objectUrl}" alt="Receipt ${index + 1}" class="h-48 w-full object-cover bg-gray-100">
        </button>
        <div class="p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-wide text-gray-400">${date}</p>
              <p class="mt-1 text-sm font-semibold text-gray-900">${category}</p>
            </div>
            <button type="button" onclick="deleteReceipt('${rowKey}')" class="inline-flex items-center gap-1 rounded-lg bg-red-50 px-2 py-1 text-xs font-semibold text-red-600 hover:bg-red-100">
              <i data-lucide="trash-2" class="w-3 h-3"></i>
              Delete
            </button>
          </div>
          <p class="mt-2 text-xs text-gray-500">${description}</p>
          <p class="mt-2 text-xs font-medium text-blue-600 truncate">${file.name}</p>
        </div>
      </div>
    `);
  });
  if (!cards.length) {
    gallery.innerHTML = `
      <div id="receipt-gallery-empty" class="border border-dashed border-gray-300 rounded-xl px-4 py-8 text-center text-sm text-gray-400 md:col-span-2 xl:col-span-4">
        No receipt images attached yet.
      </div>
    `;
    lucide.createIcons();
    return;
  }
  gallery.innerHTML = cards.join("");
  lucide.createIcons();
}

function updateTotals() {
  let income = 0;
  let expense = 0;
  document.querySelectorAll(".entry-row").forEach((row) => {
    const amount = parseFloat(row.querySelector(".amount-input")?.value) || 0;
    if (row.dataset.type === "income") income += amount;
    else expense += amount;
  });
  const net = income - expense;
  const netEl = document.getElementById("grand-total");
  document.getElementById("income-total").textContent = money(income);
  document.getElementById("expense-total").textContent = money(expense);
  netEl.textContent = `${net < 0 ? "-" : ""}${money(Math.abs(net))}`;
  netEl.className = `text-sm font-extrabold ${net >= 0 ? "text-green-700" : "text-red-700"}`;
}

function handleQtyChange(input) {
  const row = input.closest("tr");
  const qty = parseFloat(input.value) || 1;
  const unit = parseFloat(row.querySelector(".unit-price-input")?.value) || 0;
  const amountInput = row.querySelector(".amount-input");
  if (amountInput) amountInput.value = (qty * unit).toFixed(2);
  updateTotals();
}

function handleUnitPriceChange(input) {
  const row = input.closest("tr");
  const qty = parseFloat(row.querySelector(".qty-input")?.value) || 1;
  const unit = parseFloat(input.value) || 0;
  const amountInput = row.querySelector(".amount-input");
  if (amountInput) amountInput.value = (qty * unit).toFixed(2);
  updateTotals();
}

function clearLockedIncomeFields(row) {
  const qtyInput = row.querySelector(".qty-input");
  const unitPriceInput = row.querySelector(".unit-price-input");
  const amountInput = row.querySelector(".amount-input");
  const ayInput = row.querySelector(".society-ay-input");
  const productIdInput = row.querySelector(".product-id-input");
  const variantIdInput = row.querySelector(".variant-id-input");
  if (ayInput) ayInput.value = "";
  if (productIdInput) productIdInput.value = "";
  if (variantIdInput) variantIdInput.value = "";
  [qtyInput, unitPriceInput, amountInput].forEach((field) => {
    if (!field) return;
    field.readOnly = false;
    field.classList.remove("opacity-70", "cursor-not-allowed");
  });
}

function handleIncomeSourceChange(select) {
  const row = select.closest("tr");
  if (select.value === "society") {
    openSocietyModal(row);
    return;
  }
  if (select.value === "product") {
    openProductModal(row);
    return;
  }
  if (select.value === "voluntary") {
    openVoluntaryModal(row);
    return;
  }
  clearLockedIncomeFields(row);
}

// ── Society Fee ───────────────────────────────────────────────────

function openSocietyModal(row) {
  pendingSocietyRowTarget = row;
  societyPreviewData = null;
  document.getElementById("modal-ay").value = "";
  document.getElementById("society-preview").classList.add("hidden");
  document.getElementById("society-error").classList.add("hidden");
  document.getElementById("society-confirm-btn").disabled = true;
  document.getElementById("society-modal").showModal();
}

function closeSocietyModal() {
  if (pendingSocietyRowTarget) {
    const select = pendingSocietyRowTarget.querySelector(".income-source-select");
    if (select) select.value = "other";
    clearLockedIncomeFields(pendingSocietyRowTarget);
  }
  document.getElementById("society-modal").close();
  pendingSocietyRowTarget = null;
}

async function previewSocietyFee() {
  const ay = document.getElementById("modal-ay").value;
  const previewEl = document.getElementById("society-preview");
  const errorEl = document.getElementById("society-error");
  const confirmBtn = document.getElementById("society-confirm-btn");
  previewEl.classList.add("hidden");
  errorEl.classList.add("hidden");
  confirmBtn.disabled = true;
  societyPreviewData = null;
  if (!ay) {
    errorEl.textContent = "Please select an academic year.";
    errorEl.classList.remove("hidden");
    return;
  }
  try {
    const res = await fetch(`${URLS.societyFeePreview}?academic_year=${ay}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    societyPreviewData = data;
    document.getElementById("preview-count").textContent = data.student_count;
    document.getElementById("preview-fee").textContent = money(data.total);
    document.getElementById("society-preview-total").textContent = money(data.total);
    previewEl.classList.remove("hidden");
    confirmBtn.disabled = false;
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
}

function confirmSocietyFee() {
  if (!societyPreviewData || !pendingSocietyRowTarget) return;
  const row = pendingSocietyRowTarget;
  const ay = document.getElementById("modal-ay").value;
  const ayLabel = academicYears.find((item) => item.id === ay)?.label || ay;
  const qtyInput = row.querySelector(".qty-input");
  const unitPriceInput = row.querySelector(".unit-price-input");
  const amountInput = row.querySelector(".amount-input");
  const ayInput = row.querySelector(".society-ay-input");
  const categoryInput = row.querySelector('input[name="category[]"]');
  const descriptionInput = row.querySelector('input[name="description[]"]');
  if (ayInput) ayInput.value = ay;
  if (qtyInput) {
    qtyInput.value = societyPreviewData.student_count;
    qtyInput.readOnly = true;
    qtyInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (unitPriceInput) {
    unitPriceInput.value = 0;
    unitPriceInput.readOnly = true;
    unitPriceInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (amountInput) {
    amountInput.value = Number(societyPreviewData.total).toFixed(2);
    amountInput.readOnly = true;
    amountInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (categoryInput) categoryInput.value = "Society Fee";
  if (descriptionInput) {
    descriptionInput.value = `Society Fee - ${ayLabel} (${societyPreviewData.student_count} students paid ${money(societyPreviewData.total)})`;
  }
  updateTotals();
  document.getElementById("society-modal").close();
  pendingSocietyRowTarget = null;
}

// ── Product Sale ──────────────────────────────────────────────────

function openProductModal(row) {
  pendingProductRow = row;
  productPreviewData = null;
  document.getElementById("modal-product").value = "";
  document.getElementById("modal-variant").innerHTML = '<option value="">-- Select Variant --</option>';
  document.getElementById("modal-qty").value = 1;
  document.getElementById("product-preview").classList.add("hidden");
  document.getElementById("product-confirm-btn").disabled = true;
  document.getElementById("product-modal").showModal();
}

function closeProductModal() {
  if (pendingProductRow) {
    const select = pendingProductRow.querySelector(".income-source-select");
    if (select) select.value = "other";
    clearLockedIncomeFields(pendingProductRow);
  }
  document.getElementById("product-modal").close();
  pendingProductRow = null;
}

function loadModalVariants() {
  const productId = document.getElementById("modal-product").value;
  const variantSelect = document.getElementById("modal-variant");
  variantSelect.innerHTML = '<option value="">-- Select Variant --</option>';
  if (!productId || !PRODUCTS[productId]) return;
  PRODUCTS[productId].forEach((variant) => {
    const option = document.createElement("option");
    option.value = variant.id;
    option.dataset.price = variant.price;
    option.textContent = `${variant.label} - ${money(variant.price)}`;
    variantSelect.appendChild(option);
  });
}

function localPreview() {
  const variantSelect = document.getElementById("modal-variant");
  const qty = parseInt(document.getElementById("modal-qty").value || 1, 10);
  const price = parseFloat(variantSelect.selectedOptions[0]?.dataset.price || 0);
  if (!price) {
    document.getElementById("product-preview").classList.add("hidden");
    document.getElementById("product-confirm-btn").disabled = true;
    productPreviewData = null;
    return;
  }
  const total = price * qty;
  document.getElementById("product-preview-unit").textContent = money(price);
  document.getElementById("product-preview-qty").textContent = qty;
  document.getElementById("product-preview-total").textContent = money(total);
  document.getElementById("product-preview").classList.remove("hidden");
  document.getElementById("product-confirm-btn").disabled = false;
  productPreviewData = { unit_price: price, quantity: qty, total };
}

function confirmProduct() {
  if (!productPreviewData || !pendingProductRow) return;
  const row = pendingProductRow;
  const qty = parseFloat(document.getElementById("modal-qty").value || 1);
  const productId = document.getElementById("modal-product").value;
  const variantId = document.getElementById("modal-variant").value;
  const productName = document.getElementById("modal-product").selectedOptions[0]?.text || "";
  const variantName = document.getElementById("modal-variant").selectedOptions[0]?.text || "";
  const qtyInput = row.querySelector(".qty-input");
  const unitPriceInput = row.querySelector(".unit-price-input");
  const amountInput = row.querySelector(".amount-input");
  row.querySelector(".product-id-input").value = productId;
  row.querySelector(".variant-id-input").value = variantId;
  if (qtyInput) {
    qtyInput.value = qty;
    qtyInput.readOnly = true;
    qtyInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (unitPriceInput) {
    unitPriceInput.value = productPreviewData.unit_price;
    unitPriceInput.readOnly = true;
    unitPriceInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (amountInput) {
    amountInput.value = (productPreviewData.unit_price * qty).toFixed(2);
    amountInput.readOnly = true;
    amountInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  row.querySelector('input[name="category[]"]').value = "Product Sale";
  row.querySelector('input[name="description[]"]').value = `Product Sale - ${productName} (${variantName}) x${qty}`;
  updateTotals();
  document.getElementById("product-modal").close();
  pendingProductRow = null;
}

// ── Voluntary Funds ───────────────────────────────────────────────

async function openVoluntaryModal(row) {
  pendingVoluntaryRow = row;
  Object.keys(voluntarySelections).forEach((k) => delete voluntarySelections[k]);
  document.getElementById("voluntary-search").value = "";
  document.getElementById("voluntary-preview").classList.add("hidden");
  document.getElementById("voluntary-preview").classList.remove("flex");
  document.getElementById("voluntary-confirm-btn").disabled = true;
  document.getElementById("voluntary-member-list").innerHTML =
    '<p class="text-xs text-gray-400 text-center py-4">Loading members...</p>';
  document.getElementById("voluntary-showing-count").textContent = "0";
  document.getElementById("voluntary-modal").showModal();
  lucide.createIcons();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(URLS.voluntaryMembers, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    voluntaryAllMembers = data.members || [];
    voluntaryFiltered = [...voluntaryAllMembers];
    renderVoluntaryList();
  } catch (err) {
    if (err.name === "AbortError") {
      document.getElementById("voluntary-member-list").innerHTML =
        '<p class="text-xs text-red-500 text-center py-4">Request timed out. Please try again.</p>';
    } else if (err.message.includes("message channel closed")) {
      console.warn("Extension interference detected, retrying...");
      try {
        const res = await fetch(URLS.voluntaryMembers, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const data = await res.json();
        voluntaryAllMembers = data.members || [];
        voluntaryFiltered = [...voluntaryAllMembers];
        renderVoluntaryList();
      } catch {
        document.getElementById("voluntary-member-list").innerHTML =
          '<p class="text-xs text-red-500 text-center py-4">Failed to load members. Please try again.</p>';
      }
    } else {
      document.getElementById("voluntary-member-list").innerHTML =
        '<p class="text-xs text-red-500 text-center py-4">Failed to load members. Please try again.</p>';
      console.error("Voluntary modal fetch error:", err);
    }
  }
}

function closeVoluntaryModal() {
  if (pendingVoluntaryRow) {
    const select = pendingVoluntaryRow.querySelector(".income-source-select");
    if (select) select.value = "other";
    clearLockedIncomeFields(pendingVoluntaryRow);
  }
  document.getElementById("voluntary-modal").close();
  pendingVoluntaryRow = null;
}

function filterVoluntaryMembers() {
  const q = document.getElementById("voluntary-search").value.toLowerCase().trim();
  voluntaryFiltered = q
    ? voluntaryAllMembers.filter((m) => m.name.toLowerCase().includes(q) || String(m.student_id).includes(q))
    : [...voluntaryAllMembers];
  renderVoluntaryList();
}

function renderVoluntaryList() {
  const container = document.getElementById("voluntary-member-list");
  document.getElementById("voluntary-showing-count").textContent = voluntaryFiltered.length;

  if (!voluntaryFiltered.length) {
    container.innerHTML = `
      <div class="flex flex-col items-center gap-2 py-6 text-center">
        <div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
          <i data-lucide="user-x" class="w-5 h-5 text-gray-400"></i>
        </div>
        <p class="text-sm font-semibold text-gray-500">No members found</p>
        <p class="text-xs text-gray-400">Try a different name or ID</p>
      </div>`;
    lucide.createIcons();
    return;
  }

  function getInitials(name) {
    return name
      .split(" ")
      .map((w) => w[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }

  container.innerHTML = voluntaryFiltered
    .map((m) => {
      const sel = voluntarySelections[m.id] || {};
      const checked = sel.checked || false;
      const amount = sel.amount || "";

      const rowBase = checked
        ? "flex items-center gap-3 rounded-xl px-3 py-2.5 border border-purple-300 bg-purple-50 transition-colors"
        : "flex items-center gap-3 rounded-xl px-3 py-2.5 border border-gray-100 bg-white hover:border-gray-200 transition-colors";

      const avatarBase = checked
        ? "w-8 h-8 rounded-full bg-purple-200 flex items-center justify-center text-xs font-bold text-purple-800 shrink-0"
        : "w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 shrink-0";

      return `
      <div class="${rowBase}">
        <input type="checkbox" class="checkbox checkbox-sm voluntary-checkbox"
          style="accent-color:#7e22ce;"
          data-id="${m.id}" data-name="${m.name}"
          ${checked ? "checked" : ""}
          onchange="onVoluntaryCheck(this)" />
        <div class="${avatarBase}">${getInitials(m.name)}</div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-gray-800 truncate">${m.name}</p>
          <p class="text-xs text-gray-400">${m.student_id} · ${m.program} · Year ${m.year}</p>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <span class="text-xs text-gray-400">PHP</span>
          <input type="number" min="0" step="0.01" placeholder="0.00"
            value="${amount}"
            class="input input-xs w-20 text-right border voluntary-amount ${checked ? "border-purple-200 bg-white" : "border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed"}"
            data-id="${m.id}"
            ${checked ? "" : "disabled"}
            oninput="onVoluntaryAmount(this)" />
        </div>
      </div>`;
    })
    .join("");

  lucide.createIcons();
  updateVoluntaryPreview();
}

function onVoluntaryCheck(cb) {
  const id = cb.dataset.id;
  if (!voluntarySelections[id]) voluntarySelections[id] = { checked: false, amount: "" };
  voluntarySelections[id].checked = cb.checked;

  const amountInput = document.querySelector(`.voluntary-amount[data-id="${id}"]`);
  if (amountInput) {
    amountInput.disabled = !cb.checked;
    amountInput.classList.toggle("opacity-50", !cb.checked);
    amountInput.classList.toggle("cursor-not-allowed", !cb.checked);
    amountInput.classList.toggle("bg-gray-50", !cb.checked);
    amountInput.classList.toggle("bg-white", cb.checked);
    amountInput.classList.toggle("border-purple-200", cb.checked);
    amountInput.classList.toggle("border-gray-200", !cb.checked);
    if (cb.checked) amountInput.focus();
  }

  const rowDiv = cb.closest("div");
  if (rowDiv) {
    rowDiv.classList.toggle("border-purple-300", cb.checked);
    rowDiv.classList.toggle("bg-purple-50", cb.checked);
    rowDiv.classList.toggle("border-gray-100", !cb.checked);
    rowDiv.classList.toggle("bg-white", !cb.checked);
  }

  updateVoluntaryPreview();
}

function onVoluntaryAmount(input) {
  const id = input.dataset.id;
  if (!voluntarySelections[id]) voluntarySelections[id] = { checked: false, amount: "" };
  voluntarySelections[id].amount = input.value;
  if (parseFloat(input.value) > 0 && !voluntarySelections[id].checked) {
    voluntarySelections[id].checked = true;
    const cb = document.querySelector(`.voluntary-checkbox[data-id="${id}"]`);
    if (cb) {
      cb.checked = true;
      onVoluntaryCheck(cb);
    }
  }
  updateVoluntaryPreview();
}

function clearAllVoluntarySelections() {
  Object.keys(voluntarySelections).forEach((k) => delete voluntarySelections[k]);
  renderVoluntaryList();
}

function updateVoluntaryPreview() {
  let total = 0,
    count = 0;
  Object.values(voluntarySelections).forEach((sel) => {
    if (sel.checked) {
      total += parseFloat(sel.amount || 0);
      count++;
    }
  });
  const previewEl = document.getElementById("voluntary-preview");
  const summaryEl = document.getElementById("voluntary-footer-summary");
  document.getElementById("voluntary-donor-count").textContent = count;
  document.getElementById("voluntary-total").textContent = money(total);
  if (summaryEl) {
    summaryEl.textContent =
      count > 0 ? `${count} donor${count > 1 ? "s" : ""} · ${money(total)} total` : "No donors selected";
  }
  if (count > 0) {
    previewEl.classList.remove("hidden");
    previewEl.classList.add("flex");
    document.getElementById("voluntary-confirm-btn").disabled = false;
  } else {
    previewEl.classList.add("hidden");
    previewEl.classList.remove("flex");
    document.getElementById("voluntary-confirm-btn").disabled = true;
  }
}

function confirmVoluntary() {
  if (!pendingVoluntaryRow) return;
  const donors = [];
  voluntaryAllMembers.forEach((m) => {
    const sel = voluntarySelections[m.id];
    if (sel?.checked) {
      donors.push({ name: m.name, amount: parseFloat(sel.amount || 0) });
    }
  });
  if (!donors.length) return;
  const tbody = document.getElementById("entries-body");
  const originalRow = pendingVoluntaryRow;
  const sharedDate = originalRow.querySelector(".date-input")?.value || "";
  donors.forEach((donor, index) => {
    if (index === 0) {
      _fillVoluntaryRow(originalRow, donor, sharedDate);
    } else {
      document.getElementById("empty-row")?.remove();
      const rowKey = nextRowKey();
      const row = document.createElement("tr");
      row.className = "entry-row border-b border-gray-50 align-top";
      row.dataset.type = "income";
      row.dataset.rowKey = rowKey;
      row.innerHTML = buildRowHTML("income", rowKey, {});
      tbody.appendChild(row);
      lucide.createIcons();
      const sourceSelect = row.querySelector(".income-source-select");
      if (sourceSelect) sourceSelect.value = "voluntary";
      _fillVoluntaryRow(row, donor, sharedDate);
    }
  });
  updateTotals();
  renderReceiptGallery();
  document.getElementById("voluntary-modal").close();
  pendingVoluntaryRow = null;
}

function _fillVoluntaryRow(row, donor, date = "") {
  const amountInput = row.querySelector(".amount-input");
  const qtyInput = row.querySelector(".qty-input");
  const unitPriceInput = row.querySelector(".unit-price-input");
  const categoryInput = row.querySelector('input[name="category[]"]');
  const descInput = row.querySelector('input[name="description[]"]');
  const dateInput = row.querySelector(".date-input");
  if (dateInput && date) dateInput.value = date;
  if (categoryInput) categoryInput.value = "Voluntary Funds";
  if (descInput) descInput.value = donor.name;
  if (amountInput) {
    amountInput.value = donor.amount.toFixed(2);
    amountInput.readOnly = true;
    amountInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (qtyInput) {
    qtyInput.value = 1;
    qtyInput.readOnly = true;
    qtyInput.classList.add("opacity-70", "cursor-not-allowed");
  }
  if (unitPriceInput) {
    unitPriceInput.value = donor.amount.toFixed(2);
    unitPriceInput.readOnly = true;
    unitPriceInput.classList.add("opacity-70", "cursor-not-allowed");
  }
}
