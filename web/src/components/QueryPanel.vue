<template>
  <div class="query-panel">
    <h3>知识库问答</h3>
    <textarea
      v-model="question"
      placeholder="请输入您的问题..."
      rows="3"
      @keydown.ctrl.enter="handleQuery"
    ></textarea>
    <div class="query-options">
      <div class="option-field">
        <label>Top K</label>
        <input type="number" v-model.number="topK" min="1" max="20" />
      </div>
      <div class="option-field">
        <label>标签过滤</label>
        <select v-model="tagFilter">
          <option :value="null">全部</option>
          <option v-for="t in tags" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
    </div>
    <button class="btn-query" @click="handleQuery" :disabled="loading || !question.trim()">
      {{ loading ? '查询中...' : '查询 (Ctrl+Enter)' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  tags: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['query'])

const question = ref('')
const topK = ref(5)
const tagFilter = ref(null)

function handleQuery() {
  if (!question.value.trim() || props.loading) return
  emit('query', {
    question: question.value.trim(),
    topK: topK.value,
    tagFilter: tagFilter.value,
  })
}
</script>

<style scoped>
.query-panel {
  padding: 16px;
}
.query-panel h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #1a1a2e;
}
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
}
textarea:focus {
  outline: none;
  border-color: #4361ee;
}
.query-options {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}
.option-field {
  display: flex;
  align-items: center;
  gap: 6px;
}
.option-field label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}
.option-field input,
.option-field select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}
.option-field input {
  width: 60px;
}
.btn-query {
  margin-top: 12px;
  padding: 10px 24px;
  background: #4361ee;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.btn-query:hover {
  background: #3a56d4;
}
.btn-query:disabled {
  background: #999;
  cursor: not-allowed;
}
</style>
