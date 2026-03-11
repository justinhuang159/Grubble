<script setup lang="ts">
import { computed, ref } from "vue";

import { useSessionStore } from "../stores/session";

const emit = defineEmits<{
  joined: [];
}>();

const store = useSessionStore();
const roomCode = ref("");
const userName = ref("");
const submitted = ref(false);

const roomCodeError = computed(() => {
  if (!submitted.value) {
    return "";
  }
  return roomCode.value.trim() ? "" : "Room code is required.";
});

const userNameError = computed(() => {
  if (!submitted.value) {
    return "";
  }
  return userName.value.trim() ? "" : "Your name is required.";
});

async function submit() {
  submitted.value = true;
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
        :class="[
          'w-full rounded-md border px-3 py-2 uppercase outline-none focus:border-slate-500',
          roomCodeError ? 'border-red-400 focus:border-red-500' : 'border-slate-300',
        ]"
        placeholder="Room code"
      />
      <p v-if="roomCodeError" class="text-xs text-red-600">{{ roomCodeError }}</p>
      <input
        v-model="userName"
        :class="[
          'w-full rounded-md border px-3 py-2 outline-none focus:border-slate-500',
          userNameError ? 'border-red-400 focus:border-red-500' : 'border-slate-300',
        ]"
        placeholder="Your name"
      />
      <p v-if="userNameError" class="text-xs text-red-600">{{ userNameError }}</p>
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
