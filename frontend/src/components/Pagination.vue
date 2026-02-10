<script setup lang="ts">
import { computed } from 'vue';
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';

// Props
const props = withDefaults(defineProps<{
    currentPage: number;
    totalPages: number;
    scrollToTop?: boolean;
}>(), {
    scrollToTop: true
});

// Emits
const emit = defineEmits<{
    (e: 'update:currentPage', page: number): void;
    (e: 'change', page: number): void;
}>();

// Methods
const handlePageChange = (page: number) => {
    if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
        emit('update:currentPage', page);
        emit('change', page);
        // Scroll to top when page changes if enabled
        if (props.scrollToTop) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
};

const visiblePages = computed(() => {
    const pages: (number | string)[] = [];
    const { currentPage, totalPages } = props;
    
    // If total pages is small, show all
    if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) {
            pages.push(i);
        }
        return pages;
    }

    // Determine the range of pages to show around current
    let start, end;
    
    if (currentPage <= 4) {
        // Near start
        start = 1;
        end = 5;
    } else if (currentPage >= totalPages - 3) {
        // Near end
        start = totalPages - 4;
        end = totalPages;
    } else {
        // Middle
        start = currentPage - 1;
        end = currentPage + 1;
    }
    
    // Safety check
    if (start < 1) start = 1;
    if (end > totalPages) end = totalPages;

    // Build the list
    if (start > 1) {
        pages.push(1);
        if (start > 2) pages.push('...');
    }
    
    for (let i = start; i <= end; i++) {
        pages.push(i);
    }
    
    if (end < totalPages) {
        if (end < totalPages - 1) pages.push('...');
        pages.push(totalPages);
    }

    return pages;
});
</script>

<template>
    <div class="pagination-container" v-if="totalPages > 1">
        <button 
            class="nav-btn prev"
            :disabled="currentPage === 1"
            @click="handlePageChange(currentPage - 1)"
            aria-label="Previous Page"
        >
            <ChevronLeft :size="20" />
            <span class="label">Previous</span>
        </button>
        
        <div class="pages-list">
            <template v-for="(item, index) in visiblePages" :key="index">
                <span v-if="item === '...'" class="ellipsis">...</span>
                
                <button 
                    v-else
                    class="page-btn"
                    :class="{ active: item === currentPage }"
                    @click="handlePageChange(item as number)"
                    :aria-current="item === currentPage ? 'page' : undefined"
                >
                    {{ item }}
                </button>
            </template>
        </div>

        <button 
            class="nav-btn next"
            :disabled="currentPage === totalPages"
            @click="handlePageChange(currentPage + 1)"
            aria-label="Next Page"
        >
            <span class="label">Next</span>
            <ChevronRight :size="20" />
        </button>
    </div>
</template>

<style scoped>
.pagination-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    padding: 1.5rem;
    width: 100%;
    margin-top: 2rem;
}

.nav-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}

.nav-btn:hover:not(:disabled) {
    color: var(--text);
    background: rgba(255, 255, 255, 0.05);
}

.nav-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.pages-list {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.page-btn {
    min-width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: transparent; /* Default inactive bg */
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-btn:hover:not(.active) {
    background: rgba(255, 255, 255, 0.08); /* Hover effect for inactive */
    border-color: rgba(255, 255, 255, 0.2);
    color: var(--text);
    transform: translateY(-2px);
}

.page-btn.active {
    background: var(--surface-highlight);
    border-color: var(--primary);
    color: var(--primary);
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(138, 180, 248, 0.3);
    transform: scale(1.05);
}

.ellipsis {
    color: var(--text-muted);
    padding: 0 0.25rem;
    font-size: 1.2rem;
    letter-spacing: 2px;
}

/* Responsive adjustments */
@media (max-width: 640px) {
    .pagination-container {
        gap: 0.5rem;
        padding: 1rem 0.5rem;
    }
    
    .nav-btn {
        padding: 0.5rem;
    }
    
    .nav-btn .label {
        display: none;
    }
    
    .page-btn {
        min-width: 36px;
        height: 36px;
        font-size: 0.9rem;
        border-radius: 10px;
    }

    .pages-list {
        gap: 0.3rem;
    }
}
</style>
