// inspector.js

function initInspector(iframe, pageUrl, pageTitle) {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    let selectedElement = null; // Variable to keep track of the selected element

    // Move the event listener before dispatching the click event
    iframeDoc.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();

        // Clear outline from previously selected element
        if (selectedElement) {
            selectedElement.style.outline = '';
        }

        // Set the new selected element and apply a persistent outline
        const clickedElement = event.target.nodeType === Node.TEXT_NODE ? event.target.parentElement : event.target;
        selectedElement = clickedElement;
        selectedElement.style.outline = '3px solid #007bff'; // Blue, thicker outline for selection

        const selector = getCssSelector(clickedElement);
        const text = clickedElement.textContent.trim();

        // --- Helper function to clear selection ---
        function clearSelection() {
            if (selectedElement) {
                selectedElement.style.outline = '';
                selectedElement = null;
            }
        }

        const body = document.createElement('div');
        body.innerHTML = `
            <p><strong>Selected Text:</strong> ${text}</p>
            <form id="track-item-modal-form" style="display: flex; flex-direction: column; gap: 10px;">
                <label for="product-name-input">Product Name:</label>
                <input type="text" id="product-name-input" value="${pageTitle}" required>
                <label for="target-price-input">Target Price:</label>
                <input type="text" id="target-price-input" placeholder="99.99" required>
            </form>
        `;

        showModal({
            title: 'Track New Item',
            body: body,
            buttons: [
                {
                    text: 'Cancel',
                    className: 'cancel-btn',
                    onClick: () => {
                        clearSelection();
                        return true; // Close modal
                    }
                },
                {
                    text: 'Track Item',
                    className: 'track-btn-confirm',
                    onClick: () => {
                        const productName = document.getElementById('product-name-input').value;
                        const targetPrice = document.getElementById('target-price-input').value;

                        if (productName.trim() === '' || targetPrice.trim() === '') {
                            Toastify({ text: "Product name and target price are required.", duration: 3000, backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                            return false; // Keep modal open
                        }

                        // Send data to backend
                        const formData = new FormData();
                        formData.append('url', pageUrl);
                        formData.append('css_selector', selector);
                        formData.append('target_price', targetPrice);
                        formData.append('product_name', productName);

                        fetch(`${APPLICATION_ROOT}/track_item`, {
                            method: 'POST',
                            body: formData,
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                Toastify({ text: `Error: ${data.error}`, duration: 3000, close: true, gravity: "top", position: "right", backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                            } else {
                                Toastify({ text: data.message, duration: 3000, close: true, gravity: "top", position: "right", backgroundColor: "linear-gradient(to right, #00b09b, #96c93d)" }).showToast();
                                loadTrackedItems();
                            }
                        })
                        .catch(error => {
                            console.error('Fetch error:', error);
                            Toastify({ text: `Network Error: ${error}`, duration: 3000, close: true, gravity: "top", position: "right", backgroundColor: "linear-gradient(to right, #ff5f6d, #ffc371)" }).showToast();
                        })
                        .finally(() => {
                            clearSelection();
                        });
                        
                        return true; // Close modal
                    }
                }
            ]
        });
    });

    // Auto-detect price
    const detectedPriceElement = autoDetectPrice(iframeDoc);
    if (detectedPriceElement) {
        // Simulate a click on the detected element
        const clickEvent = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: iframe.contentWindow
        });
        detectedPriceElement.dispatchEvent(clickEvent); // This should trigger the click listener
    }
}

function getCssSelector(el) {
    // Check if el is an element by checking its nodeType
    if (el.nodeType !== Node.ELEMENT_NODE) {
        return;
    }
    const path = [];
    while (el.nodeType === Node.ELEMENT_NODE) {
        let selector = el.nodeName.toLowerCase();
        if (el.id) {
            selector += '#' + el.id;
            path.unshift(selector);
            break;
        }
        let sib = el, nth = 1;
        while (sib = sib.previousElementSibling) {
            if (sib.nodeName.toLowerCase() == selector) nth++;
        }
        if (nth != 1) selector += ":nth-of-type("+nth+")";
        path.unshift(selector);
        el = el.parentNode;
    }
    return path.join(" > ");
}

function autoDetectPrice(iframeDoc) {
    const currencySymbols = ['$', '£', '€']; // Moved back inside the function
    const priceRegex = /([$£€]\s*\d+[.,]\d{2})/;

    let potentialElements = [];

    // 1. Look for elements with itemprop="price"
    const itempropElements = Array.from(iframeDoc.querySelectorAll('[itemprop="price"]'));
    potentialElements.push(...itempropElements);

    // 2. Look for elements with a content attribute that contains a price
    const contentElements = Array.from(iframeDoc.querySelectorAll('[content*="$"], [content*="£"], [content*="€"]'));
    potentialElements.push(...contentElements);

    // 3. Search for elements containing currency symbols
    let textElements = [];
    const allElements = Array.from(iframeDoc.querySelectorAll('*:not(script):not(style)'));
    for (const element of allElements) {
        if (element.children.length === 0) { // Only consider leaf nodes
            const text = element.textContent.trim();
            if (currencySymbols.some(symbol => text.includes(symbol))) {
                textElements.push(element);
            }
        }
    }
    potentialElements.push(...textElements);

    // 4. Filter and rank the potential elements
    const rankedElements = potentialElements.map(el => {
        if (el.offsetParent === null) { // Re-added the visibility check
            return null; // Element is not visible
        }
        const text = el.textContent.trim() || el.getAttribute('content') || '';
        const match = text.match(priceRegex);
        if (match) {
            let score = 1 / (text.length + 1); // Shorter text is better
            if (el.hasAttribute('itemprop') && el.getAttribute('itemprop') === 'price') {
                score += 10;
            }
            return {
                element: el,
                price: match[1],
                score: score
            };
        }
        return null;
    }).filter(Boolean);

    // 4. Sort by score
    rankedElements.sort((a, b) => b.score - a.score);

    // 5. Return the best candidate
    if (rankedElements.length > 0) {
        return rankedElements[0].element;
    }

    return null;
}