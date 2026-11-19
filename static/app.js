/**
 * My Wardrobe - AI Outfit Recommendation System
 * Client Application Logic
 */

// Global State
const state = {
  items: [],
  selectedCategory: 'all',
  searchQuery: '',
  currentUploadedImage: null,
  customTags: [],
  selectedAnchorId: '',
  selectedOccasion: 'casual',
  selectedGender: 'men',
  pinterestToken: localStorage.getItem('pinterest_token') || ''
};

// DOM Elements
const DOM = {
  // KPIs
  kpiTotal: document.getElementById('kpiTotal'),
  kpiTops: document.getElementById('kpiTops'),
  kpiBottoms: document.getElementById('kpiBottoms'),
  kpiOuterwear: document.getElementById('kpiOuterwear'),
  kpiFootwear: document.getElementById('kpiFootwear'),
  badgeClosetCount: document.getElementById('badgeClosetCount'),

  // Tabs
  tabButtons: document.querySelectorAll('.nav-tab-btn'),
  tabPanels: document.querySelectorAll('.tab-panel'),

  // Closet
  wardrobeGrid: document.getElementById('wardrobeGrid'),
  categoryFilters: document.getElementById('categoryFilters'),
  searchInput: document.getElementById('searchInput'),

  // Studio
  selectAnchorItem: document.getElementById('selectAnchorItem'),
  anchorPreviewCard: document.getElementById('anchorPreviewCard'),
  anchorThumb: document.getElementById('anchorThumb'),
  anchorName: document.getElementById('anchorName'),
  anchorTags: document.getElementById('anchorTags'),
  selectStudioOccasion: document.getElementById('selectStudioOccasion'),
  selectStudioGender: document.getElementById('selectStudioGender'),
  btnGenerateRecommendations: document.getElementById('btnGenerateRecommendations'),
  currentPinterestQuery: document.getElementById('currentPinterestQuery'),
  recommendationsContainer: document.getElementById('recommendationsContainer'),

  // Lookbook
  lookbookOccasionFilters: document.getElementById('lookbookOccasionFilters'),
  lookbookContainer: document.getElementById('lookbookContainer'),

  // Pinterest
  pinterestMoodboardGrid: document.getElementById('pinterestMoodboardGrid'),

  // Upload Modal
  uploadModal: document.getElementById('uploadModal'),
  btnOpenUploadModal: document.getElementById('btnOpenUploadModal'),
  btnCloseUploadModal: document.getElementById('btnCloseUploadModal'),
  btnCancelUpload: document.getElementById('btnCancelUpload'),
  uploadDropzone: document.getElementById('uploadDropzone'),
  clothingFileInput: document.getElementById('clothingFileInput'),
  scanningIndicator: document.getElementById('scanningIndicator'),
  tagProposalSection: document.getElementById('tagProposalSection'),
  proposedChipsContainer: document.getElementById('proposedChipsContainer'),
  inputItemName: document.getElementById('inputItemName'),
  selectItemCategory: document.getElementById('selectItemCategory'),
  inputItemColor: document.getElementById('inputItemColor'),
  inputItemStyle: document.getElementById('inputItemStyle'),
  occasionCheckboxes: document.getElementById('occasionCheckboxes'),
  inputCustomTags: document.getElementById('inputCustomTags'),
  customChipsContainer: document.getElementById('customChipsContainer'),
  btnConfirmSaveItem: document.getElementById('btnConfirmSaveItem'),
  proposalConfidence: document.getElementById('proposalConfidence'),

  // Settings Modal
  settingsModal: document.getElementById('settingsModal'),
  btnOpenSettings: document.getElementById('btnOpenSettings'),
  btnCloseSettingsModal: document.getElementById('btnCloseSettingsModal'),
  btnCloseSettings: document.getElementById('btnCloseSettings'),
  btnSaveSettings: document.getElementById('btnSaveSettings'),
  inputPinterestToken: document.getElementById('inputPinterestToken'),
  btnSeedSample: document.getElementById('btnSeedSample')
};

// -------------------------------------------------------------
// App Initialization
// -------------------------------------------------------------
async function initApp() {
  setupEventListeners();
  if (state.pinterestToken) {
    DOM.inputPinterestToken.value = state.pinterestToken;
  }
  await fetchWardrobeItems();
  await fetchPinterestMoodboard();
}

// -------------------------------------------------------------
// Event Listeners
// -------------------------------------------------------------
function setupEventListeners() {
  // Tab Switching
  DOM.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.tabButtons.forEach(b => b.classList.remove('active'));
      DOM.tabPanels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add('active');

      if (targetId === 'tabLookbook') {
        loadOccasionLookbook('casual');
      }
    });
  });

  // Closet Filters & Search
  DOM.categoryFilters.addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-pill')) {
      DOM.categoryFilters.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      state.selectedCategory = e.target.getAttribute('data-category');
      renderWardrobeGrid();
    }
  });

  DOM.searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    renderWardrobeGrid();
  });

  // Studio Controls
  DOM.selectAnchorItem.addEventListener('change', (e) => {
    state.selectedAnchorId = e.target.value;
    updateAnchorPreview();
  });

  DOM.btnGenerateRecommendations.addEventListener('click', () => {
    if (!state.selectedAnchorId) {
      alert('Please select an item from your closet to style.');
      return;
    }
    generateOutfitRecommendations();
  });

  // Lookbook Occasion Filters
  DOM.lookbookOccasionFilters.addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-pill')) {
      DOM.lookbookOccasionFilters.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      loadOccasionLookbook(e.target.getAttribute('data-occ'));
    }
  });

  // Modals Open/Close
  DOM.btnOpenUploadModal.addEventListener('click', openUploadModal);
  DOM.btnCloseUploadModal.addEventListener('click', closeUploadModal);
  DOM.btnCancelUpload.addEventListener('click', closeUploadModal);

  DOM.btnOpenSettings.addEventListener('click', () => DOM.settingsModal.classList.add('active'));
  DOM.btnCloseSettingsModal.addEventListener('click', () => DOM.settingsModal.classList.remove('active'));
  DOM.btnCloseSettings.addEventListener('click', () => DOM.settingsModal.classList.remove('active'));

  DOM.btnSaveSettings.addEventListener('click', async () => {
    const token = DOM.inputPinterestToken.value.trim();
    state.pinterestToken = token;
    localStorage.setItem('pinterest_token', token);
    await fetch('/api/settings/pinterest-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: token })
    });
    DOM.settingsModal.classList.remove('active');
    alert('Settings saved successfully!');
  });

  DOM.btnSeedSample.addEventListener('click', async () => {
    if (confirm('Reset and re-index the curated starter wardrobe into Qdrant?')) {
      await fetch('/api/catalog/seed?force=true', { method: 'POST' });
      await fetchWardrobeItems();
      alert('Curated wardrobe restored with high quality items and CLIP embeddings!');
    }
  });

  // Drag & Drop / File Upload
  DOM.uploadDropzone.addEventListener('click', () => DOM.clothingFileInput.click());
  DOM.clothingFileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleImageUpload(e.target.files[0]);
  });

  DOM.uploadDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    DOM.uploadDropzone.classList.add('dragover');
  });

  DOM.uploadDropzone.addEventListener('dragleave', () => {
    DOM.uploadDropzone.classList.remove('dragover');
  });

  DOM.uploadDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    DOM.uploadDropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleImageUpload(e.dataTransfer.files[0]);
  });

  // Custom Tags Input
  DOM.inputCustomTags.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const val = DOM.inputCustomTags.value.trim().toLowerCase();
      if (val && !state.customTags.includes(val)) {
        state.customTags.push(val);
        DOM.inputCustomTags.value = '';
        renderCustomChips();
      }
    }
  });

  // Save Item to Qdrant
  DOM.btnConfirmSaveItem.addEventListener('click', saveAndIndexItem);
}

// -------------------------------------------------------------
// Data Fetching & Rendering
// -------------------------------------------------------------
async function fetchWardrobeItems() {
  try {
    const res = await fetch('/api/catalog/items');
    state.items = await res.json();
    updateKPIs();
    renderWardrobeGrid();
    populateStudioDropdown();
  } catch (err) {
    console.error('Failed to load items:', err);
  }
}

function updateKPIs() {
  const total = state.items.length;
  const tops = state.items.filter(i => i.category === 'top').length;
  const bottoms = state.items.filter(i => i.category === 'bottom').length;
  const outerwear = state.items.filter(i => i.category === 'outerwear').length;
  const footwear = state.items.filter(i => i.category === 'footwear').length;

  DOM.kpiTotal.textContent = total;
  DOM.kpiTops.textContent = tops;
  DOM.kpiBottoms.textContent = bottoms;
  DOM.kpiOuterwear.textContent = outerwear;
  DOM.kpiFootwear.textContent = footwear;
  DOM.badgeClosetCount.textContent = total;
}

function renderWardrobeGrid() {
  let filtered = [...state.items];

  if (state.selectedCategory !== 'all') {
    filtered = filtered.filter(i => i.category === state.selectedCategory);
  }

  if (state.searchQuery) {
    const q = state.searchQuery;
    filtered = filtered.filter(i =>
      i.name.toLowerCase().includes(q) ||
      i.color.toLowerCase().includes(q) ||
      i.garment_type.toLowerCase().includes(q) ||
      i.tags.some(t => t.toLowerCase().includes(q))
    );
  }

  if (filtered.length === 0) {
    DOM.wardrobeGrid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-icon">👕</div>
        <h3>No clothing items found</h3>
        <p>Try clearing your filters or add a new piece to your closet using the "+ Add Clothes" button.</p>
      </div>
    `;
    return;
  }

  DOM.wardrobeGrid.innerHTML = filtered.map(item => `
    <article class="wardrobe-card" data-id="${item.id}">
      <div class="card-img-wrap">
        <img src="${item.image_url}" alt="${item.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400'">
        <span class="card-category-badge">${item.category}</span>
        <button class="card-delete-btn" onclick="deleteItem('${item.id}', event)" title="Remove item">&times;</button>
      </div>
      <div class="card-body">
        <h3 class="card-title">${item.name}</h3>
        <div class="tag-list">
          <span class="tag-badge color-tag">${item.color}</span>
          <span class="tag-badge">${item.style}</span>
          ${item.occasions.map(o => `<span class="tag-badge occasion-tag">${o}</span>`).join('')}
        </div>
        <div class="card-actions">
          <button class="btn btn-style-item" onclick="styleThisItem('${item.id}')">
            ✨ Style with Pinterest AI
          </button>
        </div>
      </div>
    </article>
  `).join('');
}

function populateStudioDropdown() {
  DOM.selectAnchorItem.innerHTML = `
    <option value="">-- Select an item from your closet --</option>
    ${state.items.map(it => `
      <option value="${it.id}">${it.name} (${it.category} • ${it.color})</option>
    `).join('')}
  `;
}

function updateAnchorPreview() {
  const item = state.items.find(i => i.id === state.selectedAnchorId);
  if (item) {
    DOM.anchorPreviewCard.style.display = 'flex';
    DOM.anchorThumb.src = item.image_url;
    DOM.anchorName.textContent = item.name;
    DOM.anchorTags.textContent = `${item.color.toUpperCase()} • ${item.garment_type.toUpperCase()} • ${item.style}`;
    
    // Auto set Pinterest query preview
    const occ = DOM.selectStudioOccasion.value;
    const gender = DOM.selectStudioGender.value;
    DOM.currentPinterestQuery.textContent = `"${item.color} ${item.garment_type} outfit ${gender} ${occ}"`;
  } else {
    DOM.anchorPreviewCard.style.display = 'none';
    DOM.currentPinterestQuery.textContent = 'Select an item to begin matching';
  }
}

// Jump directly to Studio from any card
window.styleThisItem = function(itemId) {
  state.selectedAnchorId = itemId;
  DOM.selectAnchorItem.value = itemId;
  updateAnchorPreview();

  // Switch to studio tab
  DOM.tabButtons.forEach(b => b.classList.remove('active'));
  DOM.tabPanels.forEach(p => p.classList.remove('active'));
  document.getElementById('tabBtnStudio').classList.add('active');
  document.getElementById('tabStudio').classList.add('active');

  // Trigger matching
  generateOutfitRecommendations();
};

window.deleteItem = async function(itemId, event) {
  event.stopPropagation();
  if (confirm('Are you sure you want to remove this item from your wardrobe?')) {
    await fetch(`/api/catalog/items/${itemId}`, { method: 'DELETE' });
    await fetchWardrobeItems();
  }
};

// -------------------------------------------------------------
// AI Recommendation & Pinterest Outfit Matching
// -------------------------------------------------------------
async function generateOutfitRecommendations() {
  const item = state.items.find(i => i.id === state.selectedAnchorId);
  if (!item) return;

  const occasion = DOM.selectStudioOccasion.value;
  const gender = DOM.selectStudioGender.value;

  DOM.currentPinterestQuery.textContent = `Searching Pinterest: "${item.color} ${item.garment_type} outfit ${gender} ${occasion}"`;
  DOM.recommendationsContainer.innerHTML = `
    <div class="scanning-spinner" style="padding: 40px;">
      <div class="spinner"></div>
      <span>Extracting visual features with CLIP & cross-referencing your Qdrant closet...</span>
    </div>
  `;

  try {
    const res = await fetch('/api/recommend/by-item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: item.id,
        occasion: occasion,
        gender: gender
      })
    });

    const recommendations = await res.json();
    renderRecommendations(recommendations, DOM.recommendationsContainer);
  } catch (err) {
    console.error('Error generating recommendations:', err);
    DOM.recommendationsContainer.innerHTML = `
      <div class="empty-state">
        <p style="color: var(--accent-rose);">Failed to generate recommendations. Please try again.</p>
      </div>
    `;
  }
}

function renderRecommendations(recs, container) {
  if (!recs || recs.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>No matching Pinterest outfits found</h3>
        <p>Try switching the style aesthetic or occasion.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = recs.map(rec => `
    <div class="outfit-card">
      <div class="outfit-card-header">
        <div class="outfit-title-group">
          <h3>${rec.title}</h3>
          <div class="outfit-meta">
            <span class="tag-badge occasion-tag">${rec.occasion}</span>
            <span class="tag-badge">${rec.style}</span>
            <span class="tag-badge" style="color: #6ee7b7;">${rec.color_palette.join(' • ')}</span>
          </div>
        </div>
        <div class="score-badge">
          <span>⚡ ${rec.overall_match_score}% Match</span>
        </div>
      </div>

      <!-- Side-by-side comparison: Pinterest Look vs Your Closet -->
      <div class="comparison-grid">
        
        <!-- Left: Pinterest Inspiration -->
        <div class="inspiration-column">
          <div class="inspiration-label">
            <span>📌 Pinterest Inspiration Look</span>
          </div>
          <div class="inspiration-img-wrap">
            <img src="${rec.inspiration.image_url}" alt="${rec.inspiration.title}" loading="lazy">
          </div>
          <p class="inspiration-vibe">"${rec.inspiration.vibe_description}"</p>
        </div>

        <!-- Right: Your Wardrobe Pieces Matched -->
        <div class="closet-match-column">
          <div class="closet-match-label">
            <span>🧥 Recreated from Your Closet</span>
          </div>

          <div class="slots-grid">
            ${rec.matched_slots.map(slot => `
              <div class="slot-item-card ${slot.status === 'matched' ? 'is-matched' : 'is-missing'}">
                <span class="slot-badge ${slot.slot}">${slot.slot}</span>
                ${slot.user_item ? `
                  <img src="${slot.user_item.image_url}" class="slot-thumb" alt="${slot.user_item.name}">
                  <span class="slot-name">${slot.user_item.name}</span>
                  <span class="slot-sim">✓ ${Math.round(slot.similarity_score * 100)}% Match</span>
                ` : `
                  <div class="slot-missing-placeholder">
                    <span>⚠️ Missing Piece</span>
                    <span>${slot.target_description}</span>
                  </div>
                  <span class="slot-name" style="color: var(--text-dim);">${slot.slot.toUpperCase()} NOT IN CLOSET</span>
                `}
              </div>
            `).join('')}
          </div>

          <div class="advice-bar">
            <strong>Stylist Tip:</strong> ${rec.styling_advice}
          </div>
        </div>

      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------
// Occasion Lookbook
// -------------------------------------------------------------
async function loadOccasionLookbook(occ) {
  DOM.lookbookContainer.innerHTML = `
    <div class="scanning-spinner" style="padding: 40px;">
      <div class="spinner"></div>
      <span>Assembling complete outfits for ${occ.toUpperCase()}...</span>
    </div>
  `;

  try {
    const res = await fetch('/api/recommend/by-occasion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ occasion: occ, gender: 'men' })
    });
    const recs = await res.json();
    renderRecommendations(recs, DOM.lookbookContainer);
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// Pinterest Moodboard Grid
// -------------------------------------------------------------
async function fetchPinterestMoodboard() {
  try {
    const res = await fetch('/api/pinterest/trends');
    const pins = await res.json();
    DOM.pinterestMoodboardGrid.innerHTML = pins.map(pin => `
      <article class="wardrobe-card">
        <div class="card-img-wrap" style="height: 320px;">
          <img src="${pin.image_url}" alt="${pin.title}" loading="lazy">
          <span class="card-category-badge" style="background: rgba(230,0,35,0.8); color: #fff; border-color: transparent;">Pinterest</span>
        </div>
        <div class="card-body">
          <h3 class="card-title">${pin.title}</h3>
          <p style="font-size: 12px; color: var(--text-muted);">${pin.vibe_description}</p>
          <div class="tag-list" style="margin-top: 6px;">
            <span class="tag-badge occasion-tag">${pin.occasion}</span>
            <span class="tag-badge">${pin.style}</span>
          </div>
        </div>
      </article>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// Image Upload & Vision-Language Auto Tagging
// -------------------------------------------------------------
function openUploadModal() {
  DOM.uploadModal.classList.add('active');
  resetUploadState();
}

function closeUploadModal() {
  DOM.uploadModal.classList.remove('active');
  resetUploadState();
}

function resetUploadState() {
  state.currentUploadedImage = null;
  state.customTags = [];
  DOM.clothingFileInput.value = '';
  DOM.uploadDropzone.style.display = 'flex';
  DOM.scanningIndicator.style.display = 'none';
  DOM.tagProposalSection.style.display = 'none';
  DOM.btnConfirmSaveItem.disabled = true;
  DOM.customChipsContainer.innerHTML = '';
}

async function handleImageUpload(file) {
  DOM.uploadDropzone.style.display = 'none';
  DOM.scanningIndicator.style.display = 'flex';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/catalog/upload-and-tag', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error('Classification failed');
    const data = await res.json();
    
    state.currentUploadedImage = data.image_url;
    DOM.scanningIndicator.style.display = 'none';
    DOM.tagProposalSection.style.display = 'flex';

    // Populate auto-detected fields
    DOM.inputItemName.value = data.suggested_name;
    DOM.selectItemCategory.value = data.proposal.category;
    DOM.inputItemColor.value = data.proposal.color;
    DOM.inputItemStyle.value = data.proposal.style;

    // Check occasions
    const occInputs = DOM.occasionCheckboxes.querySelectorAll('input[type="checkbox"]');
    occInputs.forEach(input => {
      input.checked = data.proposal.occasions.includes(input.value);
    });

    // Populate chips
    DOM.proposedChipsContainer.innerHTML = data.proposal.suggested_tags.map(tag => `
      <span class="chip-tag">${tag}</span>
    `).join('');

    state.customTags = [...data.proposal.suggested_tags];
    renderCustomChips();

    const confScore = Math.round(data.proposal.confidence_scores.garment_confidence * 100);
    DOM.proposalConfidence.textContent = `${confScore}% AI confidence`;

    DOM.btnConfirmSaveItem.disabled = false;
  } catch (err) {
    console.error(err);
    alert('Failed to classify image. Please try a different photo.');
    resetUploadState();
  }
}

function renderCustomChips() {
  DOM.customChipsContainer.innerHTML = state.customTags.map((tag, idx) => `
    <span class="chip-tag">
      ${tag}
      <span class="chip-remove" onclick="removeCustomTag(${idx})">&times;</span>
    </span>
  `).join('');
}

window.removeCustomTag = function(idx) {
  state.customTags.splice(idx, 1);
  renderCustomChips();
};

async function saveAndIndexItem() {
  const name = DOM.inputItemName.value.trim();
  const category = DOM.selectItemCategory.value;
  const color = DOM.inputItemColor.value.trim();
  const style = DOM.inputItemStyle.value.trim();
  
  const selectedOccasions = Array.from(
    DOM.occasionCheckboxes.querySelectorAll('input[type="checkbox"]:checked')
  ).map(cb => cb.value);

  if (!name || !color) {
    alert('Please enter a name and color.');
    return;
  }

  DOM.btnConfirmSaveItem.disabled = true;
  DOM.btnConfirmSaveItem.textContent = 'Indexing in Qdrant...';

  try {
    const res = await fetch('/api/catalog/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        category: category,
        garment_type: name.toLowerCase(),
        color: color,
        style: style,
        occasions: selectedOccasions,
        tags: state.customTags,
        image_url: state.currentUploadedImage
      })
    });

    if (!res.ok) throw new Error('Save failed');
    closeUploadModal();
    await fetchWardrobeItems();
    alert(`🎉 Successfully indexed "${name}" in your Qdrant wardrobe!`);
  } catch (err) {
    console.error(err);
    alert('Failed to index item.');
  } finally {
    DOM.btnConfirmSaveItem.textContent = '💾 Save & Index to Qdrant';
    DOM.btnConfirmSaveItem.disabled = false;
  }
}

// Start
document.addEventListener('DOMContentLoaded', initApp);
