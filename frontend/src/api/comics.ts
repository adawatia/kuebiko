import apiClient from './client';
import type { Chapter } from './chapters';

export interface ComicGenre {
  value: string;
}

export interface Comic {
  id: number;
  title: string;
  description: string;
  author: string;
  status: string; // 'ongoing' | 'completed' | 'hiatus'
  genres: string[];
  cover_image_url: string | null;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  chapters: Chapter[];
}

export interface ComicListResponse {
  items: Comic[];
  total_comics: number;
  total_pages: number;
  current_page: number;
  items_per_page: number;
  next_page_available: boolean;
  prev_page_available: boolean;
}

export const getComics = async (page = 1, perPage = 10, search = '', genres: string[] = []): Promise<ComicListResponse> => {
  const params: any = { page, per_page: perPage };
  if (search) params.search = search;
  if (genres.length > 0) params.genres = genres;
  
  const response = await apiClient.get('/comics/', {
    params,
    paramsSerializer: {
       indexes: null 
    }
  });
  return response.data;
};

export const getComic = async (id: number): Promise<Comic> => {
  const response = await apiClient.get(`/comics/${id}`);
  return response.data;
};

export const createComic = async (comicData: { title: string; description: string; author: string; status?: string; genres: string[]; cover_image?: string | null }): Promise<Comic> => {
  const response = await apiClient.post('/comics/', comicData);
  return response.data;
};

export const updateComic = async (id: number, comicData: { title?: string; description?: string; author?: string; status?: string; genres?: string[]; cover_image?: string | null }): Promise<Comic> => {
  const response = await apiClient.put(`/comics/${id}`, comicData);
  return response.data;
};

export const deleteComic = async (id: number): Promise<void> => {
   await apiClient.delete(`/comics/${id}`);
};

export const bulkDeleteComics = async (ids: number[]): Promise<void> => {
    await apiClient.post('/comics/batch-delete', ids);
};
