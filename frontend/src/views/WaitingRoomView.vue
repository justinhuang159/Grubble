<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { useSessionStore } from "../stores/session";

const store = useSessionStore();
const startLoading = ref(false);
let timer: ReturnType<typeof setInterval> | null = null;

const participantCount = computed(() => store.session?.participants.length ?? 0);

async function startSession() {
  startLoading.value = true;
  try {
    await store.start();
  } finally {
    startLoading.value = false;
  }
}

onMounted(async () => {
  await store.refresh();
  timer = setInterval(() => {
    store.refresh().catch(() => {
      // Store error message is enough for this MVP view.
    });
  }, 2500);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<template>
  <section v-if="store.session" class="rounded-xl bg-white p-6 shadow">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">Waiting Room</h2>
        <p class="mt-1 text-sm text-slate-600">
          Room: <span class="font-semibold text-slate-900">{{ store.session.room_code }}</span>
        </p>
      </div>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
        Status: {{ store.session.status }}
      </span>
    </div>

    <div class="mt-4 rounded-md border border-slate-200 p-4">
      <p class="text-sm text-slate-700">Participants ({{ participantCount }})</p>
      <ul class="mt-2 space-y-2">
        <li
          v-for="name in store.session.participants"
          :key="name"
          class="flex items-center justify-between rounded bg-slate-50 px-3 py-2"
        >
          <span>{{ name }}</span>
          <span v-if="name === store.session.host_name" class="text-xs font-semibold text-slate-600">Host</span>
        </li>
      </ul>
    </div>

    <div class="mt-4 flex items-center justify-between gap-4">
      <p class="text-sm text-slate-600">Share room code so others can join.</p>
      <button
        v-if="store.isHost && store.session.status === 'waiting'"
        :disabled="startLoading"
        class="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white disabled:opacity-60"
        @click="startSession"
      >
        {{ startLoading ? "Starting..." : "Start Session" }}
      </button>
    </div>

    <p v-if="store.session.status === 'active'" class="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
      Session is active. Swipe UI is the next step.
    </p>
  </section>
</template>
