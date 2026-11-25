import { createRouter, createWebHashHistory } from 'vue-router'
import Workspace from '../views/Workspace.vue'
import Characters from '../views/Characters.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'workspace', component: Workspace },
    { path: '/characters', name: 'characters', component: Characters },
    { path: '/settings', name: 'settings', component: Settings }
  ]
})

export default router