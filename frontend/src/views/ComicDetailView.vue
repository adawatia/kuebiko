<script setup lang="ts">
import { ref, onMounted } from 'vue';
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
const scale = ref(1.0);
const pageNum = ref(1);
const pageCount = ref(0);

const zoomIn = () => {
    scale.value = Math.min(scale.value + 0.2, 3.0);
};

const zoomOut = () => {
    scale.value = Math.max(scale.value - 0.2, 0.5);
};

const onPdfLoaded = (pdfDoc: any) => {
    pageCount.value = pdfDoc.numPages;
};

const prevPage = () => {
    if (pageNum.value > 1) pageNum.value--;
};

const nextPage = () => {
    if (pageNum.value < pageCount.value) pageNum.value++;
};

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

const handleReadOnline = async () => {
    if (pdfUrl.value) {
        readingMode.value = true;
        return;
    }
    
    loading.value = true; // Use separate loading state if preferred, but this blocks UI
    const url = await getPdfBlob();
    if (url) {
        pdfUrl.value = url;
        readingMode.value = true;
    }
    loading.value = false;
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
    <div v-if="readingMode" class="reading-overlay">
        <div class="reader-header">
            <h3>Reading: {{ comic.title }}</h3>
            
            <div class="reader-pagination" v-if="pageCount > 0">
                <button @click="prevPage" :disabled="pageNum <= 1" class="btn btn-sm">Prev</button>
                <span>{{ pageNum }} / {{ pageCount }}</span>
                <button @click="nextPage" :disabled="pageNum >= pageCount" class="btn btn-sm">Next</button>
            </div>

            <div class="reader-controls">
                <button @click="zoomOut" class="btn btn-sm">-</button>
                <span>{{ Math.round(scale * 100) }}%</span>
                <button @click="zoomIn" class="btn btn-sm">+</button>
                <button @click="readingMode = false" class="btn btn-close">Close</button>
            </div>
        </div>
        <div class="reader-content scroll-container">
            <VuePdfEmbed 
                :source="pdfUrl" 
                :page="pageNum"
                :scale="scale"
                @loaded="onPdfLoaded"
                class="pdf-viewer"
            />
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

/* Reader Overlay */
.reading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.95);
    z-index: 1000;
    display: flex;
    flex-direction: column;
}

.reader-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #111;
    border-bottom: 1px solid #333;
}

.reader-header h3 {
    margin: 0;
    color: white;
}

.btn-close {
    background: transparent;
    border: 1px solid #fff;
    color: #fff;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-radius: 4px;
}

.btn-close:hover {
    background: white;
    color: black;
}

.reader-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    color: white;
}

.reader-pagination {
    display: flex;
    align-items: center;
    gap: 1rem;
    color: white;
    font-variant-numeric: tabular-nums;
}

.btn-sm {
    padding: 0.2rem 0.6rem;
    background: #333;
    color: white;
    border: 1px solid #555;
    cursor: pointer;
    border-radius: 4px;
}

.scroll-container {
    overflow-y: auto;
    display: flex;
    justify-content: center;
    background: #333;
    padding: 2rem;
}

.pdf-viewer {
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
    max-width: 100%;
}
.reader-content {
    flex: 1;
    overflow: hidden;
}

.pdf-frame {
    width: 100%;
    height: 100%;
    border: none;
}

.read-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.btn-lg {
    padding: 0.8rem 2rem;
    font-size: 1.1rem;
}

.upload-hint {
    font-size: 0.8rem;
    color: #666;
    align-self: center;
}
</style>
