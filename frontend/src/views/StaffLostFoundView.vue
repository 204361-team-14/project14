<script setup>
import { onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'

const items = ref([])
const statuses = ref({})
const filters = reactive({ q: '', status: '' })

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

async function loadItems() {
  const params = new URLSearchParams()
  if (filters.q) params.set('q', filters.q)
  if (filters.status) params.set('status', filters.status)

  const response = await fetch(`/api/staff/lost-found?${params}`, {
    headers: getHeaders()
  })
  const data = await response.json()

  items.value = data.items || []
  statuses.value = data.statuses || {}
}

onMounted(loadItems)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>ของหาย-ของได้คืน</h1>
      <p>จัดการรายการของที่มีผู้พบและแจ้งเข้ามาในระบบ</p>
    </div>

    <section class="card">
      <form class="filter-grid lost-found" @submit.prevent="loadItems">
        <input v-model="filters.q" placeholder="ค้นหาสิ่งของ สถานที่...">

        <select v-model="filters.status">
          <option value="">ทุกสถานะ</option>
          <option v-for="(label, key) in statuses" :key="key" :value="key">
            {{ label }}
          </option>
        </select>

        <button class="btn-primary">ค้นหา</button>
      </form>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>สิ่งของ</th>
              <th>สถานที่</th>
              <th>วันที่</th>
              <th>สถานะ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>LF-{{ String(item.id).padStart(6, '0') }}</td>
              <td>{{ item.item_name }}</td>
              <td>{{ item.location || '-' }}</td>
              <td>{{ item.event_date || '-' }}</td>
              <td>
                <StatusBadge
                  :status="item.status"
                  :label="statuses[item.status] || item.status"
                />
              </td>
              <td>
                <RouterLink class="text-link" :to="`/staff/lost-found/${item.id}`">
                  ดูรายละเอียด
                </RouterLink>
              </td>
            </tr>

            <tr v-if="!items.length">
              <td colspan="6">ยังไม่มีรายการ</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </StaffLayout>
</template>
