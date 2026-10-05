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
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8125rem;
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
  background: rgba(16, 185, 129, 0.12);
  color: #065f46;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.online .status-dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

.status-badge.offline {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-badge.offline .status-dot {
  background: #ef4444;
}

.status-badge.loading {
  background: rgba(245, 158, 11, 0.12);
  color: #92400e;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-badge.loading .status-dot {
  background: #f59e0b;
  animation: pulse 1.5s infinite;
}

.status-badge.idle {
  background: rgba(148, 163, 184, 0.15);
  color: #475569;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.status-badge.idle .status-dot {
  background: #94a3b8;
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
