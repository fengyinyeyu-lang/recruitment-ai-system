import { defineStore } from 'pinia'
import { authAPI } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    isLoggedIn: !!localStorage.getItem('token')
  }),

  actions: {
    async login(credentials) {
      const res = await authAPI.login(credentials)
      this.token = res.data.data.token
      this.username = res.data.data.username || credentials.username
      this.isLoggedIn = true
      localStorage.setItem('token', this.token)
      localStorage.setItem('username', this.username)
      return res
    },

    async register(data) {
      const res = await authAPI.register(data)
      this.token = res.data.data.token
      this.username = res.data.data.username || data.username
      this.isLoggedIn = true
      localStorage.setItem('token', this.token)
      localStorage.setItem('username', this.username)
      return res
    },

    async getMe() {
      try {
        const res = await authAPI.getMe()
        this.username = res.data.data.username
        return res
      } catch {
        this.logout()
      }
    },

    logout() {
      this.token = ''
      this.username = ''
      this.isLoggedIn = false
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    }
  }
})
