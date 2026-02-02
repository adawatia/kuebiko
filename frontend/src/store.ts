import { reactive, computed } from 'vue';
import { getMe, type User } from './api/auth';

interface State {
    user: User | null;
    isAuthenticated: boolean;
    loading: boolean;
}

const state = reactive<State>({
    user: null,
    isAuthenticated: !!localStorage.getItem('token'),
    loading: false
});

export const useAuth = () => {
    const fetchUser = async () => {
        if (!state.isAuthenticated) return;
        state.loading = true;
        try {
            const user = await getMe();
            state.user = user;
        } catch (e) {
            // If fetch fails (likely 401 caught by interceptor), reset state
            state.user = null;
            state.isAuthenticated = false;
        } finally {
            state.loading = false;
        }
    };

    const login = () => {
        state.isAuthenticated = true;
        fetchUser();
    };

    const logout = () => {
        localStorage.removeItem('token');
        state.user = null;
        state.isAuthenticated = false;
    };

    return {
        state,
        fetchUser,
        login,
        logout,
        isSuperuser: computed(() => state.user?.is_superuser || false)
    };
};
