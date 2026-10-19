<script setup lang="ts">
import { ref } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import SaleDetailView from './SaleDetailView.vue'
import type { BasketTemplate, Product, Sale } from '../../api/types'
import type { Payment, PaymentTotal } from '../../api/payments'

const props = withDefaults(
  defineProps<{
    open: boolean
    sale: Sale | null
    templates: BasketTemplate[]
    products?: Product[]
    paymentTotal: PaymentTotal | null
    payments: Payment[]
    paymentLoading: boolean
    paymentError: string
    confirmErrorType: 'payment' | 'stock' | 'delivery' | null
  }>(),
  {
    products: () => [],
    paymentTotal: null,
    payments: () => [],
    paymentLoading: false,
    paymentError: '',
    confirmErrorType: null,
  },
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm', saleId: number): void
  (e: 'start-prep', saleId: number): void
  (e: 'cancel', saleId: number): void
  (e: 'reopen', saleId: number, payload: { reason: string; operator_name: string }): void
  (e: 'add-basket', saleId: number, payload: { template_id: number }): void
  (e: 'remove-basket', saleId: number, basketId: number): void
  (e: 'update-price', saleId: number, basketId: number, price: string): void
  (e: 'update-delivery', saleId: number, basketId: number, delivery: { recipient_name: string; delivery_address: string; delivery_date: string; delivery_time: string }): void
  (e: 'prepare-basket', saleId: number, basketId: number): void
  (e: 'deliver-basket', saleId: number, basketId: number, operatorName: string): void
  (e: 'update-composition', saleId: number, basketId: number, items: Array<{ product_id: number; quantity: string }>): void
  (e: 'record-payment', saleId: number, payload: { amount: string; method: string; idempotency_key: string }): void
  (e: 'retry-payments'): void
}>()

const saleDetailRef = ref<InstanceType<typeof SaleDetailView> | null>(null)
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="sale ? `Venda #${sale.id} — ${sale.customer_name}` : 'Detalhes da Venda'"
    width="1300px"
  >
    <template #body>
      <div v-if="sale" class="sale-detail-modal-body">
        <SaleDetailView
          ref="saleDetailRef"
          :sale="sale"
          :templates="templates"
          :products="products"
          :payment-total="paymentTotal"
          :payments="payments"
          :payment-loading="paymentLoading"
          :payment-error="paymentError"
          :confirm-error-type="confirmErrorType"
          @back="emit('update:open', false)"
          @confirm="(id) => emit('confirm', id)"
          @start-prep="(id) => emit('start-prep', id)"
          @cancel="(id) => emit('cancel', id)"
          @reopen="(id, p) => emit('reopen', id, p)"
          @add-basket="(id, p) => emit('add-basket', id, p)"
          @remove-basket="(id, bId) => emit('remove-basket', id, bId)"
          @update-price="(id, bId, pr) => emit('update-price', id, bId, pr)"
          @update-delivery="(id, bId, d) => emit('update-delivery', id, bId, d)"
          @prepare-basket="(id, bId) => emit('prepare-basket', id, bId)"
          @deliver-basket="(id, bId, op) => emit('deliver-basket', id, bId, op)"
          @update-composition="(id, bId, items) => emit('update-composition', id, bId, items)"
          @record-payment="(saleId, payload) => emit('record-payment', saleId, payload)"
          @retry-payments="emit('retry-payments')"
        />
      </div>
    </template>
  </BaseModal>
</template>

<style scoped>
.sale-detail-modal-body {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
