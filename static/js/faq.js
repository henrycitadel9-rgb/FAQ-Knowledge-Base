// FAQ JavaScript

let allFaqs = [];
let currentCategory = '';
let currentSearch = '';

async function loadFAQ() {
    try {
        const response = await fetch('/api/faq/');
        const data = await response.json();
        allFaqs = data.faqs;
        populateCategories();
        displayFAQ(allFaqs);
    } catch (error) {
        console.error('Error loading FAQ:', error);
        document.getElementById('faq-container').innerHTML = '<p>Error loading FAQs. Please try again later.</p>';
    }
}

function populateCategories() {
    const categories = [...new Set(allFaqs.map(faq => faq.category))].sort();
    const filterDiv = document.querySelector('.category-filter');

    categories.forEach(category => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.textContent = category;
        btn.setAttribute('data-category', category);
        btn.addEventListener('click', () => filterByCategory(category));
        filterDiv.appendChild(btn);
    });
}

function filterByCategory(category) {
    currentCategory = category;
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-category') === category);
    });
    applyFilters();
}

function searchFAQs() {
    currentSearch = document.getElementById('search-input').value.trim();
    if (currentSearch) {
        // Use search API
        fetch(`/api/faq/search/?q=${encodeURIComponent(currentSearch)}`)
            .then(response => response.json())
            .then(data => {
                displayFAQ(data.faqs);
                logInteraction('search', currentSearch, null, '', 0, '');
            })
            .catch(error => console.error('Search error:', error));
    } else {
        applyFilters();
    }
}

function applyFilters() {
    let filtered = allFaqs;

    if (currentCategory) {
        filtered = filtered.filter(faq => faq.category === currentCategory);
    }

    displayFAQ(filtered);
}

function displayFAQ(faqs) {
    const container = document.getElementById('faq-container');

    if (!faqs || faqs.length === 0) {
        container.innerHTML = '<p>No FAQs found.</p>';
        return;
    }

    // Group FAQs by category
    const faqsByCategory = {};
    faqs.forEach(faq => {
        if (!faqsByCategory[faq.category]) {
            faqsByCategory[faq.category] = [];
        }
        faqsByCategory[faq.category].push(faq);
    });

    let html = '';
    for (const [category, categoryFaqs] of Object.entries(faqsByCategory)) {
        html += `<h2>${category}</h2>`;
        html += '<div class="faq-list">';
        categoryFaqs.forEach(faq => {
            html += `
                <div class="faq-card">
                    <div class="faq-question" onclick="toggleAnswer(this)">
                        <h3>${faq.question}</h3>
                        <span class="expand-icon">+</span>
                    </div>
                    <div class="faq-answer">
                        <p>${faq.answer}</p>
                        ${faq.source_ref ? `<p class="source">Source: ${faq.source_ref}</p>` : ''}
                        <a href="/faq/${faq.id}" class="detail-link" onclick="logInteraction('detail_click', '', ${faq.id}, '', 0, '${faq.source_ref || ''}')">View Full Details</a>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }

    container.innerHTML = html;
}

function toggleAnswer(element) {
    const card = element.parentElement;
    const isExpanded = card.classList.contains('expanded');

    // Log interaction
    const faqId = card.querySelector('.detail-link').href.split('/').pop();
    logInteraction('expand', '', parseInt(faqId), '', 0, '');

    card.classList.toggle('expanded');
    element.querySelector('.expand-icon').textContent = isExpanded ? '+' : '−';
}

function logInteraction(interfaceType, query, faqId, answer, latency, source) {
    fetch('/api/faq/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            interface_type: interfaceType,
            user_query: query,
            matched_faq_id: faqId,
            system_answer: answer,
            latency_ms: latency,
            source_ref: source
        })
    }).catch(error => console.error('Logging error:', error));
}

// Event listeners
document.addEventListener('DOMContentLoaded', loadFAQ);

document.getElementById('search-btn').addEventListener('click', searchFAQs);
document.getElementById('search-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchFAQs();
    }
});
