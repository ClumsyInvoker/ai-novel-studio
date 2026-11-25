<template>
  <div class="workspace">
    <!-- 移动端菜单按钮 -->
    <div class="top-bar">
      <el-dropdown trigger="click" @command="(id)=>onPickWork(Number(id))" style="flex:1;min-width:0">
        <el-button class="work-sel" style="width:100%">
          <span class="work-sel-txt">{{ currentWork?.title || '选择作品' }}</span>
          <span class="caret">▾</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu style="max-height:60vh;overflow:auto">
            <el-dropdown-item v-for="w in works" :key="w.id" :command="w.id">{{ w.title }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button class="menu-btn" @click="showDrawer = true">☰ 章节</el-button>
      <el-button type="primary" @click="workDialog = true">＋ 作品</el-button>
      <el-button v-if="currentWork" size="small" type="danger" plain title="删除当前作品" @click="deleteCurrentWork">🗑</el-button>
    </div>

    <!-- 宽屏章树 -->
    <aside v-if="!isNarrow" class="chapter-col">
      <ChapterTree
        :work="currentWork"
        :active-chapter-id="activeChapterId"
        @open="selectChapter"
        @new="addChapter"
        @new-volume="addVolume"
        @rename-volume="renameVolume"
        @delete-volume="deleteVolume"
        @move-chapter="moveChapter"
      />
    </aside>

    <!-- 窄屏章树抽屉 -->
    <el-drawer v-model="showDrawer" size="78%" title="章节" :with-header="true">
      <ChapterTree
        :work="currentWork"
        :active-chapter-id="activeChapterId"
        @open="(id)=>{selectChapter(id);showDrawer=false}"
        @new="addChapter"
        @new-volume="addVolume"
        @rename-volume="renameVolume"
        @delete-volume="deleteVolume"
        @move-chapter="moveChapter"
      />
    </el-drawer>

    <!-- 主编辑区 -->
    <main class="editor-col">
      <template v-if="activeChapter">
        <div class="editor-head">
          <el-input v-model="activeChapterTitle" size="small" placeholder="章节标题（可编辑）" maxlength="60" class="ch-title-input" @change="scheduleSave" />
          <div class="head-actions">
            <el-button size="small" type="success" @click="addChapter" v-if="isNarrow">＋ 章</el-button>
            <el-dropdown trigger="click" @command="downloadExport">
              <el-button size="small">⬇ 导出</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="txt">TXT 纯文本</el-dropdown-item>
                  <el-dropdown-item command="md">Markdown</el-dropdown-item>
                  <el-dropdown-item command="docx">Word (DOCX)</el-dropdown-item>
                  <el-dropdown-item command="pdf">PDF</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" @click="outlineOpen = true">🧭 大纲</el-button>
            <el-button size="small" @click="aiDraft" :loading="aiLoading">🧩 按章纲扩写</el-button>
            <el-button size="small" @click="openStyle">🎨 风格</el-button>
            <el-button size="small" :loading="aiLoading" @click="consistencyCheck">🔍 校验</el-button>
          </div>
        </div>

        <el-input v-model="activeChapterOutline" placeholder="本章要点 / 章纲（供 AI 参考）" class="outline-input" @change="scheduleSave" />

        <div class="editor-wrap">
          <textarea
            ref="editorRef"
            v-model="activeChapterContent"
            class="editor-textarea"
            placeholder="在这里写作正文……"
            @input="scheduleSave"
          ></textarea>
        </div>

        <div class="editor-foot">
          <span>{{ activeChapter.word_count }} 字</span>
          <span v-if="savedAt" class="saved-at">✓ 已保存</span>
        </div>

        <!-- AI 操作 -->
        <div class="ai-bar">
          <el-input-number v-model="genLen" :min="100" :max="3000" :step="100" size="small" controls-position="right" style="width:110px" />
          <el-button type="warning" size="small" :loading="aiLoading" @click="aiContinue">✍ 续写</el-button>
          <el-button v-if="streaming" size="small" type="danger" @click="stopStream">⏹ 停止</el-button>
          <el-button size="small" :loading="aiLoading" @click="insertToCursor(aiResult)">插入结果</el-button>
        </div>

        <!-- AI 结果区：流式实时显示 -->
        <div v-if="aiResult" class="ai-result" @click="!streaming && insertToCursor(aiResult)">
          <div class="ai-result-head">{{ streaming ? '⏳ 正在生成…（可 ⏹ 停止，完成后点这里插入光标处）' : '📄 AI 结果（点此插入到光标处）' }}</div>
          <div class="ai-result-body">{{ aiResult }}<span v-if="streaming" class="caret-blink">▌</span></div>
        </div>
        <div v-else class="ai-result empty">用上方「✍ 续写」或「🧩 按章纲扩写」让 AI 帮你写。</div>
      </template>
      <el-empty v-else :description="currentWork ? '先在左侧选择或新建一个章节' : '先在上方选择或新建一个作品'" />
    </main>

    <!-- 新建作品弹窗 -->
    <el-dialog v-model="workDialog" title="新建作品" width="92%" append-to-body>
      <!-- AI 灵感 -->
      <div class="inspire">
        <el-input v-model="inspireKeywords" size="small" placeholder="灵感方向/关键词（可选）" style="flex:1;min-width:0" @keyup.enter="aiInspire('keyword')" />
        <el-button size="small" :loading="inspireLoading" @click="aiInspire('random')">🎲 随机</el-button>
        <el-button size="small" type="warning" :loading="inspireLoading" @click="aiInspire('keyword')">✨ 灵感</el-button>
        <el-button size="small" type="danger" plain :loading="inspireLoading" title="抓番茄榜单元数据→AI分析趋势→灵感" @click="aiInspire('hot')">🔥 番茄</el-button>
      </div>
      <div v-if="inspireLoading" class="inspire-tip">AI 构思中…</div>
      <template v-else-if="inspireItem">
        <div class="inspire-head">
          <span>💡 {{ inspireItem.sourced === false ? '（未抓到榜单，已用通用趋势）' : 'AI 灵感（点击可直接填入）' }}</span>
        </div>
        <div class="inspire-raw" @click="useInspire">{{ inspireItem.raw }}</div>
      </template>

      <el-divider style="margin:12px 0" />
      <el-input v-model="newWorkTitle" placeholder="书名" maxlength="40" show-word-limit autofocus @keyup.enter="submitNewWork" />
      <el-input v-model="newIntro" type="textarea" :rows="2" placeholder="简介（可选）" style="margin-top:8px" />
      <el-input v-model="newSetting" type="textarea" :rows="2" placeholder="世界观/设定（可选）" style="margin-top:8px" />
      <template #footer>
        <el-button @click="workDialog = false">取消</el-button>
        <el-button type="primary" @click="submitNewWork">创建</el-button>
      </template>
    </el-dialog>

    <!-- 大纲交互抽屉 -->
    <el-drawer
      v-model="outlineOpen"
      :size="isNarrow ? '100%' : '44%'"
      title="🧭 大纲对话"
      :with-header="true"
      append-to-body
    >
      <OutlinePanel v-if="outlineOpen && currentWork" :work-id="currentWork.id" @created="refreshWork" />
    </el-drawer>

    <!-- 风格卡弹窗 -->
    <el-dialog v-model="styleDialog" title="🎨 文风设定（风格卡）" width="92%" append-to-body>
      <el-input v-model="styleText" type="textarea" :rows="7" maxlength="2000" show-word-limit
        placeholder="描述本书文风，如：节奏紧凑、爽点密集、第三人称、金手指=xx、语言口语化。AI 的续写 / 扩写 / 大纲都会按此风格。留空则用默认。" />
      <div class="style-tip">保存后对本书所有 AI 生成生效，全本文风统一。</div>
      <template #footer>
        <el-button @click="styleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveStyle">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/client.js'
import ChapterTree from '../components/ChapterTree.vue'
import OutlinePanel from '../components/OutlinePanel.vue'

// ---------- 状态 ----------
const works = ref([])
const newWorkTitle = ref('')
const currentWork = ref(null)
const currentWorkId = ref(null)
const activeChapterId = ref(null)
const activeChapter = ref(null)
const activeChapterTitle = ref('')
const activeChapterContent = ref('')
const activeChapterOutline = ref('')
const editorRef = ref(null)
const genLen = ref(500)
const aiLoading = ref(false)
const aiResult = ref('')
const streaming = ref(false)
let abortCtrl = null
const savedAt = ref('')
const showDrawer = ref(false)
const isNarrow = ref(false)

// 新建作品弹窗
const workDialog = ref(false)
const outlineOpen = ref(false)
const newIntro = ref('')
const newSetting = ref('')
const inspireKeywords = ref('')
const inspireLoading = ref(false)
const inspireItem = ref(null)

async function submitNewWork() {
  const title = newWorkTitle.value.trim() || '未命名作品'
  const w = await api.post('/works', { title, intro: newIntro.value, setting: newSetting.value })
  newWorkTitle.value = ''; newIntro.value = ''; newSetting.value = ''
  workDialog.value = false
  await loadWorks()
  await selectWork(w.id)
  ElMessage.success('已创建《' + title + '》')
}

async function aiInspire(mode) {
  inspireLoading.value = true
  inspireItem.value = null
  try {
    const kw = mode === 'random' ? '' : inspireKeywords.value.trim()
    const endpoint = mode === 'hot' ? '/ai/hot-inspired' : '/ai/inspire'
    const r = await api.post(endpoint, { keywords: kw })
    inspireItem.value = r
  } finally { inspireLoading.value = false }
}
async function useInspire() {
  if (!inspireItem.value) return
  newWorkTitle.value = inspireItem.value.title || newWorkTitle.value
  newIntro.value = inspireItem.value.intro || newIntro.value
  newSetting.value = inspireItem.value.setting || newSetting.value
}

// ---------- 作品操作 ----------
async function deleteCurrentWork() {
  if (!currentWork.value) return
  try {
    await ElMessageBox.confirm(`删除作品《${currentWork.value.title}》？其全部卷、章、人物将一并删除，不可恢复！`, '删除作品', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
  } catch { return }
  await api.delete('/works/' + currentWork.value.id)
  ElMessage.success('作品已删除')
  await loadWorks()
  currentWork.value = null; currentWorkId.value = null
  activeChapterId.value = null; activeChapter.value = null
  activeChapterTitle.value = ''; activeChapterContent.value = ''; activeChapterOutline.value = ''
  if (works.value.length) await selectWork(works.value[0].id)
}

const mq = window.matchMedia('(max-width: 900px)')
function onResize() { isNarrow.value = mq.matches }
onMounted(() => { onResize(); mq.addEventListener('change', onResize) })
onBeforeUnmount(() => mq.removeEventListener('change', onResize))

// ---------- 数据加载 ----------
async function loadWorks() {
  works.value = await api.get('/works')
  if (!currentWork && works.value.length) await selectWork(works.value[0].id)
}

async function onPickWork(id) { await selectWork(id) }

async function selectWork(id) {
  currentWork.value = await api.get('/works/' + id)
  currentWorkId.value = id
  const first = currentWork.value.chapters?.[0]
  if (first) await selectChapter(first.id)
  else { activeChapter.value = null; activeChapterContent.value = ''; activeChapterOutline.value = '' }
}

async function selectChapter(id) {
  if (abortCtrl) abortCtrl.abort()   // 切章时中断未完成的续写
  activeChapterId.value = id
  activeChapter.value = await api.get('/chapters/' + id)
  activeChapterTitle.value = activeChapter.value.title
  activeChapterContent.value = activeChapter.value.content
  activeChapterOutline.value = activeChapter.value.outline
}

// ---------- 新建 ----------
async function addChapter() {
  if (!currentWork.value) return ElMessage.warning('先选一个作品')
  const w = currentWork.value
  const ch = await api.post(`/works/${w.id}/chapters`, { title: `第 ${(w.chapters?.length || 0) + 1} 章` })
  w.chapters.push(await api.get('/chapters/' + ch.id))
  await selectChapter(ch.id)
}

// ---------- 导出 ----------
async function downloadExport(fmt) {
  if (!currentWork.value) return
  const blob = await api.get(`/works/${currentWork.value.id}/export?fmt=${fmt}`, { responseType: 'blob' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentWork.value.title}.${fmt}`   // fmt 为 txt / md
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// ---------- 卷管理 ----------
async function refreshWork() {
  currentWork.value = await api.get('/works/' + currentWorkId.value)
}
async function addVolume() {
  if (!currentWork.value) return
  const { value } = await ElMessageBox.prompt('卷名', '新建卷', { inputValue: '第一卷' })
  if (value === null) return
  await api.post(`/works/${currentWork.value.id}/volumes`, { title: value })
  await refreshWork()
}
async function renameVolume(vol) {
  const { value } = await ElMessageBox.prompt('卷名', '重命名卷', { inputValue: vol.title })
  if (value === null) return
  await api.put(`/volumes/${vol.id}`, { title: value, outline: vol.outline || '' })
  await refreshWork()
}
async function deleteVolume(vol) {
  try {
    await ElMessageBox.confirm(`删除卷「${vol.title}」？其中的章节会移出该卷（章节本身不删除）`, '删除卷', { type: 'warning' })
  } catch { return }
  await api.delete(`/volumes/${vol.id}`)
  await refreshWork()
}
async function moveChapter(ch, targetVolId) {
  const volId = (targetVolId === 'none' || targetVolId == null) ? null : targetVolId
  await api.put(`/chapters/${ch.id}`, { volume_id: volId })
  await refreshWork()
}

// ---------- 保存（防抖自动保存）----------
let saveTimer = null
function scheduleSave() { clearTimeout(saveTimer); saveTimer = setTimeout(saveChapter, 700) }
async function saveChapter() {
  if (!activeChapter.value) return
  const updated = await api.put('/chapters/' + activeChapter.value.id, {
    title: activeChapterTitle.value,
    outline: activeChapterOutline.value,
    content: activeChapterContent.value,
    status: activeChapter.value.status
  })
  activeChapter.value = updated
  activeChapterTitle.value = updated.title
  activeChapterContent.value = updated.content
  activeChapterOutline.value = updated.outline
  savedAt.value = true; setTimeout(() => (savedAt.value = false), 2000)
}

// ---------- AI ----------
async function aiContinue() {
  if (!activeChapterContent.value) return ElMessage.warning('先写几行正文再续写')
  aiResult.value = ''; aiLoading.value = true; streaming.value = true
  abortCtrl = new AbortController()
  try {
    const resp = await fetch('/api/ai/continue-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        work_id: currentWork.value.id,
        chapter_id: activeChapter.value.id,
        target_len: genLen.value
      }),
      signal: abortCtrl.signal
    })
    if (!resp.ok || !resp.body) throw new Error('HTTP ' + resp.status)
    const reader = resp.body.getReader()
    const dec = new TextDecoder()
    let buf = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      let i
      while ((i = buf.indexOf('\n\n')) >= 0) {
        const line = buf.slice(0, i).trim(); buf = buf.slice(i + 2)
        if (!line.startsWith('data:')) continue
        const payload = line.slice(5).trim()
        if (payload === '[DONE]') return
        try {
          const d = JSON.parse(payload)
          if (d.error) throw new Error(d.error)
          if (d.text) aiResult.value += d.text
        } catch (e) { if (e.message) throw e }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') ElMessage.error(e.message || '续写中断或失败')
  } finally {
    aiLoading.value = false; streaming.value = false
  }
}
function stopStream() { if (abortCtrl) abortCtrl.abort() }

async function aiDraft() {
  if (!activeChapterOutline.value) return ElMessage.warning('本章还没有章纲，请先在"要点/章纲"里写上')
  aiLoading.value = true; aiResult.value = ''
  try {
    const r = await api.post('/ai/draft', { chapter_id: activeChapter.value.id })
    await selectChapter(activeChapter.value.id)
    ElMessage.success(`章节已生成并写回（${r.content.length} 字）`)
    // 不填 aiResult：正文已写回编辑器，避免点"插入结果"再重复插入一次
  } finally { aiLoading.value = false }
}

async function aiOutline() {
  if (!currentWork.value) return
  aiLoading.value = true
  try {
    const r = await api.post('/ai/outline', { work_id: currentWork.value.id })
    aiResult.value = r.content
  } finally { aiLoading.value = false }
}

function insertToCursor(text) { insertText(text) }
function insertText(text) {
  if (!text) return
  const ta = editorRef.value
  const content = ta ? activeChapterContent.value : activeChapterContent.value
  const start = ta ? (ta.selectionStart ?? content.length) : content.length
  const end = ta ? (ta.selectionEnd ?? start) : start
  activeChapterContent.value = content.slice(0, start) + text + content.slice(end)
  scheduleSave()
  nextTick(() => { if (ta) { try { ta.setSelectionRange(start + text.length, start + text.length); ta.focus() } catch {} } })
}

// ---------- 风格卡 ----------
const styleDialog = ref(false)
const styleText = ref('')
function openStyle() {
  if (!currentWork.value) return
  styleText.value = currentWork.value.style || ''
  styleDialog.value = true
}
async function saveStyle() {
  await api.put('/works/' + currentWork.value.id, { ...currentWork.value, style: styleText.value })
  currentWork.value.style = styleText.value
  styleDialog.value = false
  ElMessage.success('🎨 风格已保存，对本作 AI 生成生效')
}
// ---------- 一致性校验 ----------
async function consistencyCheck() {
  if (!activeChapterContent.value) return ElMessage.warning('先写正文再校验')
  aiLoading.value = true
  try {
    const r = await api.post('/ai/consistency-check', {
      work_id: currentWork.value.id, chapter_id: activeChapter.value.id })
    ElMessageBox.alert(r.content, '🔍 一致性校验结果', { confirmButtonText: '知道了' })
  } finally { aiLoading.value = false }
}

loadWorks()
</script>

<style scoped>
.workspace { height: 100%; display: flex; flex-direction: column; }
.top-bar { display: flex; gap: 8px; padding: 10px 12px; background: #fff; border-bottom: 1px solid #e6e8eb; align-items: center; flex-wrap: wrap; }
.work-sel { display: flex; justify-content: space-between; align-items: center; }
.work-sel-txt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; text-align: left; }
.caret { margin-left: 6px; color: #888; }
.menu-btn { display: none; }

.chapter-col {
  width: 260px; flex: none; background: #fff;
  border-right: 1px solid #e6e8eb; overflow: auto; height: 100%;
}
.editor-col { flex: 1; min-width: 0; display: flex; flex-direction: column; padding: 12px 14px; }
.editor-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 6px; }
.ch-title-input { flex: 1; max-width: 320px; min-width: 120px; }
.head-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.style-tip { font-size: 12px; color: #909399; margin-top: 6px; }
.outline-input { margin-bottom: 8px; }
.editor-wrap { flex: 1; min-height: 0; }
.editor-foot { color: #999; font-size: 12px; display: flex; gap: 12px; margin: 4px 0; }
.ai-bar { display: flex; align-items: center; gap: 8px; margin: 6px 0; flex-wrap: wrap; }
.ai-result {
  background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px;
  max-height: 40vh; overflow: auto; cursor: pointer;
}
.ai-result-head { padding: 8px 12px; font-size: 12px; color: #b8860b; border-bottom: 1px dashed #ffe58f; }
.ai-result-body { padding: 10px 12px; font-size: 14px; line-height: 1.8; white-space: pre-wrap; }
.ai-result.empty { background: #f7f8fa; border-color: #ebeef5; color: #a0a3a8; cursor: default; padding: 14px; text-align: center; }
.ai-result.loading { background: #ecf5ff; border-color: #d9ecff; color: #409eff; padding: 14px; text-align: center; }
.caret-blink { animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }

.inspire { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.inspire-tip { color: #909399; font-size: 13px; margin-top: 8px; }
.inspire-head { margin-top: 8px; font-size: 13px; color: #b8860b; }
.inspire-raw {
  background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px;
  padding: 8px 10px; font-size: 13px; line-height: 1.6; white-space: pre-wrap;
  margin-top: 4px; cursor: pointer; max-height: 140px; overflow: auto; color: #5a4a1a;
}

@media (max-width: 900px) {
  .chapter-col { display: none; }
  .menu-btn { display: inline-flex; }
  .editor-col { padding: 10px; }
  .workspace { display: flex; flex-direction: column; }
}
</style>