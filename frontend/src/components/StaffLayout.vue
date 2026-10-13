<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

function logout() {
  if (confirm('คุณต้องการออกจากระบบใช่หรือไม่?')) {
    localStorage.removeItem('token')
    router.push('/login')
  }
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
        <div class="user-badge">
          <i class="fa-solid fa-circle-user"></i>
          <span>
            <strong>{{ username }}</strong>
            <small class="role-text">({{ roleLabel }})</small>
          </span>
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
  </div>
</template>
