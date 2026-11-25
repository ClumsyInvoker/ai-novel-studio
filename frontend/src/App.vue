<template>
  <div class="app-shell">
    <!-- 顶部栏：移动端友好 -->
    <header class="app-bar">
      <div class="app-title">📖 AI 网文写作助手</div>
      <nav class="app-nav">
        <router-link to="/" class="nav-link" active-class="active">工作台</router-link>
        <router-link to="/characters" class="nav-link" active-class="active">人物</router-link>
        <router-link to="/settings" class="nav-link" active-class="active">设置</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-shell { height: 100%; display: flex; flex-direction: column; }
.app-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 14px; height: 50px; flex: none;
  background: #fff; border-bottom: 1px solid #e6e8eb;
}
.app-title { font-weight: 700; font-size: 16px; }
.app-nav { display: flex; gap: 4px; }
.nav-link {
  padding: 6px 12px; border-radius: 16px; text-decoration: none;
  color: #555; font-size: 14px;
}
.nav-link.active { background: #409eff; color: #fff; }
.app-main { flex: 1; min-height: 0; }
@media (max-width: 900px) {
  .app-title { font-size: 14px; }
  .nav-link { padding: 5px 10px; font-size: 13px; }
}
</style>