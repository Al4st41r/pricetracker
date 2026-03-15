// main.js

// --- STATE MANAGEMENT ---
let allItems = [];
let currentSort = {
    column: null,
    order: 'asc'
};
let isSaleFilterActive = false;

// --- HELPER FUNCTIONS ---
function formatCurrency(priceStr, currency) {
    const displayCurrency = currency || 'GBP';
    if (priceStr === null || priceStr === undefined || String(priceStr).trim() === 'N/A' || String(priceStr).trim() === '') {
        return 'N/A';
    }
    const number = parseFloat(String(priceStr).replace(/[^\d.]/g, ''));
    if (isNaN(number)) {
        return priceStr;
    }
    return number.toLocaleString('en-GB', {
        style: 'currency',
        currency: displayCurrency,
    });
}

function parsePrice(priceStr) {
    if (priceStr === null || priceStr === undefined) {
        return null;
    }
    // Convert to string and remove any non-numeric characters except for the decimal point
    const cleanedPriceStr = String(priceStr).replace(/[^0-9.-]+/g, "");
    if (cleanedPriceStr === '') {
        return null;
    }
    const num = parseFloat(cleanedPriceStr);
    return isNaN(num) ? null : num;
}

// --- RENDERING ---
function renderTable(items) {
    const trackedItemsList = document.getElementById('tracked-items-list');
    trackedItemsList.innerHTML = '';

    if (items.length === 0) {
        trackedItemsList.innerHTML = '<p>No items match the current filter.</p>';
        return;
    }

    const table = document.createElement('table');
    const sortIndicator = (column) => {
        if (currentSort.column === column) {
            return currentSort.order === 'asc' ? ' ▲' : ' ▼';
        }
        return '';
    };

    table.innerHTML = `
        <thead>
            <tr>
                <th class="sortable-header" data-sort-by="Product Name">Product Name${sortIndicator('Product Name')}</th>
                <th>URL</th>
                <th>CSS Selector</th>
                <th class="sortable-header" data-sort-by="Current Price">Current Price${sortIndicator('Current Price')}</th>
                <th class="sortable-header" data-sort-by="Target Price">Target Price${sortIndicator('Target Price')}</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    const tbody = table.querySelector('tbody');

    items.forEach(item => {
        const row = document.createElement('tr');
        row.dataset.id = item['id'];
        row.dataset.url = item['URL'];
        row.dataset.selector = item['CSS Selector'];

        const currentPrice = parsePrice(item['Current Price']);
        const targetPrice = parsePrice(item['Target Price']);

        if (currentPrice !== null && targetPrice !== null) {
            if (currentPrice > targetPrice) {
                row.classList.add('price-above-target');
            } else {
                row.classList.add('price-at-or-below-target');
            }
        }

        let priceChangeIndicator = '';
        const status = item['Price Change Status'];
        if (status === 'up') {
            priceChangeIndicator = '<span class="price-up"> ▲</span>';
        } else if (status === 'down') {
            priceChangeIndicator = '<span class="price-down"> ▼</span>';
        }

        let saleBadge = '';
        if (currentPrice !== null && targetPrice !== null && currentPrice <= targetPrice) {
            saleBadge = '<span class="sale-badge">On Sale!</span>';
        }

        row.innerHTML = `
            <td data-field="Product Name">${item['Product Name']} ${saleBadge}</td>
            <td data-field="URL"><a href="${item['URL']}" target="_blank">${item['URL'].substring(0, 40)}...</a></td>
            <td data-field="CSS Selector">${item['CSS Selector'].substring(0, 40)}...</td>
            <td data-field="Current Price">${formatCurrency(item['Current Price'], item['Currency'])}${priceChangeIndicator}</td>
            <td data-field="Target Price">${formatCurrency(item['Target Price'], item['Currency'])}</td>
            <td data-field="Actions">
                <button class="edit-btn">Edit</button>
                <button class="delete-btn">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    trackedItemsList.appendChild(table);
}

// --- DATA & LOGIC ---
function applyFiltersAndSort() {
    let itemsToDisplay = [...allItems];

    // Apply filtering
    if (isSaleFilterActive) {
        itemsToDisplay = itemsToDisplay.filter(item => {
            const currentPrice = parsePrice(item['Current Price']);
            const targetPrice = parsePrice(item['Target Price']);
            return currentPrice !== null && targetPrice !== null && currentPrice <= targetPrice;
        });
    }

    // Apply sorting
    if (currentSort.column) {
        itemsToDisplay.sort((a, b) => {
            const valA = a[currentSort.column];
            const valB = b[currentSort.column];
            let comparison = 0;

            if (currentSort.column.includes('Price')) {
                comparison = (parsePrice(valA) || 0) - (parsePrice(valB) || 0);
            } else {
                comparison = String(valA).localeCompare(String(valB));
            }

            return currentSort.order === 'asc' ? comparison : -comparison;
        });
    }

    renderTable(itemsToDisplay);
}

// --- MODAL ---
const modal = document.getElementById('custom-modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalFooter = document.getElementById('modal-footer');
const closeModalButton = document.querySelector('.close-button');

function showModal({ title, body, buttons }) {
    modalTitle.textContent = title;
    modalBody.innerHTML = '';
    modalBody.appendChild(body);

    modalFooter.innerHTML = '';
    buttons.forEach(btn => {
        const button = document.createElement('button');
        button.textContent = btn.text;
        button.className = btn.className || '';
        button.addEventListener('click', () => {
            if (btn.onClick) {
                const shouldClose = btn.onClick();
                if (shouldClose !== false) {
                    hideModal();
                }
            } else {
                hideModal();
            }
        });
        modalFooter.appendChild(button);
    });

    modal.style.cssText = 'display: block !important;';
    // Scroll to top when modal opens
    window.scrollTo(0, 0);
}

function hideModal() {
    modal.style.cssText = 'display: none !important;';
}

closeModalButton.addEventListener('click', hideModal);

window.addEventListener('click', (event) => {
    if (event.target == modal) {
        hideModal();
    }
});

function loadTrackedItems() {
    if (!isAuthenticated) {
        return;
    }
    const trackedItemsList = document.getElementById('tracked-items-list');
    trackedItemsList.innerHTML = '<p>Loading items...</p>'; // Show loading message

    fetch(`${APPLICATION_ROOT}/get_tracked_items`)
        .then(response => response.json())
        .then(items => {
            allItems = items;
            applyFiltersAndSort();
        })
        .catch(error => {
            console.error('Error loading tracked items:', error);
            trackedItemsList.innerHTML = '<p>Error loading tracked items.</p>';
        });
}

// --- EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', function() {
    loadTrackedItems();

    // Listener for table controls (filter, sort)
    document.getElementById('sale-filter').addEventListener('change', function(event) {
        isSaleFilterActive = event.target.checked;
        applyFiltersAndSort();
    });

    document.getElementById('tracked-items-list').addEventListener('click', function(event) {
        const header = event.target.closest('th.sortable-header');
        if (header && header.dataset.sortBy) {
            const column = header.dataset.sortBy;
            if (currentSort.column === column) {
                currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.order = 'asc';
            }
            applyFiltersAndSort();
            return; // Stop further processing
        }

        const target = event.target;
        const row = target.closest('tr');
        if (!row) return;

        const id = row.dataset.id;

        // --- Delete Button ---
        if (target.classList.contains('delete-btn')) {
            const body = document.createElement('p');
            body.textContent = `Are you sure you want to delete this item?\n\nURL: ${url}`;

            showModal({
                title: 'Confirm Deletion',
                body: body,
                buttons: [
                    {
                        text: 'Cancel',
                        className: 'cancel-btn',
                        onClick: () => {} // Just close the modal
                    },
                    {
                        text: 'Delete',
                        className: 'delete-btn-confirm', // for styling if needed
                        onClick: () => {
                            const formData = new FormData();
                            formData.append('id', id);

                            fetch(`${APPLICATION_ROOT}/delete_item`, {
                                    method: 'POST',
                                    body: formData
                                })
                                .then(response => response.json())
                                .then(data => {
                                    if (data.error) {
                                        Toastify({ text: `Error: ${data.error}`, duration: 3000, backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                                    } else {
                                        Toastify({ text: data.message, duration: 3000, backgroundColor: "linear-gradient(to right, #00b09b, #96c93d)" }).showToast();
                                        loadTrackedItems(); // Refresh the table
                                    }
                                })
                                .catch(error => {
                                    Toastify({ text: `Network Error: ${error}`, duration: 3000, backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                                });
                        }
                    }
                ]
            });
        }

        // --- Edit Button ---
        if (target.classList.contains('edit-btn')) {
            const nameCell = row.querySelector('td[data-field="Product Name"]');
            const priceCell = row.querySelector('td[data-field="Target Price"]');
            const actionsCell = row.querySelector('td[data-field="Actions"]');

            const currentName = nameCell.textContent;
            const currentPrice = parsePrice(priceCell.textContent) || '';

            nameCell.innerHTML = `<input type="text" value="${currentName}">`;
            priceCell.innerHTML = `<input type="text" value="${currentPrice}">`;
            actionsCell.innerHTML = '<button class="save-btn">Save</button><button class="cancel-btn">Cancel</button>';
        }

        // --- Cancel Button ---
        if (target.classList.contains('cancel-btn')) {
            applyFiltersAndSort(); // Just re-render the table
        }

        // --- Save Button ---
        if (target.classList.contains('save-btn')) {
            const nameInput = row.querySelector('td[data-field="Product Name"] input');
            const priceInput = row.querySelector('td[data-field="Target Price"] input');

            const newName = nameInput.value;
            const newPrice = priceInput.value;

            const formData = new FormData();
            formData.append('id', row.dataset.id);
            formData.append('product_name', newName);
            formData.append('target_price', newPrice);

            fetch(`${APPLICATION_ROOT}/update_item`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        Toastify({ text: `Error: ${data.error}`, duration: 3000, backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                    } else {
                        Toastify({ text: data.message, duration: 3000, backgroundColor: "linear-gradient(to right, #00b09b, #96c93d)" }).showToast();
                        loadTrackedItems(); // Refresh the table
                    }
                })
                .catch(error => {
                    Toastify({ text: `Network Error: ${error}`, duration: 3000, backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                });
        }
    });
});

// Listener for the main track form
document.getElementById('track-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const url = document.getElementById('url-input').value;
    const loader = document.getElementById('loader');
    const pageContent = document.getElementById('page-content');

    loader.style.display = 'block';
    loader.textContent = 'Loading page with browser emulation...';
    pageContent.innerHTML = '';

    fetch(`${APPLICATION_ROOT}/discover_price`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: url})
    })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';
            loader.textContent = 'Loading...';

            if (data.error) {
                pageContent.innerHTML = `<p style="color: var(--color-danger);">Error: ${data.error}</p>`;
            } else {
                // Show screenshot and detected price
                const resultHtml = `
                    <div style="padding: var(--spacing-lg);">
                        <h3>Page Loaded: ${data.page_title || 'Product Page'}</h3>
                        ${data.success ? `
                            <div style="margin: var(--spacing-md) 0; padding: var(--spacing-md); background: var(--color-success); color: white;">
                                <strong>✓ Auto-detected price: ${data.price}</strong>
                            </div>
                        ` : `
                            <div style="margin: var(--spacing-md) 0; padding: var(--spacing-md); background: var(--color-warning); color: white;">
                                <strong>⚠ Could not auto-detect price</strong>
                                <p style="margin-top: 8px;">You can manually enter the price information below.</p>
                            </div>
                        `}
                        <div style="margin: var(--spacing-lg) 0;">
                            <img src="data:image/png;base64,${data.screenshot}"
                                 style="max-width: 100%; border: 2px solid var(--color-border);"
                                 alt="Page screenshot">
                        </div>
                        <form id="confirm-track-form" style="margin-top: var(--spacing-lg);">
                            <div class="form-group">
                                <label for="confirm-product-name">Product Name:</label>
                                <input type="text" id="confirm-product-name" value="${data.page_title || ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="confirm-price">Current Price:</label>
                                <input type="text" id="confirm-price" value="${data.price || ''}"
                                       placeholder="e.g., £99.99" required>
                            </div>
                            <div class="form-group">
                                <label for="confirm-target-price">Target Price:</label>
                                <input type="text" id="confirm-target-price"
                                       placeholder="e.g., 79.99" required>
                            </div>
                            <div class="form-group">
                                <label for="confirm-selector">CSS Selector:</label>
                                <input type="text" id="confirm-selector" value="${data.selector || ''}"
                                       placeholder="Leave empty to use auto-detect" readonly>
                            </div>
                            <button type="submit" class="btn btn-primary">Track This Item</button>
                            <button type="button" class="btn btn-secondary" onclick="document.getElementById('page-content').innerHTML = ''">Cancel</button>
                        </form>
                    </div>
                `;

                pageContent.innerHTML = resultHtml;

                // Handle form submission
                document.getElementById('confirm-track-form').addEventListener('submit', function(e) {
                    e.preventDefault();

                    const productName = document.getElementById('confirm-product-name').value;
                    const currentPrice = document.getElementById('confirm-price').value;
                    const targetPrice = document.getElementById('confirm-target-price').value;
                    const selector = document.getElementById('confirm-selector').value;

                    // Extract numeric target price
                    const numericTargetPrice = targetPrice.replace(/[^\d.]/g, '');

                    const formData = new FormData();
                    formData.append('url', url);
                    formData.append('product_name', productName);
                    formData.append('target_price', numericTargetPrice);
                    formData.append('css_selector', selector);

                    fetch(`${APPLICATION_ROOT}/track_item`, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            Toastify({
                                text: `Error: ${data.error}`,
                                duration: 5000,
                                backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)"
                            }).showToast();
                        } else {
                            Toastify({
                                text: data.message,
                                duration: 3000,
                                backgroundColor: "linear-gradient(to right, #00b09b, #96c93d)"
                            }).showToast();
                            pageContent.innerHTML = '';
                            document.getElementById('url-input').value = '';
                            loadTrackedItems();
                        }
                    })
                    .catch(error => {
                        Toastify({
                            text: `Error: ${error}`,
                            duration: 3000,
                            backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)"
                        }).showToast();
                    });
                });
            }
        })
        .catch(error => {
            loader.style.display = 'none';
            loader.textContent = 'Loading...';
            pageContent.innerHTML = `<p style="color: var(--color-danger);">Error: ${error}</p>`;
        });
});
