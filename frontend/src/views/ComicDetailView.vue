<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch, nextTick, shallowRef } from 'vue';
import { BookOpen, Image as ImageIcon, FileText, Trash2, X, AlertCircle, Book, Loader2, ArrowUpDown, ChevronLeft, ChevronRight, Plus, Minus, Minimize, Maximize } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router';
import { getComic, deleteComic, uploadComicPdf, updateComic, type Comic } from '../api/comics';
import apiClient, { API_URL } from '../api/client';
import VuePdfEmbed from 'vue-pdf-embed';
import { useAuth } from '../store';
import InfiniteLoading from "v3-infinite-loading";
import "v3-infinite-loading/lib/style.css";
import * as pdfjsLib from 'pdfjs-dist';

// Configure Worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const route = useRoute();
const router = useRouter();
const { isSuperuser } = useAuth();
const comic = ref<Comic | null>(null);
const loading = ref(true);
const uploading = ref(false);
const readingMode = ref(false);

const pdfSource = ref<string | object | null>(null);
const pdfDocument = shallowRef<any>(null); // Optimization: Cache loaded PDF document

// Reader state
const pageNum = ref(1);
const pageCount = ref(0);
const zoomLevel = ref(0.8);
const windowWidth = ref(document.documentElement.clientWidth || window.innerWidth);
const readerScroll = ref<HTMLElement | null>(null);
const pageRefs = ref<HTMLElement[]>([]);

// Scroll Mode
const scrollMode = ref<'horizontal' | 'vertical'>('horizontal');
const verticalPages = ref<number[]>([]);
const hasMorePages = computed(() => verticalPages.value.length < pageCount.value);

let observer: IntersectionObserver | null = null;

// Returns either the document proxy (if loaded) or the source URL
// This ensures subsequent pages in vertical mode load instantly from memory
const actualSource = computed(() => pdfDocument.value || pdfSource.value);

const pdfWidth = computed(() => {
    return Math.floor(windowWidth.value * zoomLevel.value);
});

const updateWindowWidth = () => {
    windowWidth.value = document.documentElement.clientWidth || window.innerWidth;
};

// Intersection Observer for Vertical Page Tracking
watch(verticalPages, async (newPages, oldPages) => {
    // Only update observer if pages were added, not reset
    if (newPages.length === 0) {
        if (observer) {
            observer.disconnect();
        }
        return;
    }
    
    await nextTick();
    
    // Create observer once if it doesn't exist
    if (!observer) {
        observer = new IntersectionObserver((entries) => {
            // Find the most visible page (highest intersection ratio)
            let mostVisible = entries[0];
            for (const entry of entries) {
                if (entry.isIntersecting && entry.intersectionRatio > (mostVisible?.intersectionRatio || 0)) {
                    mostVisible = entry;
                }
            }
            
            if (mostVisible && mostVisible.isIntersecting && mostVisible.intersectionRatio > 0.3) {
                const p = Number(mostVisible.target.getAttribute('data-page'));
                if (p && p !== pageNum.value) {
                    pageNum.value = p;
                }
            }
        }, { threshold: [0, 0.3, 0.5, 0.7, 1.0] });
    }
    
    // Observe only newly added pages
    const startIndex = oldPages?.length || 0;
    for (let i = startIndex; i < newPages.length; i++) {
        await nextTick();
        const el = pageRefs.value[i];
        if (el && !el.hasAttribute('data-observed')) {
            observer.observe(el);
            el.setAttribute('data-observed', 'true');
        }
    }
});

// Watch for route changes to close reader if navigating to another comic
watch(() => route.params.id, (newId, oldId) => {
    if (newId !== oldId && readingMode.value) {
        closeReader();
    }
});

const onPdfLoaded = (pdfDoc: any) => {
    // Set page count only once from the first loaded instance
    if (pageCount.value === 0 && pdfDoc?.numPages) {
        pageCount.value = pdfDoc.numPages;
    }
    // Optimization: Store the loaded document proxy (only once)
    if (!pdfDocument.value && pdfDoc) {
        pdfDocument.value = pdfDoc;
    }
};

const toggleScrollMode = async () => {
    const prevMode = scrollMode.value;
    scrollMode.value = scrollMode.value === 'horizontal' ? 'vertical' : 'horizontal';
    
    // Clean up observer when switching modes
    if (observer) {
        observer.disconnect();
        observer = null;
    }
    
    await nextTick();

    if (scrollMode.value === 'vertical') {
        // Initialize vertical mode with pages up to current page
        verticalPages.value = [];
        const pagesToLoad = Math.min(pageNum.value || 1, pageCount.value || 1);
        for(let i = 1; i <= pagesToLoad; i++) {
            verticalPages.value.push(i);
        }
        // Scroll to top of vertical reader
        await nextTick();
        scrollToTop();
    } else {
        // Switching to horizontal mode - maintain current page
        verticalPages.value = [];
        pageRefs.value = [];
        // Ensure pageNum is valid
        if (pageNum.value < 1) pageNum.value = 1;
        if (pageCount.value > 0 && pageNum.value > pageCount.value) {
            pageNum.value = pageCount.value;
        }
        await nextTick();
        scrollToTop();
    }
};

const handleLoadMore = ($state: any) => {
    // Guard against loading before pageCount is known
    if (pageCount.value === 0) {
        // Defer until pageCount is set
        setTimeout(() => handleLoadMore($state), 100);
        return;
    }
    
    const nextPage = verticalPages.value.length + 1;
    
    if (nextPage <= pageCount.value) {
        // Check if page isn't already in the array (prevent duplicates)
        if (!verticalPages.value.includes(nextPage)) {
            verticalPages.value.push(nextPage);
        }
        $state.loaded();
    } else {
        $state.complete();
    }
};

const fitToWidth = () => {
    if (Math.abs(zoomLevel.value - 1.0) < 0.01) {
        zoomLevel.value = 0.8;
    } else {
        zoomLevel.value = 1.0;
    }
};

const zoomIn = () => {
    zoomLevel.value = Math.min(zoomLevel.value + 0.1, 2.0);
};

const zoomOut = () => {
    zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.3);
};

const scrollToTop = () => {
    if (readerScroll.value) {
        readerScroll.value.scrollTop = 0;
    }
};

const prevPage = () => {
    if (pageNum.value > 1) {
        pageNum.value--;
        scrollToTop();
    }
};

const nextPage = () => {
    if (pageNum.value < pageCount.value) {
        pageNum.value++;
        scrollToTop();
    }
};

const closeReader = () => {
    readingMode.value = false;
    pdfSource.value = null; 
    pdfDocument.value = null; // Clear cached doc
    verticalPages.value = [];
    pageNum.value = 1;
    pageCount.value = 0;
    pageRefs.value = [];
    if (observer) {
        observer.disconnect();
        observer = null;
    }
};

const handleReadOnline = () => {
    try {
        if (!comic.value?.pdf_path) {
            alert('No PDF available for this comic.');
            return;
        }
        
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Please log in to read comics.');
            router.push('/login');
            return;
        }
        
        pdfSource.value = {
            url: `${API_URL}/comics/${comicId}/pdf`,
            httpHeaders: { Authorization: `Bearer ${token}` },
            withCredentials: false
        };

        // Initialize based on current scroll mode
        if (scrollMode.value === 'vertical') {
            verticalPages.value = [1];
        } else {
            verticalPages.value = [];
        }
        
        pageNum.value = 1; // Reset to page 1 for reader open
        readingMode.value = true;
    } catch (e) {
        console.error('Error opening PDF reader:', e);
        alert('Failed to open PDF reader.');
    }
};

const handleKeydown = (e: KeyboardEvent) => {
    if (!readingMode.value) return;
    
    // Disable arrow paging in vertical mode to allow natural scrolling
    if (scrollMode.value === 'vertical') {
       if (e.key === 'Escape') {
           e.preventDefault();
           closeReader();
       }
       if (e.key === '+' || e.key === '=') {
           e.preventDefault();
           zoomIn();
       }
       if (e.key === '-' || e.key === '_') {
           e.preventDefault();
           zoomOut();
       }
       return; 
    }

    // Horizontal mode with keyboard navigation
    if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        nextPage();
    } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevPage();
    } else if (e.key === 'Escape') {
        e.preventDefault();
        closeReader();
    } else if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomIn();
    } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        zoomOut();
    }
};

const comicId = parseInt(route.params.id as string);

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
    
    const shouldRead = route.query.read === 'true';
    await fetchComic();
    
    if (shouldRead && comic.value?.pdf_path) {
        handleReadOnline();
    }
});

onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth);
    window.removeEventListener('keydown', handleKeydown);
    if (observer) {
        observer.disconnect();
        observer = null;
    }
});

const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this comic?')) {
        try {
            await deleteComic(comicId);
            router.push('/');
        } catch (e) {
            alert('Failed to delete comic');
        }
    }
};

const getPdfBlob = async () => {
    try {
        const response = await apiClient.get(`/comics/${comicId}/pdf`, { responseType: 'blob' });
        return window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    } catch (e) {
        alert('Failed to load PDF.');
        return null;
    }
};

const downloadPdf = async () => {
    const url = await getPdfBlob();
    if (url) {
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${comic.value?.title || 'comic'}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    }
};

const handleUploadPdf = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
        const file = target.files[0];
        if (!file) return;
        uploading.value = true;
        try {
            await uploadComicPdf(comicId, file);
            await fetchComic(); // Refresh to see updated status
            pdfSource.value = null; // Reset cached source
            pdfDocument.value = null; // Clear cached document
            alert('PDF uploaded successfully!');
        } catch (e) {
            alert('Failed to upload PDF');
        } finally {
            uploading.value = false;
            // Clear input
            target.value = '';
        }
    }
}


const handleUploadCover = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
        const file = target.files[0];
        if (!file) return;
        
        if (file.size > 5 * 1024 * 1024) {
            alert("Image file is too large. Maximum size is 5MB.");
            target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = async () => {
            try {
                uploading.value = true;
                const base64String = reader.result as string;
                await updateComic(comicId, { cover_image: base64String });
                await fetchComic();
                alert('Cover image updated successfully!');
            } catch (e: any) {
                console.error(e);
                alert('Failed to update cover image.');
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
                 <button @click="toggleScrollMode" class="btn-icon" :title="scrollMode === 'horizontal' ? 'Switch to Vertical Scroll' : 'Switch to Horizontal Standard'">
                    <ArrowUpDown v-if="scrollMode === 'horizontal'" />
                    <BookOpen v-else />
                </button>
            </div>

            <button @click="closeReader" class="btn-icon close-btn" title="Close Reader">
                <X />
            </button>
        </div>

        <div class="reader-content scroll-container" ref="readerScroll">
            <div class="pdf-wrapper" :style="{ width: pdfWidth + 'px' }">
                
                <!-- Horizontal Mode -->
                <div v-if="scrollMode === 'horizontal'" class="horizontal-reader">
                    <VuePdfEmbed 
                        v-if="pdfSource"
                        :source="pdfSource" 
                        :page="pageNum"
                        @loaded="onPdfLoaded"
                        class="pdf-viewer"
                        :width="pdfWidth"
                    />
                    <div v-else class="pdf-loading">
                        <Loader2 class="spinner-icon" />
                        <p>Loading PDF...</p>
                    </div>
                </div>

                <!-- Vertical Mode -->
                <div v-else class="vertical-reader">
                    <div v-for="page in verticalPages" :key="page" class="page-wrapper" :data-page="page" ref="pageRefs">
                        <VuePdfEmbed 
                            :source="pdfSource" 
                            :page="page"
                            @loaded="onPdfLoaded"
                            class="pdf-page"
                            :width="pdfWidth"
                        />
                    </div>
                    <InfiniteLoading @infinite="handleLoadMore" v-if="pageCount > 0">
                        <template #complete>
                            <span class="end-message">End of Comic</span>
                        </template>
                        <template #error>
                             <span class="error-message">Error loading pages</span>
                        </template>
                    </InfiniteLoading>
                </div>

            </div>
        </div>

        <div class="reader-footer" v-if="scrollMode === 'horizontal'">
            <div class="zoom-controls">
                <button @click="zoomOut" class="btn-icon">－</button>
                <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="btn-icon">＋</button>
                <button @click="fitToWidth" class="btn-text">Fit Width</button>
            </div>

            <div class="pagination-controls" v-if="pageCount > 0">
                <button @click="prevPage" :disabled="pageNum <= 1" class="btn-icon">←</button>
                <span class="page-counter">{{ pageNum }} / {{ pageCount }}</span>
                <button @click="nextPage" :disabled="pageNum >= pageCount" class="btn-icon">→</button>
            </div>
        </div>
        
        <!-- Vertical Footer (Simplified) -->
        <div class="reader-footer" v-else>
             <div class="zoom-controls">
                <button @click="zoomOut" class="btn-icon">－</button>
                <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="btn-icon">＋</button>
                <button @click="fitToWidth" class="btn-text">Fit Width</button>
            </div>
             <div class="pagination-controls">
                <span class="page-counter">{{ pageNum }} / {{ pageCount }}</span>
            </div>
        </div>
    </div>

    <!-- Background Hero -->
    <div class="hero-bg">
        <div class="hero-image" 
             :style="comic.cover_image_path ? { backgroundImage: `url(${API_URL}/comics/${comic.id}/cover?v=${comic.cover_image_path})` } : {}">
        </div>
        <div class="hero-overlay"></div>
    </div>

    <div class="content-container">
        <!-- Main Content -->
        <div class="comic-layout">
            <!-- Left Column: Cover & Actions -->
            <div class="left-col">
                <div class="cover-card">
                    <div v-if="comic.cover_image_path" class="cover-image-wrapper">
                        <img :src="`${API_URL}/comics/${comic.id}/cover?v=${comic.cover_image_path}`" :alt="comic.title" class="cover-image" />
                    </div>
                    <div v-else class="cover-placeholder">
                        <Book class="placeholder-icon" :size="48" />
                        <span class="placeholder-text">No Cover</span>
                    </div>
                </div>

                <div class="primary-actions">
                    <button v-if="comic.pdf_path" @click="handleReadOnline" class="btn btn-read">
                        <BookOpen class="icon" :size="20" /> Read Now
                    </button>
                    <button v-else disabled class="btn btn-disabled">
                        No PDF Available
                    </button>
                    <!-- Future: Add Favorite / Download buttons here -->
                </div>
            </div>

            <!-- Right Column: Details -->
            <div class="right-col">
                <div class="header-info">
                    <h1 class="comic-title">{{ comic.title }}</h1>
                    <div class="genres">
                        <span v-for="g in comic.genres" :key="g" class="genre-tag">{{ g }}</span>
                    </div>
                </div>

                <div class="description-box">
                    <h3>Synopsis</h3>
                    <p>{{ comic.description }}</p>
                </div>
                
                <!-- Admin Zone -->
                <div v-if="isSuperuser" class="admin-panel">
                    <div class="admin-header">Admin Controls</div>
                    <div class="admin-grid">
                        <label class="btn btn-admin" :class="{ 'uploading': uploading }">
                            <FileText :size="18" />
                            {{ uploading ? 'Wait...' : (comic.pdf_path ? 'Replace PDF' : 'Upload PDF') }}
                            <input type="file" accept="application/pdf" @change="handleUploadPdf" :disabled="uploading" style="display:none;" />
                        </label>
                        
                        <label class="btn btn-admin" :class="{ 'uploading': uploading }">
                            <ImageIcon :size="18" />
                            {{ uploading ? 'Wait...' : (comic.cover_image_path ? 'Replace Cover' : 'Upload Cover') }}
                            <input type="file" accept="image/*" @change="handleUploadCover" :disabled="uploading" style="display:none;" />
                        </label>

                        <button @click="handleDelete" class="btn btn-admin btn-danger">
                            <Trash2 :size="18" /> Delete
                        </button>
                    </div>
                    <p class="admin-hint">Max file sizes: PDF 100MB, Image 5MB</p>
                </div>
            </div>
        </div>
    </div>
  </div>
  
  <div v-else class="not-found">
      <h2>404</h2>
      <p>Comic not found</p>
      <RouterLink to="/" class="btn btn-primary">Go Home</RouterLink>
  </div>
</template>

<style scoped>
/* Layout & Container */
.detail-wrapper {
    position: relative;
    min-height: 90vh;
    color: #fff;
    overflow-x: hidden;
}

.content-container {
    position: relative;
    max-width: 1200px;
    margin: 0 auto;
    padding: 3rem 2rem;
    z-index: 2;
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
    background-repeat: no-repeat;
    filter: blur(20px) brightness(0.4);
    transform: scale(1.1); /* Prevent blur edges */
}

.hero-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to bottom, rgba(18,18,18,0.8) 0%, rgba(18,18,18,1) 90%);
}

/* Grid Layout */
.comic-layout {
    display: grid;
    grid-template-columns: 350px 1fr;
    gap: 4rem;
    align-items: start;
}

@media (max-width: 900px) {
    .comic-layout {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .left-col {
        max-width: 400px;
        margin: 0 auto;
        width: 100%;
    }
}

/* Cover Image */
.cover-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    transition: transform 0.3s ease;
    background: #1e1e1e;
    aspect-ratio: 2/3;
    position: relative;
}

.cover-card:hover {
    transform: translateY(-5px);
}

.cover-image-wrapper {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
}

.cover-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.cover-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    color: #666;
    border: 2px dashed #444;
}

.placeholder-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.placeholder-text {
    font-weight: 600;
    font-size: 1.2rem;
}

/* Actions */
.primary-actions {
    margin-top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.btn-read {
    background: linear-gradient(135deg, var(--primary) 0%, #4a90e2 100%);
    color: white;
    font-size: 1.1rem;
    font-weight: 700;
    padding: 1rem;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
    box-shadow: 0 4px 20px rgba(138, 180, 248, 0.3);
}

.btn-read:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(138, 180, 248, 0.5);
    filter: brightness(1.1);
}

.btn-disabled {
    background: rgba(255,255,255,0.1);
    color: #888;
    cursor: not-allowed;
    border: 1px solid rgba(255,255,255,0.05);
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
}

/* Right Column Info */
.comic-title {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin: 0 0 1rem 0;
    background: linear-gradient(90deg, #fff 0%, #bbb 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.genres {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    margin-bottom: 2.5rem;
}

.genre-tag {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.4rem 1rem;
    border-radius: 50px;
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: #ddd;
    text-transform: uppercase;
}

.description-box {
    margin-bottom: 3rem;
}

.description-box h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: var(--primary);
    font-weight: 600;
}

.description-box p {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #ccc;
    white-space: pre-wrap;
}

/* Admin Panel */
.admin-panel {
    background: rgba(30, 30, 30, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
}

.admin-header {
    font-size: 0.85rem;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #666;
    margin-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding-bottom: 0.5rem;
}

.admin-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
}

.btn-admin {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #ccc;
    padding: 0.8rem;
    border-radius: 8px;
    font-size: 0.9rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: background 0.2s;
}

.btn-admin:hover {
    background: rgba(255,255,255,0.1);
    color: white;
    border-color: rgba(255,255,255,0.2);
}

.btn-danger {
    background: rgba(207, 102, 121, 0.1);
    border-color: rgba(207, 102, 121, 0.3);
    color: #cf6679;
}

.btn-danger:hover {
    background: rgba(207, 102, 121, 0.2);
    color: white;
    border-color: #cf6679;
}

.admin-hint {
    font-size: 0.8rem;
    color: #555;
    margin-top: 1rem;
    text-align: center;
}

/* Loading & Error */
.loading, .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    color: #888;
}

.spinner-icon {
    width: 40px;
    height: 40px;
    color: var(--primary);
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

/* Reader Styles (Reused & Tweaked) */
/* Reader Styles (Premium) */
.reading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000;
    z-index: 9999;
    display: flex;
    flex-direction: column;
}

.reader-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 1.5rem;
    background: rgba(20, 20, 20, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: fixed;
    top: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: auto;
    min-width: 320px;
    max-width: 90vw;
    z-index: 10;
    height: auto;
    border-radius: 50px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    box-sizing: border-box;
}

.reader-title {
    margin: 0;
    color: #e0e0e0;
    font-size: 1rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
}

.reader-content {
    flex: 1;
    overflow-y: auto;
    background: #050505;
    display: flex;
    justify-content: center;
    padding-top: 100px;
    padding-bottom: 120px;
}

.reader-footer {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(20, 20, 20, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.8rem 2rem;
    border-radius: 50px;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2rem;
    z-index: 10;
    box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    height: auto;
    width: auto;
}

/* Reader Controls */
.zoom-controls, .pagination-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.btn-icon {
    background: transparent;
    border: none;
    color: #fff;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    font-size: 1.2rem;
}

.btn-icon:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.15);
    transform: scale(1.1);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
}

.btn-icon:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.close-btn {
    color: #aaa;
}

.close-btn:hover {
    background: rgba(255, 59, 48, 0.15);
    color: #ff3b30;
}

.btn-text {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ccc;
    font-size: 0.75rem;
    padding: 0.4rem 0.8rem;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
}

.btn-text:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.3);
}

.zoom-label, .page-counter {
    font-family: 'JetBrains Mono', monospace; /* Monospace for steady numbers */
    color: #aaa;
    font-size: 0.9rem;
    min-width: 40px;
    text-align: center;
    font-weight: 500;
    user-select: none;
}

.page-counter {
    min-width: 80px;
    background: rgba(0, 0, 0, 0.3);
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
}

.pdf-wrapper {
    box-shadow: 0 0 50px rgba(0,0,0,0.8);
    transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* Vertical Reader */
.vertical-reader {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0; 
    width: 100%;
}

/* Horizontal Reader */
.horizontal-reader {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    width: 100%;
    min-height: 70vh;
}

.pdf-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    color: #888;
}

.pdf-page {
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    background: white; 
    margin-bottom: 0;
    display: block;
}

.end-message {
    color: #fff;
    padding: 2rem;
    font-size: 1.1rem;
    opacity: 0.7;
}

.error-message {
    color: #cf6679;
    margin: 2rem 0;
}

.reader-controls-center {
    flex: 1;
    display: flex;
    justify-content: center;
}

.page-wrapper {
    min-height: 50vh; /* Prevent collapse before load */
    width: 100%;
    display: flex;
    justify-content: center;
}

.pdf-viewer {
    box-shadow: 0 0 30px rgba(0,0,0,0.5);
    background: white;
    min-height: 50vh;
    display: block;
}
</style>
