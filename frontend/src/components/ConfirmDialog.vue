<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { dialogState as d, resolveDialog } from '../composables/useDialog'

const confirmBtn = ref(null)

const iconClass = computed(() => {
  if (d.variant === 'danger') return 'fa-solid fa-trash'
  if (d.variant === 'error') return 'fa-solid fa-circle-xmark'
  if (d.variant === 'warning') return 'fa-solid fa-triangle-exclamation'
  return 'fa-solid fa-circle-question'
})

function accept() {
  resolveDialog(true)
}

function cancel() {
  resolveDialog(d.type === 'alert')
}

function onKeydown(event) {
  if (d.open && event.key === 'Escape') {
    event.preventDefault()
    cancel()
  }
}

watch(() => d.open, async (open) => {
  if (!open) return
  await nextTick()
  confirmBtn.value?.focus()
})

onMounted(() => window.addEventListener('keydown', onKeydown))

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  if (d.open) resolveDialog(false)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div v-if="d.open" class="app-dialog-backdrop" @click.self="cancel">
        <div
          class="app-dialog"
          :class="`is-${d.variant}`"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="app-dialog-title"
          aria-describedby="app-dialog-message"
        >
          <div class="app-dialog-icon" aria-hidden="true">
            <i :class="iconClass"></i>
          </div>

          <h2 id="app-dialog-title">{{ d.title }}</h2>
          <p id="app-dialog-message">{{ d.message }}</p>

          <div class="app-dialog-actions">
            <button
              v-if="d.type === 'confirm'"
              type="button"
              class="btn-soft"
              @click="cancel"
            >
              {{ d.cancelText }}
            </button>
            <button
              ref="confirmBtn"
              type="button"
              :class="d.variant === 'danger' ? 'btn-danger' : 'btn-primary'"
              @click="accept"
            >
              {{ d.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.app-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 22, 42, 0.6); 
}

.app-dialog {
  width: 100%;
  max-width: 380px;
  padding: 24px;
  text-align: center;
  background: #fff;
  color: var(--text);
  border-radius: 16px; 
  box-shadow: 0 22px 65px rgba(0, 0, 0, 0.25);
}

.app-dialog-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  margin: 0 auto 0.75rem;
  font-size: 1.4rem;
  border-radius: 50%;
  color: var(--blue);
  background: var(--blue-light);
}

.app-dialog.is-danger .app-dialog-icon,
.app-dialog.is-error .app-dialog-icon {
  color: var(--danger);
  background: #ffe6e6;
}

.app-dialog.is-warning .app-dialog-icon {
  color: #b45309;
  background: #fef3c7;
}

.app-dialog h2 {
  margin: 0 0 0.5rem;
  font-size: 1.15rem;
}

.app-dialog p {
  margin: 0 0 1.25rem;
  color: var(--muted);
  line-height: 1.5;
  white-space: pre-line; 
  overflow-wrap: anywhere;
}

.app-dialog-actions {
  display: flex;
  gap: 0.5rem;
}

.app-dialog-actions > * {
  flex: 1;
  min-height: 44px;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.15s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
</style>
