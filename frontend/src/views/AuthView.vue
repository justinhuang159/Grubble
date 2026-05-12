<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const mode = ref<"signin" | "signup">("signin");
const email = ref("");
const password = ref("");
const displayName = ref("");
const error = ref("");
const loading = ref(false);
const signedUp = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    if (mode.value === "signup") {
      await auth.signUp(email.value, password.value, displayName.value);
      signedUp.value = true;
    } else {
      await auth.signIn(email.value, password.value);
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Something went wrong.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="glass-card">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">
          {{ mode === "signin" ? "Sign In to Host" : "Create an Account" }}
        </h2>
        <p class="section-copy">
          {{ mode === "signin"
            ? "Sign in to create a session and track your dining history."
            : "Create a free account to host sessions and see your history." }}
        </p>
      </div>
      <span class="status-pill">Host Flow</span>
    </div>

    <div v-if="signedUp" class="mt-4 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
      Check your email to confirm your account, then sign in.
    </div>

    <form v-else class="mt-4 space-y-4" @submit.prevent="submit">
      <Transition name="error-banner">
        <div
          v-if="error"
          class="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          <svg class="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          {{ error }}
        </div>
      </Transition>

      <div>
        <label class="field-label" for="auth-email">Email <span class="text-orange-600">*</span></label>
        <input
          id="auth-email"
          v-model="email"
          class="app-input"
          type="email"
          placeholder="you@example.com"
          autocomplete="email"
          required
        />
      </div>

      <div>
        <label class="field-label" for="auth-password">Password <span class="text-orange-600">*</span></label>
        <input
          id="auth-password"
          v-model="password"
          class="app-input"
          type="password"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />
      </div>

      <div v-if="mode === 'signup'">
        <label class="field-label" for="auth-display-name">Display Name <span class="text-orange-600">*</span></label>
        <input
          id="auth-display-name"
          v-model="displayName"
          class="app-input"
          type="text"
          placeholder="How the table will know you"
          autocomplete="nickname"
          required
        />
      </div>

      <button :disabled="loading" class="app-button w-full" type="submit">
        {{ loading ? "Please wait..." : mode === "signin" ? "Sign In" : "Create Account" }}
      </button>

      <p class="text-center text-xs text-stone-400">
        {{ mode === "signin" ? "Don't have an account?" : "Already have an account?" }}
        <button
          type="button"
          class="ml-1 font-medium text-orange-600 hover:text-orange-700"
          @click="mode = mode === 'signin' ? 'signup' : 'signin'; error = ''; signedUp = false; displayName = ''"
        >
          {{ mode === "signin" ? "Sign up" : "Sign in" }}
        </button>
      </p>
    </form>
  </section>
</template>

<style scoped>
.error-banner-enter-active,
.error-banner-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.error-banner-enter-from,
.error-banner-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
