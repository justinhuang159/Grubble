<script setup lang="ts">
import { ref, watch } from "vue";
import { useAuthStore } from "../stores/auth";

const emit = defineEmits<{ close: [] }>();

const auth = useAuthStore();
const nameInput = ref(auth.displayName);
const loading = ref(false);
const error = ref("");
const saved = ref(false);

watch(() => auth.displayName, (val) => {
  if (!loading.value) nameInput.value = val;
});

async function save() {
  error.value = "";
  saved.value = false;
  loading.value = true;
  try {
    await auth.updateDisplayName(nameInput.value);
    saved.value = true;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Could not save changes.";
  } finally {
    loading.value = false;
  }
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) emit("close");
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      @click="onBackdropClick"
      @keydown="onKeydown"
    >
      <div class="glass-card w-full max-w-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="section-title text-stone-900">Account Settings</h2>
            <p class="section-copy">Update your display name.</p>
          </div>
          <button
            class="mt-0.5 rounded-full p-1 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
            aria-label="Close"
            @click="emit('close')"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="mt-4 space-y-4">
          <div>
            <label class="field-label">Email</label>
            <p class="mt-1 rounded-xl border border-stone-100 bg-stone-50 px-3 py-2 text-sm text-stone-500">
              {{ auth.user?.email }}
            </p>
          </div>

          <div>
            <label class="field-label" for="settings-display-name">Display Name</label>
            <input
              id="settings-display-name"
              v-model="nameInput"
              class="app-input"
              type="text"
              placeholder="How the table will know you"
              autocomplete="nickname"
              @input="saved = false"
            />
          </div>

          <Transition name="error-banner">
            <div
              v-if="error"
              class="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {{ error }}
            </div>
          </Transition>

          <Transition name="error-banner">
            <div
              v-if="saved"
              class="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700"
            >
              Display name updated.
            </div>
          </Transition>

          <div class="flex gap-2">
            <button class="app-button flex-1" :disabled="loading" @click="save">
              {{ loading ? "Saving..." : "Save" }}
            </button>
            <button
              class="flex-1 rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:border-stone-300 hover:text-stone-800"
              @click="emit('close')"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
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
