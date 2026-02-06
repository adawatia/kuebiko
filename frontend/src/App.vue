<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { onMounted, ref, watch } from 'vue'
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

// Prevent body scroll when mobile menu is open
watch(isMenuOpen, (newValue) => {
    if (newValue) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
});

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
                <Home class="nav-icon" :size="20" /> 
                <span class="link-text">Home</span>
            </RouterLink>
            <!-- Only show Upload if superuser -->
            <RouterLink v-if="isSuperuser" to="/create" @click="closeMenu">
                <Upload class="nav-icon" :size="20" /> 
                <span class="link-text">Upload Comic</span>
            </RouterLink>
            <div class="user-info" v-if="state.user">
                <User :size="18" />
                <span class="user-email">{{ state.user.email }}</span>
                <span v-if="isSuperuser" class="badge">Admin</span>
            </div>
            <button @click="handleLogout" class="logout-btn">
                <LogOut :size="18" /> 
                <span>Logout</span>
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
    width: 100%;
    overflow-x: hidden;
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
    color: #94a3b8;
    text-decoration: none;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}

.nav-links a:hover, .nav-links a.router-link-active {
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
}

.nav-icon {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.nav-links a:hover .nav-icon {
    transform: scale(1.1);
    color: #818cf8;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 0.9rem;
    color: #e2e8f0;
    background: rgba(30, 41, 59, 0.5);
    padding: 0.5rem 1rem;
    border-radius: 50px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.badge {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    font-size: 0.65rem;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
}

.logout-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #cbd5e1;
    padding: 0.6rem 1.2rem;
    cursor: pointer;
    border-radius: 50px;
    transition: all 0.3s;
    font-size: 0.9rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.logout-btn:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
}

.menu-btn {
    display: none;
    background: transparent;
    border: none;
    color: white;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 50%;
    transition: background 0.2s;
}

.menu-btn:hover {
    background: rgba(255,255,255,0.1);
}

.menu-btn:focus {
    outline: none;
    box-shadow: none;
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
        height: 100dvh;
        width: 100%;
        max-width: 100%;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(10, 10, 10, 0.99) 100%);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        padding: 2rem;
        transform: translateX(100%);
        transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 2000;
        overflow-y: auto;
    }

    .nav-links.active {
        transform: translateX(0);
    }

    .nav-links a {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        padding: 1rem 2rem;
        background: transparent;
    }

    .nav-links a:hover {
        color: #818cf8;
        transform: scale(1.05);
        background: rgba(255, 255, 255, 0.03);
    }

    .nav-links.active a {
        opacity: 1;
        transform: translateY(0);
    }
    
    .nav-links.active a:nth-child(1) { transition-delay: 0.1s; }
    .nav-links.active a:nth-child(2) { transition-delay: 0.15s; }

    .nav-links.active .user-info {
        opacity: 1;
        transform: translateY(0);
        transition-delay: 0.25s;
    }
    
    .nav-links.active .logout-btn {
        opacity: 1;
        transform: translateY(0);
        transition-delay: 0.3s;
    }

    .user-info {
        flex-direction: column;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 23, 42, 0.6));
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 2rem;
        border-radius: 24px;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
        margin-top: 2rem;
        min-width: 260px;
        justify-content: center;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }

    .user-info svg {
        width: 48px;
        height: 48px;
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 50%;
        margin-bottom: 0.5rem;
        color: #e2e8f0;
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.05);
    }

    .user-email {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f8fafc;
        margin: 0.5rem 0;
        text-align: center;
        letter-spacing: 0.02em;
    }

    .badge {
        font-size: 0.75rem;
        padding: 0.4rem 1.2rem;
        margin-top: 0.5rem;
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        letter-spacing: 0.1em;
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
        margin-top: 0;
        width: 100%;
        overflow-x: hidden;
        box-sizing: border-box;
    }
}

@media (max-width: 480px) {
    .nav-links {
        width: 100%;
        max-width: 100%;
    }
}
</style>
