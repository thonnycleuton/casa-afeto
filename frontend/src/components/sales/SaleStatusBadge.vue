<script setup lang="ts">
import { computed } from 'vue'
import type { SaleStatus } from '../../api/types'

const props = defineProps<{
  status: SaleStatus
}>()

const statusClass = computed(() => {
  switch (props.status) {
    case 'RASCUNHO':
      return 'badge-rascunho'
    case 'CONFIRMADA':
      return 'badge-confirmada'
    case 'EM PREPARAÇÃO':
      return 'badge-preparacao'
    case 'PRONTA':
      return 'badge-pronta'
    case 'ENTREGUE':
      return 'badge-entregue'
    case 'CANCELADA':
      return 'badge-cancelada'
    default:
      return 'badge-default'
  }
})
</script>

<template>
  <span :class="['sale-status-badge', statusClass]">
    <span class="badge-dot"></span>
    <span>{{ status }}</span>
  </span>
</template>

<style scoped>
.sale-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 9px;
  min-height: 24px;
  border-radius: var(--radius-pill);
  border: 1px solid transparent;
  font-size: var(--font-size-xs);
  font-weight: 600;
  white-space: nowrap;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.badge-rascunho {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border-color: var(--color-border);
}
.badge-rascunho .badge-dot {
  background: var(--color-text-disabled);
}

.badge-confirmada {
  background: var(--color-sale-badge-primary-bg);
  color: var(--color-primary);
  border-color: var(--color-sale-badge-primary-border);
}
.badge-confirmada .badge-dot {
  background: var(--color-primary);
}

.badge-preparacao {
  background: var(--color-sale-badge-warning-bg);
  color: var(--color-warning);
  border-color: var(--color-sale-badge-warning-border);
}
.badge-preparacao .badge-dot {
  background: var(--color-warning);
}

.badge-pronta {
  background: var(--color-sale-badge-primary-bg);
  color: var(--color-primary);
  border-color: var(--color-sale-badge-primary-border);
}
.badge-pronta .badge-dot {
  background: var(--color-primary);
}

.badge-entregue {
  background: var(--color-sale-badge-success-bg);
  color: var(--color-success);
  border-color: var(--color-sale-badge-success-border);
}
.badge-entregue .badge-dot {
  background: var(--color-success);
}

.badge-cancelada {
  background: var(--color-sale-badge-error-bg);
  color: var(--color-error);
  border-color: var(--color-sale-badge-error-border);
}
.badge-cancelada .badge-dot {
  background: var(--color-error);
}
</style>
