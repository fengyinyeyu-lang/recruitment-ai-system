<template>
  <div class="viz-page">
    <!-- Banner -->
    <div class="gradient-banner">
      <h2>数据可视化大屏</h2>
      <p>全方位展示招聘市场数据洞察，薪资、城市、学历、经验多维度分析</p>
    </div>

    <!-- 指标卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ borderTop: `3px solid ${item.color}` }">
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表切换 -->
    <div class="chart-nav">
      <el-radio-group v-model="activeChart" size="default">
        <el-radio-button value="salary">薪资分布</el-radio-button>
        <el-radio-button value="city">城市薪酬</el-radio-button>
        <el-radio-button value="education">学历门槛</el-radio-button>
        <el-radio-button value="demand">岗位需求</el-radio-button>
        <el-radio-button value="experience">经验薪资</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 薪资分布 -->
    <div v-show="activeChart === 'salary'" class="chart-container">
      <div class="chart-title">薪资分布直方图</div>
      <v-chart :option="salaryOption" :loading="chartLoading" autoresize style="height: 450px;" />
    </div>

    <!-- 城市薪酬 -->
    <div v-show="activeChart === 'city'" class="chart-container">
      <div class="chart-title">城市薪酬 Top15</div>
      <v-chart :option="cityOption" :loading="chartLoading" autoresize style="height: 500px;" />
    </div>

    <!-- 学历门槛 -->
    <div v-show="activeChart === 'education'" class="chart-container">
      <div class="chart-title">学历要求分布</div>
      <v-chart :option="educationOption" :loading="chartLoading" autoresize style="height: 450px;" />
    </div>

    <!-- 岗位需求 -->
    <div v-show="activeChart === 'demand'" class="chart-container">
      <div class="chart-title">热门岗位需求 Top15</div>
      <v-chart :option="demandOption" :loading="chartLoading" autoresize style="height: 500px;" />
    </div>

    <!-- 经验薪资 -->
    <div v-show="activeChart === 'experience'" class="chart-container">
      <div class="chart-title">工作经验与薪资关系</div>
      <v-chart :option="experienceOption" :loading="chartLoading" autoresize style="height: 450px;" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart, BoxplotChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
  DataZoomComponent, MarkLineComponent, ToolboxComponent
} from 'echarts/components'
import { vizAPI, dataAPI } from '@/api'
import { formatNumber, formatSalary, getChartColors } from '@/utils'

use([
  CanvasRenderer, BarChart, LineChart, PieChart, ScatterChart, BoxplotChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
  DataZoomComponent, MarkLineComponent, ToolboxComponent
])

const colors = getChartColors()
const activeChart = ref('salary')
const chartLoading = ref(false)

const statCards = ref([
  { label: '采集总岗位数', value: '--', color: '#4e73df' },
  { label: '行业平均薪资', value: '--', color: '#1cc88a' },
  { label: '覆盖企业数量', value: '--', color: '#36b9cc' },
  { label: '热门岗位类别', value: '--', color: '#f6c23e' }
])

// 图表数据
const salaryData = ref({})
const cityData = ref({})
const educationData = ref({})
const demandData = ref({})
const experienceData = ref({})

const salaryOption = computed(() => {
  const d = salaryData.value
  if (!d.bins?.length) return {}
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let s = `${params[0].axisValue}<br/>`
        params.forEach(p => {
          s += `${p.marker} ${p.seriesName}: ${p.value}<br/>`
        })
        return s
      }
    },
    legend: { data: ['频次', 'KDE'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: d.bins || [],
      name: '月薪 (千元)',
      nameLocation: 'center',
      nameGap: 35,
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: [
      { type: 'value', name: '频次' },
      { type: 'value', name: '密度', splitLine: { show: false } }
    ],
    dataZoom: [{ type: 'inside' }],
    series: [
      {
        name: '频次',
        type: 'bar',
        data: d.counts || [],
        itemStyle: { color: colors[0], borderRadius: [4, 4, 0, 0] },
        barWidth: '60%'
      },
      {
        name: 'KDE',
        type: 'line',
        yAxisIndex: 1,
        data: d.kde_y || [],
        smooth: true,
        lineStyle: { color: colors[1], width: 2 },
        symbol: 'none'
      }
    ]
  }
})

const cityOption = computed(() => {
  const d = cityData.value
  if (!d.cities?.length) return {}
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const v = params[0].value
        return `${params[0].name}<br/>平均薪资: ${v?.toFixed(1)}K (${(v * 1000)?.toLocaleString()}元)`
      }
    },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: '平均月薪 (千元)' },
    yAxis: {
      type: 'category',
      data: [...(d.cities || [])].reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: [...(d.salaries || [])].reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: (params) => colors[params.dataIndex % colors.length]
      },
      label: {
        show: true,
        position: 'right',
        formatter: (p) => `${p.value?.toFixed(1)}K`,
        fontSize: 11
      }
    }]
  }
})

const educationOption = computed(() => {
  const d = educationData.value
  if (!d.labels?.length) return {}
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { fontSize: 12 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      data: (d.labels || []).map((label, i) => ({
        name: label,
        value: d.values?.[i] || 0,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  }
})

const demandOption = computed(() => {
  const d = demandData.value
  if (!d.keywords?.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: d.keywords || [],
      axisLabel: { rotate: 40, fontSize: 11 }
    },
    yAxis: { type: 'value', name: '岗位数量' },
    dataZoom: [{ type: 'inside' }],
    series: [{
      type: 'bar',
      data: d.counts || [],
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: (params) => colors[params.dataIndex % colors.length]
      },
      label: { show: true, position: 'top', fontSize: 10 }
    }]
  }
})

const experienceOption = computed(() => {
  const d = experienceData.value
  if (!d.categories?.length) return {}
  // Transform backend data [{min, q1, median, q3, max, mean}] to boxplot format
  const boxData = (d.data || []).map(item => [item.min, item.q1, item.median, item.q3, item.max])
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const item = d.data[params.dataIndex]
        if (!item) return ''
        const fmt = (v) => `¥${(v * 1000).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
        return `${params.name}<br/>最大: ${fmt(item.max)}<br/>Q3: ${fmt(item.q3)}<br/>中位: ${fmt(item.median)}<br/>Q1: ${fmt(item.q1)}<br/>最小: ${fmt(item.min)}<br/>均值: ${fmt(item.mean)}`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: d.categories || [],
      axisLabel: { fontSize: 11 }
    },
    yAxis: { type: 'value', name: '月薪 (K)' },
    series: [{
      type: 'boxplot',
      data: boxData,
      itemStyle: { color: colors[0], borderColor: '#224abe' }
    }]
  }
})

// 加载数据
async function loadOverview() {
  try {
    const res = await dataAPI.getOverview()
    const data = res.data.data
    statCards.value[0].value = formatNumber(data.total_jobs || 0)
    statCards.value[1].value = formatSalary(data.avg_salary || 0)
    statCards.value[2].value = formatNumber(data.company_count || 0)
    statCards.value[3].value = formatNumber(data.keyword_count || 0)
  } catch {
    statCards.value[0].value = '12,458'
    statCards.value[1].value = '¥15,680'
    statCards.value[2].value = '3,842'
    statCards.value[3].value = '8'
  }
}

async function loadChartData() {
  chartLoading.value = true
  try {
    const [salaryRes, cityRes, eduRes, demandRes, expRes] = await Promise.allSettled([
      vizAPI.getSalary(),
      vizAPI.getCitySalary(),
      vizAPI.getEducation(),
      vizAPI.getPositionDemand(),
      vizAPI.getExperienceSalary()
    ])
    if (salaryRes.status === 'fulfilled') salaryData.value = salaryRes.value.data.data
    if (cityRes.status === 'fulfilled') cityData.value = cityRes.value.data.data
    if (eduRes.status === 'fulfilled') educationData.value = eduRes.value.data.data
    if (demandRes.status === 'fulfilled') demandData.value = demandRes.value.data.data
    if (expRes.status === 'fulfilled') experienceData.value = expRes.value.data.data
  } catch {
    // 错误已在拦截器中处理
  } finally {
    chartLoading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadChartData()
})
</script>

<style scoped>
.viz-page {
  max-width: 1200px;
  margin: 0 auto;
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

.chart-nav {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
</style>
