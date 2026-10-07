<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const role = ref('')
const roleLabel = ref('')

// จับคู่ภาษาอังกฤษ เป็นชื่อตำแหน่งภาษาไทย
const roleMap = {
  'admin': 'ผู้ดูแลระบบ',
  'technician': 'ช่าง',
  'maid': 'แม่บ้าน'
}

onMounted(() => {
  const token = localStorage.getItem('token')
  
  if (token) {
    try {
      // ถอดรหัส Token เพื่อดึงข้อมูล User ออกมา
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
    // ลบ Token ทิ้ง และเด้งกลับไปหน้าเว็บหลัก (หรือหน้าล็อกอิน)
    localStorage.removeItem('token')
    router.push('/login') // หรือ router.push('/') แล้วแต่ว่าคุณตั้งหน้า login ไว้ที่ไหน
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
      
      <!-- ส่วนแสดงข้อมูลผู้ใช้งานตรงมุมขวาบน -->
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

          <!-- ตัวกั้นเมนูกับปุ่ม Logout -->
          <hr class="menu-divider" />

          <!-- ปุ่มออกจากระบบ -->
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

<style scoped>
.staff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1.5rem;
}

.staff-user-info .user-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 50px;
  color: white; 
}

.staff-user-info i {
  font-size: 1.5rem;
}

.staff-user-info span {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.role-text {
  font-size: 0.75rem;
  opacity: 0.8;
}

.menu-divider {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.1); 
  margin: 1rem 0;
}

/* ตกแต่งปุ่ม Logout */
.logout-btn {
  color: #dc3545 !important; 
  font-weight: bold;
}

.logout-btn:hover {
  background-color: #fee2e2 !important; 
}
</style>
