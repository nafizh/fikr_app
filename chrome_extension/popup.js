document.addEventListener('DOMContentLoaded', async () => {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    document.getElementById('title').value = tab.title;
    document.getElementById('url').value = tab.url;
    
    // Focus tags field immediately
    document.getElementById('tags').focus();

    document.getElementById('save').addEventListener('click', async () => {
        const data = {
            url: document.getElementById('url').value,
            title: document.getElementById('title').value,
            tags: document.getElementById('tags').value,
            description: document.getElementById('desc').value
        };
        
        try {
            const response = await fetch('http://localhost:8000/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.textContent = 'Saved successfully!';
                setTimeout(() => window.close(), 700);
            } else {
                alert('Error saving bookmark');
            }
        } catch (e) {
            alert('Connection error. Is the server running?');
        }
    });

    // --- Autocomplete & AI Logic ---

    const tagInput = document.getElementById('tags');
    const suggestionsEl = document.getElementById('tag-suggestions'); 
    const aiBtn = document.getElementById('ai-btn');
    const aiContainer = document.getElementById('ai-chips');

    let allTags = [];
    let selectedIndex = -1;
    
    // 1. Fetch existing tags for autocomplete
    fetch('http://localhost:8000/api/tags')
        .then(r => r.json())
        .then(data => { 
            allTags = data.tags || []; 
            console.log("Loaded tags:", allTags.length);
        })
        .catch(e => console.error("Failed to load tags", e));

    // 2. Check if bookmark exists and pre-fill
    const currentUrl = document.getElementById('url').value;
    if (currentUrl) {
        fetch(`http://localhost:8000/api/check?url=${encodeURIComponent(currentUrl)}`)
            .then(r => r.json())
            .then(data => {
                if (data) {
                    console.log("Found existing bookmark:", data);
                    if (data.title) document.getElementById('title').value = data.title;
                    if (data.tags) document.getElementById('tags').value = data.tags + ' ';
                    if (data.description) document.getElementById('desc').value = data.description;
                    const status = document.getElementById('status');
                    status.textContent = "Found existing bookmark";
                    status.style.display = 'block';
                    document.getElementById('save').textContent = "Update Bookmark";
                }
                // Trigger AI automatically after data check
                triggerAI(); 
            })
            .catch(e => {
                console.error("Check failed", e);
                triggerAI();
            });
    }

    function showSuggestions(matches) {
        if (!suggestionsEl) return;
        suggestionsEl.innerHTML = '';
        selectedIndex = -1;
        
        if (!matches.length) {
            suggestionsEl.style.display = 'none';
            return;
        }
        
        suggestionsEl.style.display = 'block';
        suggestionsEl.style.top = '100%';
        suggestionsEl.style.left = '0';
        suggestionsEl.style.width = '100%';

        matches.forEach((tag, index) => {
            const li = document.createElement('li');
            li.textContent = tag;
            li.dataset.index = index;
            
            li.onmousedown = (e) => { 
                e.preventDefault();
                insertTag(tag);
            };
            suggestionsEl.appendChild(li);
        });
    }

    function insertTag(tag) {
        const current = tagInput.value;
        const parts = current.split(/\s+/);
        parts.pop(); 
        parts.push(tag);
        tagInput.value = parts.join(' ') + ' ';
        tagInput.focus();
        suggestionsEl.style.display = 'none';
        selectedIndex = -1;
    }

    if (tagInput) {
        tagInput.addEventListener('input', () => {
            const val = tagInput.value;
            const parts = val.split(/\s+/);
            const currentWord = parts[parts.length - 1].toLowerCase();
            
            if (!currentWord) {
                if (suggestionsEl) suggestionsEl.style.display = 'none';
                return;
            }
            
            const matches = allTags.filter(t => t.toLowerCase().startsWith(currentWord)).slice(0, 5);
            showSuggestions(matches);
        });

        // Keyboard Navigation for Autocomplete
        tagInput.addEventListener('keydown', (e) => {
            if (!suggestionsEl || suggestionsEl.style.display === 'none') return;
            
            const items = suggestionsEl.querySelectorAll('li');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                updateSelection(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                updateSelection(items);
            } else if (e.key === 'Enter' || e.key === 'Tab') {
                if (selectedIndex >= 0) {
                    e.preventDefault();
                    insertTag(items[selectedIndex].textContent);
                }
            } else if (e.key === 'Escape') {
                suggestionsEl.style.display = 'none';
            }
        });
    }

    function updateSelection(items) {
        items.forEach((item, idx) => {
            if (idx === selectedIndex) {
                item.style.backgroundColor = '#f0f0f0'; // Highlight
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.style.backgroundColor = '';
            }
        });
    }

    // Hide suggestions on click outside
    document.addEventListener('click', (e) => {
        if (e.target !== tagInput && !suggestionsEl.contains(e.target)) {
            suggestionsEl.style.display = 'none';
        }
    });

    // AI Suggestions
    async function triggerAI() {
        if (!aiBtn) return;
        
        // Don't re-trigger if already running
        if (aiBtn.disabled) return;

        aiBtn.disabled = true;
        aiBtn.textContent = "✨ Thinking...";
        aiContainer.innerHTML = '';

        try {
            // Fetch page content via scripting
            let pageContent = "";
            try {
                const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                if (tab && tab.id) {
                    const results = await chrome.scripting.executeScript({
                        target: { tabId: tab.id },
                        func: () => {
                            const metaDesc = document.querySelector('meta[name="description"]');
                            const desc = metaDesc ? metaDesc.content : "";
                            // Get clean body text (simple heuristic)
                            const bodyText = document.body.innerText
                                .replace(/\s+/g, ' ')
                                .slice(0, 2000); // First 2000 chars
                            return `Meta Description: ${desc}\n\nBody Text: ${bodyText}`;
                        }
                    });
                    if (results && results[0] && results[0].result) {
                        pageContent = results[0].result;
                    }
                }
            } catch (scriptErr) {
                console.warn("Could not fetch page content:", scriptErr);
            }

            const payload = {
                url: document.getElementById('url').value,
                title: document.getElementById('title').value,
                description: document.getElementById('desc').value,
                page_content: pageContent,
                existing_tags: document.getElementById('tags').value.split(/\s+/).filter(Boolean)
            };

            const res = await fetch('http://localhost:8000/api/suggest-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("AI failed");
            const data = await res.json();
            
            if (data.tags && data.tags.length) {
                data.tags.forEach(tag => {
                    const chip = document.createElement('span');
                    chip.className = 'chip';
                    chip.textContent = tag;
                    chip.onclick = () => {
                        const current = tagInput.value.trim();
                        tagInput.value = (current ? current + ' ' : '') + tag + ' ';
                        chip.remove();
                    };
                    aiContainer.appendChild(chip);
                });
            } else {
                aiContainer.textContent = "No suggestions found.";
            }
        } catch (e) {
            aiContainer.textContent = "Error fetching suggestions.";
            console.error(e);
        } finally {
            aiBtn.disabled = false;
            aiBtn.textContent = "✨ AI Suggestions";
        }
    }

    if (aiBtn) {
        aiBtn.addEventListener('click', triggerAI);
    } else {
        console.error("AI Button not found in DOM");
    }

    // Enter key in tags field submits form
    document.getElementById('tags').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('save').click();
        }
    });
});

