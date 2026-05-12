import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import "./style.css";
import { useAuthStore } from "./stores/auth";

const app = createApp(App);
app.use(createPinia());

const authStore = useAuthStore();
authStore.init().then(() => app.mount("#app"));
