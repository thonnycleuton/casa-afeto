<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { InventoryMovement, Product } from '../../api/types'

const props = defineProps<{
  open: boolean
  product: Product | null
  movements: InventoryMovement[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'entry', quantity: string, unitCost: string | null): void
  (e: 'adjustment', quantity: string): void
}>()

const entryQuantity = ref('')
const entryUnitCost = ref('')
const adjustmentQuantity = ref('')
const entryError = ref('')
const adjustmentError = ref('')

const entryQuantityError = computed(() => {
  if (!entryQuantity.value) return ''
  const num = Number(entryQuantity.value)
  if (isNaN(num) || num <= 0) return 'Informe uma quantidade maior que zero.'
  return ''
})

const entryCostError = computed(() => {
  if (!entryUnitCost.value.trim()) return ''
  const val = entryUnitCost.value.trim()
  const num = Number(val)
  if (isNaN(num) || num < 0) return 'Informe um valor maior ou igual a zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  return ''
})

const adjustmentQuantityError = computed(() => {
  if (!adjustmentQuantity.value) return ''
  const num = Number(adjustmentQuantity.value)
  if (isNaN(num) || num === 0) return 'Informe um valor diferente de zero.'
  return ''
})

watch(
  () => [props.open, props.product],
  ([isOpen]) => {
    if (isOpen) {
      entryQuantity.value = ''
      entryUnitCost.value = ''
      adjustmentQuantity.value = ''
      entryError.value = ''
      adjustmentError.value = ''
    }
  },
)

function formatQuantity(value: string): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, integer, fraction] = match
  const groupedInteger = new Intl.NumberFormat('pt-BR').format(BigInt(integer))
  return `${sign}${groupedInteger}${fraction ? `,${fraction}` : ''}`
}

function formatCurrency(value: string | null | undefined): string {
  if (!value) return '—'
  const num = Number(value)
  if (isNaN(num)) return value
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function submitEntry(): void {
  if (entryQuantityError.value) return
  if (entryCostError.value) return
  emit('entry', entryQuantity.value, entryUnitCost.value.trim() || null)
  entryQuantity.value = ''
  entryUnitCost.value = ''
}

function submitAdjustment(): void {
  if (adjustmentQuantityError.value) return
  emit('adjustment', adjustmentQuantity.value)
  adjustmentQuantity.value = ''
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="product ? `Estoque — ${product.name}` : 'Estoque'"
    width="700px"
  >
    <template #body>
      <div v-if="product" class="inventory-header">
        <div class="inventory-balance">
          <span class="balance-label">Saldo atual</span>
          <strong>{{ formatQuantity(product.inventory_balance) }} {{ product.base_unit }}</strong>
        </div>
        <span v-if="product.average_cost" class="field-hint">
          Custo médio: {{ formatCurrency(product.average_cost) }}
        </span>
        <span :class="['status-pill', product.active ? 'status-success' : 'status-muted']">
          <span class="status-dot" aria-hidden="true"></span>
          {{ product.active ? 'Ativo' : 'Inativo' }}
        </span>
      </div>

      <div v-if="product" class="inventory-operations">
        <form class="card operation-card" @submit.prevent="submitEntry">
          <div class="card-heading">
            <div>
              <h2>Registrar entrada</h2>
              <p>Uma entrada aumenta o saldo disponível.</p>
            </div>
          </div>
          <div class="form-group">
            <label for="inv-entry-qty">Quantidade ({{ product.base_unit }})</label>
            <input
              id="inv-entry-qty"
              v-model="entryQuantity"
              type="number"
              :step="product.base_unit === 'UN' ? '1' : 'any'"
              min="0"
              required
              class="form-input"
              :class="{ 'form-input-error': entryQuantityError }"
            />
            <p v-if="entryQuantityError" class="field-error">{{ entryQuantityError }}</p>
          </div>
          <div class="form-group">
            <label for="inv-entry-cost">Custo unitário (R$, opcional)</label>
            <input
              id="inv-entry-cost"
              v-model="entryUnitCost"
              type="text"
              inputmode="decimal"
              placeholder="Opcional (ex.: 15.50)"
              class="form-input"
              :class="{ 'form-input-error': entryCostError }"
            />
            <p v-if="entryCostError" class="field-error">{{ entryCostError }}</p>
            <p v-else class="field-hint">Usado no cálculo do custo médio ponderado.</p>
          </div>
          <button class="button primary" type="submit" :disabled="!product.active">
            Registrar entrada
          </button>
          <p v-if="!product.active" class="field-hint">Reative este produto para alterar o estoque.</p>
        </form>

        <form class="card operation-card" @submit.prevent="submitAdjustment">
          <div class="card-heading">
            <div>
              <h2>Ajustar estoque</h2>
              <p>Use um valor positivo para aumentar ou negativo para reduzir.</p>
            </div>
          </div>
          <div class="form-group">
            <label for="inv-adjust-qty">Quantidade com sinal ({{ product.base_unit }})</label>
            <input
              id="inv-adjust-qty"
              v-model="adjustmentQuantity"
              type="number"
              :step="product.base_unit === 'UN' ? '1' : 'any'"
              required
              class="form-input"
              :class="{ 'form-input-error': adjustmentQuantityError }"
            />
            <p v-if="adjustmentQuantityError" class="field-error">{{ adjustmentQuantityError }}</p>
          </div>
          <button class="button primary" type="submit" :disabled="!product.active">
            Registrar ajuste
          </button>
          <p v-if="!product.active" class="field-hint">Reative este produto para alterar o estoque.</p>
        </form>
      </div>

      <div v-if="movements.length" class="card table-card">
        <div class="table-heading">
          <div>
            <h2>Histórico de movimentações</h2>
            <p>Entradas e ajustes registrados.</p>
          </div>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Data e hora</th>
                <th>Tipo</th>
                <th class="numeric">Quantidade</th>
                <th>Custo un.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="movement in movements" :key="movement.id">
                <td>{{ new Date(movement.created_at).toLocaleString('pt-BR') }}</td>
                <td>
                  <span :class="['movement-pill', movement.type === 'ENTRY' ? 'movement-entry' : 'movement-adjustment']">
                    {{ movement.type === 'ENTRY' ? 'Entrada' : 'Ajuste' }}
                  </span>
                </td>
                <td class="numeric">{{ formatQuantity(movement.quantity) }} {{ product?.base_unit }}</td>
                <td>{{ movement.unit_cost ? formatCurrency(movement.unit_cost) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else-if="product" class="card empty-panel">
        <strong>Nenhuma movimentação de estoque.</strong>
        <span>As entradas e os ajustes aparecerão aqui.</span>
      </div>
    </template>
    <template #footer>
      <button class="button secondary" type="button" @click="emit('update:open', false)">Fechar</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.inventory-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.inventory-balance {
  display: flex;
  flex-direction: column;
}
.balance-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inventory-operations {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
.operation-card {
  padding: var(--space-4);
}
.operation-card .card-heading {
  margin-bottom: var(--space-3);
}
.operation-card .card-heading h2 {
  font-size: var(--font-size-base);
}
.operation-card .card-heading p {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
</style>
