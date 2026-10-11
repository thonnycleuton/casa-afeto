<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'close'): void
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
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-box">
      <header class="modal-header">
        <h3>Reabrir Venda Pronta</h3>
        <button type="button" class="close-btn" @click="emit('close')">×</button>
      </header>

      <div class="modal-body">
        <p class="modal-info">
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
      </div>

      <footer class="modal-footer">
        <button type="button" class="button secondary" @click="emit('close')">Cancelar</button>
        <button
          type="button"
          class="button primary"
          :disabled="!reason.trim() || !operatorName.trim()"
          @click="submit"
        >
          Confirmar Reabertura
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--color-modal-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}
.modal-box {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  max-width: 480px;
  width: 100%;
  box-shadow: var(--shadow-overlay);
}
.modal-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  line-height: 1;
}
.close-btn:hover {
  color: var(--color-text-primary);
}
.modal-body {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.modal-info {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}
.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 550;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}
.form-input {
  width: 100%;
  min-height: 38px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
}
.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
