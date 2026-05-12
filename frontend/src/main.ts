import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import 'highlight.js/styles/atom-one-dark.css'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'

const app = createApp(App)
app.use(Antd)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
