import apiClient from './client';

export interface ComicGenre {
  value: string;
}

export interface Comic {
  id: number;
  title: string;
  description: string;
  genres: string[]; // Backend returns list of strings/enums
  pdf_path: string | null;
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
  // Handle array params for genres if needed, axios handles this usually but might need specific format for FastAPI
  // FastAPI expects `genres=Action&genres=Fantasy`
  if (genres.length > 0) params.genres = genres;
  
  const response = await apiClient.get('/comics/', {
    params,
    paramsSerializer: {
       indexes: null // to produce param=val&param=val2
    }
  });
  return response.data;
};

export const getComic = async (id: number): Promise<Comic> => {
  const response = await apiClient.get(`/comics/${id}`);
  return response.data;
};

export const createComic = async (comicData: { title: string; description: string; genres: string[] }): Promise<Comic> => {
  const response = await apiClient.post('/comics/', comicData);
  return response.data;
};

export const deleteComic = async (id: number): Promise<void> => {
   await apiClient.delete(`/comics/${id}`);
};

export const uploadComicPdf = async (id: number, file: File) => {
  const formData = new FormData();
  formData.append('pdf', file);
  const response = await apiClient.post(`/comics/${id}/pdf`, formData);
  return response.data;
};

export const bulkDeleteComics = async (ids: number[]): Promise<void> => {
    await apiClient.post('/comics/batch-delete', ids);
};
