import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import Dashboard from "./pages/Dashboard.vue";
import News from "./pages/News.vue";
import Settings from "./pages/Settings.vue";
import Wallets from "./pages/Wallets.vue";
import WalletDetail from "./pages/WalletDetail.vue";
import FundDetail from "./pages/FundDetail.vue";
import { useFundStore } from "./stores/fund";
import { isApiKeySet } from "./lib/api";
import { bootstrapLocale } from "./i18n";
import "./assets/main.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: Dashboard },
    {
      path: "/wallets",
      name: "wallets",
      component: Wallets,
      meta: { requiresAuth: true },
    },
    {
      path: "/wallets/:uuid",
      name: "wallet-detail",
      component: WalletDetail,
      meta: { requiresAuth: true },
    },
    {
      path: "/wallets/:walletUuid/funds/:fundUuid",
      name: "fund-detail",
      component: FundDetail,
      meta: { requiresAuth: true },
    },
    {
      path: "/news",
      name: "news",
      component: News,
      meta: { requiresAuth: true },
    },
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

// Resolve UI locale: localStorage first, then settings.json via backend.
bootstrapLocale();

app.mount("#app");
