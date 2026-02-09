import apiClient from './client';

export interface Chapter {
    id: number;
    comic_id: number;
    chapter_number: number;
    title: string;
    pdf_url: string | null;
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

export const getChapters = async (comicId: number, skip = 0, limit = 100): Promise<Chapter[]> => {
    const response = await apiClient.get('/chapters/', {
        params: { comic_id: comicId, skip, limit }
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

export const uploadChapterPdf = async (id: number, file: File) => {
    const formData = new FormData();
    formData.append('pdf', file);
    const response = await apiClient.post(`/chapters/${id}/pdf`, formData);
    return response.data;
};

export const bulkDeleteChapters = async (ids: number[]): Promise<void> => {
    await apiClient.post('/chapters/batch-delete', ids);
};
