<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ConfirmDialog from './ConfirmDialog.vue'
import { confirmDialog } from '../composables/useDialog'

const router = useRouter()
const username = ref('')
const role = ref('')
const roleLabel = ref('')
const roleMap = {
  'admin': 'ผู้ดูแลระบบ',
  'technician': 'ช่าง',
  'maid': 'แม่บ้าน'
}

onMounted(() => {
  const token = localStorage.getItem('token')
  
  if (token) {
    try {
      const payloadBase64 = token.split('.')[1]
      const decodedJson = atob(payloadBase64)
      const payload = JSON.parse(decodedJson)

      username.value = payload.username
      role.value = payload.role
      roleLabel.value = roleMap[payload.role] || payload.role
    } catch (e) {
      console.error("Token ไม่ถูกต้อง")
    }
  }
})

async function logout() {
  const ok = await confirmDialog('คุณต้องการออกจากระบบใช่หรือไม่?', {
    title: 'ออกจากระบบ',
    confirmText: 'ออกจากระบบ',
    cancelText: 'ยกเลิก'
  })
  if (!ok) return

  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <div class="staff-shell">
    <header class="staff-header">
      <div class="staff-brand">
        <strong>CS BUILDING SERVICES</strong>
        <small>ระบบบริหารจัดการงานบริการอาคารเรียน</small>
      </div>
      
      <div class="staff-user-info" v-if="username">
        <div
          class="user-badge user-badge-action"
          role="button"
          tabindex="0"
          aria-label="ออกจากระบบ"
          title="แตะเพื่อออกจากระบบ"
          @click="logout"
          @keydown.enter.prevent="logout"
          @keydown.space.prevent="logout"
        >
          <i class="fa-solid fa-circle-user"></i>
          <span>
            <strong>{{ username }}</strong>
            <small class="role-text">({{ roleLabel }})</small>
          </span>
          <i class="fa-solid fa-right-from-bracket badge-logout-icon" aria-hidden="true"></i>
        </div>
      </div>
    </header>

    <div class="staff-body">
      <aside class="staff-sidebar">
        <nav class="staff-menu">
          <RouterLink to="/staff/dashboard" v-if="role === 'admin'">
            <i class="fa-solid fa-chart-line"></i>
            แดชบอร์ด
          </RouterLink>

          <RouterLink to="/staff/requests">
            <i class="fa-solid fa-clipboard-list"></i>
            คำขอบริการ
          </RouterLink>

          <RouterLink to="/staff/lost-found" v-if="role === 'admin'">
            <i class="fa-solid fa-box"></i>
            ของหาย-ของได้คืน
          </RouterLink>

          <RouterLink to="/staff/rooms" v-if="role === 'admin'">
            <i class="fa-solid fa-door-open"></i>
            จัดการห้อง / QR
          </RouterLink>


          <RouterLink to="/staff/users" v-if="role === 'admin'">
            <i class="fa-solid fa-users"></i>
            จัดการผู้ใช้งาน
          </RouterLink>

          <RouterLink to="/">
            <i class="fa-solid fa-house"></i>
            หน้าผู้ใช้งาน
          </RouterLink>

          <hr class="menu-divider" />

          <a href="#" @click.prevent="logout" class="logout-btn">
            <i class="fa-solid fa-right-from-bracket"></i>
            ออกจากระบบ
          </a>
        </nav>
      </aside>

      <main class="staff-main">
        <slot />
      </main>
    </div>

    <ConfirmDialog />
  </div>
</template>

<style scoped>
.user-badge-action {
  cursor: pointer;
  user-select: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  transition: opacity 0.15s ease;
}

.user-badge-action:hover {
  opacity: 0.85;
}

.user-badge-action:active {
  opacity: 0.7;
}

.staff-user-info .badge-logout-icon {
  margin-left: 0.25rem;
  font-size: 1rem;
  opacity: 0.8;
}
</style>
