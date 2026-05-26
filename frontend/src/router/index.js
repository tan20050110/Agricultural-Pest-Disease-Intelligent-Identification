import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "登录",
    component: () => import("../views/LoginPage.vue"),
  },
  {
    path: "/register",
    name: "注册",
    component: () => import("../views/RegisterPage.vue"),
  },
  {
    path: "/forgot-password",
    name: "忘记密码",
    component: () => import("../views/ForgotPasswordPage.vue"),
  },
  {
    path: "/detection",
    name: "虫害检测",
    component: () => import("../views/DetectionPage.vue"),
  },
  {
    path: "/disease",
    name: "病害识别",
    component: () => import("../views/DiseasePage.vue"),
  },
  {
    path: "/history",
    name: "历史记录",
    component: () => import("../views/HistoryPage.vue"),
  },
  {
    path: "/qa",
    name: "AI问答",
    component: () => import("../views/QAPage.vue"),
  },
  {
    path: "/targets",
    name: "目标库",
    component: () => import("../views/TargetsPage.vue"),
  },
  {
    path: "/profile",
    name: "个人中心",
    component: () => import("../views/ProfilePage.vue"),
  },
  {
    path: "/camera",
    name: "摄像头检测",
    component: () => import("../views/CameraPage.vue"),
  },
  {
    path: "/settings",
    name: "系统设置",
    component: () => import("../views/Settings.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const authPaths = ["/login", "/register", "/forgot-password"];
  
  if (authPaths.includes(to.path)) {
    next();
  } else if (!token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
