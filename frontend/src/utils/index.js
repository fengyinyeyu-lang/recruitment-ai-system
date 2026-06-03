import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

export function renderMarkdown(text) {
  return md.render(text || '')
}

export function formatSalary(value) {
  if (value === null || value === undefined) return '--'
  // 后端 salary_avg 以千元（K）为单位，转为元显示
  const yuan = Number(value) * 1000
  return `¥${yuan.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export function formatNumber(value) {
  if (value === null || value === undefined) return '--'
  return Number(value).toLocaleString('zh-CN')
}

export function getChartColors() {
  return ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf']
}

export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}
