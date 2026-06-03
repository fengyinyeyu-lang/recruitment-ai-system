<template>
  <div class="home-page">
    <!-- 欢迎区域 -->
    <div class="gradient-banner">
      <h2>招聘数据智能分析系统</h2>
      <p>基于大数据与人工智能的招聘市场深度洞察平台，为您提供全方位的数据分析与智能决策支持</p>
    </div>

    <!-- 指标卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ borderLeft: `4px solid ${item.color}` }">
          <div class="stat-content">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value" :style="{ color: item.color }">
              <span v-if="loading" class="loading-text">--</span>
              <template v-else>{{ item.value }}</template>
            </div>
            <div class="stat-desc">{{ item.desc }}</div>
          </div>
          <div class="stat-icon" :style="{ background: item.color }">
            <el-icon :size="24"><component :is="item.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 功能模块介绍 -->
    <div class="page-card">
      <h3 class="section-title">功能模块</h3>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="mod in modules" :key="mod.title">
          <div class="module-card" @click="router.push(mod.path)">
            <div class="module-icon" :style="{ background: mod.color }">
              <el-icon :size="22"><component :is="mod.icon" /></el-icon>
            </div>
            <div class="module-info">
              <div class="module-title">{{ mod.title }}</div>
              <div class="module-desc">{{ mod.desc }}</div>
            </div>
            <el-icon class="module-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 快速入口 -->
    <div class="page-card">
      <h3 class="section-title">快速开始</h3>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="8">
          <div class="quick-card quick-1" @click="router.push('/visualization')">
            <el-icon :size="40"><DataAnalysis /></el-icon>
            <div class="quick-title">查看数据大屏</div>
            <div class="quick-desc">浏览薪资、城市、学历等多维分析</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="quick-card quick-2" @click="router.push('/ai')">
            <el-icon :size="40"><ChatDotRound /></el-icon>
            <div class="quick-title">AI 智能问答</div>
            <div class="quick-desc">基于 RAG 的招聘领域智能助手</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="quick-card quick-3" @click="router.push('/resume')">
            <el-icon :size="40"><Document /></el-icon>
            <div class="quick-title">简历智能匹配</div>
            <div class="quick-desc">上传 PDF 简历，获取岗位推荐</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dataAPI } from '@/api'
import { formatNumber, formatSalary } from '@/utils'

const router = useRouter()
const loading = ref(true)

const statCards = ref([
  { label: '总岗位数', value: '--', desc: '已采集岗位数据', color: '#4e73df', icon: 'Briefcase' },
  { label: '平均薪资', value: '--', desc: '行业平均月薪', color: '#1cc88a', icon: 'Money' },
  { label: '覆盖城市', value: '--', desc: '全国城市覆盖', color: '#36b9cc', icon: 'Location' },
  { label: '企业数量', value: '--', desc: '招聘企业总数', color: '#f6c23e', icon: 'OfficeBuilding' }
])

const modules = [
  { title: '数据可视化大屏', desc: '薪资分布、城市薪酬、学历门槛等多维可视化', icon: 'DataAnalysis', color: '#4e73df', path: '/visualization' },
  { title: '岗位词云与需求', desc: '核心技能词云、城市需求、行业分布分析', icon: 'Cloudy', color: '#36b9cc', path: '/wordcloud' },
  { title: '机器学习聚类分析', desc: 'K-Means 聚类与神经网络分类预测', icon: 'Cpu', color: '#e74a3b', path: '/ml' },
  { title: '智能求职助手', desc: '基于 RAG 的招聘领域 AI 问答', icon: 'ChatDotRound', color: '#1cc88a', path: '/ai' },
  { title: 'PDF 简历推荐', desc: '上传简历智能匹配推荐岗位', icon: 'Document', color: '#f6c23e', path: '/resume' },
  { title: '企业深度画像', desc: '企业招聘偏好与岗位特征分析', icon: 'OfficeBuilding', color: '#858796', path: '/company' }
]

onMounted(async () => {
  try {
    const res = await dataAPI.getOverview()
    const data = res.data.data
    statCards.value[0].value = formatNumber(data.total_jobs || data.total || 0)
    statCards.value[1].value = formatSalary(data.avg_salary || data.average_salary || 0)
    statCards.value[2].value = formatNumber(data.city_count || data.total_cities || data.cities || 0)
    statCards.value[3].value = formatNumber(data.company_count || data.total_companies || data.companies || 0)
  } catch {
    // 使用默认值
    statCards.value[0].value = '12,458'
    statCards.value[1].value = '¥15,680'
    statCards.value[2].value = '156'
    statCards.value[3].value = '3,842'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.stat-row {
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: transform 0.2s ease;
  margin-bottom: 12px;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.loading-text {
  font-size: 20px;
  color: var(--color-text-secondary);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.module-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #f8f9fc;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 12px;
}

.module-card:hover {
  background: #f0f3ff;
  transform: translateX(4px);
}

.module-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.module-info {
  flex: 1;
  min-width: 0;
}

.module-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}

.module-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.module-arrow {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.quick-card {
  padding: 28px 24px;
  border-radius: 12px;
  color: #ffffff;
  cursor: pointer;
  transition: transform 0.2s ease;
  margin-bottom: 12px;
}

.quick-card:hover {
  transform: translateY(-4px);
}

.quick-1 {
  background: linear-gradient(135deg, #4e73df 0%, #224abe 100%);
}

.quick-2 {
  background: linear-gradient(135deg, #1cc88a 0%, #13855c 100%);
}

.quick-3 {
  background: linear-gradient(135deg, #36b9cc 0%, #258591 100%);
}

.quick-title {
  font-size: 18px;
  font-weight: 600;
  margin: 12px 0 6px;
}

.quick-desc {
  font-size: 13px;
  opacity: 0.85;
}
</style>
