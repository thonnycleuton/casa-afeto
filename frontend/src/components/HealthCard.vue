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
        <h3>Conexão com a API do servidor</h3>
        <p class="subtitle">Comunicação com o serviço REST do FastAPI</p>
      </div>
      <StatusBadge
        :status="loading ? 'loading' : error ? 'offline' : health ? 'online' : 'idle'"
        :label="loading ? 'Verificando...' : error ? 'Desconectado' : health ? 'Conectado' : 'Desconhecido'"
      />
    </div>

    <div v-if="loading" class="card-state">
      <div class="spinner"></div>
      <span>Verificando a comunicação com a API...</span>
    </div>

    <div v-else-if="error" class="card-state error-state">
      <div class="error-icon">!</div>
      <div>
        <p class="error-title">Não foi possível acessar a API do servidor</p>
        <p class="error-detail">{{ error }}</p>
      </div>
    </div>

    <div v-else-if="health" class="health-details">
      <div class="detail-row">
        <span class="detail-label">Situação</span>
        <span class="detail-value status-ok">{{ health.status.toUpperCase() }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Projeto</span>
        <span class="detail-value">{{ health.project_name }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Ambiente</span>
        <span class="detail-value badge-env">{{ health.environment }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button class="btn-refresh" :disabled="loading" @click="emit('refresh')">
        {{ loading ? 'Verificando...' : 'Verificar conexão' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.health-card {
  background: var(--color-health-card-bg);
  border: 1px solid var(--color-health-card-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--color-health-card-shadow);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.health-card:hover {
  border-color: var(--color-health-card-hover-border);
  box-shadow: var(--color-health-card-hover-shadow);
}

.health-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

.header-info h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

.subtitle {
  margin: var(--space-1) 0 0 0;
  font-size: var(--font-size-base);
  color: var(--color-text-muted);
}

.card-state {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-health-card-state-bg);
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
}

.error-state {
  background: var(--color-health-card-error-bg);
  color: var(--color-health-card-error-text);
  border: 1px solid var(--color-health-card-error-border);
}

.error-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-health-card-error-icon-bg);
  color: var(--color-health-card-error-icon-text);
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
  margin: var(--space-1) 0 0 0;
  font-size: var(--font-size-sm);
  opacity: 0.9;
}

.health-details {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  background: var(--color-health-card-details-bg);
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-health-card-details-border);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-base);
}

.detail-label {
  color: var(--color-health-card-label-text);
  font-weight: 500;
}

.detail-value {
  color: var(--color-health-card-value-text);
  font-weight: 600;
}

.status-ok {
  color: var(--color-health-card-status-ok);
}

.badge-env {
  background: var(--color-health-card-env-bg);
  color: var(--color-health-card-env-text);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-refresh {
  background: var(--color-health-card-btn-bg);
  color: var(--color-health-card-btn-text);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--color-health-card-btn-hover-bg);
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-health-card-spinner-border);
  border-top-color: var(--color-health-card-spinner-top);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
