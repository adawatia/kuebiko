<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getComic, deleteComic, uploadComicPdf, type Comic } from '../api/comics';
import apiClient from '../api/client';
import VuePdfEmbed from 'vue-pdf-embed';
import { useAuth } from '../store';

const route = useRoute();
const router = useRouter();
const { isSuperuser } = useAuth();
const comic = ref<Comic | null>(null);
const loading = ref(true);
const uploading = ref(false);
const readingMode = ref(false);
const pdfUrl = ref<string | null>(null);

// Reader state
const pageNum = ref(1);
const pageCount = ref(0);
const zoomLevel = ref(0.8); // 80% screen width by default
const windowWidth = ref(window.innerWidth);
const readerScroll = ref<HTMLElement | null>(null);

const pdfWidth = computed(() => {
    return Math.floor(windowWidth.value * zoomLevel.value);
});

const updateWindowWidth = () => {
    windowWidth.value = window.innerWidth;
};

const fitToWidth = () => {
    zoomLevel.value = 0.95; 
};

const zoomIn = () => {
    zoomLevel.value = Math.min(zoomLevel.value + 0.1, 2.0);
};

const zoomOut = () => {
    zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.3);
};

const onPdfLoaded = (pdfDoc: any) => {
    pageCount.value = pdfDoc.numPages;
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
    // Cleanup blob url to free memory
    if (pdfUrl.value) {
        URL.revokeObjectURL(pdfUrl.value);
        pdfUrl.value = null; // Will trigger re-fetch if opened again, ensuring fresh data
    }
};

const handleReadOnline = async () => {
    if (pdfUrl.value) {
        readingMode.value = true;
        return;
    }
    
    loading.value = true; 
    const url = await getPdfBlob();
    if (url) {
        pdfUrl.value = url;
        readingMode.value = true;
    }
    loading.value = false;
};

const handleKeydown = (e: KeyboardEvent) => {
    if (!readingMode.value) return;
    
    if (e.key === 'ArrowRight' || e.key === ' ') {
        nextPage();
    } else if (e.key === 'ArrowLeft') {
        prevPage();
    } else if (e.key === 'Escape') {
        closeReader();
    } else if (e.key === '+') {
        zoomIn();
    } else if (e.key === '-') {
        zoomOut();
    }
};

onMounted(() => {
    fetchComic();
    window.addEventListener('resize', updateWindowWidth);
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth);
    window.removeEventListener('keydown', handleKeydown);
});

const comicId = parseInt(route.params.id as string);

const fetchComic = async () => {
    try {
        comic.value = await getComic(comicId);
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchComic();
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
        uploading.value = true;
        try {
            await uploadComicPdf(comicId, file);
            await fetchComic(); // Refresh to see updated status
            pdfUrl.value = null; // Reset cached URL
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
</script>

<template>
  <div class="detail-container" v-if="comic">
    <!-- Reading Mode Overlay -->
    <!-- Reading Mode Overlay -->
    <div v-if="readingMode" class="reading-overlay">
        <!-- Top Bar: Title & Close -->
        <div class="reader-header">
            <h3 class="reader-title">{{ comic.title }}</h3>
            <button @click="closeReader" class="btn-icon close-btn" title="Close Reader">
                ✕
            </button>
        </div>

        <!-- Main Content Area -->
        <div class="reader-content scroll-container" ref="readerScroll">
            <div class="pdf-wrapper" :style="{ width: pdfWidth + 'px' }">
                <VuePdfEmbed 
                    :source="pdfUrl" 
                    :page="pageNum"
                    @loaded="onPdfLoaded"
                    class="pdf-viewer"
                    :width="pdfWidth"
                />
            </div>
        </div>

        <!-- Bottom Bar: Controls -->
        <div class="reader-footer">
            <div class="zoom-controls">
                <button @click="zoomOut" class="btn-icon" title="Zoom Out">−</button>
                <span class="zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="btn-icon" title="Zoom In">+</button>
                <button @click="fitToWidth" class="btn-text">Fit Width</button>
            </div>

            <div class="pagination-controls" v-if="pageCount > 0">
                <button @click="prevPage" :disabled="pageNum <= 1" class="btn-icon">←</button>
                <span class="page-counter">Page {{ pageNum }} / {{ pageCount }}</span>
                <button @click="nextPage" :disabled="pageNum >= pageCount" class="btn-icon">→</button>
            </div>
        </div>
    </div>

    <div class="comic-header">
        <h1>{{ comic.title }}</h1>
        <div class="meta">
            <span class="genre" v-for="g in comic.genres" :key="g">{{ g }}</span>
        </div>
    </div>

    <div class="content-split">
        <div class="info-section">
            <h3>Description</h3>
            <p class="description">{{ comic.description }}</p>

            <div class="actions">
                <div v-if="comic.pdf_path" class="read-actions">
                    <button @click="handleReadOnline" class="btn btn-primary btn-lg">
                        Read Online
                    </button>
                    <button @click="downloadPdf" class="btn btn-outline">
                        Download PDF
                    </button>
                </div>
                <div v-else class="no-pdf">
                    <button disabled class="btn btn-secondary">
                        No PDF Available
                    </button>
                </div>
                
                <div v-if="isSuperuser" class="admin-actions">
                    <label class="btn btn-outline" :class="{ 'uploading': uploading }">
                        {{ uploading ? 'Uploading...' : (comic.pdf_path ? 'Replace PDF' : 'Upload PDF') }}
                        <input type="file" accept="application/pdf" @change="handleUploadPdf" :disabled="uploading" style="display:none;" />
                    </label>
                    <span class="upload-hint">Max 100MB</span>
                    
                    <button @click="handleDelete" class="btn btn-danger">Delete Comic</button>
                </div>
            </div>
        </div>
        
        <!-- Placeholder for cover image if we had one -->
        <div class="cover-placeholder">
            <div class="placeholder-text">Cover Image</div>
        </div>
    </div>
  </div>
  <div v-else-if="loading" class="loading">Loading...</div>
  <div v-else class="not-found">Comic not found</div>
</template>

<style scoped>
.detail-container {
    padding: 2rem 0;
}

.comic-header {
    margin-bottom: 2rem;
    border-bottom: 1px solid #333;
    padding-bottom: 1rem;
}

h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.meta {
    display: flex;
    gap: 1rem;
}

.genre {
    background: #333;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.9rem;
}

.content-split {
    display: flex;
    gap: 3rem;
    flex-wrap: wrap;
}

.info-section {
    flex: 2;
    min-width: 300px;
}

.description {
    font-size: 1.1rem;
    line-height: 1.6;
    color: #ccc;
    margin-bottom: 2rem;
}

.actions {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    align-items: flex-start;
}

.admin-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #333;
    width: 100%;
}

.cover-placeholder {
    flex: 1;
    min-width: 250px;
    height: 400px;
    background: #1e1e1e;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #444;
}

.placeholder-text {
    color: #444;
    font-weight: 700;
    font-size: 1.5rem;
}

.btn-secondary {
    background: #333;
    color: #aaa;
    cursor: default;
}

.btn-danger {
    background: transparent;
    border: 1px solid #cf6679;
    color: #cf6679;
}

.btn-danger:hover {
    background: #cf6679;
    color: white;
}

.btn-outline {
    background: transparent;
    border: 1px solid var(--primary);
    color: var(--primary);
    cursor: pointer;
}

.btn-outline:hover {
    background: rgba(187, 134, 252, 0.1);
}

.loading {
    text-align: center;
    padding: 2rem;
    color: #888;
}

.not-found {
    text-align: center;
    padding: 2rem;
    font-size: 1.5rem;
    color: #aaa;
}

/* Modern Reader UI */
.reading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000; /* Deep dark background */
    z-index: 2000;
    display: flex;
    flex-direction: column;
}

.reader-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: rgba(20, 20, 20, 0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    position: absolute;
    top: 0;
    width: 100%;
    z-index: 10;
    height: 60px;
    box-sizing: border-box;
}

.reader-title {
    margin: 0;
    color: #e0e0e0;
    font-size: 1.1rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.reader-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 80px; /* Header space */
    padding-bottom: 100px; /* Footer space */
    background: #0a0a0a;
}

.pdf-wrapper {
    transition: width 0.2s ease-out;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}

.pdf-viewer {
    display: block;
    width: 100%;
}

.reader-footer {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(30, 30, 30, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.8rem 1.5rem;
    border-radius: 50px;
    display: flex;
    gap: 2rem;
    align-items: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    z-index: 10;
}

.zoom-controls, .pagination-controls {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.btn-icon {
    background: transparent;
    border: none;
    color: #fff;
    font-size: 1.2rem;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-icon:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.15);
}

.btn-icon:disabled {
    opacity: 0.3;
    cursor: default;
}

.zoom-label, .page-counter {
    color: #ccc;
    font-size: 0.9rem;
    font-variant-numeric: tabular-nums;
    font-weight: 500;
    min-width: 3ch;
    text-align: center;
}

.page-counter {
    min-width: 80px;
}

.btn-text {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.2);
    color: #aaa;
    font-size: 0.75rem;
    padding: 0.3rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
}

.btn-text:hover {
    border-color: #fff;
    color: #fff;
}

.page-loader {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    background: rgba(0,0,0,0.7);
    padding: 1rem 2rem;
    border-radius: 8px;
    pointer-events: none;
}

.close-btn {
    font-size: 1.2rem;
    color: #aaa;
}
.close-btn:hover {
    color: #fff;
    background: rgba(255, 0, 0, 0.2);
}
</style>
