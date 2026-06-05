<template>
  <div class="ai-page">
    <!-- 顶部控制栏 -->
    <div class="ai-header">
      <div class="gradient-banner" style="background: linear-gradient(135deg, #1cc88a 0%, #13855c 100%); margin-bottom: 0;">
        <div class="banner-content">
          <div>
            <h2>智能求职助手</h2>
            <p>基于 RAG 知识库的招聘领域 AI 问答，为您提供专业的求职建议</p>
          </div>
          <div class="header-controls">
            <div class="mode-switch">
              <el-radio-group v-model="chatMode" size="small">
                <el-radio-button value="agent">智能体</el-radio-button>
                <el-radio-button value="rag">RAG</el-radio-button>
                <el-radio-button value="normal">普通</el-radio-button>
              </el-radio-group>
            </div>
            <el-button v-if="chatMode !== 'agent'" size="small" type="warning" :loading="rebuilding" @click="rebuildRAG">
              <el-icon><RefreshRight /></el-icon> 重建知识库
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="chat-container">
      <div class="chat-messages" ref="messagesRef">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon">
            <el-icon :size="48"><ChatDotRound /></el-icon>
          </div>
          <h3>你好！我是招聘智能助手</h3>
          <p>我可以帮你分析招聘市场趋势、提供求职建议、解读岗位要求</p>
          <div class="quick-questions">
            <div class="quick-label">快捷提问：</div>
            <el-button
              v-for="q in quickQuestions"
              :key="q"
              size="default"
              round
              @click="sendQuickQuestion(q)"
            >
              {{ q }}
            </el-button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="32" class="avatar-user">我</el-avatar>
            <el-avatar v-else :size="32" class="avatar-ai">
              <el-icon><Cpu /></el-icon>
            </el-avatar>
          </div>
          <div class="message-body">
            <div v-if="msg.role === 'assistant'" class="message-content">
              <!-- 流式输出中：显示纯文本 + 光标动画 -->
              <template v-if="msg.streaming">
                <span class="streaming-text">{{ msg.content }}</span>
                <span class="streaming-cursor">|</span>
              </template>
              <!-- 流式输出完成：渲染 Markdown -->
              <template v-else>
                <div v-html="renderMarkdown(msg.content)"></div>
              </template>
            </div>
            <div v-else class="message-content">{{ msg.content }}</div>
            <!-- 知识来源 -->
            <div v-if="msg.sources && msg.sources.length" class="message-sources">
              <el-collapse>
                <el-collapse-item title="知识来源">
                  <div v-for="(src, si) in msg.sources" :key="si" class="source-item">
                    <el-tag size="small" type="info">{{ src.source || `来源 ${si + 1}` }}</el-tag>
                    <span class="source-text">{{ src.content || src.text || '' }}</span>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>

        <!-- 加载中（仅非智能体模式显示） -->
        <div v-if="chatLoading && chatMode !== 'agent'" class="message assistant">
          <div class="message-avatar">
            <el-avatar :size="32" class="avatar-ai">
              <el-icon><Cpu /></el-icon>
            </el-avatar>
          </div>
          <div class="message-body">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入您的问题，按 Enter 发送，Shift+Enter 换行..."
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button
            type="primary"
            circle
            :disabled="!inputText.trim() || chatLoading"
            :loading="chatLoading"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { aiAPI } from '@/api'
import { renderMarkdown } from '@/utils'

const chatMode = ref('agent')
const chatLoading = ref(false)
const rebuilding = ref(false)
const inputText = ref('')
const messagesRef = ref(null)
const agentSessionId = ref(null)

const messages = ref([])

const quickQuestions = [
  '目前哪些城市的技术岗位需求最大？',
  '数据分析师的薪资水平如何？',
  '转行做产品经理需要哪些技能？',
  '如何提高面试通过率？'
]

// 节流滚动：避免每个 chunk 都触发 DOM 操作
let scrollTimer = null
function scrollToBottom() {
  if (scrollTimer) return
  scrollTimer = setTimeout(() => {
    scrollTimer = null
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
    })
  }, 50)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatLoading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  chatLoading.value = true
  scrollToBottom()

  try {
    if (chatMode.value === 'agent') {
      // 智能体模式：流式接收
      const assistantMsg = { role: 'assistant', content: '', sources: [], streaming: true }
      messages.value.push(assistantMsg)
      const msgIndex = messages.value.length - 1

      const response = await aiAPI.agentChatStream({
        message: text,
        session_id: agentSessionId.value
      })

      if (!response.ok) {
        messages.value[msgIndex].content = '抱歉，请求出错了，请稍后重试。'
        messages.value[msgIndex].streaming = false
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const chunk = JSON.parse(line.slice(6))
            if (chunk.type === 'text') {
              messages.value[msgIndex].content += chunk.content
              scrollToBottom()
            } else if (chunk.type === 'done') {
              if (chunk.session_id) {
                agentSessionId.value = chunk.session_id
              }
              // 流式结束，切换到 Markdown 渲染
              messages.value[msgIndex].streaming = false
            }
          } catch { /* 忽略解析错误 */ }
        }
      }
      // 兜底：确保 streaming 状态关闭
      if (messages.value[msgIndex].streaming) {
        messages.value[msgIndex].streaming = false
      }
    } else {
      // RAG / 普通模式：同步请求
      let res
      if (chatMode.value === 'rag') {
        res = await aiAPI.ragChat({ message: text, history: [] })
      } else {
        res = await aiAPI.chat({ message: text, history: [] })
      }

      const data = res.data.data
      messages.value.push({
        role: 'assistant',
        content: data.reply || '暂无回复',
        sources: data.sources || [],
        streaming: false
      })
    }
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，请求出错了，请稍后重试。',
      streaming: false
    })
  } finally {
    chatLoading.value = false
    scrollToBottom()
  }
}

function sendQuickQuestion(q) {
  inputText.value = q
  sendMessage()
}

async function rebuildRAG() {
  rebuilding.value = true
  try {
    await aiAPI.rebuildRag()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    rebuilding.value = false
  }
}
</script>

<style scoped>
.ai-page {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 104px);
}

.ai-header {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.banner-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 欢迎区域 */
.welcome-section {
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1cc88a, #13855c);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  margin: 0 auto 20px;
}

.welcome-section h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.welcome-section p {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.quick-label {
  width: 100%;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

/* 消息样式 */
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-user {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: #ffffff;
  font-size: 13px;
}

.avatar-ai {
  background: linear-gradient(135deg, #1cc88a, #13855c);
  color: #ffffff;
}

.message-body {
  max-width: 70%;
}

.message.user .message-content {
  background: linear-gradient(135deg, #4e73df, #3a5fc8);
  color: #ffffff;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
}

.message.assistant .message-content {
  background: #f8f9fc;
  border-radius: 16px 16px 16px 4px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}

.message.assistant .message-content :deep(p) {
  margin-bottom: 8px;
}

.message.assistant .message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message.assistant .message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message.assistant .message-content :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message.assistant .message-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

/* 知识来源 */
.message-sources {
  margin-top: 8px;
}

.message-sources :deep(.el-collapse-item__header) {
  font-size: 12px;
  color: var(--color-text-secondary);
  height: 32px;
  line-height: 32px;
}

.source-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.source-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 流式输出光标 */
.streaming-cursor {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  color: var(--color-text-secondary);
  font-weight: 300;
  margin-left: 1px;
}

@keyframes blink {
  50% { opacity: 0; }
}

/* 输入中动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.chat-input-area {
  border-top: 1px solid var(--color-border);
  padding: 16px 20px;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 10px 14px;
}

.input-wrapper .el-button {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}
</style>
