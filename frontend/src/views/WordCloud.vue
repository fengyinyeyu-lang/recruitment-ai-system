<template>
  <div class="wordcloud-page">
    <!-- Banner -->
    <div class="gradient-banner" style="background: linear-gradient(135deg, #36b9cc 0%, #258591 100%);">
      <h2>核心技能需求画像</h2>
      <p>基于岗位描述文本的词云分析与城市、行业需求洞察</p>
    </div>

    <!-- 采样控制 -->
    <div class="page-card control-bar">
      <div class="control-item">
        <span class="control-label">采样条数：</span>
        <el-slider
          v-model="sampleSize"
          :min="100"
          :max="5000"
          :step="100"
          :show-input="true"
          input-size="small"
          style="width: 400px; max-width: 100%;"
        />
      </div>
      <el-button type="primary" :loading="loading" @click="loadWordCloud">
        <el-icon><Refresh /></el-icon> 生成词云
      </el-button>
    </div>

    <!-- 词云图 -->
    <div class="chart-container">
      <div class="chart-title">岗位技能关键词云</div>
      <v-chart :option="wordCloudOption" :loading="loading" autoresize style="height: 500px;" />
    </div>

    <!-- 城市需求 + 行业分布 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="chart-container">
          <div class="chart-title">城市岗位需求 Top15</div>
          <v-chart :option="cityDemandOption" :loading="cityLoading" autoresize style="height: 420px;" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="chart-container">
          <div class="chart-title">行业领域分布 Top15</div>
          <v-chart :option="industryOption" :loading="industryLoading" autoresize style="height: 420px;" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { TooltipComponent, GridComponent } from 'echarts/components'
import 'echarts-wordcloud'
import { vizAPI } from '@/api'
import { getChartColors } from '@/utils'

use([CanvasRenderer, BarChart, TooltipComponent, GridComponent])

const colors = getChartColors()
const sampleSize = ref(2000)
const loading = ref(false)
const cityLoading = ref(false)
const industryLoading = ref(false)

const wordCloudData = ref([])
const cityDemandData = ref({})
const industryData = ref({})

const wordCloudOption = computed(() => {
  if (!wordCloudData.value.length) return {}
  return {
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      sizeRange: [14, 60],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
        fontWeight: 'bold',
        color: () => colors[Math.floor(Math.random() * colors.length)]
      },
      emphasis: {
        textStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
      },
      data: wordCloudData.value
    }]
  }
})

const cityDemandOption = computed(() => {
  const d = cityDemandData.value
  if (!d.cities?.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: '岗位数量' },
    yAxis: {
      type: 'category',
      data: [...(d.cities || [])].reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: [...(d.counts || [])].reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: (params) => colors[params.dataIndex % colors.length]
      },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  }
})

const industryOption = computed(() => {
  const d = industryData.value
  if (!d.industries?.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: '岗位数量' },
    yAxis: {
      type: 'category',
      data: [...(d.industries || [])].reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: [...(d.counts || [])].reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: (params) => colors[params.dataIndex % colors.length]
      },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  }
})

async function loadWordCloud() {
  loading.value = true
  try {
    const res = await vizAPI.getWordCloud({ sample_size: sampleSize.value })
    const data = res.data.data
    wordCloudData.value = (data.words || []).map(w => ({
      name: w.text,
      value: w.weight
    }))
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function loadCityDemand() {
  cityLoading.value = true
  try {
    const res = await vizAPI.getCityDemand()
    cityDemandData.value = res.data.data
  } catch {
    // 错误已在拦截器中处理
  } finally {
    cityLoading.value = false
  }
}

async function loadIndustry() {
  industryLoading.value = true
  try {
    const res = await vizAPI.getIndustry()
    industryData.value = res.data.data
  } catch {
    // 错误已在拦截器中处理
  } finally {
    industryLoading.value = false
  }
}

onMounted(() => {
  loadWordCloud()
  loadCityDemand()
  loadIndustry()
})
</script>

<style scoped>
.wordcloud-page {
  max-width: 1200px;
  margin: 0 auto;
}

.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 300px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
}
</style>
