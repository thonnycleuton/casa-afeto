<script setup lang="ts">
import { ref } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import { forgotPassword } from '../../api/auth'

defineProps<{ open: boolean }>()
const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'success'): void
}>()

const email = ref('')
const error = ref('')
const success = ref(false)
const loading = ref(false)

async function submit(): Promise<void> {
  error.value = ''
  success.value = false
  if (!email.value.trim()) return
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    error.value = 'Informe um e-mail válido.'
    return
  }
  loading.value = true
  try {
    await forgotPassword(email.value.trim())
    success.value = true
    email.value = ''
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível enviar o e-mail.'
  } finally {
    loading.value = false
  }
}

function close(): void {
  emit('update:open', false)
  email.value = ''
  error.value = ''
  success.value = false
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="close"
    title="Recuperar senha"
    width="480px"
  >
    <template #body>
      <p class="modal-description">
        Informe o e-mail da sua conta e enviaremos um link para redefinir sua senha.
      </p>
      <div v-if="success" class="feedback feedback-success" role="alert">
        Se existir uma conta com este e-mail, você receberá um link de recuperação em breve.
      </div>
      <div v-if="error" class="feedback feedback-error" role="alert">{{ error }}</div>
      <div v-if="!success" class="form-group">
        <label for="fp-email">E-mail</label>
        <input
          id="fp-email"
          v-model="email"
          type="email"
          required
          class="form-input"
          placeholder="seu@email.com"
        />
      </div>
    </template>
    <template #footer>
      <button class="btn" type="button" @click="close">Cancelar</button>
      <button
        v-if="!success"
        class="btn primary"
        type="button"
        :disabled="loading"
        @click="submit"
      >
        {{ loading ? 'Enviando...' : 'Enviar link' }}
      </button>
      <button v-else class="btn primary" type="button" @click="emit('success'); close()">
        Entendido
      </button>
    </template>
  </BaseModal>
</template>

