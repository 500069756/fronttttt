document.addEventListener('DOMContentLoaded', () => {
    const citySelect = document.getElementById('location');
    const locSelect = document.getElementById('locality');
    const form = document.getElementById('recommendation-form');
    const submitBtn = document.getElementById('submit-btn');
    const loader = document.getElementById('results-loader');
    const summaryBox = document.getElementById('results-summary');
    const grid = document.getElementById('results-grid');

    // Fetch cities (locations)
    fetch('/api/v1/cities')
        .then(res => res.json())
        .then(data => {
            citySelect.innerHTML = '';
            if (data.locations && data.locations.length > 0) {
                let defaultOption = document.createElement('option');
                defaultOption.value = "";
                defaultOption.text = "Select a city...";
                defaultOption.disabled = true;
                defaultOption.selected = true;
                citySelect.appendChild(defaultOption);

                data.locations.forEach(loc => {
                    const option = document.createElement('option');
                    option.value = loc;
                    option.text = loc;
                    citySelect.appendChild(option);
                });
            } else {
                citySelect.innerHTML = '<option value="">No cities found</option>';
            }
        })
        .catch(err => {
            console.error('Failed to load cities:', err);
            citySelect.innerHTML = '<option value="">Error loading cities</option>';
        });

    // Fetch localities when city changes
    citySelect.addEventListener('change', () => {
        const selectedCity = citySelect.value;
        if (!selectedCity) return;

        locSelect.innerHTML = '<option value="" disabled selected>Loading...</option>';
        
        fetch(`/api/v1/localities?city=${encodeURIComponent(selectedCity)}`)
            .then(res => res.json())
            .then(data => {
                locSelect.innerHTML = '';
                if (data.localities && data.localities.length > 0) {
                    data.localities.forEach(loc => {
                        const option = document.createElement('option');
                        option.value = loc;
                        option.text = loc;
                        locSelect.appendChild(option);
                    });
                } else {
                    locSelect.innerHTML = '<option value="">No sub-areas found</option>';
                }
            })
            .catch(err => {
                console.error('Failed to load localities:', err);
                locSelect.innerHTML = '<option value="">Error</option>';
            });
    });

    // Handle form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Searching...';
        loader.classList.remove('hidden');
        summaryBox.classList.add('hidden');
        grid.innerHTML = '';

        const formData = new FormData(form);
        const city = formData.get('location');
        const locality = formData.get('locality');
        const rawCuisine = formData.get('cuisine');
        
        let cuisines = rawCuisine ? rawCuisine.split(',').map(s => s.trim()).filter(s => s.length > 0) : [];
        if (cuisines.length === 0) cuisines = ['Any'];

        const payload = {
            city: city || "",
            location: locality || "",
            budget: formData.get('budget_max_inr') > 1500 ? "high" : (formData.get('budget_max_inr') > 500 ? "medium" : "low"),
            cuisines: cuisines,
            min_rating: parseFloat(formData.get('min_rating')),
            use_ai: true
        };

        try {
            const res = await fetch('/api/v1/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                console.error(errData);
                throw new Error(errData.detail ? JSON.stringify(errData.detail) : 'Failed to fetch recommendations');
            }

            const data = await res.json();
            renderResults(data);

        } catch (error) {
            console.error(error);
            summaryBox.textContent = "Error: " + String(error);
            summaryBox.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Get Recommendations';
            loader.classList.add('hidden');
        }
    });

    function renderResults(data) {
        summaryBox.textContent = data.summary || 'Recommendations ready';
        summaryBox.classList.remove('hidden');

        if (!data.items || data.items.length === 0) {
            return;
        }

        data.items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'restaurant-card';
            card.style.animationDelay = `${index * 0.1}s`;

            const tagsHTML = item.cuisines.map(c => `<span class="tag">${c}</span>`).join('');
            
            card.innerHTML = `
                <div class="card-header">
                    <div class="card-title">${item.name || 'Unknown Restaurant'}</div>
                    <div class="card-rank">#${item.rank || (index + 1)}</div>
                </div>
                <div class="card-body">
                    <div class="tag-list">${tagsHTML}</div>
                    <div class="meta-info">
                        <span>📍 ${item.locality || 'Unknown'}</span>
                        <span>💰 ₹${item.cost_for_two || '?'} for two</span>
                        <span class="rating">★ ${item.rating || 'N/A'}</span>
                    </div>
                    ${item.explanation ? `<div class="reasoning">"${item.explanation}"</div>` : ''}
                </div>
            `;
            grid.appendChild(card);
        });
    }
});
