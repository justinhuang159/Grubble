<script setup lang="ts">
import { ref } from "vue";

import { useSessionStore } from "../stores/session";

const emit = defineEmits<{
  joined: [];
}>();

const store = useSessionStore();
const roomCode = ref("");
const userName = ref("");

async function submit() {
  if (!roomCode.value.trim() || !userName.value.trim()) {
    return;
  }
  await store.join(roomCode.value, userName.value);
  emit("joined");
}
</script>

<template>
  <section class="glass-card">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">Join a Table</h2>
        <p class="section-copy">Drop in with a room code, set your name, and you’re ready to start voting.</p>
      </div>
      <span class="status-pill">Guest Flow</span>
    </div>
    <form class="mt-4 space-y-4" @submit.prevent="submit">
      <div>
        <label class="field-label" for="room-code">Room Code</label>
        <input
          id="room-code"
          v-model="roomCode"
          class="app-input uppercase"
          placeholder="Enter the six-character code"
        />
      </div>
      <div>
        <label class="field-label" for="user-name">Display Name</label>
        <input
          id="user-name"
          v-model="userName"
          class="app-input"
          placeholder="How the table will know you"
        />
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
