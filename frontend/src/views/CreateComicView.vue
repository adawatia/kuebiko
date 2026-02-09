<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { createComic } from '../api/comics';
import { useAuth } from '../store';

const router = useRouter();
const { isSuperuser, state } = useAuth();
const title = ref('');
const description = ref('');
const author = ref('');
const status = ref('ongoing');
const statusOptions = [
    { value: 'ongoing', label: 'Ongoing' },
    { value: 'completed', label: 'Completed' },
    { value: 'hiatus', label: 'Hiatus' }
];
const availableGenres = [
    'Action', 'Adventure', 'Fantasy', 'Horror', 'Romance', 'Sci-Fi', 'Mystery', 'Slice of Life', 'Other'
];
const selectedGenres = ref<string[]>([]);
const coverImage = ref<string | null>(null);
const loading = ref(false);
const errorMsg = ref('');

onMounted(() => {
    // Basic protection (though better done in router guard)
    // We wait for user check to complete if loading
    if (!state.loading && !isSuperuser.value) {
       // redirect or show message
    }
});

const handleImageUpload = (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.');
            input.value = '';
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) {
            alert("Image file is too large. Maximum size is 5MB.");
            input.value = ''; // Clear input
            return;
        }
        
        const reader = new FileReader();
        reader.onerror = () => {
            alert('Failed to read image file.');
            input.value = '';
        };
        reader.onload = () => {
             coverImage.value = reader.result as string;
        };
        reader.readAsDataURL(file);
    }
};

const handleSubmit = async () => {
    if (!isSuperuser.value) {
        errorMsg.value = "You do not have permission to upload comics.";
        return;
    }
    
    if (!title.value || !title.value.trim()) {
        alert('Please enter a title');
        return;
    }
    
    if (!description.value || !description.value.trim()) {
        alert('Please enter a description');
        return;
    }

    if (!author.value || !author.value.trim()) {
        alert('Please enter an author');
        return;
    }

    if (selectedGenres.value.length === 0) {
        alert('Please select at least one genre');
        return;
    }

    loading.value = true;
    errorMsg.value = '';

    try {
        // 1. Create Comic Only
        const comic = await createComic({
            title: title.value.trim(),
            description: description.value.trim(),
            author: author.value.trim(),
            status: status.value,
            genres: selectedGenres.value,
            cover_image: coverImage.value
        });
        
        // 2. Redirect to detail page to upload PDF
        router.push(`/comic/${comic.id}`);
        
    } catch (e: any) {
        console.error(e);
        if (e.response && e.response.data && e.response.data.detail) {
             errorMsg.value = typeof e.response.data.detail === 'string' 
                ? e.response.data.detail 
                : JSON.stringify(e.response.data.detail);
        } else {
            errorMsg.value = "Failed to create comic. Please try again.";
        }
    } finally {
        loading.value = false;
    }
};
</script>

<template>
  <div class="create-container">
    <h2>Upload New Comic</h2>
    
    <div v-if="state.loading" class="loading-check">
        Verifying permissions...
    </div>

    <div v-else-if="!isSuperuser" class="permission-denied">
        <p>You do not have permission to perform this action.</p>
        <p class="small">Contact an administrator to request access.</p>
        <RouterLink to="/" class="btn btn-primary">Go Back</RouterLink>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="create-form">
        <div class="form-group">
            <label>Title</label>
            <input type="text" v-model="title" required />
        </div>

        <div class="form-group">
            <label>Author</label>
            <input type="text" v-model="author" required />
        </div>

        <div class="form-group">
            <label>Status</label>
            <div class="status-select">
                <label v-for="opt in statusOptions" :key="opt.value" class="radio-label">
                    <input type="radio" :value="opt.value" v-model="status">
                    <span class="custom-radio">{{ opt.label }}</span>
                </label>
            </div>
        </div>

        <div class="form-group">
            <label>Description</label>
            <textarea v-model="description" rows="5" required></textarea>
        </div>

        <div class="form-group">
            <label>Cover Image (Optional)</label>
            <input type="file" @change="handleImageUpload" accept="image/*" class="file-input" />
            <div v-if="coverImage" class="image-preview">
                <img :src="coverImage" alt="Cover Preview" />
            </div>
        </div>

        <div class="form-group">
            <label>Genres</label>
            <div class="genre-select">
                <label v-for="genre in availableGenres" :key="genre" class="checkbox-label">
                    <input type="checkbox" :value="genre" v-model="selectedGenres">
                    <span class="custom-checkbox">{{ genre }}</span>
                </label>
            </div>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Creating...' : 'Create & Next' }}
        </button>
    </form>
  </div>
</template>

<style scoped>
/* Container */
.create-container {
    max-width: 800px;
    margin: 0 auto;
    padding-top: 2rem;
}

h2 {
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 2.5rem;
    background: linear-gradient(135deg, #fff 0%, #aaa 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}

/* Glassmorphic Form */
.create-form {
    background: rgba(30, 30, 30, 0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    padding: 3rem;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

.form-group {
    margin-bottom: 2.5rem;
}

label {
    display: block;
    margin-bottom: 0.8rem;
    color: var(--text);
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.02em;
}

/* Chips for Genres */
.genre-select {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.checkbox-label {
    position: relative;
    cursor: pointer;
}

.checkbox-label input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.custom-checkbox {
    display: inline-block;
    padding: 0.6rem 1.2rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50px;
    font-size: 0.9rem;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    color: #aaa;
    user-select: none;
}

.checkbox-label:hover .custom-checkbox {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    color: #fff;
}

.checkbox-label input:checked + .custom-checkbox {
    background: var(--primary);
    color: #121212;
    border-color: var(--primary);
    box-shadow: 0 4px 15px rgba(138, 180, 248, 0.4);
    font-weight: 600;
}

/* File Input */
.file-input {
    background: rgba(255,255,255,0.03);
    padding: 1rem;
    border: 2px dashed rgba(255,255,255,0.1);
    border-radius: 12px;
    width: 100%;
    cursor: pointer;
    transition: all 0.2s;
    color: #888;
}

.file-input:hover {
    border-color: rgba(255,255,255,0.3);
    background: rgba(255,255,255,0.05);
}

.image-preview {
    margin-top: 1.5rem;
    width: 200px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
}

.image-preview img {
    width: 100%;
    display: block;
}

/* Messages */
.permission-denied, .loading-check {
    text-align: center;
    padding: 4rem 2rem;
    background: rgba(30, 30, 30, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.permission-denied .small {
    font-size: 0.95rem;
    color: var(--text-muted);
    margin-bottom: 2rem;
}

.error-msg {
    margin-bottom: 2rem;
    padding: 1rem;
    border-radius: 8px;
    background: rgba(242, 139, 130, 0.1);
    color: #F28B82;
    border: 1px solid rgba(242, 139, 130, 0.2);
    text-align: center;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    .create-container {
        padding: 1rem;
    }

    h2 {
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
    }

    .create-form {
        padding: 1.5rem;
        border-radius: 16px;
    }

    .form-group {
        margin-bottom: 1.5rem;
    }

    .genre-select {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
}

@media (max-width: 480px) {
    h2 {
        font-size: 1.5rem;
    }

    .create-form {
        padding: 1.2rem;
    }

    .genre-select {
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
    }

    .custom-checkbox {
        font-size: 0.85rem;
        padding: 0.6rem;
    }
}

.select-input {
    width: 100%;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    color: #fff;
    font-size: 1rem;
    outline: none;
    transition: all 0.2s;
}

.select-input:focus {
    border-color: var(--primary);
    background: rgba(255, 255, 255, 0.08);
}

/* Status Radio Buttons */
.status-select {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.radio-label {
    position: relative;
    cursor: pointer;
}

.radio-label input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.custom-radio {
    display: inline-block;
    padding: 0.6rem 1.2rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50px;
    font-size: 0.9rem;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    color: #aaa;
    user-select: none;
}

.radio-label:hover .custom-radio {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    color: #fff;
}

.radio-label input:checked + .custom-radio {
    background: var(--primary);
    color: #121212;
    border-color: var(--primary);
    box-shadow: 0 4px 15px rgba(138, 180, 248, 0.4);
    font-weight: 600;
}
</style>
