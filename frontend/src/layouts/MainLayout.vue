<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '260px'" class="sidebar">
      <div class="sidebar-inner">
        <!-- Logo 区域 -->
        <div class="logo-area">
          <div class="logo-icon">
            <el-icon :size="28"><DataAnalysis /></el-icon>
          </div>
          <transition name="fade">
            <div v-show="!appStore.sidebarCollapsed" class="logo-text">
              <span class="logo-title">RECRUIT</span>
              <span class="logo-subtitle">AI</span>
            </div>
          </transition>
        </div>

        <!-- 用户信息 -->
        <transition name="fade">
          <div v-show="!appStore.sidebarCollapsed" class="user-card">
            <el-avatar :size="36" class="user-avatar">
              {{ authStore.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div class="user-info">
              <div class="user-name">{{ authStore.username || '用户' }}</div>
              <div class="user-role">系统管理员</div>
            </div>
          </div>
        </transition>

        <!-- 导航菜单 -->
        <el-menu
          :default-active="currentRoute"
          :collapse="appStore.sidebarCollapsed"
          :collapse-transition="true"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/home">
            <el-icon><HomeFilled /></el-icon>
            <template #title>系统首页</template>
          </el-menu-item>

          <el-menu-item index="/visualization">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>数据可视化大屏</template>
          </el-menu-item>

          <el-menu-item index="/wordcloud">
            <el-icon><Cloudy /></el-icon>
            <template #title>岗位词云与需求</template>
          </el-menu-item>

          <el-menu-item index="/ml">
            <el-icon><Cpu /></el-icon>
            <template #title>机器学习聚类分析</template>
          </el-menu-item>

          <el-menu-item index="/ai">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>智能求职助手</template>
          </el-menu-item>

          <el-menu-item index="/resume">
            <el-icon><Document /></el-icon>
            <template #title>PDF简历推荐</template>
          </el-menu-item>

          <el-divider v-if="!appStore.sidebarCollapsed" class="menu-divider" />

          <div v-if="!appStore.sidebarCollapsed" class="section-label">高级功能</div>

          <el-menu-item index="/company">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>企业深度画像</template>
          </el-menu-item>

          <el-menu-item index="/report">
            <el-icon><Download /></el-icon>
            <template #title>分析报告导出</template>
          </el-menu-item>
        </el-menu>

        <!-- 底部系统状态 -->
        <transition name="fade">
          <div v-show="!appStore.sidebarCollapsed" class="system-status">
            <div class="status-card">
              <div class="status-title">系统状态</div>
              <div class="status-item">
                <span class="status-dot online"></span>
                <span>服务运行中</span>
              </div>
              <div class="status-item">
                <span class="status-dot"></span>
                <span>API 正常</span>
              </div>
            </div>
          </div>
        </transition>

        <!-- 退出登录 -->
        <div class="logout-area">
          <el-button
            type="danger"
            text
            :class="{ 'logout-btn-collapsed': appStore.sidebarCollapsed }"
            @click="handleLogout"
          >
            <el-icon><SwitchButton /></el-icon>
            <span v-if="!appStore.sidebarCollapsed">退出登录</span>
          </el-button>
        </div>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部栏 -->
      <el-header class="top-header" height="56px">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            :size="20"
            @click="appStore.toggleSidebar()"
          >
            <Fold v-if="!appStore.sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="dark" size="small" round>
            <el-icon><CircleCheck /></el-icon> 在线
          </el-tag>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="slide-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '招聘数据智能分析系统')

function handleMenuSelect(index) {
  router.push(index)
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    authStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: #ffffff;
  border-right: 1px solid var(--color-border);
  transition: width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Logo 区域 */
.logo-area {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #4e73df 0%, #224abe 100%);
  gap: 12px;
  min-height: 64px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.logo-title {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
}

.logo-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #1cc88a;
}

/* 用户信息 */
.user-card {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  gap: 12px;
  border-bottom: 1px solid var(--color-border);
}

.user-avatar {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: #ffffff;
  font-weight: 600;
  flex-shrink: 0;
}

.user-info {
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 导航菜单 */
.sidebar-menu {
  padding: 8px;
  flex: 1;
}

.sidebar-menu .el-menu-item {
  margin-bottom: 4px;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
  font-size: 13.5px;
  color: var(--color-text);
  transition: all 0.2s ease;
}

.sidebar-menu .el-menu-item:hover {
  background: #f0f3ff;
  color: var(--color-primary);
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #4e73df 0%, #3a5fc8 100%);
  color: #ffffff;
  font-weight: 500;
}

.menu-divider {
  margin: 8px 12px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  padding: 8px 16px 4px;
}

/* 系统状态 */
.system-status {
  padding: 12px 16px;
}

.status-card {
  background: #f8f9fc;
  border-radius: 8px;
  padding: 12px 16px;
}

.status-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-success);
}

.status-dot.online {
  background: var(--color-success);
  box-shadow: 0 0 6px rgba(28, 200, 138, 0.5);
}

/* 退出登录 */
.logout-area {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border);
}

.logout-area .el-button {
  width: 100%;
  justify-content: flex-start;
  gap: 8px;
}

.logout-btn-collapsed {
  justify-content: center !important;
}

/* 主内容区 */
.main-container {
  background: var(--color-bg);
}

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  box-shadow: var(--shadow-sm);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: var(--color-primary);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  padding: 24px;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
