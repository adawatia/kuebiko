<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch, nextTick } from 'vue';
import { BookOpen, Image as ImageIcon, Trash2, X, AlertCircle, Book, Loader2, ArrowUpDown, ChevronLeft, ChevronRight, Plus, Edit2, Check } from 'lucide-vue-next';
import Pagination from '../components/Pagination.vue';
import { useRoute, useRouter } from 'vue-router';
import { getComic, deleteComic, updateComic, type Comic } from '../api/comics';
import { createChapter, uploadChapterImages, deleteChapter, updateChapter, getChapters, type Chapter } from '../api/chapters';
import { API_URL } from '../api/client';
import { useAuth } from '../store';

const getAssetUrl = (url: string | null) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    return `${API_URL}${url.startsWith('/') ? '' : '/'}${url}`;
};

const route = useRoute();
const router = useRouter();
const { isSuperuser, state } = useAuth();
const comic = ref<Comic | null>(null);
const loading = ref(true);
const uploading = ref(false);
const readingMode = ref(false);

// Chapter Pagination State
const chapters = ref<Chapter[]>([]);
const chaptersPage = ref(1);
const chaptersTotal = ref(0);
const chaptersTotalPages = ref(1);
const chaptersLoading = ref(false);

// Reader state
const currentImages = ref<string[]>([]);
const currentPageIndex = ref(0);
const windowWidth = ref(document.documentElement.clientWidth || window.innerWidth);
const readerScroll = ref<HTMLElement | null>(null);

// Scroll Mode
const scrollMode = ref<'single' | 'vertical'>('single');

// Zoom controls
const zoomLevel = ref(1.0); // 1.0 = 100%, 0.5 = 50%, 2.0 = 200%
const fitMode = ref<'width' | 'height' | 'none'>('width'); // Default to fit width

const currentPage = computed(() => currentPageIndex.value + 1);
const totalPages = computed(() => currentImages.value.length);

const updateWindowWidth = () => {
    windowWidth.value = document.documentElement.clientWidth || window.innerWidth;
};

const scrollToTop = () => {
    if (readerScroll.value) {
        readerScroll.value.scrollTop = 0;
    }
};

const zoomIn = () => {
    fitMode.value = 'none';
    zoomLevel.value = Math.min(zoomLevel.value + 0.2, 3.0); // Max 300%
};

const zoomOut = () => {
    fitMode.value = 'none';
    zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.3); // Min 30%
};

const fitToWidth = () => {
    fitMode.value = 'width';
    zoomLevel.value = 1.0;
};

const fitToHeight = () => {
    fitMode.value = 'height';
    zoomLevel.value = 1.0;
};

const resetZoom = () => {
    fitMode.value = 'none';
    zoomLevel.value = 1.0;
};

const prevPage = () => {
    if (currentPageIndex.value > 0) {
        currentPageIndex.value--;
        scrollToTop();
    }
};

const nextPage = () => {
    if (currentPageIndex.value < currentImages.value.length - 1) {
        currentPageIndex.value++;
        scrollToTop();
    }
};

const toggleScrollMode = () => {
    scrollMode.value = scrollMode.value === 'single' ? 'vertical' : 'single';
    scrollToTop();
};

const closeReader = () => {
    readingMode.value = false;
    currentImages.value = [];
    currentPageIndex.value = 0;
    zoomLevel.value = 1.0;
    fitMode.value = 'width';
};

const handleReadChapter = (chapter: Chapter) => {
    // Check if user is authenticated before allowing reading
    if (!state.isAuthenticated) {
        // Store intended destination for redirect after login
        const returnPath = `/comic/${route.params.id}`;
        router.push({ 
            name: 'login', 
            query: { redirect: returnPath }
        });
        return;
    }
    
    try {
        // Additional check: if image_urls is missing, it means the API didn't return them
        // This shouldn't happen for authenticated users, but let's be safe
        if (!chapter.image_urls || chapter.image_urls.length === 0) {
            alert('No images available for this chapter.');
            return;
        }
        
        currentImages.value = chapter.image_urls.map(url => getAssetUrl(url));
        currentPageIndex.value = 0;
        readingMode.value = true;
    } catch (e) {
        console.error('Error opening chapter:', e);
        alert('Failed to open chapter.');
    }
};

const newChapterNumber = ref<number | null>(null);
const newChapterTitle = ref('');
const creatingChapter = ref(false);
const showAddChapter = ref(false);
const chaptersUploading = ref(new Set<number>());

const comicId = parseInt(route.params.id as string);

const loadChapters = async (page = 1) => {
    chaptersLoading.value = true;
    try {
        const response = await getChapters(comicId, page, 10);
        chapters.value = response.items;
        chaptersTotal.value = response.total_chapters;
        chaptersTotalPages.value = response.total_pages;
        chaptersPage.value = response.current_page;
    } catch (e) {
        console.error("Failed to load chapters", e);
    } finally {
        chaptersLoading.value = false;
    }
};

const fetchComic = async () => {
    try {
        comic.value = await getComic(comicId);
    } catch (e) {
        console.error('Error fetching comic:', e);
    } finally {
        loading.value = false;
    }
};

onMounted(async () => {
    window.addEventListener('resize', updateWindowWidth);
    window.addEventListener('keydown', handleKeydown);
    
    // Initial load
    await fetchComic();
    await loadChapters();
    
    const shouldRead = route.query.read === 'true';
    const firstChapter = chapters.value?.[0]; // Use paginated list
    if (shouldRead && firstChapter && firstChapter.image_urls && firstChapter.image_urls.length > 0) {
        handleReadChapter(firstChapter);
    }
});

const openFirstChapter = () => {
    const firstChapter = comic.value?.chapters?.[0];
    if (firstChapter) {
        handleReadChapter(firstChapter);
    }
};

onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth);
    window.removeEventListener('keydown', handleKeydown);
});

// Update handlers to reload chapters
const handleCreateChapter = async () => {
    if (!newChapterNumber.value || !newChapterTitle.value) {
        alert("Please enter chapter number and title.");
        return;
    }
    
    creatingChapter.value = true;
    try {
        await createChapter({
            comic_id: comicId,
            chapter_number: newChapterNumber.value,
            title: newChapterTitle.value,
            page_count: 0,
            is_published: true
        });
        await loadChapters(chaptersPage.value); // Reload current page
        newChapterNumber.value = null;
        newChapterTitle.value = '';
        alert("Chapter created successfully!");
    } catch (e: any) {
        console.error(e);
        alert(e.response?.data?.detail || "Failed to create chapter");
    } finally {
        creatingChapter.value = false;
    }
};

const handleDeleteChapter = async (chapterId: number) => {
    if (confirm("Are you sure you want to delete this chapter?")) {
        try {
            await deleteChapter(chapterId);
            await loadChapters(chaptersPage.value);
        } catch (e) {
            alert("Failed to delete chapter");
        }
    }
};

const handleChapterImagesUpload = async (chapterId: number, event: Event) => {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
        const files = Array.from(input.files);
        
        // Validate files
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        for (const file of files) {
            if (!validTypes.includes(file.type)) {
                alert(`Invalid file type: ${file.name}. Only JPG, PNG, GIF, and WebP are allowed.`);
                input.value = '';
                return;
            }
        }
        
        chaptersUploading.value.add(chapterId);
        try {
            await uploadChapterImages(chapterId, files);
            await loadChapters(chaptersPage.value);
            alert(`${files.length} image(s) uploaded successfully!`);
        } catch (e) {
            console.error(e);
            alert("Failed to upload images");
        } finally {
            chaptersUploading.value.delete(chapterId);
            input.value = '';
        }
    }
};

const saveChapterEdit = async () => {
    if (!editingChapterId.value) return;
    
    try {
        await updateChapter(editingChapterId.value, {
            chapter_number: editForm.value.chapter_number,
            title: editForm.value.title
        });
        await loadChapters(chaptersPage.value);
        editingChapterId.value = null;
    } catch (e) {
        console.error(e);
        alert("Failed to update chapter details");
    }
};

// Auto-calculate next chapter number when adding
watch(showAddChapter, (newVal) => {
    if (newVal) {
        let maxNum = 0;
        // Try to find max from full list first
        if (comic.value?.chapters && comic.value.chapters.length > 0) {
             const numbers = comic.value.chapters.map(c => c.chapter_number);
             maxNum = Math.max(...numbers);
        } 
        // Fallback to current page
        else if (chapters.value.length > 0) {
             const numbers = chapters.value.map(c => c.chapter_number);
             maxNum = Math.max(...numbers);
        }
        newChapterNumber.value = maxNum + 1;
    }
});

// Edit Chapter Functionality
const editingChapterId = ref<number | null>(null);
const editForm = ref({
    chapter_number: 0,
    title: ''
});

const startEditingChapter = (chapter: Chapter) => {
    editingChapterId.value = chapter.id;
    editForm.value = {
        chapter_number: chapter.chapter_number,
        title: chapter.title
    };
};

const cancelEditChapter = () => {
    editingChapterId.value = null;
    editForm.value = { chapter_number: 0, title: '' };
};

const handleKeydown = (e: KeyboardEvent) => {
    if (!readingMode.value) return;
    
    // Zoom controls (work in both modes)
    if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomIn();
        return;
    }
    if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        zoomOut();
        return;
    }
    if (e.key === '0') {
        e.preventDefault();
        resetZoom();
        return;
    }
    if (e.key === 'w' || e.key === 'W') {
        e.preventDefault();
        fitToWidth();
        return;
    }
    if (e.key === 'h' || e.key === 'H') {
        e.preventDefault();
        fitToHeight();
        return;
    }
    
    if (scrollMode.value === 'vertical') {
       if (e.key === 'Escape') {
           e.preventDefault();
           closeReader();
       }
       return; 
    }

    // Single page mode with keyboard navigation
    if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        nextPage();
    } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevPage();
    } else if (e.key === 'Escape') {
        e.preventDefault();
        closeReader();
    }
};

const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this comic?')) {
        try {
            await deleteComic(comicId);
            router.push('/explore');
        } catch (e) {
            alert('Failed to delete comic');
        }
    }
};

const handleUploadCover = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
        const file = target.files[0];
        if (!file) return;
        
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.');
            target.value = '';
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) {
            alert("Image file is too large. Maximum size is 5MB.");
            target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onerror = () => {
            alert('Failed to read image file.');
            target.value = '';
        };
        reader.onload = async () => {
            try {
                uploading.value = true;
                const base64String = reader.result as string;
                await updateComic(comicId, { cover_image: base64String });
                await fetchComic();
                alert('Cover image updated successfully!');
            } catch (e: any) {
                console.error(e);
                const errorMsg = e?.response?.data?.detail || 'Failed to update cover image.';
                alert(errorMsg);
            } finally {
                uploading.value = false;
                target.value = '';
            }
        };
        reader.readAsDataURL(file);
    }
};

</script>

<template>
  <div v-if="loading" class="loading">
      <Loader2 class="spinner-icon" />
      <p>Loading Comic...</p>
  </div>
  
  <div v-else-if="comic" class="detail-wrapper">
    <!-- Reading Mode Overlay -->
    <div v-if="readingMode" class="reading-overlay">
        <div class="reader-header">
            <h3 class="reader-title">{{ comic.title }}</h3>
            
            <div class="reader-controls-center">
                 <button @click="toggleScrollMode" class="btn-icon" :title="scrollMode === 'single' ? 'Switch to Vertical Scroll' : 'Switch to Single Page'">
                    <ArrowUpDown v-if="scrollMode === 'single'" />
                    <BookOpen v-else />
                </button>
            </div>

            <button @click="closeReader" class="btn-icon close-btn" title="Close Reader">
                <X />
            </button>
        </div>

        <div class="reader-content scroll-container" ref="readerScroll">
            <!-- Single Page Mode -->
            <div v-if="scrollMode === 'single'" class="single-page-reader">
                <img 
                    v-if="currentImages[currentPageIndex]"
                    :src="currentImages[currentPageIndex]" 
                    :alt="`Page ${currentPage}`"
                    class="comic-page-image"
                    :class="{ 
                        'fit-width': fitMode === 'width',
                        'fit-height': fitMode === 'height',
                        'manual-zoom': fitMode === 'none'
                    }"
                    :style="fitMode === 'none' ? { transform: `scale(${zoomLevel})` } : {}"
                    loading="eager"
                />
            </div>

            <!-- Vertical Scroll Mode -->
            <div v-else class="vertical-reader">
                <img 
                    v-for="(imageUrl, index) in currentImages" 
                    :key="index"
                    :src="imageUrl" 
                    :alt="`Page ${index + 1}`"
                    class="comic-page-image vertical-image"
                    :class="{ 
                        'fit-width': fitMode === 'width',
                        'manual-zoom': fitMode === 'none'
                    }"
                    :style="fitMode === 'none' ? { transform: `scale(${zoomLevel})`, transformOrigin: 'top center' } : {}"
                    :loading="index < 3 ? 'eager' : 'lazy'"
                />
            </div>
        </div>

        <div class="reader-footer" v-if="scrollMode === 'single'">
            <div class="zoom-controls">
                <button @click="zoomOut" class="btn-icon" title="Zoom Out (-)"  >−</button>
                <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="btn-icon" title="Zoom In (+)">+</button>
                <button @click="fitToWidth" class="btn-text" :class="{ 'active': fitMode === 'width' }" title="Fit to Width (W)">Fit Width</button>
                <button @click="fitToHeight" class="btn-text" :class="{ 'active': fitMode === 'height' }" title="Fit to Height (H)">Fit Height</button>
                <button @click="resetZoom" class="btn-text" title="Reset Zoom (0)">100%</button>
            </div>

            <div class="pagination-controls">
                <button @click="prevPage" :disabled="currentPageIndex <= 0" class="btn-icon">←</button>
                <span class="page-counter">{{ currentPage }} / {{ totalPages }}</span>
                <button @click="nextPage" :disabled="currentPageIndex >= totalPages - 1" class="btn-icon">→</button>
            </div>
        </div>
        
        <div class="reader-footer" v-else>
             <div class="zoom-controls">
                <button @click="zoomOut" class="btn-icon" title="Zoom Out (-)" >−</button>
                <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="btn-icon" title="Zoom In (+)">+</button>
                <button @click="fitToWidth" class="btn-text" :class="{ 'active': fitMode === 'width' }" title="Fit to Width (W)">Fit Width</button>
                <button @click="resetZoom" class="btn-text" title="Reset Zoom (0)">100%</button>
            </div>
             <div class="pagination-controls">
                <span class="page-counter">{{ totalPages }} Pages</span>
            </div>
        </div>
    </div>

    <!-- Background Hero -->
    <div class="hero-bg">
        <div class="hero-image" 
             :style="comic.cover_image_url ? { backgroundImage: `url(${getAssetUrl(comic.cover_image_url)})` } : {}">
        </div>
        <div class="hero-overlay"></div>
    </div>

    <div class="content-container">
        <!-- Main Content -->
        <div class="comic-layout">
            <!-- Left Column: Cover & Actions -->
            <div class="left-col">
                <div class="cover-card">
                    <div v-if="comic.cover_image_url" class="cover-image-wrapper">
                        <img :src="getAssetUrl(comic.cover_image_url)" :alt="comic.title" class="cover-image" />
                    </div>
                    <div v-else class="cover-placeholder">
                        <Book class="placeholder-icon" :size="48" />
                        <span class="placeholder-text">No Cover</span>
                    </div>

                    <!-- Superuser Cover Edit Overlay -->
                    <label v-if="isSuperuser" class="cover-edit-overlay" :class="{ 'uploading': uploading }">
                        <div class="edit-icon-bg">
                            <ImageIcon :size="20" />
                        </div>
                        <input type="file" accept="image/*" @change="handleUploadCover" :disabled="uploading" style="display:none;" />
                    </label>
                </div>

                <div class="primary-actions">
                    <button v-if="comic.chapters && comic.chapters.length > 0" @click="openFirstChapter" class="btn btn-read">
                        <BookOpen class="icon" :size="20" /> Start Reading
                    </button>
                    <button v-else disabled class="btn btn-disabled">
                        No Chapters
                    </button>
                </div>
            </div>

            <!-- Right Column: Details -->
            <div class="right-col">
                <div class="header-info">
                    <h1 class="comic-title">{{ comic.title }}</h1>
                    <div class="meta-row">
                        <span class="author">By {{ comic.author }}</span>
                        <span class="status-badge" :class="comic.status.toLowerCase()">{{ comic.status }}</span>
                    </div>
                    <div class="genres">
                        <span v-for="g in comic.genres" :key="g" class="genre-tag">{{ g }}</span>
                    </div>
                </div>

                <div class="description-box">
                    <h3>Synopsis</h3>
                    <p>{{ comic.description }}</p>
                </div>

                <!-- Chapters Section -->
                <div class="chapters-section">
                    <div class="section-header">
                        <h3>Chapters</h3>
                        <button v-if="isSuperuser" @click="showAddChapter = !showAddChapter" class="btn-icon-text">
                            <Plus :size="16" /> {{ showAddChapter ? 'Cancel' : 'Add Chapter' }}
                        </button>
                    </div>

                    <!-- Add Chapter Form (Inline) -->
                    <div v-if="showAddChapter" class="add-chapter-inline">
                         <div class="form-row">
                            <input type="number" v-model="newChapterNumber" placeholder="Num" class="input-inline num-input" step="0.1" />
                            <input type="text" v-model="newChapterTitle" placeholder="Chapter Title" class="input-inline text-input" />
                            <button @click="handleCreateChapter" :disabled="creatingChapter" class="btn btn-primary btn-sm">
                                <Plus :size="16" /> Add
                            </button>
                        </div>
                    </div>

                    <div v-if="chapters && chapters.length > 0" class="chapter-list" :class="{ 'loading': chaptersLoading }">
                        <div v-for="chapter in chapters" :key="chapter.id" class="chapter-item" :class="{ 'editing': editingChapterId === chapter.id }">
                            
                            <!-- VIEW MODE -->
                            <template v-if="editingChapterId !== chapter.id">
                                <div class="chapter-info">
                                    <span class="chapter-num">Ch. {{ chapter.chapter_number }}</span>
                                    <span class="chapter-title">{{ chapter.title }}</span>
                                    <span v-if="chapter.page_count" class="page-count">{{ chapter.page_count }} pages</span>
                                </div>
                                <div class="chapter-actions">
                                    <button v-if="chapter.image_urls && chapter.image_urls.length > 0" @click="handleReadChapter(chapter)" class="btn-sm btn-read-chapter">Read</button>
                                    
                                    <div v-if="isSuperuser" class="admin-chapter-actions">
                                        <button @click="startEditingChapter(chapter)" class="btn-icon-sm" title="Edit Info">
                                            <Edit2 :size="14" />
                                        </button>

                                        <label class="btn-icon-sm" :title="chapter.image_urls?.length ? 'Replace Images' : 'Upload Images'" :class="{ 'has-images': chapter.image_urls?.length, 'uploading': chaptersUploading.has(chapter.id) }">
                                            <Loader2 v-if="chaptersUploading.has(chapter.id)" class="spinner-icon-sm" :size="14" />
                                            <ImageIcon v-else :size="14" />
                                            <input type="file" multiple accept="image/*" @change="handleChapterImagesUpload(chapter.id, $event)" :disabled="chaptersUploading.has(chapter.id)" style="display:none;" />
                                        </label>
                                        
                                        <button @click="handleDeleteChapter(chapter.id)" class="btn-icon-sm text-danger" title="Delete">
                                            <Trash2 :size="14" />
                                        </button>
                                    </div>
                                </div>
                            </template>

                            <!-- EDIT MODE -->
                            <template v-else>
                                <div class="chapter-edit-form">
                                    <div class="edit-inputs">
                                        <div class="input-group">
                                            <label class="input-label">Num</label>
                                            <input type="number" v-model="editForm.chapter_number" class="input-inline num-input" step="0.1" />
                                        </div>
                                        <div class="input-group">
                                            <label class="input-label">Title</label>
                                            <input type="text" v-model="editForm.title" class="input-inline text-input" />
                                        </div>
                                    </div>
                                    <div class="edit-actions">
                                        <button @click="saveChapterEdit" class="btn-sm btn-save">
                                            <Check :size="14" /> Save
                                        </button>
                                        <button @click="cancelEditChapter" class="btn-sm btn-cancel">
                                            <X :size="14" />
                                        </button>
                                    </div>
                                </div>
                            </template>

                        </div>
                    </div>
                    <div v-else-if="!chaptersLoading" class="no-chapters">
                        <p>No chapters available yet.</p>
                    </div>
                    
                    <!-- Pagination Controls -->
                    <Pagination 
                        v-if="chaptersTotalPages > 1"
                        :current-page="chaptersPage"
                        :total-pages="chaptersTotalPages"
                        :scroll-to-top="false"
                        @update:current-page="chaptersPage = $event"
                        @change="loadChapters"
                    />
                </div>
                
                <!-- Danger Zone -->
                <div v-if="isSuperuser" class="danger-zone">
                    <div class="danger-header">
                        <h4>Danger Zone</h4>
                    </div>
                    <div class="danger-content">
                         <p>Once you delete a comic, there is no going back. Please be certain.</p>
                         <button @click="handleDelete" class="btn btn-danger-outline">
                            <Trash2 :size="16" /> Delete Comic
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
  
  <div v-else class="not-found">
      <h2>404</h2>
      <p>Comic not found</p>
      <RouterLink to="/explore" class="btn btn-primary">Go Home</RouterLink>
  </div>
</template>

<style scoped>
/* Layout & Container */
.detail-wrapper {
    position: relative;
    min-height: 90vh;
    color: #fff;
    width: 100%;
    overflow-x: hidden;
}

.content-container {
    position: relative;
    max-width: 1200px;
    margin: 0 auto;
    padding: 3rem 2rem;
    z-index: 2;
    width: 100%;
    box-sizing: border-box;
}

/* Background Hero */
.hero-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
}

.hero-image {
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    filter: blur(20px);
    transform: scale(1.1);
}

.hero-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to bottom, rgba(10,10,15,0.7) 0%, rgba(10,10,15,0.95) 100%);
}

/* Comic Layout */
.comic-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 3rem;
    align-items: start;
}

.left-col {
    position: sticky;
    top: 100px;
}

/* Cover Card */
.cover-card {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    margin-bottom: 1.5rem;
    background: var(--surface-highlight);
}

.cover-image-wrapper {
    width: 100%;
    aspect-ratio: 2/3;
    overflow: hidden;
}

.cover-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.cover-placeholder {
    width: 100%;
    aspect-ratio: 2/3;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #2d3436, #636e72);
    color: rgba(255,255,255,0.3);
    gap: 1rem;
}

.placeholder-text {
    font-size: 0.9rem;
    font-weight: 600;
}

/* Cover Edit Overlay */
.cover-edit-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s;
    cursor: pointer;
}

.cover-card:hover .cover-edit-overlay {
    opacity: 1;
}

.edit-icon-bg {
    background: var(--primary);
    padding: 1rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #000;
}

.cover-edit-overlay.uploading {
    opacity: 1;
    cursor: wait;
}

/* Primary Actions */
.primary-actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.btn-read {
    background: linear-gradient(135deg, var(--primary), #6366f1);
    color: #000;
    font-weight: 700;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 1.1rem;
}

.btn-read:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(129, 140, 248, 0.4);
}

.btn-disabled {
    background: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.4);
    cursor: not-allowed;
}

/* Right Column */
.header-info {
    margin-bottom: 2rem;
}

.comic-title {
    font-size: 3rem;
    font-weight: 800;
    margin: 0 0 1rem 0;
    line-height: 1.1;
    background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.meta-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.author {
    color: var(--text-muted);
    font-size: 1.1rem;
}

.status-badge {
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.status-badge.ongoing {
    background: rgba(52, 211, 153, 0.2);
    color: #34d399;
}

.status-badge.completed {
    background: rgba(96, 165, 250, 0.2);
    color: #60a5fa;
}

.status-badge.hiatus {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
}

.genres {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}

.genre-tag {
    padding: 0.4rem 1rem;
    background: rgba(255,255,255,0.1);
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.2);
}

/* Description Box */
.description-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(10px);
}

.description-box h3 {
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
    color: var(--primary);
}

.description-box p {
    margin: 0;
    line-height: 1.7;
    color: var(--text-muted);
}

/* Chapters Section */
.chapters-section {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.section-header h3 {
    margin: 0;
    font-size: 1.5rem;
}

.btn-icon-text {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    color: white;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-icon-text:hover {
    background: rgba(255,255,255,0.15);
}

/* Add Chapter Form */
.add-chapter-inline {
    background: rgba(255,255,255,0.05);
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}

.form-row {
    display: flex;
    gap: 0.75rem;
    align-items: center;
}

.input-inline {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
    padding: 0.6rem;
    border-radius: 8px;
    font-size: 0.9rem;
}

.input-inline:focus {
    outline: none;
    border-color: var(--primary);
    background: rgba(255,255,255,0.15);
}

.num-input {
    width: 80px;
}

.text-input {
    flex: 1;
}

/* Chapter List */
.chapter-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}



.chapter-item {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
}

.chapter-item:hover {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.2);
}

.chapter-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
    min-width: 0; /* Allow shrinking below content size */
    margin-right: 1rem;
}

.chapter-num {
    font-weight: 700;
    color: var(--primary);
    min-width: 60px;
    white-space: nowrap;
}

.chapter-title {
    flex: 1;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.page-count {
    font-size: 0.85rem;
    color: var(--text-muted);
    white-space: nowrap;
    flex-shrink: 0;
}

.chapter-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0; /* Prevent actions from shrinking */
}

.admin-chapter-actions {
    display: flex;
    gap: 0.5rem;
}

.btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    border-radius: 8px;
}

.btn-read-chapter {
    background: var(--primary);
    color: #000;
    font-weight: 600;
}

.btn-icon-sm {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    padding: 0.5rem;
    border-radius: 6px;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.btn-icon-sm:hover {
    background: rgba(255,255,255,0.15);
}

.btn-icon-sm.has-images {
    border-color: var(--primary);
    color: var(--primary);
}

.btn-icon-sm.uploading {
    cursor: wait;
}

.text-danger {
    color: #ef4444;
}

.text-danger:hover {
    background: rgba(239, 68, 68, 0.2);
}

/* Edit Form */
.chapter-edit-form {
    display: flex;
    gap: 1rem;
    width: 100%;
    align-items: center;
}

.edit-inputs {
    display: flex;
    gap: 0.75rem;
    flex: 1;
}

.input-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.input-label {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.edit-actions {
    display: flex;
    gap: 0.5rem;
}

.btn-save {
    background: var(--primary);
    color: #000;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.btn-cancel {
    background: rgba(255,255,255,0.1);
    color: white;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.no-chapters {
    text-align: center;
    color: var(--text-muted);
    padding: 2rem;
}

/* Danger Zone */
.danger-zone {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 16px;
    overflow: hidden;
}

.danger-header {
    background: rgba(239, 68, 68, 0.2);
    padding: 1rem 1.5rem;
    border-bottom: 1px solid rgba(239, 68, 68, 0.3);
}

.danger-header h4 {
    margin: 0;
    color: #ef4444;
    font-size: 1.1rem;
}

.danger-content {
    padding: 1.5rem;
}

.danger-content p {
    margin: 0 0 1rem 0;
    color: var(--text-muted);
}

.btn-danger-outline {
    background: transparent;
    border: 2px solid #ef4444;
    color: #ef4444;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.btn-danger-outline:hover {
    background: rgba(239, 68, 68, 0.2);
}

/* Reading Overlay */
/* Reading Overlay */
.reading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #0a0a0f; /* Deep dark background */
    z-index: 9999;
    display: flex;
    flex-direction: column;
}

.reader-header {
    background: rgba(20, 20, 30, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 0.75rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: fixed;
    top: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 800px;
    z-index: 100;
    border-radius: 50px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    gap: 1rem;
}

.reader-title {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
}

.reader-controls-center {
    display: flex;
    gap: 1rem;
}

.btn-icon {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    padding: 0.6rem;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-icon:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-icon:active {
    transform: translateY(0);
}

.btn-icon:disabled {
    opacity: 0.3;
    cursor: not-allowed;
    background: rgba(255, 255, 255, 0.02);
}

.close-btn {
    background: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
    color: #ef4444;
}

.close-btn:hover {
    background: rgba(239, 68, 68, 0.3);
}

.reader-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    position: relative;
}

.scroll-container {
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.3) transparent;
}

.scroll-container::-webkit-scrollbar {
    width: 8px;
}

.scroll-container::-webkit-scrollbar-track {
    background: transparent;
}

.scroll-container::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.3);
    border-radius: 4px;
}

.single-page-reader {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 100%;
    padding: 2rem;
}

.vertical-reader {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 0;
}

.comic-page-image {
    display: block;
    transition: transform 0.2s ease;
    cursor: grab;
}

.comic-page-image:active {
    cursor: grabbing;
}

/* Fit modes */
.comic-page-image.fit-width {
    width: 100%;
    height: auto;
    max-width: 100%;
}

.comic-page-image.fit-height {
    width: auto;
    height: 100%;
    max-height: calc(100vh - 200px);
}

.comic-page-image.manual-zoom {
    max-width: none;
    max-height: none;
}

.vertical-reader .comic-page-image {
    width: 100%;
    height: auto;
    max-width: 100%;
}

.vertical-reader .comic-page-image.manual-zoom {
    width: auto;
}

.reader-footer {
    background: rgba(20, 20, 30, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 0.75rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: fixed;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: auto;
    max-width: 90%;
    z-index: 100;
    border-radius: 50px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.zoom-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.zoom-label {
    font-weight: 600;
    min-width: 60px;
    text-align: center;
    font-size: 0.9rem;
}

.btn-text {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    font-weight: 500;
}

.btn-text:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.25);
    color: #fff;
    transform: translateY(-1px);
}

.btn-text:active {
    transform: translateY(0);
}

.btn-text.active {
    background: var(--primary);
    border-color: var(--primary);
    color: #000;
    font-weight: 700;
    box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.3);
}

.pagination-controls {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.page-counter {
    font-weight: 600;
    min-width: 100px;
    text-align: center;
    background: rgba(0, 0, 0, 0.3);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Loading & Not Found */
.loading, .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 80vh;
    gap: 1rem;
}

.spinner-icon {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.spinner-icon-sm {
    animation: spin 1s linear infinite;
}

/* Responsive */
@media (max-width: 968px) {
    .comic-layout {
        grid-template-columns: 1fr;
        gap: 2rem;
    }

    .left-col {
        position: static;
        max-width: 300px;
        margin: 0 auto;
    }

    .comic-title {
        font-size: 2rem;
    }
}

@media (max-width: 640px) {
    .content-container {
        padding: 2rem 1rem;
    }

    .reader-header, .reader-footer {
        padding: 0.6rem 0.8rem;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        width: 95%;
        max-width: none;
        border-radius: 20px;
    }
    
    .reader-footer {
        bottom: 1rem;
    }

    .reader-header {
        top: 1rem;
        bottom: auto;
    }

    .reader-title {
        font-size: 0.9rem;
        flex: 1;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .reader-content {
        padding: 0.5rem;
    }

    .single-page-reader {
        padding: 1rem;
    }

    .zoom-controls {
        gap: 0.4rem;
        flex-wrap: wrap;
        justify-content: center;
        width: 100%;
    }
    
    .pagination-controls {
        gap: 0.75rem;
    }

    .btn-text {
        padding: 0.4rem 0.6rem;
        font-size: 0.7rem;
    }
    
    .btn-icon {
        padding: 0.5rem;
    }

    .zoom-label {
        min-width: 45px;
        font-size: 0.8rem;
    }
    
    .page-counter {
        min-width: 80px;
        font-size: 0.85rem;
    }

    .chapter-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.85rem;
    }
    
    .chapter-info {
        margin-right: 0;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .chapter-actions {
        width: 100%;
        justify-content: flex-start;
        flex-wrap: wrap;
    }
    
    .admin-chapter-actions {
        flex: 1;
        justify-content: flex-end;
    }
}

@media (max-width: 480px) {
    .content-container {
        padding: 1.5rem 0.75rem;
    }
    
    .comic-title {
        font-size: 1.75rem;
    }
    
    .left-col {
        max-width: 100%;
    }
    
    .btn-sm {
        padding: 0.4rem 0.75rem;
        font-size: 0.8rem;
    }
    
    .input-inline {
        padding: 0.5rem;
        font-size: 0.85rem;
    }
    
    .num-input {
        width: 70px;
    }
}
</style>
