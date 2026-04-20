<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { useSessionStore } from "../stores/session";
import type { SessionResponse } from "../types";

const store = useSessionStore();
const startLoading = ref(false);
let timer: ReturnType<typeof setInterval> | null = null;
let socket: WebSocket | null = null;
const socketConnected = ref(false);

const participantCount = computed(() => store.session?.participants.length ?? 0);

function buildWsUrl(roomCode: string): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
  const wsBase = apiBase.replace(/^http/, "ws");
  return `${wsBase}/ws/sessions/${roomCode}`;
}

function connectSocket(roomCode: string) {
  socket = new WebSocket(buildWsUrl(roomCode));

  socket.onopen = () => {
    socketConnected.value = true;
  };

  socket.onclose = () => {
    socketConnected.value = false;
  };

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data) as {
        event?: string;
        session?: SessionResponse;
      };
      if (message.event === "session_started" && message.session) {
        store.setSession(message.session);
      }
    } catch {
      // Ignore malformed messages and rely on polling fallback.
    }
  };
}

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
  if (store.session) {
    connectSocket(store.session.room_code);
  }
  timer = setInterval(() => {
    store.refresh().catch(() => {
      // Store error message is enough for this MVP view.
    });
  }, 5000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
  socket?.close();
});
</script>

<template>
  <section v-if="store.session" class="glass-card">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="section-title text-stone-900">Waiting Room</h2>
        <p class="section-copy">
          Room: <span class="font-semibold text-stone-900">{{ store.session.room_code }}</span>
        </p>
      </div>
      <span class="status-pill">
        Status: {{ store.session.status }}
      </span>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-[minmax(0,1fr)_13rem]">
      <div class="rounded-[1.5rem] border border-orange-950/10 bg-white/65 p-4">
        <p class="text-sm font-semibold text-stone-800">Participants ({{ participantCount }})</p>
        <ul class="mt-3 space-y-2">
          <li
            v-for="name in store.session.participants"
            :key="name"
            class="flex items-center justify-between rounded-2xl bg-orange-50/80 px-3 py-3 text-sm text-stone-800"
          >
            <span>{{ name }}</span>
            <span v-if="name === store.session.host_name" class="metric-chip">Host</span>
          </li>
        </ul>
      </div>
      <div class="rounded-[1.5rem] border border-orange-950/10 bg-stone-900 p-5 text-stone-50">
        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-orange-200">Session Pulse</p>
        <p class="mt-3 text-3xl font-semibold">{{ participantCount }}</p>
        <p class="mt-1 text-sm text-stone-300">people ready to vote</p>
        <p class="mt-5 text-sm text-stone-300">
          {{ socketConnected ? "Live updates connected." : "Polling for updates every 5 seconds." }}
        </p>
      </div>
    </div>

    <div class="mt-6 flex flex-col gap-3 rounded-[1.5rem] border border-orange-950/10 bg-white/60 p-4 sm:flex-row sm:items-center sm:justify-between">
      <p class="text-sm leading-6 text-stone-600">Share the room code and wait until everyone is settled before you open voting.</p>
      <button
        v-if="store.isHost && store.session.status === 'waiting'"
        :disabled="startLoading"
        class="app-button"
        @click="startSession"
      >
        {{ startLoading ? "Starting..." : "Start Session" }}
      </button>
    </div>

    <p
      v-if="store.session.status === 'active'"
      class="soft-alert mt-4 bg-emerald-50 text-emerald-700"
    >
      Session is live. The swipe stack is ready.
    </p>
  </section>
</template>
