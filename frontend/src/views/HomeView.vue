<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue';
import { getComics, bulkDeleteComics, type Comic, type ComicListResponse } from '../api/comics';
import { useAuth } from '../store';

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
</script>

<template>
  <div class="home-container">
    <div class="header-section">
        <h1>Explore Comics</h1>
        <div class="search-bar">
            <input type="text" v-model.lazy="search" placeholder="Search by title or description..." />
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
                <div class="card-content">
                    <div class="card-header">
                        <h3>{{ comic.title }}</h3>
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
                    <div class="actions">
                        <RouterLink :to="`/comic/${comic.id}`" class="btn btn-primary" @click.stop>Read Now</RouterLink>
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
.home-container {
    padding-top: 1rem;
}

.header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
}

h1 {
    font-size: 2.5rem;
    font-weight: 800;
}

.search-bar input {
    width: 300px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 25px;
    padding: 0.8rem 1.5rem;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
}

.comic-card {
    background: #1e1e1e;
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s;
    border: 1px solid #333;
    display: flex;
    flex-direction: column;
}

.comic-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    border-color: var(--primary);
}

.card-content {
    padding: 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
}

h3 {
    margin-bottom: 0.5rem;
    font-size: 1.25rem;
}

.genres {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.genre-tag {
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    color: #fff;
    font-weight: 600;
    text-transform: uppercase;
}

.description {
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex: 1;
}

.actions {
    margin-top: auto;
}

.pagination {
    margin-top: 3rem;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
}

.pagination button {
    padding: 0.5rem 1rem;
    background: #333;
    border: none;
    color: white;
    border-radius: 4px;
    cursor: pointer;
}

.pagination button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Admin Features */
.admin-toolbar {
    background: #2d2d2d;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid #444;
}

.selection-info a {
    color: #aaa;
    text-decoration: none;
    font-size: 0.9rem;
}

.selection-info a:hover {
    color: white;
}

.comic-card.selected {
    border-color: var(--primary);
    background: #252525;
    box-shadow: 0 0 0 2px var(--primary);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.checkbox-wrapper {
    padding-left: 0.5rem;
}

.checkbox-wrapper input {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: var(--primary);
}

.select-all label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-weight: 500;
}

.btn-danger {
    background: #cf6679; /* Red-ish */
    color: white;
}

.btn-danger:hover {
    background: #b00020;
}
</style>
