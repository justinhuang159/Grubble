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
  <section class="rounded-xl bg-white p-6 shadow">
    <h2 class="text-xl font-semibold text-slate-900">Join Session</h2>
    <p class="mt-1 text-sm text-slate-600">Enter room code and your display name.</p>
    <form class="mt-4 space-y-4" @submit.prevent="submit">
      <input
        v-model="roomCode"
        class="w-full rounded-md border border-slate-300 px-3 py-2 uppercase outline-none focus:border-slate-500"
        placeholder="Room code"
      />
      <input
        v-model="userName"
        class="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
        placeholder="Your name"
      />
      <button
        :disabled="store.loading"
        class="w-full rounded-md bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-60"
        type="submit"
      >
        {{ store.loading ? "Joining..." : "Join Session" }}
      </button>
    </form>
  </section>
</template>
