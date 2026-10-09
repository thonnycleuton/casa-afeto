<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  createCustomer,
  createImportantDate,
  fetchCustomer,
  fetchCustomers,
  fetchImportantDates,
  setCustomerStatus,
  setImportantDateStatus,
  updateCustomer,
  updateImportantDate,
} from '../api/customers'
import type {
  Customer,
  CustomerInput,
  CustomerStatus,
  ImportantDate,
  ImportantDateInput,
} from '../api/types'

const pageSize = 10
const customers = ref<Customer[]>([])
const selectedCustomer = ref<Customer | null>(null)
const importantDates = ref<ImportantDate[]>([])
const search = ref('')
const statusFilter = ref<CustomerStatus | 'ALL'>('ACTIVE')
const page = ref(1)
const creating = ref(false)
const editing = ref(false)
const editingDateId = ref<number | null>(null)
const dateFormVisible = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const duplicateWarning = ref(false)
const customerForm = ref<CustomerInput>({ name: '', phone: '', email: '', notes: '' })
const dateForm = ref<ImportantDateInput>({
  description: '',
  recurring: true,
  day: undefined,
  month: undefined,
  date: undefined,
})

const hasNextPage = ref(false)
const customerStatusLabel = computed(() =>
  selectedCustomer.value?.status === 'ACTIVE' ? 'Ativo' : 'Inativo',
)

watch(selectedCustomer, (customer) => {
  if (customer && !editing.value) {
    customerForm.value = {
      name: customer.name,
      phone: customer.phone,
      email: customer.email ?? '',
      notes: customer.notes ?? '',
    }
  }
})

async function run(action: () => Promise<void>): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  duplicateWarning.value = false
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível concluir a operação.'
  } finally {
    loading.value = false
  }
}

async function loadCustomers(): Promise<void> {
  const result = await fetchCustomers({
    search: search.value,
    status: statusFilter.value,
    page: page.value,
    pageSize: pageSize + 1,
  })
  hasNextPage.value = result.length > pageSize
  customers.value = result.slice(0, pageSize)
}

async function searchCustomers(): Promise<void> {
  page.value = 1
  await run(loadCustomers)
}

async function selectCustomer(id: number): Promise<void> {
  await run(async () => {
    const [customer, dates] = await Promise.all([
      fetchCustomer(id),
      fetchImportantDates(id),
    ])
    selectedCustomer.value = customer
    importantDates.value = dates
    creating.value = false
    editing.value = false
    dateFormVisible.value = false
  })
}

function beginCreate(): void {
  selectedCustomer.value = null
  importantDates.value = []
  creating.value = true
  editing.value = false
  customerForm.value = { name: '', phone: '', email: '', notes: '' }
}

function beginEdit(): void {
  if (!selectedCustomer.value) return
  customerForm.value = {
    name: selectedCustomer.value.name,
    phone: selectedCustomer.value.phone,
    email: selectedCustomer.value.email ?? '',
    notes: selectedCustomer.value.notes ?? '',
  }
  editing.value = true
}

async function saveCustomer(): Promise<void> {
  await run(async () => {
    const wasCreating = creating.value
    const input: CustomerInput = {
      name: customerForm.value.name,
      phone: customerForm.value.phone,
      email: customerForm.value.email || null,
      notes: customerForm.value.notes || null,
    }
    const saved = creating.value
      ? await createCustomer(input)
      : await updateCustomer(selectedCustomer.value!.id, input)
    duplicateWarning.value = saved.warning?.code === 'DUPLICATE_PHONE'
    selectedCustomer.value = await fetchCustomer(saved.id)
    importantDates.value = await fetchImportantDates(saved.id)
    creating.value = false
    editing.value = false
    await loadCustomers()
    notice.value = duplicateWarning.value
      ? 'Cliente salvo. Este telefone já está cadastrado em outro cliente.'
      : wasCreating
        ? 'Cliente criado.'
        : 'Cliente atualizado.'
  })
}

async function changeCustomerStatus(): Promise<void> {
  const customer = selectedCustomer.value
  if (!customer) return
  const nextStatus = customer.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const action = nextStatus === 'ACTIVE' ? 'reativar' : 'inativar'
  if (!window.confirm(`Confirma ${action} este cliente?`)) return
  await run(async () => {
    selectedCustomer.value = await setCustomerStatus(customer.id, nextStatus)
    await loadCustomers()
    notice.value = nextStatus === 'ACTIVE' ? 'Cliente reativado.' : 'Cliente inativado.'
  })
}

function beginNewDate(): void {
  editingDateId.value = null
  dateForm.value = {
    description: '',
    recurring: true,
    day: undefined,
    month: undefined,
    date: undefined,
  }
  dateFormVisible.value = true
}

function beginEditDate(date: ImportantDate): void {
  editingDateId.value = date.id
  dateForm.value = {
    description: date.description,
    recurring: date.recurring,
    day: date.day ?? undefined,
    month: date.month ?? undefined,
    date: date.date ?? undefined,
  }
  dateFormVisible.value = true
}

async function saveDate(): Promise<void> {
  const customer = selectedCustomer.value
  if (!customer) return
  await run(async () => {
    const input: ImportantDateInput = dateForm.value.recurring
      ? {
          description: dateForm.value.description,
          recurring: true,
          day: Number(dateForm.value.day),
          month: Number(dateForm.value.month),
        }
      : {
          description: dateForm.value.description,
          recurring: false,
          date: dateForm.value.date,
        }
    if (editingDateId.value === null) {
      await createImportantDate(customer.id, input)
      notice.value = 'Data importante criada.'
    } else {
      await updateImportantDate(customer.id, editingDateId.value, input)
      notice.value = 'Data importante atualizada.'
    }
    importantDates.value = await fetchImportantDates(customer.id)
    dateFormVisible.value = false
  })
}

async function changeDateStatus(date: ImportantDate): Promise<void> {
  const customer = selectedCustomer.value
  if (!customer) return
  const nextStatus = date.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const action = nextStatus === 'ACTIVE' ? 'reativar' : 'inativar'
  if (!window.confirm(`Confirma ${action} esta data importante?`)) return
  await run(async () => {
    await setImportantDateStatus(customer.id, date.id, nextStatus)
    importantDates.value = await fetchImportantDates(customer.id)
    notice.value = nextStatus === 'ACTIVE' ? 'Data importante reativada.' : 'Data importante inativada.'
  })
}

function displayImportantDate(date: ImportantDate): string {
  if (!date.recurring || date.day == null || date.month == null) {
    return date.date ? new Date(`${date.date}T00:00:00`).toLocaleDateString('pt-BR') : ''
  }
  return `${String(date.day).padStart(2, '0')}/${String(date.month).padStart(2, '0')} (anual)`
}

async function changePage(delta: number): Promise<void> {
  page.value += delta
  await run(loadCustomers)
}

onMounted(() => {
  void run(loadCustomers)
})
</script>

<template>
  <section aria-labelledby="customers-heading" class="customers-view">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span><span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span><span>{{ notice }}</span>
    </div>
    <div v-if="loading" class="loading-state" role="status">
      <span class="spinner" aria-hidden="true"></span><span>Atualizando informações...</span>
    </div>

    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Cadastro e relacionamento</p>
        <h1 id="customers-heading">Clientes</h1>
        <p class="page-description">Consulte clientes e registre datas importantes individualmente.</p>
      </div>
      <button class="button primary" type="button" :disabled="loading" @click="beginCreate">
        Novo cliente
      </button>
    </div>

    <div class="customer-columns">
      <div class="customer-list-column">
        <form class="card customer-filters" @submit.prevent="searchCustomers">
          <div class="form-field customer-search-field">
            <label for="customer-search">Buscar por nome ou telefone</label>
            <input
              id="customer-search"
              v-model="search"
              type="search"
              placeholder="Digite um nome ou telefone"
            />
          </div>
          <div class="form-field">
            <label for="customer-status-filter">Situação</label>
            <select id="customer-status-filter" v-model="statusFilter">
              <option value="ACTIVE">Ativos</option>
              <option value="INACTIVE">Inativos</option>
              <option value="ALL">Todos</option>
            </select>
          </div>
          <button class="button secondary" type="submit" :disabled="loading">Buscar</button>
        </form>

        <div class="card table-card">
          <div class="table-heading">
            <div><h2>Clientes cadastrados</h2><p>Selecione um cliente para consultar ou editar.</p></div>
          </div>
          <div class="table-scroll">
            <table>
              <thead><tr><th>Nome</th><th>Telefone</th><th>Situação</th></tr></thead>
              <tbody>
                <tr
                  v-for="customer in customers"
                  :key="customer.id"
                  class="selectable-row"
                  :class="{ 'selected-row': selectedCustomer?.id === customer.id }"
                  @click="selectCustomer(customer.id)"
                >
                  <td><button class="table-link" type="button" @click.stop="selectCustomer(customer.id)">{{ customer.name }}</button></td>
                  <td>{{ customer.phone }}</td>
                  <td>
                    <span :class="['status-pill', customer.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                      <span class="status-dot" aria-hidden="true"></span>
                      {{ customer.status === 'ACTIVE' ? 'Ativo' : 'Inativo' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="customers.length === 0">
                  <td colspan="3" class="empty-state">
                    <strong>{{ search ? 'Nenhum cliente encontrado.' : 'Nenhum cliente cadastrado.' }}</strong>
                    <span>{{ search ? 'Tente outro nome ou telefone.' : 'Crie um cliente para começar.' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="customer-pagination">
            <span>Página {{ page }}</span>
            <div class="form-actions">
              <button class="button compact secondary" type="button" :disabled="loading || page === 1" @click="changePage(-1)">Anterior</button>
              <button class="button compact secondary" type="button" :disabled="loading || !hasNextPage" @click="changePage(1)">Próxima</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="creating || selectedCustomer" class="customer-detail-column">
        <form
          v-if="creating || editing"
          class="card product-form"
          @submit.prevent="saveCustomer"
        >
          <div class="card-heading">
            <div>
              <p class="card-eyebrow">{{ creating ? 'Novo cadastro' : `Cliente #${selectedCustomer?.id}` }}</p>
              <h2>{{ creating ? 'Novo cliente' : 'Editar cliente' }}</h2>
            </div>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label for="customer-name">Nome</label>
              <input id="customer-name" v-model="customerForm.name" required :disabled="loading" />
            </div>
            <div class="form-field">
              <label for="customer-phone">Telefone</label>
              <input id="customer-phone" v-model="customerForm.phone" type="tel" required :disabled="loading" />
              <span class="field-hint">Telefones duplicados são permitidos e serão sinalizados.</span>
            </div>
            <div class="form-field">
              <label for="customer-email">E-mail</label>
              <input id="customer-email" v-model="customerForm.email" type="email" :disabled="loading" />
            </div>
            <div class="form-field">
              <label for="customer-notes">Observações</label>
              <textarea id="customer-notes" v-model="customerForm.notes" rows="3" :disabled="loading"></textarea>
            </div>
          </div>
          <div class="form-actions">
            <button class="button primary" type="submit" :disabled="loading">{{ creating ? 'Salvar cliente' : 'Salvar alterações' }}</button>
            <button class="button secondary" type="button" :disabled="loading" @click="creating ? creating = false : editing = false">Cancelar</button>
          </div>
        </form>

        <template v-else-if="selectedCustomer">
          <div class="card product-form">
            <div class="card-heading customer-detail-heading">
              <div>
                <p class="card-eyebrow">Cliente #{{ selectedCustomer.id }}</p>
                <h2>{{ selectedCustomer.name }}</h2>
              </div>
              <span :class="['status-pill', selectedCustomer.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                <span class="status-dot" aria-hidden="true"></span>{{ customerStatusLabel }}
              </span>
            </div>
            <dl class="customer-data">
              <div><dt>Telefone</dt><dd>{{ selectedCustomer.phone }}</dd></div>
              <div><dt>E-mail</dt><dd>{{ selectedCustomer.email || 'Não informado' }}</dd></div>
              <div><dt>Observações</dt><dd>{{ selectedCustomer.notes || 'Nenhuma observação' }}</dd></div>
            </dl>
            <div class="form-actions">
              <button class="button primary" type="button" :disabled="loading" @click="beginEdit">Editar cliente</button>
              <button class="button secondary" type="button" :disabled="loading" @click="changeCustomerStatus">
                {{ selectedCustomer.status === 'ACTIVE' ? 'Inativar' : 'Reativar' }}
              </button>
            </div>
          </div>

          <div class="card table-card important-dates-card">
            <div class="table-heading">
              <div><h2>Datas importantes</h2><p>Datas recorrentes guardam somente dia e mês.</p></div>
              <button class="button compact primary" type="button" :disabled="loading" @click="beginNewDate">Adicionar data</button>
            </div>

            <form v-if="dateFormVisible" class="important-date-form" @submit.prevent="saveDate">
              <div class="form-field">
                <label for="important-date-description">Descrição</label>
                <input id="important-date-description" v-model="dateForm.description" required :disabled="loading" />
              </div>
              <div class="form-field">
                <label for="important-date-type">Tipo de data</label>
                <select id="important-date-type" v-model="dateForm.recurring">
                  <option :value="true">Recorrente</option>
                  <option :value="false">Não recorrente</option>
                </select>
              </div>
              <div v-if="dateForm.recurring" class="date-parts">
                <div class="form-field">
                  <label for="important-date-day">Dia</label>
                  <input id="important-date-day" v-model.number="dateForm.day" type="number" min="1" max="31" required :disabled="loading" />
                </div>
                <div class="form-field">
                  <label for="important-date-month">Mês</label>
                  <select id="important-date-month" v-model.number="dateForm.month" required :disabled="loading">
                    <option :value="undefined" disabled>Selecione</option>
                    <option v-for="month in 12" :key="month" :value="month">{{ month }}</option>
                  </select>
                </div>
              </div>
              <div v-else class="form-field">
                <label for="important-date-full">Data</label>
                <input id="important-date-full" v-model="dateForm.date" type="date" required :disabled="loading" />
              </div>
              <div class="form-actions">
                <button class="button primary" type="submit" :disabled="loading">{{ editingDateId === null ? 'Salvar data' : 'Salvar alterações' }}</button>
                <button class="button secondary" type="button" :disabled="loading" @click="dateFormVisible = false">Cancelar</button>
              </div>
            </form>

            <div class="table-scroll">
              <table>
                <thead><tr><th>Descrição</th><th>Data</th><th>Situação</th><th>Ações</th></tr></thead>
                <tbody>
                  <tr v-for="date in importantDates" :key="date.id">
                    <td>{{ date.description }}</td>
                    <td>{{ displayImportantDate(date) }}</td>
                    <td>
                      <span :class="['status-pill', date.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
                        <span class="status-dot" aria-hidden="true"></span>{{ date.status === 'ACTIVE' ? 'Ativa' : 'Inativa' }}
                      </span>
                    </td>
                    <td class="row-actions">
                      <button class="button compact secondary" type="button" :disabled="loading" @click="beginEditDate(date)">Editar</button>
                      <button class="button compact ghost" type="button" :disabled="loading" @click="changeDateStatus(date)">
                        {{ date.status === 'ACTIVE' ? 'Inativar' : 'Reativar' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="importantDates.length === 0">
                    <td colspan="4" class="empty-state"><strong>Nenhuma data importante.</strong><span>Adicione datas quando necessário.</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
      <div v-else class="card empty-panel customer-empty-detail">
        <strong>Selecione um cliente</strong><span>O detalhe e as datas importantes aparecerão aqui.</span>
      </div>
    </div>
  </section>
</template>
