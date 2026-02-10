import apiClient from './client';

export interface Chapter {
    id: number;
    comic_id: number;
    chapter_number: number;
    title: string;
    image_urls: string[];
    page_count: number | null;
    is_published: boolean;
    published_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface ChapterCreate {
    comic_id: number;
    chapter_number: number;
    title: string;
    page_count?: number;
    is_published?: boolean;
}

export interface ChapterUpdate {
    chapter_number?: number;
    title?: string;
    page_count?: number;
    is_published?: boolean;
}

export interface ChapterListResponse {
    items: Chapter[];
    total_chapters: number;
    total_pages: number;
    current_page: number;
    items_per_page: number;
    next_page_available: boolean;
    prev_page_available: boolean;
}

export const getChapters = async (comicId: number, page = 1, perPage = 10): Promise<ChapterListResponse> => {
    const response = await apiClient.get('/chapters/', {
        params: { comic_id: comicId, page, per_page: perPage }
    });
    return response.data;
};

export const getChapter = async (id: number): Promise<Chapter> => {
    const response = await apiClient.get(`/chapters/${id}`);
    return response.data;
};

export const createChapter = async (chapterData: ChapterCreate): Promise<Chapter> => {
    const response = await apiClient.post('/chapters/', chapterData);
    return response.data;
};

export const updateChapter = async (id: number, chapterData: ChapterUpdate): Promise<Chapter> => {
    const response = await apiClient.put(`/chapters/${id}`, chapterData);
    return response.data;
};

export const deleteChapter = async (id: number): Promise<void> => {
    await apiClient.delete(`/chapters/${id}`);
};

export const uploadChapterImages = async (id: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => {
        formData.append('images', file);
    });
    const response = await apiClient.post(`/chapters/${id}/images`, formData);
    return response.data;
};

export const bulkDeleteChapters = async (ids: number[]): Promise<void> => {
    await apiClient.post('/chapters/batch-delete', ids);
};
