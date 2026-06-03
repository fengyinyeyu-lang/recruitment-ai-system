<template>
  <div class="company-page">
    <div class="gradient-banner" style="background: linear-gradient(135deg, #858796 0%, #5a5c69 100%);">
      <h2>企业深度画像</h2>
      <p>深入了解目标企业的招聘偏好、岗位特征与薪酬体系</p>
    </div>

    <!-- 企业选择 -->
    <div class="page-card control-bar">
      <div class="control-item">
        <span class="control-label">选择企业：</span>
        <el-select
          v-model="selectedCompany"
          filterable
          remote
          reserve-keyword
          placeholder="输入企业名称搜索"
          :remote-method="searchCompanies"
          :loading="searchLoading"
          style="width: 360px;"
          @change="loadProfile"
        >
          <el-option
            v-for="item in companyList"
            :key="item.name"
            :label="item.short_name || item.name"
            :value="item.name"
          />
        </el-select>
      </div>
    </div>

    <template v-if="profile">
      <!-- 概览指标 -->
      <el-row :gutter="16" class="stat-row">
        <el-col :xs="12" :sm="6" v-for="item in overviewCards" :key="item.label">
          <div class="stat-card" :style="{ borderTop: `3px solid ${item.color}` }">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 详细分析 Tab -->
      <el-tabs v-model="activeTab" type="border-card" class="profile-tabs">
        <el-tab-pane label="岗位类别" name="position">
          <v-chart :option="positionOption" autoresize style="height: 400px;" />
        </el-tab-pane>
        <el-tab-pane label="城市分布" name="city">
          <v-chart :option="cityOption" autoresize style="height: 400px;" />
        </el-tab-pane>
        <el-tab-pane label="学历要求" name="education">
          <v-chart :option="educationOption" autoresize style="height: 400px;" />
        </el-tab-pane>
        <el-tab-pane label="薪资分布" name="salary">
          <v-chart :option="salaryOption" autoresize style="height: 400px;" />
        </el-tab-pane>
        <el-tab-pane label="综合信息" name="overview">
          <v-chart :option="radarOption" autoresize style="height: 400px;" />
        </el-tab-pane>
      </el-tabs>

      <!-- 岗位列表 -->
      <div class="page-card" v-if="profile.jobs?.length">
        <h3 class="section-title">在招岗位</h3>
        <el-table :data="profile.jobs" stripe style="width: 100%">
          <el-table-column prop="positionName" label="岗位名称" min-width="150" />
          <el-table-column prop="city" label="城市" width="100" />
          <el-table-column prop="salary" label="薪资" width="140" />
          <el-table-column prop="education" label="学历" width="100" />
          <el-table-column prop="workYear" label="经验" width="120" />
        </el-table>
      </div>
    </template>

    <div v-else-if="!searchLoading" class="page-card empty-state">
      <el-empty description="请选择一个企业查看深度画像" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart, RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { companyAPI } from '@/api'
import { getChartColors, formatNumber } from '@/utils'

use([CanvasRenderer, BarChart, PieChart, RadarChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent])

const colors = getChartColors()

const selectedCompany = ref('')
const searchLoading = ref(false)
const companyList = ref([])
const profile = ref(null)
const activeTab = ref('position')

const overviewCards = computed(() => {
  if (!profile.value) return []
  const p = profile.value
  const topEdu = p.education ? Object.entries(p.education).sort((a, b) => b[1] - a[1])[0]?.[0] : '--'
  return [
    { label: '在招岗位', value: formatNumber(p.job_count || 0), color: '#4e73df' },
    { label: '覆盖城市', value: formatNumber(p.city_count || 0), color: '#1cc88a' },
    { label: '平均薪资', value: p.avg_salary ? `${p.avg_salary}K` : '--', color: '#36b9cc' },
    { label: '岗位类别', value: formatNumber(p.keyword_count || 0), color: '#f6c23e' }
  ]
})

const positionOption = computed(() => {
  const d = profile.value?.keywords
  if (!d || !Object.keys(d).length) return {}
  const labels = Object.keys(d)
  const values = Object.values(d)
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: '5%', top: 'center' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['40%', '50%'],
      data: labels.map((label, i) => ({
        name: label,
        value: values[i],
        itemStyle: { color: colors[i % colors.length] }
      })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: '{b}\n{d}%' }
    }]
  }
})

const cityOption = computed(() => {
  const d = profile.value?.cities
  if (!d || !Object.keys(d).length) return {}
  const cityNames = Object.keys(d)
  const counts = Object.values(d)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: [...cityNames].reverse() },
    series: [{
      type: 'bar',
      data: [...counts].reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: (params) => colors[params.dataIndex % colors.length]
      },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  }
})

const educationOption = computed(() => {
  const d = profile.value?.education
  if (!d || !Object.keys(d).length) return {}
  const labels = Object.keys(d)
  const values = Object.values(d)
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: '5%', top: 'center' },
    series: [{
      type: 'pie',
      radius: '60%',
      center: ['40%', '50%'],
      data: labels.map((label, i) => ({
        name: label,
        value: values[i],
        itemStyle: { color: colors[i % colors.length] }
      })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }
    }]
  }
})

const salaryOption = computed(() => {
  const d = profile.value?.salary_distribution
  if (!d || !Object.keys(d).length) return {}
  const ranges = Object.keys(d)
  const counts = Object.values(d)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ranges, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '岗位数量' },
    series: [{
      type: 'bar',
      data: counts,
      itemStyle: { color: colors[0], borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', fontSize: 10 }
    }]
  }
})

const radarOption = computed(() => {
  if (!profile.value) return {}
  const p = profile.value
  // Build radar from available metrics
  const indicators = [
    { name: '岗位数量', max: 100 },
    { name: '城市覆盖', max: 20 },
    { name: '平均薪资', max: 50 },
    { name: '岗位多样性', max: 15 },
    { name: '行业覆盖', max: 15 }
  ]
  const values = [
    Math.min(p.job_count || 0, 100),
    Math.min(p.city_count || 0, 20),
    Math.min(p.avg_salary || 0, 50),
    Math.min(p.keyword_count || 0, 15),
    Math.min(Object.keys(p.industries || {}).length, 15)
  ]
  return {
    tooltip: {},
    radar: { indicator: indicators, shape: 'circle' },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: selectedCompany.value,
        areaStyle: { color: 'rgba(78, 115, 223, 0.2)' },
        lineStyle: { color: '#4e73df' },
        itemStyle: { color: '#4e73df' }
      }]
    }]
  }
})

async function searchCompanies(query) {
  searchLoading.value = true
  try {
    const res = await companyAPI.getList()
    const allCompanies = res.data.data || []
    // Filter locally by query
    if (query) {
      companyList.value = allCompanies.filter(c =>
        c.name.includes(query) || c.short_name?.includes(query)
      )
    } else {
      companyList.value = allCompanies
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    searchLoading.value = false
  }
}

async function loadProfile(name) {
  if (!name) return
  try {
    const res = await companyAPI.getProfile(name)
    profile.value = res.data.data
  } catch {
    // 错误已在拦截器中处理
  }
}
</script>

<style scoped>
.company-page {
  max-width: 1200px;
  margin: 0 auto;
}

.control-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  margin-bottom: 12px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
}

.profile-tabs {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
  overflow: hidden;
}

.profile-tabs :deep(.el-tabs__header) {
  background: #f8f9fc;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.empty-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
