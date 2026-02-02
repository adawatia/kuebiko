import apiClient from './client';

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
}

export const login = async (formData: FormData): Promise<{ access_token: string; token_type: string }> => {
  // Convert to URLSearchParams to force application/x-www-form-urlencoded
  const params = new URLSearchParams();
  formData.forEach((value, key) => {
      params.append(key, value as string);
  });
  
  const response = await apiClient.post('/auth/jwt/login', params, {
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
      }
  });
  return response.data;
};

export const register = async (userData: any): Promise<User> => {
  const response = await apiClient.post('/auth/register', userData);
  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get('/users/me');
  return response.data;
};
