<script setup lang="ts">
import { ref } from 'vue'
import BaseModal from '../ui/BaseModal.vue'

defineProps<{ open: boolean }>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm', payload: { reason: string; operator_name: string }): void
}>()

const reason = ref('')
const operatorName = ref('')

function submit(): void {
  if (!reason.value.trim() || !operatorName.value.trim()) return
  emit('confirm', {
    reason: reason.value.trim(),
    operator_name: operatorName.value.trim(),
  })
  emit('update:open', false)
}
</script>

<template>
  <BaseModal :open="open" @update:open="emit('update:open', $event)" title="Reabrir Venda Pronta" width="480px">
    <template #body>
      <p class="field-hint">
        A reabertura retornará a venda para <strong>EM PREPARAÇÃO</strong>. Esta operação exige justificativa e identificação textual do operador para auditoria.
      </p>

      <div class="form-group">
        <label>Justificativa da Reabertura (obrigatória):</label>
        <textarea
          v-model="reason"
          rows="3"
          placeholder="Ex.: Troca de item solicitada pelo cliente..."
          class="form-input"
        ></textarea>
      </div>

      <div class="form-group">
        <label>Nome do Operador Responsável (obrigatório):</label>
        <input
          v-model="operatorName"
          type="text"
          placeholder="Seu nome ou identificador"
          class="form-input"
        />
      </div>
    </template>
    <template #footer>
      <button type="button" class="btn" @click="emit('update:open', false)">Cancelar</button>
      <button
        type="button"
        class="btn primary"
        :disabled="!reason.trim() || !operatorName.trim()"
        @click="submit"
      >
        Confirmar Reabertura
      </button>
    </template>
  </BaseModal>
</template>

