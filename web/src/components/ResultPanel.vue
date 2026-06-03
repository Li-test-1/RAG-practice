<template>
  <div class="result-panel" v-if="result">
    <div class="section answer-section">
      <h3>回答</h3>
      <div class="answer-content">{{ result.answer }}</div>
    </div>

    <div class="section">
      <h3 @click="showDocs = !showDocs" class="clickable">
        引用文档 ({{ result.context_documents.length }})
        <span class="toggle">{{ showDocs ? '▼' : '▶' }}</span>
      </h3>
      <div v-if="showDocs" class="docs-list">
        <div v-for="(doc, i) in result.context_documents" :key="i" class="doc-card">
          <div class="doc-header">
            <span class="doc-index">#{{ i + 1 }}</span>
            <span class="doc-source">{{ doc.source_file }}</span>
            <span class="doc-heading" v-if="doc.heading">{{ doc.heading }}</span>
            <span class="doc-tag" v-if="doc.tag">{{ doc.tag }}</span>
          </div>
          <div class="doc-scores">
            <span class="score-badge rrf" v-if="doc.rrf_score != null">
              RRF: {{ doc.rrf_score.toFixed(4) }}
            </span>
            <span class="score-badge rerank" v-if="doc.rerank_score != null">
              Rerank: {{ doc.rerank_score.toFixed(4) }}
            </span>
          </div>
          <div class="doc-text">
            <pre>{{ doc.text_content }}</pre>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3 @click="showPrompt = !showPrompt" class="clickable">
        完整提示词
        <span class="toggle">{{ showPrompt ? '▼' : '▶' }}</span>
      </h3>
      <div v-if="showPrompt" class="prompt-viewer">
        <div class="prompt-block">
          <h4>System Prompt</h4>
          <pre>{{ result.system_prompt }}</pre>
        </div>
        <div class="prompt-block">
          <h4>User Prompt</h4>
          <pre>{{ result.user_prompt }}</pre>
        </div>
      </div>
    </div>
  </div>

  <div class="result-panel empty" v-else>
    <div class="empty-hint">
      <p>请在上方输入问题并点击查询</p>
      <p class="sub">查询结果将在此展示，包括回答、引用片段和提示词</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  result: { type: Object, default: null },
})

const showDocs = ref(true)
const showPrompt = ref(false)
</script>

<style scoped>
.result-panel {
  padding: 16px;
}
.section {
  margin-bottom: 20px;
}
.section h3 {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #1a1a2e;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}
.clickable {
  cursor: pointer;
  user-select: none;
}
.clickable:hover {
  color: #4361ee;
}
.toggle {
  font-size: 12px;
  margin-left: 6px;
}
.answer-section {
  background: #f0f4ff;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #4361ee;
}
.answer-content {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14px;
  color: #333;
}
.docs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.doc-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}
.doc-header {
  background: #f8f9fa;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13px;
}
.doc-index {
  font-weight: 700;
  color: #4361ee;
}
.doc-source {
  color: #555;
  font-weight: 600;
}
.doc-heading {
  color: #888;
}
.doc-tag {
  background: #e8f0fe;
  color: #4361ee;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
}
.doc-scores {
  padding: 4px 12px;
  display: flex;
  gap: 8px;
}
.score-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.score-badge.rrf {
  background: #fff3e0;
  color: #e65100;
}
.score-badge.rerank {
  background: #e8f5e9;
  color: #2e7d32;
}
.doc-text {
  padding: 8px 12px;
}
.doc-text pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
  color: #444;
  font-family: inherit;
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}
.prompt-viewer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.prompt-block h4 {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: #666;
}
.prompt-block pre {
  margin: 0;
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}
.empty-hint {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}
.empty-hint p {
  margin: 4px 0;
}
.empty-hint .sub {
  font-size: 13px;
}
</style>
