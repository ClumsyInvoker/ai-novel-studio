<template>
  <div class="settings">
    <h2 class="pg-title">⚙️ 设置</h2>

    <el-card class="card" shadow="never">
      <template #header><b>AI 接口配置</b></template>
      <el-form label-width="110px" label-position="top" @submit.prevent>
        <el-form-item label="服务商 (Provider)">
          <el-select v-model="form.provider" style="width:100%; max-width:340px">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="火山方舟 (Ark)" value="ark" />
            <el-option label="自定义 (OpenAI 兼容)" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="status.has_key ? '已设置 · 留空保持不变' : '输入 API Key'"
            clearable
            style="max-width:420px"
          />
          <div class="tip">直接输入新 Key 会覆盖旧值；留空则保留当前配置。</div>
        </el-form-item>

        <el-form-item label="Base URL（可选）">
          <el-input v-model="form.base_url" placeholder="留空使用所选服务商默认地址" style="max-width:420px" />
        </el-form-item>

        <el-form-item label="模型名（可选）">
          <el-input v-model="form.model" placeholder="留空使用所选服务商默认模型" style="max-width:420px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
          <span v-if="savedOk" class="ok">✓ 已保存</span>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="card" shadow="never" v-if="status.provider">
      <template #header><b>当前生效</b></template>
      <div class="status-row">
        <el-tag size="small">Provider: {{ status.provider }}</el-tag>
        <el-tag size="small" type="info">模型: {{ status.model }}</el-tag>
        <el-tag size="small" :type="status.has_key ? 'success' : 'danger'">
          {{ status.has_key ? '已配置 Key' : '未配置 Key' }}
        </el-tag>
      </div>
      <div class="tip" style="margin-top:8px">AI 生成功能使用上方配置；未配 Key 时才会回退到系统环境变量。</div>
    </el-card>

    <el-card class="card" shadow="never">
      <template #header><b>数据与安全</b></template>
      <ul class="sec-list">
        <li>作品数据保存在本地 <code>data/novel.db</code>（SQLite），不出本机。</li>
        <li>API Key 只存本地 <code>data/settings.json</code>，页面始终掩码显示。</li>
        <li>密钥不会写入代码、不会出现在日志。</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/client.js'

const form = reactive({ provider: 'deepseek', api_key: '', base_url: '', model: '' })
const status = ref({})
const saving = ref(false)
const savedOk = ref(false)

async function load() {
  const s = await api.get('/settings')
  form.provider = s.provider
  form.base_url = s.base_url
  form.model = s.model
  form.api_key = ''  // 始终从空开始，用户决定是否重填
  try { status.value = await api.get('/settings/status') } catch {}
}

async function save() {
  saving.value = true
  try {
    const s = await api.put('/settings', {
      provider: form.provider,
      api_key: form.api_key,
      base_url: form.base_url,
      model: form.model
    })
    form.api_key = ''
    status.value = await api.get('/settings/status')
    savedOk.value = true; setTimeout(() => (savedOk.value = false), 2000)
    ElMessage.success('设置已保存')
  } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.settings { max-width: 760px; margin: 0 auto; padding: 16px; }
.pg-title { font-size: 18px; margin: 0 0 12px; }
.card { margin-bottom: 16px; }
.tip { font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.5; }
.ok { color: #67c23a; margin-left: 10px; }
.status-row { display: flex; gap: 8px; flex-wrap: wrap; }
.sec-list { margin: 0; padding-left: 18px; color: #555; font-size: 13px; line-height: 1.9; }
code { background: #f3f4f6; padding: 1px 5px; border-radius: 4px; }
@media (max-width:900px){ .settings{ padding: 10px; } }
</style>