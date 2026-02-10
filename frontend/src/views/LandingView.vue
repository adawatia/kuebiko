<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuth } from '../store';

const { state } = useAuth();
</script>

<template>
  <div class="landing-container">
    <div class="hero-section">
      <div class="logo-wrapper">
        <img src="../assets/logo.svg" alt="Kuebiko Logo" class="logo" />
      </div>
      
      <h1 class="title">Kuebiko Comics</h1>
      <p class="subtitle">Your personal comic library, redefined.</p>
      
      <div class="cta-group">
        <template v-if="state.isAuthenticated">
          <RouterLink to="/explore" class="btn btn-primary btn-lg">
            Go to Library
          </RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-primary btn-lg">
            Login
          </RouterLink>
          <RouterLink to="/register" class="btn btn-secondary btn-lg">
            Register
          </RouterLink>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-container {
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  background-color: var(--background);
  background-image: 
    radial-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(135deg, #000000 0%, #1e293b 100%);
  background-size: 30px 30px, 100% 100%;
  background-attachment: fixed;
}

.hero-section {
  max-width: 800px;
  width: 100%;
  padding: 3rem;
  background: rgba(30, 30, 30, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  animation: fadeIn 0.8s ease-out;
}

.logo-wrapper {
  margin-bottom: 2rem;
  animation: float 6s ease-in-out infinite;
}

.logo {
  height: 150px;
  width: auto;
  filter: drop-shadow(0 0 20px rgba(165, 180, 252, 0.3));
}

.title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 1.5rem;
  color: var(--text-muted, #94a3b8);
  margin-bottom: 3rem;
  font-weight: 400;
}

.cta-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}

.btn-lg {
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  border-radius: 12px;
  min-width: 160px;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 2rem 1.5rem;
  }
  
  .title {
    font-size: 2.5rem;
  }
  
  .subtitle {
    font-size: 1.2rem;
    margin-bottom: 2.5rem;
  }
  
  .logo {
    height: 100px;
  }
  
  .cta-group {
    flex-direction: column;
    gap: 1rem;
  }
  
  .btn-lg {
    width: 100%;
  }
}
</style>
