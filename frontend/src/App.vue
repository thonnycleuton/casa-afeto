<script setup lang="ts">
import { ref, onMounted } from 'vue'
import HealthCard from './components/HealthCard.vue'
import StatusBadge from './components/StatusBadge.vue'
import { fetchHealth } from './api/health'
import type { HealthResponse } from './api/types'

const health = ref<HealthResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function checkHealth(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    health.value = await fetchHealth()
  } catch (err: unknown) {
    health.value = null
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = 'Failed to connect to backend'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkHealth()
})
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-container">
        <div class="brand">
          <div class="brand-logo">CA</div>
          <div>
            <h1 class="brand-title">Casa Afeto</h1>
            <p class="brand-tagline">Sales & Operations Management System</p>
          </div>
        </div>
        <StatusBadge status="online" label="M0 Technical Foundation" />
      </div>
    </header>

    <main class="app-main">
      <div class="content-container">
        <section class="intro-section">
          <span class="eyebrow">Milestone M0</span>
          <h2 class="section-title">Technical Foundation Active</h2>
          <p class="section-desc">
            The minimal technical foundation has been established to support incremental development of Casa Afeto operations safely.
          </p>
        </section>

        <section class="grid-section">
          <HealthCard
            :health="health"
            :loading="loading"
            :error="error"
            @refresh="checkHealth"
          />

          <div class="stack-card">
            <h3 class="stack-title">Approved Technical Stack</h3>
            <ul class="stack-list">
              <li>
                <strong>Backend:</strong>
                <span>Python + FastAPI (REST / JSON)</span>
              </li>
              <li>
                <strong>Database:</strong>
                <span>PostgreSQL 16 + SQLAlchemy 2.x</span>
              </li>
              <li>
                <strong>Migrations:</strong>
                <span>Alembic</span>
              </li>
              <li>
                <strong>Frontend:</strong>
                <span>Vue 3 + TypeScript + Vite</span>
              </li>
              <li>
                <strong>Testing:</strong>
                <span>pytest (backend) + Vitest (frontend)</span>
              </li>
              <li>
                <strong>Environment:</strong>
                <span>Docker & Docker Compose</span>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </main>

    <footer class="app-footer">
      <p>Casa Afeto &bull; Build little, validate, learn, then build the next thing.</p>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #ffffff;
  border-bottom: 1px solid var(--color-border);
  padding: 1.25rem 1.5rem;
}

.header-container {
  max-width: 1040px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.brand-logo {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #7c2d12, #c2410c);
  color: #ffffff;
  font-weight: 700;
  font-size: 1.125rem;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 6px -1px rgba(124, 45, 18, 0.25);
}

.brand-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.01em;
}

.brand-tagline {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.app-main {
  flex: 1;
  padding: 3rem 1.5rem;
}

.content-container {
  max-width: 1040px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.eyebrow {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent);
  background: rgba(194, 65, 12, 0.1);
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  margin-bottom: 0.75rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.02em;
}

.section-desc {
  margin-top: 0.5rem;
  font-size: 1rem;
  color: var(--color-text-muted);
  max-width: 640px;
}

.grid-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.stack-card {
  background: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.stack-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 1rem;
}

.stack-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stack-list li {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border-light);
}

.stack-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.stack-list strong {
  color: var(--color-text-main);
}

.stack-list span {
  color: var(--color-text-muted);
  text-align: right;
}

.app-footer {
  border-top: 1px solid var(--color-border);
  background: #ffffff;
  padding: 1.5rem;
  text-align: center;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}
</style>
