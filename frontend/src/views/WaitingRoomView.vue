<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import EditFiltersModal from "./EditFiltersModal.vue";
import { useSessionStore } from "../stores/session";
import type { SessionResponse } from "../types";

const store = useSessionStore();
const startLoading = ref(false);
const showEditFilters = ref(false);
const removingParticipant = ref<string | null>(null);
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

async function kickParticipant(userName: string) {
  if (!store.session) return;
  removingParticipant.value = userName;
  try {
    await store.removeParticipant(store.session.room_code, userName);
  } finally {
    removingParticipant.value = null;
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
      </div>
      <div class="flex items-center gap-3">
        <span class="status-pill">Room: {{ store.session.room_code }}</span>
        <button
          class="app-button"
          @click="store.resetState()"
        >
          Back to Home
        </button>
      </div>
    </div>

    <div class="mt-6 grid gap-4 sm:grid-cols-[minmax(0,1fr)_13rem]">
      <div class="rounded-[1.5rem] border border-orange-950/10 bg-white/65 p-4">
        <div class="flex items-center justify-between">
          <p class="text-sm font-semibold text-stone-800">Participants ({{ participantCount }})</p>
          <span class="status-pill">{{ store.session.status }}</span>
        </div>
        <ul class="mt-3 space-y-2">
          <li
            v-for="name in store.session.participants"
            :key="name"
            class="flex items-center justify-between rounded-2xl bg-orange-50/80 px-3 py-3 text-sm text-stone-800"
          >
            <span>{{ name }}</span>
            <div class="flex items-center gap-2">
              <span v-if="name === store.session.host_name" class="metric-chip">Host</span>
              <button
                v-else-if="store.isHost"
                :disabled="removingParticipant === name"
                class="flex h-5 w-5 items-center justify-center rounded-full text-stone-300 transition-colors hover:bg-red-50 hover:text-red-500 disabled:opacity-40"
                :aria-label="`Remove ${name}`"
                @click="kickParticipant(name)"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
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
      <div v-if="store.isHost && store.session.status === 'waiting'" class="flex gap-2">
        <button
          class="rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 transition-colors hover:border-stone-300 hover:text-stone-800"
          @click="showEditFilters = true"
        >
          Edit Filters
        </button>
        <button
          :disabled="startLoading"
          class="app-button"
          @click="startSession"
        >
          {{ startLoading ? "Starting..." : "Start Session" }}
        </button>
      </div>
    </div>

    <p
      v-if="store.session.status === 'active'"
      class="soft-alert mt-4 bg-emerald-50 text-emerald-700"
    >
      Session is live. The swipe stack is ready.
    </p>

    <EditFiltersModal
      v-if="showEditFilters && store.session"
      :room-code="store.session.room_code"
      :initial="{
        location_text: store.session.location_text,
        cuisine: store.session.cuisine,
        price: store.session.price,
        radius_meters: store.session.radius_meters,
      }"
      @close="showEditFilters = false"
      @saved="store.refresh()"
    />
  </section>
</template>
