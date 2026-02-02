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
    color: #e0e0e0;
    background-color: #121212;
    min-height: 100vh;
}

header {
  background-color: #1e1e1e;
  padding: 1rem 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.5);
  display: flex;
  justify-content: space-between;
  align-items: center;
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
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #888;
}

.badge {
    background: #ff6b6b;
    color: white;
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: bold;
}

.logout-btn {
    background: transparent;
    border: 1px solid #444;
    color: #aaa;
    padding: 0.4rem 0.8rem;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.3s;
    font-size: 0.85rem;
}

.logout-btn:hover {
    border-color: #ff6b6b;
    color: #ff6b6b;
}

main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}
</style>
