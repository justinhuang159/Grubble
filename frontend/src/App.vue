<script setup lang="ts">
import { computed, ref } from "vue";

import AccountSettingsModal from "./views/AccountSettingsModal.vue";
import AuthView from "./views/AuthView.vue";
import CreateSessionView from "./views/CreateSessionView.vue";
import HistoryView from "./views/HistoryView.vue";
import JoinSessionView from "./views/JoinSessionView.vue";
import ResultsSessionView from "./views/ResultsSessionView.vue";
import SwipeSessionView from "./views/SwipeSessionView.vue";
import WaitingRoomView from "./views/WaitingRoomView.vue";
import { useAuthStore } from "./stores/auth";
import { useSessionStore } from "./stores/session";

const store = useSessionStore();
const auth = useAuthStore();
const mode = ref<"create" | "join">("create");
const showSettings = ref(false);

const inSession = computed(() => Boolean(store.session));
const inActiveSession = computed(() => store.session?.status === "active");
</script>

<template>
  <main class="app-shell min-h-screen">
    <div class="hero-panel">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="hero-kicker">Group Dinner, Simplified</p>
          <h1 class="hero-title text-stone-900">Grubble</h1>
        </div>
        <div v-if="auth.isLoggedIn" class="flex shrink-0 items-center gap-2 pt-1">
          <span class="max-w-[140px] truncate text-xs text-stone-400">{{ auth.displayName || auth.user?.email }}</span>
          <button
            class="rounded-full border border-stone-200 bg-white p-1.5 text-stone-400 transition-colors hover:border-stone-300 hover:text-stone-600"
            aria-label="Account settings"
            @click="showSettings = true"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            class="rounded-full border border-stone-200 bg-white px-3 py-1 text-xs font-medium text-stone-500 transition-colors hover:border-stone-300 hover:text-stone-700"
            @click="auth.signOut()"
          >
            Sign out
          </button>
        </div>

        <AccountSettingsModal v-if="showSettings" @close="showSettings = false" />
      </div>

      <p class="hero-subtitle">
        Gather the group, narrow the neighborhood, and let the best spot rise to the top without the usual back-and-forth.
      </p>

      <p v-if="store.error" class="soft-alert mt-6 bg-red-50 text-red-700">
        {{ store.error }}
      </p>

      <ResultsSessionView v-if="inActiveSession && store.showResults" class="mt-6" />
      <SwipeSessionView v-else-if="inActiveSession" class="mt-6" />
      <WaitingRoomView v-else-if="inSession" class="mt-6" />

      <section v-else class="mt-8 space-y-5">
        <div class="segmented-shell">
          <button
            class="segmented-button"
            :class="mode === 'create' ? 'segmented-button-active' : ''"
            @click="mode = 'create'"
          >
            Create
          </button>
          <button
            class="segmented-button"
            :class="mode === 'join' ? 'segmented-button-active' : ''"
            @click="mode = 'join'"
          >
            Join
          </button>
        </div>

        <template v-if="mode === 'create'">
          <AuthView v-if="!auth.isLoggedIn" />
          <CreateSessionView v-else @created="() => {}" />
        </template>
        <JoinSessionView v-else @joined="() => {}" />

        <HistoryView v-if="auth.isLoggedIn" />
      </section>
    </div>
  </main>
</template>
