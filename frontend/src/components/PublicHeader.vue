<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const userRole = ref('')

function keepRoomQuery(path) {
  return {
    path,
    query: route.query.room ? { room: route.query.room } : {}
  }
}

const repairLink = computed(() => keepRoomQuery('/request/repair'))
const cleaningLink = computed(() => keepRoomQuery('/request/cleaning'))
const lostFoundLink = computed(() => keepRoomQuery('/lost-found'))

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

      <RouterLink :to="repairLink">
        <i class="fa-solid fa-wrench"></i>
        แจ้งซ่อม
      </RouterLink>

      <RouterLink :to="cleaningLink">
        <i class="fa-solid fa-broom"></i>
        แจ้งทำความสะอาด
      </RouterLink>

      <RouterLink :to="lostFoundLink">
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