<template>
  <div class="app">
    <header class="app-header">
      <h1>RAG-ljy 企业知识库问答系统</h1>
    </header>
    <div class="app-body">
      <aside class="sidebar">
        <ConfigPanel
          :current="config"
          :options="options"
          :loading="configLoading"
          @apply="handleApplyConfig"
        />
      </aside>
      <main class="main-content">
        <QueryPanel
          :tags="options.tags"
          :loading="queryLoading"
          @query="handleQuery"
        />
        <ResultPanel :result="queryResult" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig, query, getTags } from './api/index.js'
import ConfigPanel from './components/ConfigPanel.vue'
import QueryPanel from './components/QueryPanel.vue'
import ResultPanel from './components/ResultPanel.vue'

const config = ref({})
const options = ref({ embedding_models: [], rerank_models: [], tags: [] })
const configLoading = ref(false)
const queryLoading = ref(false)
const queryResult = ref(null)

async function loadConfig() {
  try {
    const data = await getConfig()
    config.value = data.current
    options.value = data.options
  } catch (e) {
    console.error('Failed to load config:', e)
  }
}

async function handleApplyConfig(form) {
  configLoading.value = true
  try {
    const data = await updateConfig(form)
    config.value = data.current
  } catch (e) {
    console.error('Failed to update config:', e)
  } finally {
    configLoading.value = false
  }
}

async function handleQuery({ question, topK, tagFilter }) {
  queryLoading.value = true
  queryResult.value = null
  try {
    const data = await query(question, topK, tagFilter)
    queryResult.value = data
  } catch (e) {
    console.error('Query failed:', e)
    queryResult.value = { answer: '查询失败: ' + e.message, context_documents: [], system_prompt: '', user_prompt: '' }
  } finally {
    queryLoading.value = false
  }
}

onMounted(loadConfig)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #4361ee 100%);
  color: #fff;
  padding: 14px 24px;
}
.app-header h1 {
  font-size: 18px;
  font-weight: 600;
}
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  background: #fff;
}
</style>
