<script setup>
import { onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { apiFetch } from '../composables/useAuth'
import { formatId } from '../utils/format'

const items = ref([])
const statuses = ref({})
const filters = reactive({ q: '', status: '' })
const loading = ref(true)
const error = ref('')

async function loadItems() {
  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams()
    if (filters.q.trim()) params.set('q', filters.q.trim())
    if (filters.status) params.set('status', filters.status)

    const response = await apiFetch(`/api/staff/lost-found?${params}`)
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()
    items.value = data.items || []
    statuses.value = data.statuses || {}
  } catch {
    error.value = 'ไม่สามารถโหลดรายการได้'
  } finally {
    loading.value = false
  }
}

onMounted(loadItems)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>ของหาย-ของได้คืน</h1>
      <p>จัดการรายการของที่มีผู้พบและแจ้งเข้ามาในระบบ</p>
    </div>

    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <section class="card">
      <form class="filter-grid lost-found" @submit.prevent="loadItems">
        <input v-model="filters.q" placeholder="ค้นหาสิ่งของ สถานที่..." aria-label="ค้นหา">

        <select v-model="filters.status" aria-label="กรองตามสถานะ">
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
<<<<<<< Updated upstream
              <td>LF-{{ String(item.id).padStart(6, '0') }}</td>
              <td>{{ item.item_name }}</td>
              <td>{{ item.location || '-' }}</td>
              <td>{{ item.event_date || '-' }}</td>
=======
              <td class="nowrap-cell">{{ formatId('LF', item.id) }}</td>
              <td class="text-cell">{{ item.item_name }}</td>
              <td class="text-cell">{{ item.location || '-' }}</td>
              <td class="nowrap-cell">{{ item.event_date || '-' }}</td>
>>>>>>> Stashed changes
              <td>
                <StatusBadge
                  :status="item.status"
                  :label="statuses[item.status] || item.status"
                />
              </td>
              <td>
                <div class="row-actions">
                  <RouterLink class="text-link" :to="`/staff/lost-found/${item.id}`">
                    <i class="fa-solid fa-eye"></i> ดู
                  </RouterLink>
                </div>
              </td>
            </tr>

            <tr v-if="!items.length">
              <td colspan="6">{{ loading ? 'กำลังโหลด...' : 'ยังไม่มีรายการ' }}</td>
<<<<<<< Updated upstream
              <td colspan="6">ยังไม่มีรายการ</td>
=======
              <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                <i class="fa-solid fa-folder-open" style="font-size: 24px; margin-bottom: 10px; color: #ccc; display: block;"></i>
                {{ loading ? 'กำลังโหลด...' : 'ยังไม่มีรายการ' }}
              </td>
>>>>>>> Stashed changes
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </StaffLayout>
</template>

<style scoped>
.nowrap-cell {
  white-space: nowrap;
}

.text-cell {
  min-width: 150px;
}
</style>
