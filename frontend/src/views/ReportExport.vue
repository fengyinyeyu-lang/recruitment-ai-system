<template>
  <div class="report-page">
    <div class="gradient-banner" style="background: linear-gradient(135deg, #e74a3b 0%, #be3a2e 100%);">
      <h2>分析报告导出</h2>
      <p>自定义筛选条件，生成专业的招聘市场分析报告</p>
    </div>

    <!-- 筛选条件 -->
    <div class="page-card">
      <h3 class="section-title">报告配置</h3>
      <el-form :model="reportForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <el-form-item label="目标城市">
              <el-select v-model="reportForm.city" filterable allow-create placeholder="选择或输入城市" style="width: 100%;">
                <el-option v-for="c in cityOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-form-item label="岗位方向">
              <el-select v-model="reportForm.position" filterable allow-create placeholder="选择或输入岗位" style="width: 100%;">
                <el-option v-for="p in positionOptions" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-form-item label="报告类型">
              <el-select v-model="reportForm.type" placeholder="选择报告类型" style="width: 100%;">
                <el-option label="综合分析报告" value="comprehensive" />
                <el-option label="薪资分析报告" value="salary" />
                <el-option label="岗位需求报告" value="demand" />
                <el-option label="企业画像报告" value="company" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 报告预览指标 -->
    <el-row :gutter="16" class="preview-row">
      <el-col :xs="12" :sm="6" v-for="item in previewCards" :key="item.label">
        <div class="preview-card">
          <div class="preview-icon" :style="{ background: item.color }">
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
          </div>
          <div class="preview-info">
            <div class="preview-label">{{ item.label }}</div>
            <div class="preview-value">{{ item.value }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <el-button type="primary" size="large" :loading="generating" @click="generateReport">
        <el-icon><Document /></el-icon> 生成报告
      </el-button>
      <el-button
        v-if="reportUrl"
        type="success"
        size="large"
        @click="downloadReport"
      >
        <el-icon><Download /></el-icon> 下载报告
      </el-button>
    </div>

    <!-- 报告预览 -->
    <div v-if="reportUrl" class="page-card preview-section">
      <h3 class="section-title">报告预览</h3>
      <iframe :src="reportUrl" class="report-iframe" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportAPI, dataAPI } from '@/api'
import { formatSalary } from '@/utils'
import { ElMessage } from 'element-plus'

const generating = ref(false)
const reportUrl = ref('')
const reportFilename = ref('')

const reportForm = ref({
  city: '',
  position: '',
  type: 'comprehensive'
})

const cityOptions = ref(['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '苏州', '西安'])
const positionOptions = ref(['数据分析师', '前端开发', '后端开发', '产品经理', 'UI设计师', '算法工程师', '测试工程师', '运维工程师'])

// 从后端动态加载真实城市/岗位选项
async function loadFilterOptions() {
  try {
    const res = await dataAPI.getFilters()
    const data = res.data.data
    if (data.cities?.length) {
      // 数据库城市名带"市"字，用户可见时去掉"市"便于搜索
      cityOptions.value = data.cities.map(c => c.endsWith('市') ? c.slice(0, -1) : c)
    }
    if (data.keywords?.length) {
      positionOptions.value = data.keywords
    }
  } catch {
    // 保持默认值
  }
}

const previewCards = ref([
  { label: '覆盖岗位', value: '--', color: '#4e73df', icon: 'Briefcase' },
  { label: '平均薪资', value: '--', color: '#1cc88a', icon: 'Money' },
  { label: '相关企业', value: '--', color: '#36b9cc', icon: 'OfficeBuilding' },
  { label: '数据维度', value: '8+', color: '#f6c23e', icon: 'DataAnalysis' }
])

async function loadPreview() {
  try {
    const res = await dataAPI.getOverview()
    const data = res.data.data
    previewCards.value[0].value = data.total_jobs || '--'
    previewCards.value[1].value = data.avg_salary ? formatSalary(data.avg_salary) : '--'
    previewCards.value[2].value = data.company_count || data.total_companies || '--'
  } catch {
    // 使用默认值
  }
}

async function generateReport() {
  generating.value = true
  reportUrl.value = ''
  try {
    const res = await reportAPI.generate({
      city: reportForm.value.city || '全国',
      keyword: reportForm.value.position || '全部岗位'
    })
    const data = res.data.data
    const htmlContent = data.html_content
    const blob = new Blob([htmlContent], { type: 'text/html' })
    reportUrl.value = URL.createObjectURL(blob)
    reportFilename.value = data.filename || '招聘分析报告.html'
    ElMessage.success('报告生成成功')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    generating.value = false
  }
}

function downloadReport() {
  if (!reportUrl.value) return
  const link = document.createElement('a')
  link.href = reportUrl.value
  link.download = reportFilename.value
  link.click()
}

onMounted(() => {
  loadPreview()
  loadFilterOptions()
})
</script>

<style scoped>
.report-page {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.preview-row {
  margin-bottom: 20px;
}

.preview-card {
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}

.preview-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.preview-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.preview-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.action-bar .el-button {
  border-radius: 8px;
  height: 44px;
  font-size: 15px;
}

.preview-section {
  min-height: 400px;
}

.report-iframe {
  width: 100%;
  height: 600px;
  border: none;
  border-radius: 8px;
}
</style>
