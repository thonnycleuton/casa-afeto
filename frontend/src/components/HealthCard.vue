<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'
import type { HealthResponse } from '../api/types'

defineProps<{
  health: HealthResponse | null
  loading: boolean
  error: string | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()
</script>

<template>
  <div class="health-card">
    <div class="health-card-header">
      <div class="header-info">
        <h3>Backend API Connection</h3>
        <p class="subtitle">FastAPI REST service communication</p>
      </div>
      <StatusBadge
        :status="loading ? 'loading' : error ? 'offline' : health ? 'online' : 'idle'"
        :label="loading ? 'Checking...' : error ? 'Disconnected' : health ? 'Connected' : 'Unknown'"
      />
    </div>

    <div v-if="loading" class="card-state">
      <div class="spinner"></div>
      <span>Verifying API communication...</span>
    </div>

    <div v-else-if="error" class="card-state error-state">
      <div class="error-icon">!</div>
      <div>
        <p class="error-title">Cannot reach backend API</p>
        <p class="error-detail">{{ error }}</p>
      </div>
    </div>

    <div v-else-if="health" class="health-details">
      <div class="detail-row">
        <span class="detail-label">Status</span>
        <span class="detail-value status-ok">{{ health.status.toUpperCase() }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Project</span>
        <span class="detail-value">{{ health.project_name }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Environment</span>
        <span class="detail-value badge-env">{{ health.environment }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button class="btn-refresh" :disabled="loading" @click="emit('refresh')">
        {{ loading ? 'Checking...' : 'Check Connection' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.health-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.health-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.health-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.header-info h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: #1e293b;
}

.subtitle {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: #64748b;
}

.card-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  background: #f8fafc;
  color: #475569;
  font-size: 0.875rem;
}

.error-state {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.error-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.error-title {
  margin: 0;
  font-weight: 600;
}

.error-detail {
  margin: 0.25rem 0 0 0;
  font-size: 0.8125rem;
  opacity: 0.9;
}

.health-details {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  background: #f8fafc;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #f1f5f9;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.detail-label {
  color: #64748b;
  font-weight: 500;
}

.detail-value {
  color: #1e293b;
  font-weight: 600;
}

.status-ok {
  color: #059669;
}

.badge-env {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.15rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-refresh {
  background: #4f46e5;
  color: #ffffff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #cbd5e1;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
