<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import { useAuth } from './store';
import { Menu, X, Home, Upload, LogOut, User } from 'lucide-vue-next';

const router = useRouter();
const { state, logout: authLogout, fetchUser, isSuperuser } = useAuth();
const isMenuOpen = ref(false);

const handleLogout = () => {
    authLogout();
    router.push('/login');
    isMenuOpen.value = false;
};

const toggleMenu = () => {
    isMenuOpen.value = !isMenuOpen.value;
};

const closeMenu = () => {
    isMenuOpen.value = false;
};

onMounted(() => {
    if (state.isAuthenticated) {
        fetchUser();
    }
});
</script>

<template>
  <div class="app-container">
    <header v-if="state.isAuthenticated">
      <nav>
        <div class="logo">
            <img src="./assets/logo.svg" alt="Kuebiko Logo" class="logo-img" />
            <span>Kuebiko</span>
        </div>
        
        <!-- Mobile Menu Button -->
        <button class="menu-btn" @click="toggleMenu">
            <X v-if="isMenuOpen" />
            <Menu v-else />
        </button>

        <div class="nav-links" :class="{ 'active': isMenuOpen }">
            <RouterLink to="/" @click="closeMenu">
                <Home :size="18" /> Home
            </RouterLink>
            <!-- Only show Upload if superuser -->
            <RouterLink v-if="isSuperuser" to="/create" @click="closeMenu">
                <Upload :size="18" /> Upload Comic
            </RouterLink>
            <div class="user-info" v-if="state.user">
                <User :size="16" />
                {{ state.user.email }}
                <span v-if="isSuperuser" class="badge">Admin</span>
            </div>
            <button @click="handleLogout" class="logout-btn">
                <LogOut :size="18" /> Logout
            </button>
        </div>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-container {
    font-family: 'Inter', sans-serif;
    color: var(--text);
    background-color: var(--background);
    min-height: 100vh;
}

header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(18, 18, 18, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0.8rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.logo {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
}

.logo-img {
    height: 80px;
    width: auto;
}

.logo span {
    background: linear-gradient(45deg, #fff, #ccc);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nav-links {
    display: flex;
    gap: 1.5rem;
    align-items: center;
}

.nav-links a {
    color: #aaa;
    text-decoration: none;
    transition: color 0.3s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    line-height: 1;
}

.nav-links a:hover, .nav-links a.router-link-active {
    color: #fff;
    font-weight: 500;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.9rem;
    color: #ccc;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.4rem 0.8rem;
    border-radius: 50px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.badge {
    background: linear-gradient(135deg, #ff6b6b, #ff8e53);
    color: white;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.logout-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #ccc;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-radius: 50px;
    transition: all 0.3s;
    font-size: 0.85rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.logout-btn:hover {
    border-color: #ff6b6b;
    color: #ff6b6b;
    background: rgba(255, 107, 107, 0.1);
}

.menu-btn {
    display: none;
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 0.5rem;
}

main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    header {
        padding: 0.8rem 1rem;
    }

    .logo {
        font-size: 1.2rem;
    }

    .logo-img {
        height: 50px;
    }

    .menu-btn {
        display: block;
        z-index: 2001;
        position: relative; /* Ensure it stays above the fixed menu */
    }

    .nav-links {
        position: fixed;
        top: 0;
        right: 0;
        height: 100vh;
        width: 100%;
        max-width: 100%; /* Full width for premium feel */
        background: rgba(10, 10, 10, 0.98); /* Deep dark background */
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 2.5rem;
        padding: 2rem;
        transform: translateX(100%);
        transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 2000;
    }

    .nav-links.active {
        transform: translateX(0);
        box-shadow: none;
    }

    .nav-links a {
        font-size: 1.5rem;
        font-weight: 600;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }

    .nav-links.active a {
        opacity: 1;
        transform: translateY(0);
        transition-delay: 0.1s;
    }
    
    .nav-links.active .user-info {
        opacity: 1;
        transform: translateY(0);
        transition-delay: 0.2s;
    }
    
    .nav-links.active .logout-btn {
        opacity: 1;
        transform: translateY(0);
        transition-delay: 0.3s;
    }

    .user-info {
        flex-direction: column;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem 1.5rem;
        border-radius: 16px;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }

    .logout-btn {
        width: auto;
        padding: 0.8rem 2rem;
        background: rgba(255, 107, 107, 0.1);
        color: #ff6b6b;
        border-color: rgba(255, 107, 107, 0.3);
        font-size: 1rem;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }

    main {
        padding: 1rem;
        /* Ensure content doesn't get hidden behind fixed headers oddly */
        margin-top: 0; 
    }
}

@media (max-width: 480px) {
    .nav-links {
        width: 100%;
        max-width: 100%;
    }
}
</style>
