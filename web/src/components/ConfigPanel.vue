<template>
  <div class="config-panel">
    <h3>系统配置</h3>

    <div class="config-group">
      <label>Embedding 模型</label>
      <select v-model="form.embedding_model">
        <option v-for="m in options.embedding_models" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>

    <div class="config-group">
      <label>
        <input type="checkbox" v-model="form.enable_rerank" /> 启用 Rerank
      </label>
      <select v-if="form.enable_rerank" v-model="form.rerank_model" class="sub-select">
        <option v-for="m in options.rerank_models" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>

    <div class="config-group">
      <label>
        <input type="checkbox" v-model="form.use_vector" /> 向量检索
      </label>
      <div v-if="form.use_vector" class="sub-field">
        <label>top_k_vector</label>
        <input type="number" v-model.number="form.top_k_vector" min="1" max="50" />
      </div>
    </div>

    <div class="config-group">
      <label>
        <input type="checkbox" v-model="form.use_bm25" /> BM25 检索
      </label>
      <div v-if="form.use_bm25" class="sub-field">
        <label>top_k_bm25</label>
        <input type="number" v-model.number="form.top_k_bm25" min="1" max="50" />
      </div>
    </div>

    <div class="config-group" v-if="form.use_vector && form.use_bm25">
      <label>RRF K 参数</label>
      <input type="number" v-model.number="form.rrf_k" min="1" max="200" />
    </div>

    <div class="config-group">
      <label>LLM 模型</label>
      <input type="text" v-model="form.llm_model" />
    </div>

    <div class="config-group">
      <label>Temperature: {{ form.llm_temperature }}</label>
      <input type="range" v-model.number="form.llm_temperature" min="0" max="2" step="0.1" />
    </div>

    <div class="config-group">
      <label>Max Tokens</label>
      <input type="number" v-model.number="form.llm_max_tokens" min="256" max="32768" step="256" />
    </div>

    <div class="config-group">
      <label>默认标签</label>
      <select v-model="form.default_tag">
        <option v-for="t in options.tags" :key="t" :value="t">{{ t }}</option>
      </select>
    </div>

    <button class="btn-primary" @click="$emit('apply', { ...form })" :disabled="loading">
      {{ loading ? '应用中...' : '应用配置' }}
    </button>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  current: { type: Object, required: true },
  options: { type: Object, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['apply'])

const form = reactive({ ...props.current })

watch(() => props.current, (val) => {
  Object.assign(form, val)
}, { deep: true })
</script>

<style scoped>
.config-panel {
  padding: 16px;
  overflow-y: auto;
  height: 100%;
}
.config-panel h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1a1a2e;
  border-bottom: 2px solid #4361ee;
  padding-bottom: 8px;
}
.config-group {
  margin-bottom: 14px;
}
.config-group > label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}
.config-group input[type="checkbox"] {
  margin-right: 6px;
}
.config-group select,
.config-group input[type="text"],
.config-group input[type="number"] {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  box-sizing: border-box;
}
.config-group input[type="range"] {
  width: 100%;
}
.sub-select {
  margin-top: 6px;
}
.sub-field {
  margin-top: 6px;
  padding-left: 20px;
}
.sub-field label {
  font-size: 12px;
  color: #666;
}
.sub-field input {
  width: 80px;
}
.btn-primary {
  width: 100%;
  padding: 8px;
  background: #4361ee;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 8px;
}
.btn-primary:hover {
  background: #3a56d4;
}
.btn-primary:disabled {
  background: #999;
  cursor: not-allowed;
}
</style>
