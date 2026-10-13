<script setup>
import { ref, computed, onMounted } from 'vue'

const userRole = ref('')

onMounted(() => {
  const token = localStorage.getItem('token')
  
  if (token) {
    try {
      const payloadBase64 = token.split('.')[1]
      const decodedJson = atob(payloadBase64)
      const payload = JSON.parse(decodedJson)

      userRole.value = payload.role
    } catch (e) {
      console.error("Token ไม่ถูกต้อง")
    }
  }
})

const isAdmin = computed(() => userRole.value === 'admin')
</script>

<template>
  <header class="public-header">
    <RouterLink class="public-brand" to="/">
      CS BUILDING SERVICES
    </RouterLink>

    <nav class="public-nav">
      <RouterLink to="/">
        <i class="fa-solid fa-house"></i>
        หน้าหลัก
      </RouterLink>

      <RouterLink to="/lost-found">
        <i class="fa-solid fa-magnifying-glass"></i>
        ของหาย-ของได้คืน
      </RouterLink>

      <RouterLink 
        class="staff-entry" 
        :to="isAdmin ? '/staff/dashboard' : '/staff/requests'"
      >
        สำหรับเจ้าหน้าที่
      </RouterLink>
    </nav>
  </header>
</template>