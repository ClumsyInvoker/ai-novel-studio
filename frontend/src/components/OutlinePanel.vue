<template>
  <div class="outline-panel">
    <div class="op-head">
      <span class="op-title">🧭 大纲对话</span>
      <el-button size="small" text @click="reset">新对话</el-button>
    </div>

    <div ref="listRef" class="op-messages">
      <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
        <div class="bubble">{{ m.content }}</div>
      </div>
      <div v-if="busy" class="msg ai"><div class="bubble typing">大纲思考中…</div></div>
    </div>

    <div class="op-chips">
      <el-tag v-for="c in chips" :key="c" size="small" class="chip" @click="send(c)">{{ c }}</el-tag>
    </div>

    <div class="op-struct">
      <el-button type="success" size="small" :loading="structBusy" plain @click="genStructure">📚 由大纲生成 卷/章 结构</el-button>
      <span v-if="structDiag" class="struct-diag">{{ structDiag }}</span>
    </div>

    <div class="op-input">
      <el-input
        ref="inputRef"
        v-model="input"
        type="textarea"
        :rows="2"
        resize="none"
        placeholder="追问大纲，如：聚焦第三章冲突 / 再往下推5章"
        @keydown.enter.exact.prevent="send()"
      />
      <el-button type="primary" :loading="busy" @click="send()">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/client.js'

const props = defineProps({ workId: Number })
const emit = defineEmits(['created'])

const messages = ref([])
const input = ref('')
const busy = ref(false)
const structBusy = ref(false)
const structDiag = ref('')
const listRef = ref(null)
const chips = ['接下来3章要点', '聚焦当前冲突', '完善主角成长线', '给出爽点节奏']

async function send(text) {
  const prompt = (text ?? input.value).trim()
  if (!prompt || !props.workId) return
  input.value = ''
  messages.value.push({ role: 'user', content: prompt })
  busy.value = true
  scroll()
  try {
    const r = await api.post('/ai/outline-chat', { work_id: props.workId, history: messages.value })
    messages.value.push({ role: 'assistant', content: r.content })
  } catch (e) {
    ElMessage.error(e?.detail || '大纲生成失败')
  } finally {
    busy.value = false
    scroll()
  }
}

function reset() { messages.value = []; send('请从整体给出接下来3-5章大纲') }
function scroll() { nextTick(() => { const el = listRef.value; if (el) el.scrollTop = el.scrollHeight }) }

async function genStructure() {
  if (!props.workId) return
  structBusy.value = true; structDiag.value = 'AI 编排卷章结构中…'
  try {
    const r = await api.post('/ai/generate-structure', { work_id: props.workId })
    structDiag.value = `✅ 已生成卷×${r.volumes}、章×${r.chapters}，已加入作品`
    messages.value.push({ role: 'assistant', content: `已按此结构创建 ${r.volumes} 卷、共 ${r.chapters} 章。你可以在章树里查看并逐章扩写。` })
    emit('created')
  } catch (e) {
    structDiag.value = '生成失败，请重试'
    ElMessage.error(e?.detail || '生成失败')
  } finally { structBusy.value = false }
}
</script>

<style scoped>
.outline-panel { display: flex; flex-direction: column; height: 100%; }
.op-head { display: flex; align-items: center; justify-content: space-between; padding: 8px 4px; }
.op-title { font-weight: 600; }
.op-messages { flex: 1; min-height: 0; overflow: auto; display: flex; flex-direction: column; gap: 8px; padding: 4px; }
.msg { display: flex; }
.msg.user { justify-content: flex-end; }
.msg.ai { justify-content: flex-start; }
.bubble {
  max-width: 86%; padding: 8px 11px; border-radius: 10px;
  font-size: 13px; line-height: 1.7; white-space: pre-wrap; word-break: break-word;
}
.msg.user .bubble { background: #409eff; color: #fff; border-top-right-radius: 2px; }
.msg.ai .bubble { background: #f3f4f6; color: #333; border-top-left-radius: 2px; }
.bubble.typing { color: #909399; }
.op-chips { display: flex; gap: 6px; flex-wrap: wrap; padding: 4px 2px 8px; }
.chip { cursor: pointer; }
.op-struct { display: flex; align-items: center; gap: 8px; padding: 6px 0 8px; }
.struct-diag { font-size: 12px; color: #67c23a; }
.op-input { display: flex; gap: 8px; align-items: flex-end; }
.op-input .el-button { height: 56px; width: 64px; flex: none; }
</style>