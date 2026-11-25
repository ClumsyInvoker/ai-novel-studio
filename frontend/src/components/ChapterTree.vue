<template>
  <div class="tree">
    <div class="tree-head">
      <span class="tree-title">📚 章节</span>
      <div class="ops">
        <el-button size="small" plain type="primary" @click="emit('newVolume')">＋ 卷</el-button>
        <el-button size="small" type="success" @click="emit('new')">＋ 章</el-button>
      </div>
    </div>

    <el-menu
      v-if="props.work"
      :default-active="String(activeChapterId)"
      class="chapter-menu"
      @select="(k)=>emit('open', Number(k))"
      background-color="transparent"
    >
      <!-- 卷分组 -->
      <el-sub-menu v-for="vol in volumes" :key="vol.id" :index="'vol-'+vol.id">
        <template #title>
          <span class="vol-title">▍{{ vol.title }}</span>
          <span class="vol-more" @click.stop>
            <el-dropdown trigger="click" @command="(cmd)=>onVolCmd(cmd, vol)">
              <span class="dot">⋯</span>
              <template #dropdown>
                <el-dropdown-item command="rename">重命名卷</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除卷</el-dropdown-item>
              </template>
            </el-dropdown>
          </span>
        </template>

        <el-menu-item v-for="ch in chaptersIn(vol.id)" :key="ch.id" :index="String(ch.id)">
          <span class="ch-name" :class="{ done: ch.status==='done' }">{{ ch.title }}</span>
          <span class="ch-move" @click.stop>
            <el-dropdown trigger="click" @command="(v)=>emit('moveChapter', ch, v)">
              <span class="dot" title="移到卷">📁</span>
              <template #dropdown>
                <el-dropdown-item command="none">移出卷</el-dropdown-item>
                <el-dropdown-item v-for="ov in volumes" :key="ov.id" v-if="ov.id !== vol.id" :command="ov.id">{{ ov.title }}</el-dropdown-item>
              </template>
            </el-dropdown>
          </span>
          <span class="wcnt" v-if="ch.word_count">{{ ch.word_count }}</span>
        </el-menu-item>
      </el-sub-menu>

      <!-- 未分组章节 -->
      <el-menu-item v-for="ch in noVolumeChapters" :key="ch.id" :index="String(ch.id)">
        <span class="ch-name" :class="{ done: ch.status==='done' }">{{ ch.title }}</span>
        <span class="ch-move" @click.stop>
          <el-dropdown trigger="click" @command="(v)=>emit('moveChapter', ch, v)">
            <span class="dot" title="移到卷">📁</span>
            <template #dropdown>
              <el-dropdown-item command="none">移出卷</el-dropdown-item>
              <el-dropdown-item v-for="ov in volumes" :key="ov.id" :command="ov.id">{{ ov.title }}</el-dropdown-item>
            </template>
          </el-dropdown>
        </span>
        <span class="wcnt" v-if="ch.word_count">{{ ch.word_count }}</span>
      </el-menu-item>
    </el-menu>
    <el-empty v-else description="暂无章节" :image-size="60" />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  work: Object,
  activeChapterId: [Number, null]
})
const emit = defineEmits(['open', 'new', 'newVolume', 'renameVolume', 'deleteVolume', 'moveChapter'])

const volumes = computed(() => props.work?.volumes || [])
const chaptersIn = (volId) => (props.work?.chapters || []).filter(c => c.volume_id === volId)
const noVolumeChapters = computed(() => (props.work?.chapters || []).filter(c => !c.volume_id))

function onVolCmd(cmd, vol) {
  if (cmd === 'rename') emit('renameVolume', vol)
  else if (cmd === 'delete') emit('deleteVolume', vol)
}
</script>

<style scoped>
.tree { display: flex; flex-direction: column; height: 100%; }
.tree-head { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
.tree-title { font-weight: 600; }
.ops { display: flex; gap: 6px; }
.chapter-menu { flex: 1; overflow: auto; border: none; }
.vol-title { font-size: 13px; color: #444; font-weight: 500; }
.vol-more { float: right; }
.dot { padding: 0 4px; cursor: pointer; color: #888; }
.ch-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 130px; }
.ch-move { float: right; }
.ch-name.done { text-decoration: line-through; color: #aaa; }
.wcnt { float: right; color: #999; font-size: 12px; margin-left: 6px; }
</style>