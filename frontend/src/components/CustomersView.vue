<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DataTable, { type DataColumn } from '../components/ui/DataTable.vue'
import CustomerFormModal from '../components/customers/CustomerFormModal.vue'
import ImportantDatesModal from '../components/customers/ImportantDatesModal.vue'
import {
  createCustomer,
  fetchCustomer,
  fetchCustomers,
  setCustomerStatus,
  updateCustomer,
} from '../api/customers'
import type {
  Customer,
  CustomerInput,
  CustomerStatus,
} from '../api/types'

const customers = ref<Customer[]>([])
const search = ref('')
const statusFilter = ref<CustomerStatus | 'ALL'>('ACTIVE')
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Modal state
const showFormModal = ref(false)
const editingCustomer = ref<Customer | null>(null)
const customerFormRef = ref<InstanceType<typeof CustomerFormModal> | null>(null)

// Important dates modal state
const showDatesModal = ref(false)
const datesCustomerId = ref<number | null>(null)
const datesCustomerName = ref('')

const columns: DataColumn[] = [
  { key: 'name', label: 'Nome' },
  { key: 'phone', label: 'Telefone' },
  { key: 'status', label: 'Situação' },
]

async function run(action: () => Promise<void>): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
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
  })
  customers.value = result
}

async function searchCustomers(): Promise<void> {
  await run(loadCustomers)
}

function beginCreate(): void {
  editingCustomer.value = null
  showFormModal.value = true
}

function beginEdit(customer: Customer): void {
  editingCustomer.value = customer
  showFormModal.value = true
}

async function handleSave(payload: CustomerInput): Promise<void> {
  await run(async () => {
    if (editingCustomer.value) {
      const saved = await updateCustomer(editingCustomer.value.id, payload)
      const updated = await fetchCustomer(saved.id)
      const index = customers.value.findIndex((c) => c.id === updated.id)
      if (index !== -1) customers.value[index] = updated
      notice.value = 'Cliente atualizado.'
    } else {
      const saved = await createCustomer(payload)
      const created = await fetchCustomer(saved.id)
      customers.value.unshift(created)
      notice.value = saved.warning?.code === 'DUPLICATE_PHONE'
        ? 'Cliente criado. Este telefone já está cadastrado em outro cliente.'
        : 'Cliente criado.'
    }
    showFormModal.value = false
    editingCustomer.value = null
  })
}

async function handleChangeStatus(customer: Customer): Promise<void> {
  const nextStatus = customer.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  const action = nextStatus === 'ACTIVE' ? 'reativar' : 'inativar'
  if (!window.confirm(`Confirma ${action} este cliente?`)) return
  await run(async () => {
    const updated = await setCustomerStatus(customer.id, nextStatus)
    const index = customers.value.findIndex((c) => c.id === updated.id)
    if (index !== -1) customers.value[index] = updated
    notice.value = nextStatus === 'ACTIVE' ? 'Cliente reativado.' : 'Cliente inativado.'
  })
}

function openDatesModal(customer: Customer): void {
  datesCustomerId.value = customer.id
  datesCustomerName.value = customer.name
  showDatesModal.value = true
}

onMounted(() => {
  void run(loadCustomers)
})
</script>

<template>
  <section aria-labelledby="customers-heading">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span><span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span><span>{{ notice }}</span>
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

    <form class="card" @submit.prevent="searchCustomers">
      <div class="form-row">
        <div class="form-field">
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
        <div class="form-field">
          <button class="button secondary" type="submit" :disabled="loading">Buscar</button>
        </div>
      </div>
    </form>

    <div class="card table-card">
      <DataTable
        :columns="columns"
        :rows="customers"
        :page-size="10"
        :loading="loading"
      >
        <template #cell-status="{ row }: { row: Customer }">
          <span :class="['status-pill', row.status === 'ACTIVE' ? 'status-success' : 'status-muted']">
            <span class="status-dot" aria-hidden="true"></span>
            {{ row.status === 'ACTIVE' ? 'Ativo' : 'Inativo' }}
          </span>
        </template>
        <template #actions="{ row }: { row: Customer }">
          <button class="button compact secondary" type="button" @click="beginEdit(row)">Editar</button>
          <button class="button compact ghost" type="button" @click="openDatesModal(row)">Datas</button>
          <button class="button compact ghost" type="button" @click="handleChangeStatus(row)">
            {{ row.status === 'ACTIVE' ? 'Inativar' : 'Reativar' }}
          </button>
        </template>
        <template #empty>
          <strong>{{ search ? 'Nenhum cliente encontrado.' : 'Nenhum cliente cadastrado.' }}</strong>
          <span>{{ search ? 'Tente outro nome ou telefone.' : 'Crie um cliente para começar.' }}</span>
        </template>
      </DataTable>
    </div>

    <CustomerFormModal
      ref="customerFormRef"
      v-model:open="showFormModal"
      :customer="editingCustomer"
      @save="handleSave"
    />

    <ImportantDatesModal
      v-model:open="showDatesModal"
      :customer-id="datesCustomerId"
      :customer-name="datesCustomerName"
    />
  </section>
</template>
