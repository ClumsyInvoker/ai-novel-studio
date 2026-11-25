<template>
  <div class="chars">
    <div class="chars-head">
      <el-select v-model="currentWorkId" placeholder="选择作品" style="width:200px" @change="load">
        <el-option v-for="w in works" :key="w.id" :label="w.title" :value="w.id" />
      </el-select>
      <el-button type="primary" @click="newCharacter">＋ 人物</el-button>
      <el-button v-if="selected" @click="aiCard">✨ AI 生成人设卡</el-button>
    </div>

    <div class="chars-body" v-if="characters.length">
      <!-- 人物卡片列表 -->
      <div class="card-grid">
        <div
          v-for="c in characters" :key="c.id"
          :class="['person-card', { active: selected?.id === c.id }]"
          @click="select(c)"
        >
          <div class="pc-name">{{ c.name }}</div>
          <div class="pc-identity">{{ c.identity || '未填身份' }}</div>
          <el-button link size="small" type="danger" @click.stop="del(c)">删</el-button>
        </div>
      </div>

      <!-- 编辑区 -->
      <div class="editor-pane" v-if="selected">
        <div class="editor-actions">
          <el-button size="small" type="success" @click="save">保存</el-button>
          <span v-if="saved" class="ok">✓ 已保存</span>
        </div>
        <el-form label-width="70px" label-position="top">
          <el-form-item label="名字"><el-input v-model="selected.name" /></el-form-item>
          <el-form-item label="身份"><el-input v-model="selected.identity" /></el-form-item>
          <el-form-item label="性格"><el-input type="textarea" :rows="2" v-model="selected.personality" /></el-form-item>
          <el-form-item label="动机/目标"><el-input type="textarea" :rows="2" v-model="selected.motivation" /></el-form-item>
          <el-form-item label="人际关系"><el-input type="textarea" :rows="2" v-model="selected.relationships" /></el-form-item>
          <el-form-item label="成长线"><el-input type="textarea" :rows="2" v-model="selected.growth" /></el-form-item>
          <el-form-item label="备注"><el-input type="textarea" :rows="2" v-model="selected.notes" /></el-form-item>
        </el-form>
      </div>
    </div>
    <el-empty v-else description="这是空的 · 选一个作品并新建人物，或点「✨ AI 生成人设卡」" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/client.js'

const works = ref([])
const currentWorkId = ref(null)
const currentWork = ref(null)
const characters = ref([])
const selected = ref(null)
const saved = ref(false)

async function loadWorks() {
  works.value = await api.get('/works')
  if (!currentWorkId.value && works.value.length) { currentWorkId.value = works.value[0].id; await load() }
}

async function load() {
  currentWork.value = await api.get('/works/' + currentWorkId.value)
  characters.value = currentWork.value.characters || []
  selected.value = null
}

function select(c) { selected.value = { ...c } }

async function newCharacter() {
  if (!currentWorkId.value) return ElMessage.warning('先选一个作品')
  const r = await api.post(`/works/${currentWorkId.value}/characters`, { name: '新角色' })
  await load()
  select(characters.value.find(c => c.id === r.id))
}

async function save() {
  await api.put('/characters/' + selected.value.id, selected.value)
  saved.value = true; setTimeout(() => (saved.value = false), 1500)
  await load(); selected.value = characters.value.find(c => c.id === selected.value?.id) || selected.value
}

async function del(c) {
  await ElMessageBox.confirm(`删除人物「${c.name}」？`, '确认删除', { type: 'warning' })
  await api.delete('/characters/' + c.id)
  await load()
}

let aiBusy = false
async function aiCard() {
  if (aiBusy) return
  aiBusy = true
  try {
    if (!selected.value) await newCharacter()
    const name = selected.value?.name || '新角色'
    const r = await api.post('/ai/character-card', { work_id: currentWorkId.value, name })
    if (r.fields) {
      // 自动填入对应字段并保存
      Object.keys(r.fields).forEach(k => { if (selected.value) selected.value[k] = r.fields[k] })
      await save()
      ElMessage.success('✨ AI 已自动填入人设各字段并保存')
    } else {
      ElMessageBox.alert(r.content, '✨ AI 生成（可复制整理）')
    }
  } finally { aiBusy = false }
}

loadWorks()
</script>

<style scoped>
.chars { height: 100%; display: flex; flex-direction: column; padding: 12px; gap: 12px; }
.chars-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.chars-body { flex: 1; min-height: 0; display: flex; gap: 16px; flex-wrap: wrap; overflow: auto; }
.card-grid { width: 220px; flex: none; display: flex; flex-direction: column; gap: 8px; }
.person-card {
  border: 1px solid #ebeef5; border-radius: 8px; padding: 10px 12px;
  cursor: pointer; background: #fff; transition: all .15s;
}
.person-card.active { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,.15); }
.pc-name { font-weight: 600; }
.pc-identity { font-size: 12px; color: #888; margin-top: 2px; }
.editor-pane { flex: 1; min-width: 260px; background: #fff; border-radius: 8px; padding: 14px; border: 1px solid #ebeef5; }
.editor-actions { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.ok { color: #67c23a; font-size: 13px; }
@media (max-width: 900px) {
  .card-grid { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .person-card { width: calc(50% - 4px); }
}
</style>