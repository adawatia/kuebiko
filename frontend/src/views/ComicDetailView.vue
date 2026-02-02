<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { BookOpen, Image as ImageIcon, FileText, Trash2, X, AlertCircle, Book, Loader2 } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router';
import { getComic, deleteComic, uploadComicPdf, updateComic, type Comic } from '../api/comics';
import apiClient, { API_URL } from '../api/client';
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

const fetchComic = async (finalizeLoading = true) => {
    try {
        comic.value = await getComic(comicId);
    } catch (e) {
        console.error(e);
    } finally {
        if (finalizeLoading) {
            loading.value = false;
        }
    }
};

onMounted(async () => {
    const shouldRead = route.query.read === 'true';
    // If we are going to read immediately, keep loading state active
    await fetchComic(!shouldRead);
    
    if (shouldRead) {
        await handleReadOnline();
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
            <button @click="closeReader" class="btn-icon close-btn" title="Close Reader">
                <X />
            </button>
        </div>

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

        <div class="reader-footer">
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
    height: 60px;
    background: rgba(10,10,10,0.9);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    padding: 0 2rem;
    justify-content: space-between;
    border-bottom: 1px solid #333;
}

.reader-content {
    flex: 1;
    overflow-y: auto;
    background: #050505;
    display: flex;
    justify-content: center;
    padding: 2rem 0;
}

.reader-footer {
    height: 70px;
    background: rgba(10,10,10,0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    border-top: 1px solid #333;
    gap: 2rem;
}

.pdf-wrapper {
    box-shadow: 0 0 50px rgba(0,0,0,0.8);
}
</style>
