<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { createComic } from '../api/comics';
import { useAuth } from '../store';

const router = useRouter();
const { isSuperuser, state } = useAuth();
const title = ref('');
const description = ref('');
const availableGenres = [
    'Action', 'Adventure', 'Fantasy', 'Horror', 'Romance', 'Sci-Fi', 'Mystery', 'Other'
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
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
        const reader = new FileReader();
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

    if (selectedGenres.value.length === 0) {
        alert('Please select at least one genre');
        return;
    }

    loading.value = true;
    errorMsg.value = '';
    
    let comicId: number | null = null;

    try {
        // 1. Create Comic Only
        const comic = await createComic({
            title: title.value,
            description: description.value,
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
.create-container {
    max-width: 800px;
    margin: 0 auto;
}

h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
}

.create-form {
    background: #1e1e1e;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #333;
}

.form-group {
    margin-bottom: 2rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--text-muted);
}

.hint {
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.25rem;
}

.genre-select {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1rem;
}

.checkbox-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    background: #2d2d2d;
    padding: 0.5rem;
    border-radius: 4px;
    transition: background 0.2s;
}

.checkbox-label:hover {
    background: #3d3d3d;
}

.checkbox-label input {
    margin-right: 0.5rem;
    width: auto;
}

.permission-denied {
    text-align: center;
    padding: 3rem;
    background: #1e1e1e;
    border-radius: 12px;
}

.permission-denied .small {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 2rem;
}

.loading-check {
    text-align: center;
    padding: 3rem;
    color: #888;
}

.error-msg {
    margin-bottom: 1.5rem;
    border: 1px solid var(--error);
}

.file-input {
    background: #2d2d2d;
    padding: 0.5rem;
    border-radius: 4px;
    width: 100%;
}

.image-preview {
    margin-top: 1rem;
    max-width: 200px;
}

.image-preview img {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #444;
}
</style>
