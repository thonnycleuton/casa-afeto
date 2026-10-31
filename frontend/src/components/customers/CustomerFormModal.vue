<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { Customer } from '../../api/types'

const props = defineProps<{
  open: boolean
  customer: Customer | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'save', payload: { id: number | null; name: string; phone: string; email: string | null; notes: string | null; pendingImage?: File | null }): void
  (e: 'upload-image', customerId: number, file: File): void
}>()

const isEdit = ref(false)
const name = ref('')
const phone = ref('')
const email = ref('')
const notes = ref('')
const apiError = ref('')
const submitted = ref(false)
const imagePreview = ref<string | null>(null)
const imageLoading = ref(false)
const pendingImageFile = ref<File | null>(null)

const nameError = computed(() => {
  if (!submitted.value) return ''
  if (!name.value.trim()) return 'O nome é obrigatório.'
  return ''
})

const phoneError = computed(() => {
  if (!submitted.value) return ''
  if (!phone.value.trim()) return 'O telefone é obrigatório.'
  const digits = phone.value.replace(/\D/g, '')
  if (digits.length < 10) return 'O telefone deve ter pelo menos 10 dígitos.'
  return ''
})

const emailError = computed(() => {
  if (!email.value.trim()) return ''
  const val = email.value.trim()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) return 'Informe um e-mail válido.'
  return ''
})

watch(
  () => [props.open, props.customer],
  ([isOpen, customer]) => {
    submitted.value = false
    apiError.value = ''
    if (isOpen && customer && typeof customer === 'object') {
      isEdit.value = true
      name.value = customer.name
      phone.value = customer.phone
      email.value = customer.email ?? ''
      notes.value = customer.notes ?? ''
      imagePreview.value = customer.image_url ? `${import.meta.env.VITE_API_BASE_URL || ''}${customer.image_url}` : null
    } else if (isOpen) {
      isEdit.value = false
      name.value = ''
      phone.value = ''
      email.value = ''
      notes.value = ''
      imagePreview.value = null
      pendingImageFile.value = null
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
  if (!name.value.trim() || !phone.value.trim()) return
  if (phoneError.value || emailError.value) return
  emit('save', {
    id: props.customer?.id ?? null,
    name: name.value.trim(),
    phone: phone.value.trim(),
    email: email.value.trim() || null,
    notes: notes.value.trim() || null,
    pendingImage: pendingImageFile.value,
  })
  // Reset pending image after submit
  pendingImageFile.value = null
}

async function handleImageUpload(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    apiError.value = 'Selecione uma imagem (JPEG, PNG, WebP ou GIF).'
    target.value = ''
    return
  }

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    apiError.value = 'Imagem muito grande. Tamanho máximo: 5 MB.'
    target.value = ''
    return
  }

  // Show preview immediately
  imagePreview.value = URL.createObjectURL(file)
  apiError.value = ''

  // If editing an existing customer, upload immediately
  if (props.customer?.id) {
    imageLoading.value = true
    try {
      emit('upload-image', props.customer.id, file)
    } finally {
      imageLoading.value = false
    }
  } else {
    // If creating a new customer, store the file for later upload
    pendingImageFile.value = file
  }
}

function clearImage(): void {
  imagePreview.value = null
  pendingImageFile.value = null
  if (props.customer && props.customer.image_url) {
    emit('save', {
      id: props.customer.id,
      name: props.customer.name,
      phone: props.customer.phone,
      email: props.customer.email ?? null,
      notes: props.customer.notes ?? null,
      pendingImage: null,
    })
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="isEdit ? 'Editar Cliente' : 'Novo Cliente'"
    width="520px"
  >
    <template #body>
      <div v-if="apiError" class="feedback feedback-error" role="alert">{{ apiError }}</div>
      <div class="form-group">
        <label for="cf-name">Nome</label>
        <input
          id="cf-name"
          v-model="name"
          required
          class="form-input"
          :class="{ 'form-input-error': nameError }"
        />
        <p v-if="nameError" class="field-error" role="alert">{{ nameError }}</p>
      </div>
      <div class="form-group">
        <label for="cf-phone">Telefone</label>
        <input
          id="cf-phone"
          v-model="phone"
          type="tel"
          required
          class="form-input"
          :class="{ 'form-input-error': phoneError }"
        />
        <p v-if="phoneError" class="field-error" role="alert">{{ phoneError }}</p>
      </div>
      <div class="form-group">
        <label for="cf-email">E-mail</label>
        <input
          id="cf-email"
          v-model="email"
          type="email"
          class="form-input"
          :class="{ 'form-input-error': emailError }"
        />
        <p v-if="emailError" class="field-error" role="alert">{{ emailError }}</p>
      </div>
      <div class="form-group">
        <label for="cf-notes">Observações</label>
        <textarea id="cf-notes" v-model="notes" rows="3" class="form-input"></textarea>
      </div>
      <div class="form-group">
        <label>Foto do cliente</label>
        <div v-if="imagePreview" class="product-image-preview">
          <img :src="imagePreview" alt="Foto do cliente" />
          <button type="button" class="product-image-remove" title="Remover foto" @click="clearImage">✕</button>
        </div>
        <div class="product-image-upload">
          <input
            id="cf-image"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            class="form-input"
            @change="handleImageUpload"
          />
          <p class="field-hint">JPEG, PNG, WebP ou GIF. Máximo 5 MB.</p>
        </div>
      </div>
    </template>
    <template #footer>
      <button class="btn" type="button" @click="emit('update:open', false)">Cancelar</button>
      <button class="btn primary" type="button" @click="submit">
        {{ isEdit ? 'Salvar alterações' : 'Salvar cliente' }}
      </button>
    </template>
  </BaseModal>
</template>

