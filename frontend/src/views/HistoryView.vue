<script setup lang="ts">
import { onMounted, ref } from "vue";
import { deleteSession, getMySessions } from "../lib/api";
import type { SessionSummary } from "../types";

const hosted = ref<SessionSummary[]>([]);
const joined = ref<SessionSummary[]>([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    const data = await getMySessions();
    hosted.value = data.hosted;
    joined.value = data.joined;
  } catch {
    error.value = "Could not load session history.";
  } finally {
    loading.value = false;
  }
});

async function remove(roomCode: string) {
  try {
    await deleteSession(roomCode);
    hosted.value = hosted.value.filter((s) => s.room_code !== roomCode);
  } catch {
    error.value = "Could not delete session.";
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

const statusLabel: Record<string, string> = {
  waiting: "Waiting",
  active: "Active",
  ended: "Ended",
  paused: "Paused",
};
</script>

<template>
  <section class="glass-card mt-5">
    <h2 class="section-title text-stone-900">My Sessions</h2>

    <div v-if="loading" class="mt-4 text-sm text-stone-400">Loading...</div>

    <div v-else-if="error" class="mt-4 text-sm text-red-600">{{ error }}</div>

    <div v-else-if="hosted.length === 0 && joined.length === 0" class="mt-4 text-sm text-stone-400">
      No sessions yet. Create one above to get started.
    </div>

    <div v-else class="mt-4 space-y-6">
      <div v-if="hosted.length > 0">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">Hosted</p>
        <ul class="space-y-2">
          <li
            v-for="s in hosted"
            :key="s.room_code"
            class="flex items-center justify-between gap-3 rounded-xl border border-stone-100 bg-white px-4 py-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-stone-800">{{ s.location_text ?? "No location" }}</p>
              <p class="text-xs text-stone-400">
                {{ formatDate(s.created_at) }} · {{ s.participant_count }} participant{{ s.participant_count !== 1 ? "s" : "" }}
                · <span :class="s.status === 'active' ? 'text-green-600' : 'text-stone-400'">{{ statusLabel[s.status] ?? s.status }}</span>
              </p>
            </div>
            <button
              class="shrink-0 rounded-lg border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-100"
              @click="remove(s.room_code)"
            >
              Delete
            </button>
          </li>
        </ul>
      </div>

      <div v-if="joined.length > 0">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">Joined</p>
        <ul class="space-y-2">
          <li
            v-for="s in joined"
            :key="s.room_code"
            class="flex items-center justify-between gap-3 rounded-xl border border-stone-100 bg-white px-4 py-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-stone-800">{{ s.location_text ?? "No location" }}</p>
              <p class="text-xs text-stone-400">
                Hosted by {{ s.host_name }} · {{ formatDate(s.created_at) }}
                · <span :class="s.status === 'active' ? 'text-green-600' : 'text-stone-400'">{{ statusLabel[s.status] ?? s.status }}</span>
              </p>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
