import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import Dashboard from "./pages/Dashboard.vue";
import Settings from "./pages/Settings.vue";
import { useFundStore } from "./stores/fund";
import { isApiKeySet } from "./lib/api";
import "./assets/main.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: Dashboard },
    {
      path: "/settings",
      name: "settings",
      component: Settings,
      meta: { requiresAuth: true },
    },
  ],
});

// Navigation guard — redirect to dashboard (which shows login) if not authenticated
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isApiKeySet()) {
    return { name: "dashboard" };
  }
});

const pinia = createPinia();
const app = createApp(App);
app.use(pinia);
app.use(router);

// Initialize store — load fund data if API key exists
const store = useFundStore();
store.init();

app.mount("#app");
