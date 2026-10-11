<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'online' | 'offline' | 'loading' | 'idle'
  label?: string
}>()

const displayLabel = computed(
  () =>
    props.label ??
    {
      online: 'Conectado',
      offline: 'Desconectado',
      loading: 'Carregando',
      idle: 'Aguardando',
    }[props.status],
)
</script>

<template>
  <span :class="['status-badge', status]">
    <span class="status-dot"></span>
    <span class="status-text">{{ displayLabel }}</span>
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-pill);
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-transform: capitalize;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-badge.online {
  background: var(--color-status-badge-online-bg);
  color: var(--color-status-badge-online-text);
  border: 1px solid var(--color-status-badge-online-border);
}

.status-badge.online .status-dot {
  background: var(--color-success);
  box-shadow: var(--color-status-badge-online-dot-shadow);
}

.status-badge.offline {
  background: var(--color-status-badge-offline-bg);
  color: var(--color-status-badge-offline-text);
  border: 1px solid var(--color-status-badge-offline-border);
}

.status-badge.offline .status-dot {
  background: var(--color-error);
}

.status-badge.loading {
  background: var(--color-status-badge-loading-bg);
  color: var(--color-status-badge-loading-text);
  border: 1px solid var(--color-status-badge-loading-border);
}

.status-badge.loading .status-dot {
  background: var(--color-warning);
  animation: pulse 1.5s infinite;
}

.status-badge.idle {
  background: var(--color-status-badge-idle-bg);
  color: var(--color-status-badge-idle-text);
  border: 1px solid var(--color-status-badge-idle-border);
}

.status-badge.idle .status-dot {
  background: var(--color-text-disabled);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(0.85);
  }
}
</style>
