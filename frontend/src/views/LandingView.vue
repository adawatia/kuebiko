<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useAuth } from '../store';
import logoSvg from '../assets/logo.svg';

const { state } = useAuth();
const handleImageError = (e: Event) => {
  (e.target as HTMLImageElement).style.visibility = 'hidden';
};
</script>

<template>
  <div class="landing-container">
    <div class="hero-section">
      <div class="logo-wrapper">
        <img :src="logoSvg" alt="Kuebiko Logo" class="logo" @error="handleImageError" />
      </div>
      
      <h1 class="title">Kuebiko Comics</h1>
      <p class="subtitle">Your personal comic library, redefined.</p>
      
      <div class="cta-group">
        <RouterLink to="/explore" class="btn btn-primary btn-lg">
          Explore Comics
        </RouterLink>
        <template v-if="!state.isAuthenticated">
          <RouterLink to="/login" class="btn btn-secondary btn-lg">
            Login
          </RouterLink>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-container {
  min-height: 100vh; /* Fallback */
  min-height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  margin: 0;
  background-color: var(--background);
  /* Halftone pattern for comic feel */
  background-image: 
    radial-gradient(rgba(138, 180, 248, 0.2) 2px, transparent 2px),
    linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  background-size: 24px 24px, 100% 100%;
  background-position: 0 0, 0 0;
  /* overflow: hidden; Removed to allow scrolling on small screens */
}

.hero-section {
  max-width: 800px;
  width: 100%;
  padding: 3rem;
  background: rgba(30, 30, 30, 0.6); /* Slightly more opaque */
  backdrop-filter: blur(12px);
  /* Cartoonish thick border and hard shadow */
  border: 3px solid rgba(138, 180, 248, 0.5);
  border-radius: 24px;
  box-shadow: 12px 12px 0 rgba(0, 0, 0, 0.5); /* "Pop" shadow */
  animation: fadeIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy entrance */
  transform: rotate(-1deg); /* Slight playful tilt */
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  backface-visibility: hidden; /* Prevent jagged edges */
  will-change: transform;
}

.hero-section:hover,
.hero-section:active {
  transform: rotate(0deg) scale(1.01);
}

.logo-wrapper {
  margin-bottom: 2rem;
  animation: float 4s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; /* Faster, bouncier float */
}

.logo {
  height: 150px;
  width: auto;
  filter: drop-shadow(4px 4px 0 rgba(138, 180, 248, 0.4)); /* Hard shadow on logo */
}

.title {
  font-size: 4.5rem; /* Larger */
  font-weight: 900; /* Bolder */
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
  letter-spacing: -0.02em;
  /* Cartoon title effect */
  filter: drop-shadow(3px 3px 0px rgba(138, 180, 248, 0.3));
}

.subtitle {
  font-size: 1.5rem;
  color: #c7d2e6;
  margin-bottom: 3rem;
  font-weight: 500;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.5);
}

.cta-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}

.btn {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy transition */
  font-weight: 700; /* Bolder text */
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
}

.btn:focus-visible {
  outline: 3px solid var(--primary);
  outline-offset: 4px;
}

.btn-lg {
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  border-radius: 16px; /* slightly more rounded */
  min-width: 160px;
  border: 2px solid transparent;
}

/* Specific styling for primary button to make it pop */
.btn-primary {
  box-shadow: 4px 4px 0 rgba(0,0,0, 0.4) !important;
  border: 2px solid rgba(255,255,255,0.1);
}

.btn-primary:hover {
  transform: translate(-2px, -2px) !important;
  box-shadow: 6px 6px 0 rgba(0,0,0, 0.5) !important;
}

.btn-primary:active {
  transform: translate(2px, 2px) !important;
  box-shadow: 2px 2px 0 rgba(0,0,0, 0.5) !important;
}

.btn-secondary {
  box-shadow: 4px 4px 0 rgba(0,0,0, 0.4) !important;
}

.btn-secondary:hover {
   transform: translate(-2px, -2px);
   box-shadow: 6px 6px 0 rgba(0,0,0, 0.5) !important;
   background-color: rgba(255, 255, 255, 0.15);
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); } /* Higher float */
}

@media (prefers-reduced-motion: reduce) {
  .logo-wrapper {
    animation: none;
  }
  
  .hero-section {
    animation: fadeInSimple 0.5s ease-out;
    transform: none; /* No tilt */
    transition: none;
  }
  
  .hero-section:hover {
    transform: none; /* No hover tilt/scale */
  }
  
  .btn, .btn-primary:hover, .btn-secondary:hover {
    transition: none;
    transform: none !important;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(40px) scale(0.9) rotate(-3deg); }
  to { opacity: 1; transform: translateY(0) scale(1) rotate(-1deg); }
}

@keyframes fadeInMobile {
  from { opacity: 0; transform: translateY(40px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes fadeInSimple {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 1024px) {
  .title {
    font-size: 3.5rem;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 2rem 1.5rem;
    /* transform: none; Removed to keep desktop tilt */
    animation-name: fadeInMobile; /* Non-rotating entrance for mobile */
    transform: none;
  }
  
  /* Removed .hero-section:hover override to keep desktop hover effect */
  
  .title {
    font-size: 2.8rem;
  }
  
  .subtitle {
    font-size: 1.2rem;
    margin-bottom: 2rem; /* Reduced from 2.5rem */
  }
  
  .logo-wrapper {
    animation-duration: 6s;
    margin-bottom: 1.5rem; /* Reduced margin */
  }
  
  .logo {
    height: 100px;
  }
  
  .cta-group {
    flex-direction: column;
    gap: 0.75rem; /* Tighter gap */
  }
  
  .btn-lg {
    width: 100%;
    padding: 0.8rem 2rem; /* Slightly smaller padding */
  }
}
</style>
