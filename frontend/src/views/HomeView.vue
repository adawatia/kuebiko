<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue';
import { Search } from 'lucide-vue-next';
import { getComics, bulkDeleteComics, type Comic, type ComicListResponse } from '../api/comics';
import { useAuth } from '../store';
import { API_URL } from '../api/client';

const { isSuperuser } = useAuth();
const comics = ref<Comic[]>([]);
const search = ref('');
const page = ref(1);
const totalPages = ref(1);
const loading = ref(false);
const selectedComics = reactive(new Set<number>());

const fetchComics = async () => {
    loading.value = true;
    selectedComics.clear(); // Clear selection on navigate/refresh
    try {
        const response: ComicListResponse = await getComics(page.value, 12, search.value);
        
        // Edge case: If we are on page > 1 and result is empty (e.g. after bulk delete), go back
        if (response.items.length === 0 && page.value > 1) {
            page.value--;
            // fetchComics will be triggered by watch(page), so we return here to avoid double set
            return; 
        }

        comics.value = response.items;
        totalPages.value = response.total_pages;
    } catch (e) {
        console.error(e);
        // If error occurs, maybe reset to page 1 if safe?
    } finally {
        loading.value = false;
    }
};

const toggleSelection = (id: number) => {
    if (!isSuperuser.value) return;
    
    if (selectedComics.has(id)) {
        selectedComics.delete(id);
    } else {
        selectedComics.add(id);
    }
};

const toggleSelectAll = () => {
    if (!isSuperuser.value) return;
    
    const allIdsOnPage = comics.value.map(c => c.id);
    const allSelected = allIdsOnPage.every(id => selectedComics.has(id));
    
    if (allSelected) {
        // Deselect all on this page
        allIdsOnPage.forEach(id => selectedComics.delete(id));
    } else {
        // Select all on this page
        allIdsOnPage.forEach(id => selectedComics.add(id));
    }
};

const handleBulkDelete = async () => {
    if (selectedComics.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${selectedComics.size} comics?`)) {
        try {
            await bulkDeleteComics(Array.from(selectedComics));
            selectedComics.clear();
            fetchComics(); // Refresh list
        } catch (e) {
            alert("Failed to delete comics.");
            console.error(e);
        }
    }
};

// Debounce search could be added here
watch([page, search], () => {
    fetchComics();
});

onMounted(() => {
    fetchComics();
});

const getGenreBadgeColor = (genre: string) => {
    const colors: Record<string, string> = {
        'Action': '#ff6b6b',
        'Adventure': '#feca57',
        'Fantasy': '#54a0ff',
        'Horror': '#5f27cd',
        'Romance': '#ff9ff3',
        'Sci-Fi': '#0abde3',
        'Mystery': '#2e86de',
    };
    return colors[genre] || '#8395a7';
};

const getImageUrl = (url: string | null) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    // Remove leading slash if both have it to avoid double slash, simpler:
    // API_URL usually doesn't end with slash based on client.ts default
    return `${API_URL}${url.startsWith('/') ? '' : '/'}${url}`;
};
</script>

<template>
  <div class="home-container">
    <div class="header-section">
        <div class="header-title">
            <h1>Explore Comics</h1>
            <p class="subtitle">Discover your next favorite story</p>
        </div>
        <div class="search-wrapper">
            <Search class="search-icon" :size="20" />
            <input 
                type="text" 
                v-model.lazy="search" 
                placeholder="Search titles, characters..." 
            />
        </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else>
        <div v-if="isSuperuser" class="admin-toolbar">
            <div class="checkbox-wrapper select-all">
                <label>
                    <input type="checkbox" 
                        :checked="comics.length > 0 && comics.every(c => selectedComics.has(c.id))"
                        @change="toggleSelectAll"
                    />
                    Select All
                </label>
            </div>

            <button v-if="selectedComics.size > 0" @click="handleBulkDelete" class="btn btn-danger">
                Delete Selected ({{ selectedComics.size }})
            </button>
            <div class="selection-info" v-if="selectedComics.size > 0">
                <a href="#" @click.prevent="selectedComics.clear()">Clear Selection</a>
            </div>
        </div>

        <div class="grid">
            <div 
                v-for="comic in comics" 
                :key="comic.id" 
                class="comic-card" 
                :class="{ 'selected': selectedComics.has(comic.id) }"
                @click="toggleSelection(comic.id)"
            >
                <div class="card-image" v-if="comic.cover_image_url">
                    <img :src="getImageUrl(comic.cover_image_url)" :alt="comic.title" loading="lazy" />
                </div>
                <div class="card-image placeholder" v-else>
                    <span>{{ comic.title.charAt(0) }}</span>
                </div>

                <div class="card-content">
                    <div class="card-header">
                        <div class="header-main">
                            <h3>{{ comic.title }}</h3>
                            <div class="meta-info">
                                <span class="card-author">by {{ comic.author }}</span>
                                <span class="card-status" :class="comic.status.toLowerCase()">{{ comic.status }}</span>
                            </div>
                        </div>
                        <div v-if="isSuperuser" class="checkbox-wrapper">
                            <input 
                                type="checkbox" 
                                :checked="selectedComics.has(comic.id)"
                                @click.stop="toggleSelection(comic.id)" 
                            />
                        </div>
                    </div>

                    <div class="genres">
                        <span v-for="g in comic.genres" :key="g" class="genre-tag" :style="{ backgroundColor: getGenreBadgeColor(g) }">
                            {{ g }}
                        </span>
                    </div>
                    <p class="description">{{ comic.description }}</p>
                    <div class="actions btn-group">
                        <RouterLink :to="`/comic/${comic.id}?read=true`" class="btn btn-primary" @click.stop>Read</RouterLink>
                        <RouterLink :to="`/comic/${comic.id}`" class="btn btn-secondary" @click.stop>View Details</RouterLink>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="pagination" v-if="totalPages > 1">
        <button :disabled="page <= 1" @click="page--">Previous</button>
        <span>Page {{ page }} of {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="page++">Next</button>
    </div>
  </div>
</template>

<style scoped>
/* Home Container */
.home-container {
    padding-top: 1rem;
    max-width: 1400px;
    margin: 0 auto;
    padding-bottom: 8rem;
    width: 100%;
    overflow-x: hidden;
}

/* Header Section */
.header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3rem;
    flex-wrap: wrap;
    gap: 2rem;
    padding: 1rem 0;
}

.header-title h1 {
    font-size: 3.5rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.1;
    background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
}

.subtitle {
    margin: 0.5rem 0 0 0;
    color: var(--text-muted);
    font-size: 1.1rem;
    font-weight: 400;
}

/* Search Bar */
.search-wrapper {
    position: relative;
    width: 100%;
    max-width: 400px;
}

.search-icon {
    position: absolute;
    left: 1.2rem;
    top: 50%;
    transform: translateY(-50%);
    color: #a5b4fc;
    pointer-events: none;
    transition: color 0.3s;
    z-index: 2;
}

.search-wrapper input {
    width: 100%;
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    color: white;
    border-radius: 50px;
    padding: 1rem 1.5rem 1rem 3.2rem;
    font-size: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.search-wrapper input:focus {
    background: rgba(30, 41, 59, 0.6);
    border-color: #818cf8;
    box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.15), 0 10px 25px rgba(0,0,0,0.2);
    outline: none;
    transform: translateY(-1px);
}

.search-wrapper input:focus + .search-icon {
    color: #818cf8;
}

.search-wrapper input::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

/* Grid Layout */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 2rem;
}

/* Comic Card */
.comic-card {
    background: var(--surface-highlight);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    border: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    flex-direction: column;
    position: relative;
}

.comic-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    border-color: rgba(255, 255, 255, 0.15);
    z-index: 5;
}

.comic-card.selected {
    border-color: var(--primary);
    background: rgba(138, 180, 248, 0.1);
    box-shadow: 0 0 0 2px var(--primary);
}

.card-content {
    padding: 1.8rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    flex: 1;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, rgba(30,30,30,1) 0%, rgba(20,20,20,1) 100%);
}

.card-image {
    height: 200px;
    width: 100%;
    position: relative;
    overflow: hidden;
    background: #000;
}

.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
}

.card-image.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(45deg, #2d3436, #636e72);
    font-size: 4rem;
    font-weight: 800;
    color: rgba(255,255,255,0.1);
}

.comic-card:hover .card-image img {
    transform: scale(1.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}

h3 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1.3;
}

/* Genres */
.genres {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 1.2rem;
    margin-top: 0.5rem;
}

.genre-tag {
    font-size: 0.7rem;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    color: #fff;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

/* Description */
.description {
    color: var(--text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1.8rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex: 1;
}

.actions {
    margin-top: auto;
}

.btn-group {
    display: flex;
    gap: 0.8rem;
}

.btn-group .btn {
    flex: 1;
}

/* Pagination */
/* Pagination - Floating Navigation */
.pagination {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(20, 20, 20, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.8rem 2rem;
    border-radius: 50px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
    z-index: 900;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    margin: 0;
}

.pagination button {
    padding: 0.8rem 1.5rem;
    background: var(--surface-highlight);
    border: 1px solid var(--glass-border);
    color: white;
    border-radius: 50px;
    cursor: pointer;
    transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
    background: rgba(255,255,255,0.1);
    transform: translateY(-2px);
}

.pagination button:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

/* Admin Toolbar */
.admin-toolbar {
    background: rgba(255, 255, 255, 0.03);
    padding: 1rem 1.5rem;
    border-radius: 16px;
    margin-bottom: 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}

.admin-toolbar:hover {
    border-color: rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.05);
}

/* Custom Checkboxes */
.checkbox-wrapper {
    position: relative;
    display: inline-block;
}

.checkbox-wrapper input[type="checkbox"] {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    height: 24px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease;
}

.checkbox-wrapper input[type="checkbox"]:checked {
    background: var(--primary);
    border-color: var(--primary);
}

.checkbox-wrapper input[type="checkbox"]:checked::after {
    content: '✔';
    position: absolute;
    color: #000;
    font-size: 14px;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-weight: bold;
}

.select-all label {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    cursor: pointer;
    font-weight: 600;
    color: var(--text);
    user-select: none;
}

.selection-info a {
    color: var(--text-muted);
    font-size: 0.9rem;
    border-bottom: 1px dashed var(--text-muted);
}

.selection-info a:hover {
    color: var(--text);
    border-color: var(--text);
}

/* Mobile Responsiveness */
@media (max-width: 1024px) {
    .grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
    }
}

@media (max-width: 768px) {
    .home-container {
        padding-bottom: 6rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .header-section {
        flex-direction: column;
        align-items: flex-start;
        padding: 0 1rem;
        margin-bottom: 2.5rem;
        gap: 1.5rem;
    }

    .header-title h1 {
        font-size: 2.5rem;
    }

    .search-wrapper {
        max-width: 100%;
    }

    .grid {
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 1.5rem;
    }

    .admin-toolbar {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
        padding: 1rem;
    }

    .admin-toolbar > * {
        width: 100%;
    }

    .btn-group {
        flex-direction: column;
        gap: 0.5rem;
    }

    .btn-group .btn {
        width: 100%;
    }

    .pagination {
        bottom: 1rem;
        padding: 0.6rem 1.2rem;
        gap: 1rem;
        width: 90%;
        max-width: 400px;
    }

    .pagination button {
        padding: 0.6rem 1rem;
        font-size: 0.9rem;
        flex: 1; /* Distribute space evenly */
    }
    
    .pagination span {
        font-size: 0.9rem;
        white-space: nowrap;
    }
}

@media (max-width: 480px) {
    h1 {
        font-size: 1.75rem;
    }

    .card-content {
        padding: 1.2rem;
    }

    .card-header h3 {
        font-size: 1.1rem;
    }

    .description {
        font-size: 0.85rem;
    }
}


/* Card Metadata Styling */
.header-main {
    flex: 1;
    min-width: 0; 
    margin-right: 0.5rem;
}

.meta-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.2rem;
    font-size: 0.8rem;
    color: var(--text-muted);
}

.card-author {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 150px;
}

.card-status {
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.7rem;
    text-transform: uppercase;
    font-weight: 700;
}

.card-status.ongoing {
    background: rgba(100, 200, 100, 0.15);
    color: #8f8;
}

.card-status.completed {
    background: rgba(100, 150, 255, 0.15);
    color: #8af;
}

.card-status.hiatus {
    background: rgba(255, 150, 100, 0.15);
    color: #fa8;
}
</style>
