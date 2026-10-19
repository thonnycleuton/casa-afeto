<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    width?: string
    dismissible?: boolean
  }>(),
  {
    width: '520px',
    dismissible: true,
  },
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const modalBox = ref<HTMLElement | null>(null)

function close(): void {
  emit('update:open', false)
}

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape' && props.dismissible) {
    close()
  }
}

function handleClickOutside(e: MouseEvent): void {
  if (props.dismissible && e.target === e.currentTarget) {
    close()
  }
}

function handleTrapFocus(e: KeyboardEvent): void {
  if (e.key !== 'Tab' || !modalBox.value) return
  const focusable = modalBox.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  )
  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (e.shiftKey) {
    if (document.activeElement === first) {
      e.preventDefault()
      last.focus()
    }
  } else {
    if (document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }
}

onMounted(() => {
  if (props.open) {
    document.addEventListener('keydown', handleKeydown)
    document.addEventListener('keydown', handleTrapFocus)
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('keydown', handleTrapFocus)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="modal-overlay"
      @click="handleClickOutside"
    >
      <div
        ref="modalBox"
        class="modal-box"
        :style="{ maxWidth: width }"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title ? 'modal-title' : undefined"
        @keydown="handleTrapFocus"
      >
        <header class="modal-header">
          <h3 v-if="title" id="modal-title">{{ title }}</h3>
          <slot name="header-actions" />
          <button
            type="button"
            class="modal-close-btn"
            aria-label="Fechar"
            @click="close"
          >
            ×
          </button>
        </header>
        <div class="modal-body">
          <slot name="body" />
        </div>
        <footer v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>
