<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { onMounted } from 'vue'
import { useAuth } from './store';

const router = useRouter();
const { state, logout: authLogout, fetchUser, isSuperuser } = useAuth();

const handleLogout = () => {
    authLogout();
    router.push('/login');
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
        <div class="nav-links">
            <RouterLink to="/">Home</RouterLink>
            <!-- Only show Upload if superuser -->
            <RouterLink v-if="isSuperuser" to="/create">Upload Comic</RouterLink>
            <div class="user-info" v-if="state.user">
                {{ state.user.email }}
                <span v-if="isSuperuser" class="badge">Admin</span>
            </div>
            <button @click="handleLogout" class="logout-btn">Logout</button>
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
}

.nav-links a:hover, .nav-links a.router-link-active {
    color: #fff;
    font-weight: 500;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 0.8rem;
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
}

.logout-btn:hover {
    border-color: #ff6b6b;
    color: #ff6b6b;
    background: rgba(255, 107, 107, 0.1);
}

main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}
</style>
