<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { login } from '../api/auth';
import { useAuth } from '../store';

const email = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();
const { login: authLogin } = useAuth(); // methods from store

const handleLogin = async () => {
  try {
    const formData = new FormData();
    formData.append('username', email.value); 
    formData.append('password', password.value);
    
    const response = await login(formData);
    localStorage.setItem('token', response.access_token);
    
    // Update store state
    authLogin();

    router.push('/explore');
  } catch (e) {
    error.value = 'Invalid credentials';
    console.error(e);
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="logo-container">
        <img src="../assets/logo.svg" alt="Kuebiko Logo" class="auth-logo" />
      </div>
      <h2>Welcome Back</h2>
      <p class="subtitle">Enter your credentials to access your comics</p>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="email" required placeholder="you@example.com" />
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" />
        </div>
        
        <div v-if="error" class="error-msg">{{ error }}</div>
        
        <button type="submit" class="btn btn-primary full-width">Sign In</button>
      </form>
      
      <div class="footer-links">
        <p>Don't have an account? <RouterLink to="/register">Create one</RouterLink></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.auth-card {
  background: rgba(30, 30, 30, 0.6);
  backdrop-filter: blur(10px);
  padding: 2.5rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.logo-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.auth-logo {
  height: 120px;
  width: auto;
}

h2 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #bb86fc, #03dac6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
}

.subtitle {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.full-width {
  width: 100%;
  margin-top: 1rem;
}

.error-msg {
  color: var(--error);
  font-size: 0.9rem;
  margin-bottom: 1rem;
  text-align: center;
}

.footer-links {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
}

.footer-links a {
  color: var(--primary);
  text-decoration: none;
}

.footer-links a:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  .auth-container {
    padding: 1.5rem 1rem;
    min-height: auto;
  }

  .auth-card {
    padding: 1.75rem;
    border-radius: 14px;
  }

  .auth-logo {
    height: 96px;
  }

  h2 {
    font-size: 1.6rem;
  }

  .subtitle {
    margin-bottom: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }
}
</style>
