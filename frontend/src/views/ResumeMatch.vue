<template>
  <div class="resume-page">
    <div class="gradient-banner" style="background: linear-gradient(135deg, #f6c23e 0%, #d4a017 100%);">
      <h2>PDF 简历智能推荐</h2>
      <p>上传您的 PDF 简历，AI 将自动解析并为您匹配最合适的岗位</p>
    </div>

    <el-row :gutter="20">
      <!-- 上传区域 -->
      <el-col :xs="24" :md="10">
        <div class="page-card">
          <h3 class="section-title">上传简历</h3>
          <el-upload
            ref="uploadRef"
            class="resume-upload"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将 PDF 简历拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持 PDF 格式，文件大小不超过 10MB</div>
            </template>
          </el-upload>

          <el-button
            type="primary"
            size="large"
            :loading="uploading"
            :disabled="!selectedFile"
            class="upload-btn"
            @click="uploadResume"
          >
            <el-icon><Upload /></el-icon> 解析简历并推荐岗位
          </el-button>
        </div>

        <!-- 解析结果 -->
        <div v-if="parsedResult" class="page-card">
          <h3 class="section-title">简历解析结果</h3>
          <div class="parsed-info">
            <div class="info-item" v-if="parsedResult.education">
              <span class="info-label">学历：</span>
              <el-tag type="primary">{{ parsedResult.education }}</el-tag>
            </div>
            <div class="info-item" v-if="parsedResult.experience">
              <span class="info-label">经验：</span>
              <el-tag type="success">{{ parsedResult.experience }}</el-tag>
            </div>
            <div class="info-item" v-if="parsedResult.skills?.length">
              <span class="info-label">技能：</span>
              <div class="skill-tags">
                <el-tag
                  v-for="skill in parsedResult.skills"
                  :key="skill"
                  effect="plain"
                  size="small"
                  class="skill-tag"
                >
                  {{ skill }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 推荐结果 -->
      <el-col :xs="24" :md="14">
        <div v-if="recommendations.length" class="page-card">
          <h3 class="section-title">
            推荐岗位
            <el-tag type="success" size="small" style="margin-left: 8px;">{{ recommendations.length }} 个匹配</el-tag>
          </h3>
          <div class="job-list">
            <div v-for="(job, index) in recommendations" :key="index" class="job-card">
              <div class="job-header">
                <div class="job-title">{{ job.position_name || job.position || '未知岗位' }}</div>
                <el-tag
                  :type="getMatchType(job.match_score || job.score)"
                  effect="dark"
                  size="small"
                >
                  匹配度 {{ Math.round((job.match_score || job.score || 0) * 100) }}%
                </el-tag>
              </div>
              <div class="job-meta">
                <span v-if="job.city"><el-icon><Location /></el-icon> {{ job.city }}</span>
                <span v-if="job.salary"><el-icon><Money /></el-icon> {{ job.salary }}</span>
                <span v-if="job.company"><el-icon><OfficeBuilding /></el-icon> {{ job.company }}</span>
              </div>
              <div v-if="job.matched_skills?.length" class="job-skills">
                <span class="skills-label">匹配技能：</span>
                <el-tag
                  v-for="skill in job.matched_skills"
                  :key="skill"
                  size="small"
                  type="success"
                  effect="plain"
                  class="skill-tag"
                >
                  {{ skill }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!uploading" class="page-card empty-state">
          <el-empty description="上传简历后，将为您推荐匹配的岗位" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { resumeAPI } from '@/api'
import { ElMessage } from 'element-plus'

const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const parsedResult = ref(null)
const recommendations = ref([])

function handleFileChange(file) {
  if (file.raw?.type !== 'application/pdf') {
    ElMessage.warning('请上传 PDF 格式的文件')
    selectedFile.value = null
    return
  }
  if (file.raw?.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 10MB')
    selectedFile.value = null
    return
  }
  selectedFile.value = file.raw
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件，请先删除已选文件')
}

function getMatchType(score) {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'info'
}

async function uploadResume() {
  if (!selectedFile.value) return

  uploading.value = true
  parsedResult.value = null
  recommendations.value = []

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const res = await resumeAPI.upload(formData)
    const data = res.data.data

    parsedResult.value = {
      education: data.education || '',
      experience: data.experience || 0,
      skills: data.skills || []
    }

    // 获取推荐
    const recRes = await resumeAPI.recommend({
      education: parsedResult.value.education,
      experience: parsedResult.value.experience,
      skills: parsedResult.value.skills.join(',')
    })
    recommendations.value = recRes.data.data || []
  } catch {
    // 错误已在拦截器中处理
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.resume-page {
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
  display: flex;
  align-items: center;
}

.resume-upload {
  width: 100%;
}

.resume-upload :deep(.el-upload-dragger) {
  border-radius: 12px;
  padding: 30px 20px;
}

.upload-btn {
  width: 100%;
  margin-top: 16px;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
}

.parsed-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  line-height: 24px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  border-radius: 6px;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-card {
  background: #f8f9fc;
  border-radius: 10px;
  padding: 16px;
  transition: all 0.2s ease;
  border-left: 3px solid var(--color-primary);
}

.job-card:hover {
  background: #f0f3ff;
  transform: translateX(4px);
}

.job-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.job-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.job-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.job-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.job-skills {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.skills-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 24px;
  white-space: nowrap;
}

.empty-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
