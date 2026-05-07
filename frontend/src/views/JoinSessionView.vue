<script setup lang="ts">
import { ref, computed } from "vue";

import { useSessionStore } from "../stores/session";

const emit = defineEmits<{
  joined: [];
}>();

const store = useSessionStore();
const roomCode = ref("");
const userName = ref("");
const submitted = ref(false);

const roomCodeInvalid = computed(() => submitted.value && !roomCode.value.trim());
const userNameInvalid = computed(() => submitted.value && !userName.value.trim());
const hasErrors = computed(() => roomCodeInvalid.value || userNameInvalid.value);

async function submit() {
  submitted.value = true;
  if (hasErrors.value) return;
  await store.join(roomCode.value, userName.value);
  emit("joined");
}
</script>

<template>
  <section class="glass-card">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">Join a Table</h2>
        <p class="section-copy">Drop in with a room code, set your name, and you're ready to start voting.</p>
      </div>
      <span class="status-pill">Guest Flow</span>
    </div>
    <form class="mt-4 space-y-4" @submit.prevent="submit">

      <Transition name="error-banner">
        <div
          v-if="hasErrors"
          class="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          <svg class="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          Please fill in all required fields before continuing.
        </div>
      </Transition>

      <div>
        <label class="field-label" for="room-code">Room Code</label>
        <input
          id="room-code"
          v-model="roomCode"
          class="app-input uppercase"
          :class="roomCodeInvalid ? 'border-red-400 bg-red-50/40 focus:border-red-500 focus:ring-red-200' : ''"
          placeholder="Enter the six-character code"
          @input="submitted = false"
        />
        <Transition name="field-error">
          <p v-if="roomCodeInvalid" class="mt-1.5 text-xs font-medium text-red-600">
            Room code is required.
          </p>
        </Transition>
      </div>

      <div>
        <label class="field-label" for="user-name">Display Name</label>
        <input
          id="user-name"
          v-model="userName"
          class="app-input"
          :class="userNameInvalid ? 'border-red-400 bg-red-50/40 focus:border-red-500 focus:ring-red-200' : ''"
          placeholder="How the table will know you"
          @input="submitted = false"
        />
        <Transition name="field-error">
          <p v-if="userNameInvalid" class="mt-1.5 text-xs font-medium text-red-600">
            Display name is required.
          </p>
        </Transition>
      </div>

      <button
        :disabled="store.loading"
        class="app-button w-full"
        type="submit"
      >
        {{ store.loading ? "Joining..." : "Join Session" }}
      </button>
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

.field-error-enter-active,
.field-error-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.field-error-enter-from,
.field-error-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}
</style>
