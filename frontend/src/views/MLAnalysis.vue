<template>
  <div class="ml-page">
    <el-tabs v-model="activeTab" type="border-card" class="ml-tabs">
      <!-- K-Means 聚类分析 -->
      <el-tab-pane label="K-Means 岗位聚类分析" name="kmeans">
        <div class="tab-content">
          <!-- 控制区 -->
          <div class="control-bar">
            <div class="control-item">
              <span class="control-label">聚类数 K：</span>
              <el-slider v-model="kmeansK" :min="2" :max="10" :show-input="true" input-size="small" style="width: 250px;" />
            </div>
            <el-button type="primary" :loading="kmeansLoading" @click="runKmeans">
              <el-icon><Cpu /></el-icon> 开始聚类
            </el-button>
          </div>

          <!-- 聚类结果 -->
          <template v-if="kmeansResult">
            <!-- 簇特征词 -->
            <div class="page-card" v-if="kmeansResult.cluster_keywords">
              <h3 class="section-title">各簇核心特征词</h3>
              <div class="cluster-tags">
                <div v-for="(keywords, index) in kmeansResult.cluster_keywords" :key="index" class="cluster-group">
                  <div class="cluster-label">簇 {{ index + 1 }}</div>
                  <div class="cluster-tag-list">
                    <el-tag
                      v-for="kw in keywords"
                      :key="kw"
                      :type="tagTypes[index % tagTypes.length]"
                      effect="plain"
                      class="cluster-tag"
                    >
                      {{ kw }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- PCA 散点图 -->
            <div class="chart-container">
              <div class="chart-title">PCA 降维可视化</div>
              <v-chart :option="pcaOption" autoresize style="height: 450px;" />
            </div>

            <!-- 聚类结果表格 -->
            <div class="page-card" v-if="kmeansResult.cluster_stats">
              <h3 class="section-title">聚类统计</h3>
              <el-table :data="kmeansResult.cluster_stats" stripe style="width: 100%">
                <el-table-column prop="cluster" label="簇编号" width="100" />
                <el-table-column prop="count" label="样本数" width="100" />
                <el-table-column prop="avg_salary" label="平均薪资" />
                <el-table-column prop="top_city" label="主要城市" />
                <el-table-column prop="top_position" label="主要岗位" />
              </el-table>
            </div>
          </template>
        </div>
      </el-tab-pane>

      <!-- 神经网络分类预测 -->
      <el-tab-pane label="神经网络分类预测" name="nn">
        <div class="tab-content">
          <!-- 训练参数 -->
          <div class="page-card">
            <h3 class="section-title">训练参数配置</h3>
            <el-form :model="nnParams" label-width="120px" class="param-form">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="聚类数 K">
                    <el-input-number v-model="nnParams.k" :min="2" :max="10" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="Epochs">
                    <el-input-number v-model="nnParams.epochs" :min="10" :max="500" :step="10" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="学习率">
                    <el-input-number v-model="nnParams.lr" :min="0.0001" :max="0.1" :step="0.001" :precision="4" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" :loading="nnTraining" @click="trainNN">
                  <el-icon><VideoPlay /></el-icon> 开始训练
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 训练进度 -->
            <el-progress
              v-if="nnTraining"
              :percentage="trainProgress"
              :stroke-width="20"
              :text-inside="true"
              style="margin-top: 16px;"
              status="success"
            />
          </div>

          <!-- 训练结果 -->
          <template v-if="nnResult">
            <!-- 训练曲线 -->
            <div class="chart-container">
              <div class="chart-title">训练曲线</div>
              <v-chart :option="trainCurveOption" autoresize style="height: 400px;" />
            </div>

            <!-- 分类报告 -->
            <div class="page-card" v-if="nnResult.classification_report">
              <h3 class="section-title">分类报告</h3>
              <el-table :data="formatReport(nnResult.classification_report)" stripe style="width: 100%">
                <el-table-column prop="class" label="类别" width="120" />
                <el-table-column prop="precision" label="精确率" width="120" />
                <el-table-column prop="recall" label="召回率" width="120" />
                <el-table-column prop="f1_score" label="F1 分数" width="120" />
                <el-table-column prop="support" label="样本数" width="100" />
              </el-table>
            </div>

            <!-- 预测输入 -->
            <div class="page-card">
              <h3 class="section-title">薪资预测</h3>
              <el-form :model="predictForm" label-width="100px">
                <el-row :gutter="16">
                  <el-col :span="6">
                    <el-form-item label="城市">
                      <el-input v-model="predictForm.city" placeholder="如：北京" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="6">
                    <el-form-item label="学历">
                      <el-input v-model="predictForm.education" placeholder="如：本科" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="6">
                    <el-form-item label="经验">
                      <el-input v-model="predictForm.experience" placeholder="如：3-5年" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="6">
                    <el-form-item label="岗位">
                      <el-input v-model="predictForm.keyword" placeholder="如：Java" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item>
                  <el-button type="success" :loading="predictLoading" @click="predictSalary">
                    <el-icon><Aim /></el-icon> 预测
                  </el-button>
                </el-form-item>
              </el-form>

              <el-result
                v-if="predictResult"
                icon="success"
                :title="`预测薪资区间：${predictResult}`"
              />
            </div>
          </template>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart, LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { mlAPI } from '@/api'
import { getChartColors } from '@/utils'

use([CanvasRenderer, ScatterChart, LineChart, BarChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent])

const colors = getChartColors()
const tagTypes = ['', 'success', 'warning', 'danger', 'info']

const activeTab = ref('kmeans')

// K-Means 相关
const kmeansK = ref(4)
const kmeansLoading = ref(false)
const kmeansResult = ref(null)

// 神经网络相关
const nnParams = ref({ k: 4, epochs: 100, lr: 0.01 })
const nnTraining = ref(false)
const trainProgress = ref(0)
const nnResult = ref(null)
const predictForm = ref({ city: '', education: '', experience: '', keyword: '' })
const predictLoading = ref(false)
const predictResult = ref('')

const pcaOption = computed(() => {
  if (!kmeansResult.value?.pca_data) return {}
  const data = kmeansResult.value.pca_data
  const clusters = [...new Set(data.labels)]
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => `簇 ${p.seriesName}<br/>坐标: (${p.data[0]?.toFixed(2)}, ${p.data[1]?.toFixed(2)})`
    },
    legend: { top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: 'PC1' },
    yAxis: { type: 'value', name: 'PC2' },
    series: clusters.map((c, i) => ({
      name: `簇 ${c + 1}`,
      type: 'scatter',
      data: data.points.filter((_, idx) => data.labels[idx] === c).map(p => [p[0], p[1]]),
      itemStyle: { color: colors[i % colors.length] },
      symbolSize: 6
    }))
  }
})

const trainCurveOption = computed(() => {
  if (!nnResult.value?.history) return {}
  const h = nnResult.value.history
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Loss', 'Accuracy'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: h.epochs || h.epoch_list || [], name: 'Epoch' },
    yAxis: [
      { type: 'value', name: 'Loss' },
      { type: 'value', name: 'Accuracy', max: 1 }
    ],
    series: [
      {
        name: 'Loss',
        type: 'line',
        data: h.loss || [],
        smooth: true,
        itemStyle: { color: '#e74a3b' }
      },
      {
        name: 'Accuracy',
        type: 'line',
        yAxisIndex: 1,
        data: h.accuracy || [],
        smooth: true,
        itemStyle: { color: '#1cc88a' }
      }
    ]
  }
})

function formatReport(report) {
  if (!report) return []
  if (Array.isArray(report)) return report
  // If it's a string, parse it
  return parseReport(report)
}

async function runKmeans() {
  kmeansLoading.value = true
  try {
    const res = await mlAPI.kmeans({ n_clusters: kmeansK.value })
    const rawData = res.data.data
    // Transform to frontend structure
    kmeansResult.value = {
      cluster_keywords: rawData.keywords || {},
      pca_data: {
        points: (rawData.pca_data || []).map(p => [p.x, p.y]),
        labels: (rawData.pca_data || []).map(p => p.cluster)
      },
      sample_data: rawData.sample_data || [],
      cluster_stats: rawData.cluster_stats || buildClusterStats(rawData)
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    kmeansLoading.value = false
  }
}

function buildClusterStats(data) {
  if (!data.pca_data?.length) return []
  const clusters = {}
  data.pca_data.forEach(p => {
    if (!clusters[p.cluster]) clusters[p.cluster] = { count: 0 }
    clusters[p.cluster].count++
  })
  return Object.entries(clusters).map(([c, info]) => ({
    cluster: parseInt(c) + 1,
    count: info.count,
    avg_salary: '--',
    top_city: '--',
    top_position: '--'
  }))
}

async function trainNN() {
  nnTraining.value = true
  trainProgress.value = 0
  nnResult.value = null
  predictResult.value = ''

  // 模拟进度
  const progressTimer = setInterval(() => {
    if (trainProgress.value < 90) {
      trainProgress.value += Math.random() * 10
    }
  }, 500)

  try {
    const res = await mlAPI.nnTrain({
      k: nnParams.value.k,
      epochs: nnParams.value.epochs,
      learning_rate: nnParams.value.lr
    })
    const rawData = res.data.data
    // Transform to frontend structure
    nnResult.value = {
      accuracy: rawData.accuracy,
      history: {
        epochs: Array.from({ length: (rawData.history?.train_loss || []).length }, (_, i) => i + 1),
        loss: rawData.history?.train_loss || [],
        accuracy: rawData.history?.val_acc || []
      },
      classification_report: parseReport(rawData.report),
      cluster_names: rawData.cluster_names
    }
    trainProgress.value = 100
  } catch {
    // 错误已在拦截器中处理
  } finally {
    clearInterval(progressTimer)
    nnTraining.value = false
  }
}

function parseReport(reportStr) {
  if (!reportStr) return []
  // Parse sklearn classification report string to table data
  const lines = reportStr.trim().split('\n').slice(2, -2)
  return lines.map(line => {
    const parts = line.trim().split(/\s+/)
    if (parts.length >= 5) {
      return {
        class: parts[0],
        precision: parseFloat(parts[1])?.toFixed(4) || '--',
        recall: parseFloat(parts[2])?.toFixed(4) || '--',
        f1_score: parseFloat(parts[3])?.toFixed(4) || '--',
        support: parts[4] || '--'
      }
    }
    return null
  }).filter(Boolean)
}

async function predictSalary() {
  predictLoading.value = true
  try {
    const res = await mlAPI.salaryPredict({
      city: predictForm.value.city || '北京',
      education: predictForm.value.education || '本科',
      workYear: predictForm.value.experience || '3-5年',
      keyword: predictForm.value.keyword || 'Java'
    })
    const data = res.data.data
    predictResult.value = `${data.predicted_salary?.toFixed(1)}K (${data.confidence || ''})`
  } catch {
    // 错误已在拦截器中处理
  } finally {
    predictLoading.value = false
  }
}
</script>

<style scoped>
.ml-page {
  max-width: 1200px;
  margin: 0 auto;
}

.ml-tabs {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.ml-tabs :deep(.el-tabs__header) {
  background: #f8f9fc;
}

.tab-content {
  padding: 4px;
}

.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px 24px;
  margin-bottom: 20px;
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

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.cluster-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.cluster-group {
  flex: 1;
  min-width: 200px;
}

.cluster-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.cluster-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cluster-tag {
  border-radius: 6px;
}

.param-form {
  max-width: 800px;
}
</style>
