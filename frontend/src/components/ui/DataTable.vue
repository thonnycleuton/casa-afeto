<script setup lang="ts">
import { computed } from 'vue'

export interface DataColumn {
  key: string
  label: string
  align?: 'left' | 'center' | 'right'
}

const props = withDefaults(
  defineProps<{
    columns: DataColumn[]
    rows: unknown[]
    pageSize?: number
    page?: number
    loading?: boolean
  }>(),
  {
    pageSize: 10,
    page: 1,
    loading: false,
  },
)

const emit = defineEmits<{
  (e: 'row-click', row: unknown): void
  (e: 'page-change', page: number): void
}>()

const currentPage = computed(() => {
  const page = Number(props.page)
  return isNaN(page) ? 1 : page
})

const totalPages = computed(() => Math.max(1, Math.ceil(props.rows.length / props.pageSize)))

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  return props.rows.slice(start, start + props.pageSize)
})

function goToPage(page: number): void {
  if (page < 1 || page > totalPages.value) return
  emit('page-change', page)
}
</script>

<template>
  <div class="data-table-wrapper">
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" :class="col.align ?? 'left'">
              {{ col.label }}
            </th>
            <th v-if="$slots.actions" class="left">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pagedRows" :key="(row as any).id" @click="emit('row-click', row)">
            <td v-for="col in columns" :key="col.key" :class="col.align ?? 'left'">
              <slot :name="'cell-' + col.key" :row="row">
                {{ (row as any)[col.key] }}
              </slot>
            </td>
            <td v-if="$slots.actions" class="left row-actions">
              <slot name="actions" :row="row" />
            </td>
          </tr>
          <tr v-if="pagedRows.length === 0 && !loading">
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="empty-state">
              <slot name="empty">
                <strong>Nenhum registro encontrado.</strong>
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="totalPages > 1" class="pagination-bar">
      <span class="pagination-info">Página {{ currentPage }} de {{ totalPages }}</span>
      <div class="pagination-controls">
        <button
          class="pagination-btn"
          type="button"
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          Anterior
        </button>
        <button
          class="pagination-btn"
          type="button"
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        >
          Próxima
        </button>
      </div>
    </div>
  </div>
</template>