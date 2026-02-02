<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { register } from '../api/auth';

const email = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const handleRegister = async () => {
  try {
    await register({
        email: email.value,
        password: password.value,
        is_active: true,
        is_superuser: false,
        is_verified: false
    });
    router.push('/login');
  } catch (e: any) {
    if (e.response && e.response.data && e.response.data.detail) {
        error.value = typeof e.response.data.detail === 'string' 
            ? e.response.data.detail 
            : JSON.stringify(e.response.data.detail);
    } else {
        error.value = 'Registration failed. Try again.';
    }
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>Create Account</h2>
      <p class="subtitle">Join to start reading comics</p>
      
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="email" required placeholder="you@example.com" />
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" />
        </div>
        
        <div v-if="error" class="error-msg">{{ error }}</div>
        
        <button type="submit" class="btn btn-primary full-width">Sign Up</button>
      </form>
      
      <div class="footer-links">
        <p>Already have an account? <RouterLink to="/login">Sign In</RouterLink></p>
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
</style>
