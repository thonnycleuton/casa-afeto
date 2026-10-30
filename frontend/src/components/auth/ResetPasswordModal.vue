<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { resetPassword } from '../../api/auth'

defineProps<{ open: boolean }>()
const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'success'): void
}>()

const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref(false)
const loading = ref(false)
const passwordError = ref('')

function validatePassword(): boolean {
  passwordError.value = ''
  if (!newPassword.value) {
    passwordError.value = 'A senha é obrigatória.'
    return false
  }
  if (newPassword.value.length < 8) {
    passwordError.value = 'Mínimo 8 caracteres.'
    return false
  }
  if (!/[A-Z]/.test(newPassword.value)) {
    passwordError.value = 'Pelo menos 1 maiúscula.'
    return false
  }
  if (!/\d/.test(newPassword.value)) {
    passwordError.value = 'Pelo menos 1 número.'
    return false
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'As senhas não coincidem.'
    return false
  }
  return true
}

async function submit(): Promise<void> {
  error.value = ''
  if (!validatePassword()) return
  loading.value = true
  try {
    await resetPassword(window.location.search.replace('?token=', ''), newPassword.value)
    success.value = true
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível redefinir a senha.'
  } finally {
    loading.value = false
  }
}

function close(): void {
  emit('update:open', false)
  newPassword.value = ''
  confirmPassword.value = ''
  error.value = ''
  success.value = false
  passwordError.value = ''
}

onMounted(() => {
  // If no token in URL, show error
  if (!window.location.search.includes('token=')) {
    error.value = 'Link de recuperação inválido.'
  }
})
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="close"
    title="Redefinir senha"
    width="480px"
  >
    <template #body>
      <p class="modal-description">
        {{ success ? 'Senha redefinida com sucesso!' : 'Crie uma nova senha para sua conta.' }}
      </p>
      <div v-if="success" class="feedback feedback-success" role="alert">
        Sua senha foi redefinida.
      </div>
      <div v-else-if="error" class="feedback feedback-error" role="alert">{{ error }}</div>
      <template v-else>
        <div class="form-group">
          <label for="rp-password">Nova senha</label>
          <input
            id="rp-password"
            v-model="newPassword"
            type="password"
            required
            class="form-input"
            :class="{ 'form-input-error': passwordError }"
          />
          <p v-if="passwordError" class="field-error" role="alert">{{ passwordError }}</p>
          <p class="field-hint">Mínimo 8 caracteres, 1 maiúscula e 1 número.</p>
        </div>
        <div class="form-group">
          <label for="rp-confirm">Confirmar senha</label>
          <input
            id="rp-confirm"
            v-model="confirmPassword"
            type="password"
            required
            class="form-input"
          />
        </div>
      </template>
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
        {{ loading ? 'Redefinindo...' : 'Redefinir senha' }}
      </button>
      <button v-else class="btn primary" type="button" @click="emit('success'); close()">
        Entendido
      </button>
    </template>
  </BaseModal>
</template>

