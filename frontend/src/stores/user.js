import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户信息状态
  const userInfo = ref({
    id: '',
    username: '',
    nickname: '',
    email: '',
    role: '',
    created_at: ''
  })

  // 是否已登录
  const isLoggedIn = computed(() => !!userInfo.value.id)

  // 显示名称（优先显示昵称，如果没有则显示用户名）
  const displayName = computed(() => userInfo.value.nickname || userInfo.value.username || 'User')

  // 初始化用户信息（从 localStorage 读取）
  function initUser() {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser)
        userInfo.value = { ...userInfo.value, ...parsedUser }
      } catch (error) {
        console.error('解析用户信息失败:', error)
      }
    }
  }

  // 更新用户信息
  function updateUser(updates) {
    userInfo.value = { ...userInfo.value, ...updates }
    // 同时保存到 localStorage
    localStorage.setItem('user', JSON.stringify(userInfo.value))
  }

  // 获取用户信息（优先从 localStorage 读取，无需请求后端）
  async function fetchUserInfo() {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser)
        userInfo.value = { ...userInfo.value, ...parsedUser }
      } catch (error) {
        console.error('解析用户信息失败:', error)
      }
    }
  }

  // 退出登录
  function logout() {
    userInfo.value = {
      id: '',
      username: '',
      nickname: '',
      email: '',
      role: '',
      created_at: ''
    }
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  return {
    userInfo,
    isLoggedIn,
    displayName,
    initUser,
    updateUser,
    fetchUserInfo,
    logout
  }
})
