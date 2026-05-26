<template>
  <router-view v-if="isAuthPage" />
  <MainLayout v-else>
    <template #sidebar>
      <Sidebar />
    </template>
    <template #header>
      <Header />
    </template>
    <template #content>
      <router-view />
    </template>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import MainLayout from "./layouts/MainLayout.vue"
import Sidebar from "./components/Sidebar.vue"
import Header from "./components/Header.vue"

const route = useRoute()
const userStore = useUserStore()

const isAuthPage = computed(() => {
  const authPaths = ["/login", "/register", "/forgot-password"]
  return authPaths.includes(route.path)
})

// 初始化主题
const initTheme = () => {
  try {
    const savedAppearance = localStorage.getItem("appearance")
    let theme = "light"
    
    if (savedAppearance) {
      const appearance = JSON.parse(savedAppearance)
      theme = appearance.theme || "light"
    }
    
    applyTheme(theme)
  } catch (error) {
    console.error("初始化主题失败:", error)
  }
}

const applyTheme = (theme) => {
  const html = document.documentElement
  html.classList.remove("light", "dark")
  
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    html.classList.add(prefersDark ? "dark" : "light")
  } else {
    html.classList.add(theme)
  }
}

onMounted(() => {
  initTheme()
  userStore.initUser()
  if (userStore.isLoggedIn) {
    userStore.fetchUserInfo()
  }
})
</script>

<style scoped></style>
