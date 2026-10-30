<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { UserResponse, UserCreateInput, UserUpdateInput, UserRole } from '../../api/types'

const props = defineProps<{
  open: boolean
  user: UserResponse | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'save', payload: UserCreateInput | UserUpdateInput): void
}>()

const isEdit = ref(false)
const fullName = ref('')
const email = ref('')
const role = ref<UserRole>('operator')
const password = ref('')
const apiError = ref('')
const submitted = ref(false)

const fullNameError = computed(() => {
  if (!submitted.value) return ''
  if (!fullName.value.trim()) return 'O nome é obrigatório.'
  return ''
})

const emailError = computed(() => {
  if (!submitted.value) return ''
  const val = email.value.trim()
  if (!val) return 'O e-mail é obrigatório.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) return 'Informe um e-mail válido.'
  return ''
})

const passwordError = computed(() => {
  if (!submitted.value) return ''
  if (isEdit.value) return '' // password not required on edit
  if (!password.value) return 'A senha é obrigatória.'
  if (password.value.length < 8) return 'Mínimo 8 caracteres.'
  if (!/[A-Z]/.test(password.value)) return 'Pelo menos 1 maiúscula.'
  if (!/\d/.test(password.value)) return 'Pelo menos 1 número.'
  return ''
})

watch(
  () => [props.open, props.user],
  ([isOpen, user]) => {
    submitted.value = false
    apiError.value = ''
    if (isOpen && user && typeof user === 'object') {
      isEdit.value = true
      fullName.value = user.full_name
      email.value = user.email
      role.value = user.role
      password.value = ''
    } else if (isOpen) {
      isEdit.value = false
      fullName.value = ''
      email.value = ''
      role.value = 'operator'
      password.value = ''
    }
  },
)

function setApiError(msg: string): void {
  apiError.value = msg
}

defineExpose({ setApiError })

function submit(): void {
  submitted.value = true
  apiError.value = ''
  if (!fullName.value.trim() || !email.value.trim()) return
  if (fullNameError.value || emailError.value || passwordError.value) return

  if (isEdit.value) {
    emit('save', {
      full_name: fullName.value.trim(),
      role: role.value,
    })
  } else {
    emit('save', {
      email: email.value.trim(),
      password: password.value,
      full_name: fullName.value.trim(),
      role: role.value,
    })
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="isEdit ? 'Editar Usuário' : 'Novo Usuário'"
    width="520px"
  >
    <template #body>
      <div v-if="apiError" class="feedback feedback-error" role="alert">{{ apiError }}</div>
      <div class="form-group">
        <label for="uf-name">Nome</label>
        <input
          id="uf-name"
          v-model="fullName"
          required
          class="form-input"
          :class="{ 'form-input-error': fullNameError }"
        />
        <p v-if="fullNameError" class="field-error" role="alert">{{ fullNameError }}</p>
      </div>
      <div class="form-group">
        <label for="uf-email">E-mail</label>
        <input
          id="uf-email"
          v-model="email"
          :required="!isEdit"
          :disabled="isEdit"
          class="form-input"
          :class="{ 'form-input-error': emailError }"
        />
        <p v-if="emailError" class="field-error" role="alert">{{ emailError }}</p>
      </div>
      <div class="form-group">
        <label for="uf-role">Função</label>
        <select id="uf-role" v-model="role" class="form-input">
          <option value="operator">Operador</option>
          <option value="admin">Administrador</option>
        </select>
      </div>
      <div v-if="!isEdit" class="form-group">
        <label for="uf-password">Senha</label>
        <input
          id="uf-password"
          v-model="password"
          type="password"
          required
          class="form-input"
          :class="{ 'form-input-error': passwordError }"
        />
        <p v-if="passwordError" class="field-error" role="alert">{{ passwordError }}</p>
        <p class="field-hint">Mínimo 8 caracteres, 1 maiúscula e 1 número.</p>
      </div>
    </template>
    <template #footer>
      <button class="btn" type="button" @click="emit('update:open', false)">Cancelar</button>
      <button class="btn primary" type="button" @click="submit">
        {{ isEdit ? 'Salvar alterações' : 'Criar usuário' }}
      </button>
    </template>
  </BaseModal>
</template>

