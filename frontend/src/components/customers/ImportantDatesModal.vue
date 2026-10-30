<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import {
  createImportantDate,
  fetchImportantDates,
  setImportantDateStatus,
  updateImportantDate,
} from '../../api/customers'
import type { ImportantDate, ImportantDateInput } from '../../api/types'
import { formatDate } from '../../utils/date'

const props = defineProps<{
  open: boolean
  customerId: number | null
  customerName: string
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'saved'): void
}>()

const dates = ref<ImportantDate[]>([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const formVisible = ref(false)
const editingDateId = ref<number | null>(null)
const form = ref<ImportantDateInput>({
  description: '',
  recurring: true,
  day: undefined,
  month: undefined,
  date: undefined,
})

watch(
  () => [props.open, props.customerId],
  ([isOpen, id]) => {
    if (isOpen && id !== null) {
      loadDates()
    }
    formVisible.value = false
    editingDateId.value = null
  },
)

async function loadDates(): Promise<void> {
  if (props.customerId === null) return
  loading.value = true
  error.value = ''
  try {
    dates.value = await fetchImportantDates(props.customerId)
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível carregar as datas.'
  } finally {
    loading.value = false
  }
}

function beginNewDate(): void {
  editingDateId.value = null
  form.value = {
    description: '',
    recurring: true,
    day: undefined,
    month: undefined,
    date: undefined,
  }
  formVisible.value = true
}

function beginEditDate(date: ImportantDate): void {
  editingDateId.value = date.id
  form.value = {
    description: date.description,
    recurring: date.recurring,
    day: date.day ?? undefined,
    month: date.month ?? undefined,
    date: date.date ?? undefined,
  }
  formVisible.value = true
}

async function saveDate(): Promise<void> {
  if (props.customerId === null || !form.value.description.trim()) return
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    const input: ImportantDateInput = form.value.recurring
      ? {
          description: form.value.description.trim(),
          recurring: true,
          day: Number(form.value.day),
          month: Number(form.value.month),
        }
      : {
          description: form.value.description.trim(),
          recurring: false,
          date: form.value.date,
        }
    if (editingDateId.value === null) {
      await createImportantDate(props.customerId, input)
      notice.value = 'Data importante criada.'
    } else {
      await updateImportantDate(props.customerId, editingDateId.value, input)
      notice.value = 'Data importante atualizada.'
    }
    formVisible.value = false
    await loadDates()
    emit('saved')
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível salvar a data.'
  } finally {
    loading.value = false
  }
}

async function changeDateStatus(date: ImportantDate): Promise<void> {
  if (props.customerId === null) return
  const nextStatus = date.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const action = nextStatus === 'ACTIVE' ? 'reativar' : 'inativar'
  if (!window.confirm(`Confirma ${action} esta data importante?`)) return
  loading.value = true
  error.value = ''
  try {
    await setImportantDateStatus(props.customerId, date.id, nextStatus)
    await loadDates()
    notice.value = nextStatus === 'ACTIVE' ? 'Data reativada.' : 'Data inativada.'
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível alterar o status.'
  } finally {
    loading.value = false
  }
}

function displayImportantDate(date: ImportantDate): string {
  if (!date.recurring || date.day == null || date.month == null) {
    return date.date ? formatDate(date.date) : ''
  }
  return `${String(date.day).padStart(2, '0')}/${String(date.month).padStart(2, '0')} (anual)`
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="`Datas importantes — ${customerName}`"
    width="640px"
  >
    <template #header-actions>
      <button
        v-if="!formVisible"
        class="btn primary small"
        type="button"
        :disabled="loading"
        @click="beginNewDate"
      >
        Adicionar data
      </button>
    </template>
    <template #body>
      <div v-if="error" class="feedback feedback-error" role="alert">{{ error }}</div>
      <div v-if="notice" class="feedback feedback-success" role="status">{{ notice }}</div>

      <form v-if="formVisible" class="important-date-form" @submit.prevent="saveDate">
        <div class="form-group">
          <label for="id-description">Descrição</label>
          <input id="id-description" v-model="form.description" required :disabled="loading" class="form-input" />
        </div>
        <div class="form-group">
          <label for="id-type">Tipo de data</label>
          <select id="id-type" v-model="form.recurring" class="form-input" :disabled="loading">
            <option :value="true">Recorrente</option>
            <option :value="false">Não recorrente</option>
          </select>
        </div>
        <div v-if="form.recurring" class="date-parts">
          <div class="form-group">
            <label for="id-day">Dia</label>
            <input id="id-day" v-model.number="form.day" type="number" min="1" max="31" required :disabled="loading" class="form-input" />
          </div>
          <div class="form-group">
            <label for="id-month">Mês</label>
            <select id="id-month" v-model.number="form.month" required :disabled="loading" class="form-input">
              <option :value="undefined" disabled>Selecione</option>
              <option v-for="month in 12" :key="month" :value="month">{{ month }}</option>
            </select>
          </div>
        </div>
        <div v-else class="form-group">
          <label for="id-full-date">Data</label>
          <input id="id-full-date" v-model="form.date" type="date" required :disabled="loading" class="form-input" />
        </div>
        <div class="form-actions">
          <button class="btn primary" type="submit" :disabled="loading">
            {{ editingDateId === null ? 'Salvar data' : 'Salvar alterações' }}
          </button>
          <button class="btn" type="button" :disabled="loading" @click="formVisible = false">Cancelar</button>
        </div>
      </form>

      <div v-else class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th class="left">Descrição</th>
              <th class="left">Data</th>
              <th class="left">Situação</th>
              <th class="left">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="date in dates" :key="date.id">
              <td>{{ date.description }}</td>
              <td>{{ displayImportantDate(date) }}</td>
              <td>
                <span :class="['status-pill', date.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                  <span class="status-dot" aria-hidden="true"></span>
                  {{ date.status === 'ACTIVE' ? 'Ativa' : 'Inativa' }}
                </span>
              </td>
              <td class="row-actions">
                <button class="btn small" type="button" :disabled="loading" @click="beginEditDate(date)">Editar</button>
                <button class="btn ghost small" type="button" :disabled="loading" @click="changeDateStatus(date)">
                  {{ date.status === 'ACTIVE' ? 'Inativar' : 'Reativar' }}
                </button>
              </td>
            </tr>
            <tr v-if="dates.length === 0 && !loading">
              <td colspan="4" class="empty-state">
                <strong>Nenhuma data importante.</strong>
                <span>Adicione datas quando necessário.</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <template #footer>
      <button class="btn" type="button" @click="emit('update:open', false)">Fechar</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.date-parts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.important-date-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>
