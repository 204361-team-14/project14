<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { apiFetch, getAuth } from '../composables/useAuth'
import { formatId, sameId } from '../utils/format'

const auth = getAuth()
const userRole = auth?.role ?? ''
const currentUserId = auth?.userId ?? null

const requests = ref([])
const statuses = ref({})
const currentTab = ref('my_tasks')
const loading = ref(true)
const error = ref('')
const filters = reactive({ q: '', status: '', service_type: '', urgency: '' })

function urgencyClass(value) {
  if (value === 'เร่งด่วน') return 'urgent'
  if (value === 'ไม่เร่งด่วน') return 'noturgent'
  return 'normal'
}

async function loadRequests() {
  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, typeof value === 'string' ? value.trim() : value)
    })

    const response = await apiFetch(`/api/staff/requests?${params.toString()}`)
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()
    requests.value = data.requests || []
    statuses.value = data.statuses || {}
  } catch {
    error.value = 'ไม่สามารถโหลดรายการคำขอได้'
  } finally {
    loading.value = false
  }
}

async function deleteRequest(item) {
  if (item.status !== 'completed') return
  if (!confirm(`ยืนยันลบคำขอ ${formatId('REQ', item.id)} ?`)) return

  try {
    const response = await apiFetch(`/api/staff/requests/${item.id}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      alert(data.message || 'ไม่สามารถลบรายการได้')
      return
    }

    await loadRequests()
  } catch {
    alert('ไม่สามารถเชื่อมต่อกับระบบได้')
  }
}

const roleServiceType = computed(() => {
  if (userRole === 'technician') return 'แจ้งซ่อม'
  if (userRole === 'maid') return 'แจ้งทำความสะอาด'
  return ''
})

const displayRequests = computed(() => {
  if (userRole === 'admin') return requests.value

  if (currentTab.value === 'my_tasks') {
    return requests.value.filter((r) => sameId(r.assigned_to, currentUserId))
  }

  if (currentTab.value === 'unassigned') {
    return requests.value.filter((r) => (
      !r.assigned_to &&
      (!roleServiceType.value || r.service_type === roleServiceType.value)
    ))
  }

  return requests.value
})

const currentStats = computed(() => ({
  all: displayRequests.value.length,
  pending: displayRequests.value.filter((r) => (r.status || 'pending') === 'pending').length,
  in_progress: displayRequests.value.filter((r) => r.status === 'in_progress').length,
  completed: displayRequests.value.filter((r) => r.status === 'completed').length
}))

const columnCount = computed(() => (userRole === 'admin' ? 9 : 8))

onMounted(loadRequests)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>คำขอบริการ</h1>
      <p>ค้นหา กรอง และติดตามสถานะคำขอทั้งหมด</p>
    </div>

    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <section class="stats-grid four">
      <article class="stat-card"><span>ทั้งหมด</span><strong>{{ currentStats.all }}</strong></article>
      <article class="stat-card"><span>รอดำเนินการ</span><strong>{{ currentStats.pending }}</strong></article>
      <article class="stat-card"><span>กำลังดำเนินการ</span><strong>{{ currentStats.in_progress }}</strong></article>
      <article class="stat-card"><span>เสร็จสิ้น</span><strong>{{ currentStats.completed }}</strong></article>
    </section>

    <div v-if="userRole !== 'admin'" style="display: flex; gap: 10px; margin-bottom: 20px;">
      <button
        type="button"
        :class="currentTab === 'my_tasks' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'my_tasks'"
      >
        <i class="fa-solid fa-user-check"></i> งานของฉัน
      </button>

      <button
        type="button"
        :class="currentTab === 'unassigned' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'unassigned'"
      >
        <i class="fa-solid fa-inbox"></i> ยังไม่มอบหมาย
      </button>

      <button
        type="button"
        :class="currentTab === 'all' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'all'"
      >
        <i class="fa-solid fa-list"></i> งานทั้งหมด
      </button>
    </div>

    <section class="card">
      <form class="filter-grid requests" @submit.prevent="loadRequests">
        <input v-model="filters.q" placeholder="ค้นหาเลขคำขอ รายละเอียด ห้อง..." aria-label="ค้นหา">

        <select v-model="filters.status" aria-label="กรองตามสถานะ">
          <option value="">ทุกสถานะ</option>
          <option v-for="(label, key) in statuses" :key="key" :value="key">{{ label }}</option>
        </select>

        <select v-model="filters.service_type" aria-label="กรองตามประเภท">
          <option value="">ทุกประเภท</option>
          <option>แจ้งซ่อม</option>
          <option>แจ้งทำความสะอาด</option>
        </select>

        <select v-model="filters.urgency" aria-label="กรองตามความเร่งด่วน">
          <option value="">ทุกความเร่งด่วน</option>
          <option>เร่งด่วน</option>
          <option>ปกติ</option>
          <option>ไม่เร่งด่วน</option>
        </select>

        <button class="btn-primary">ค้นหา</button>
      </form>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>เลขคำขอ</th>
              <th>ประเภท</th>
              <th>ความเร่งด่วน</th>
              <th>สถานที่</th>
              <th>รายละเอียด</th>
              <th>สถานะ</th>
              <th v-if="userRole === 'admin'">ผู้รับผิดชอบ</th>
              <th>วันที่พบ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in displayRequests" :key="item.id">
              <td>{{ formatId('REQ', item.id) }}</td>
              <td>{{ item.service_type }}</td>
              <td>
                <span class="badge" :class="urgencyClass(item.urgency)">{{ item.urgency }}</span>
              </td>
              <td>{{ item.building }} ชั้น {{ item.floor }} ห้อง {{ item.room }}</td>
              <td class="description-cell">{{ item.description }}</td>
              <td>
                <StatusBadge
                  :status="item.status || 'pending'"
                  :label="statuses[item.status || 'pending'] || item.status"
                />
              </td>
              <td v-if="userRole === 'admin'">
                {{ item.assigned_to_name || '-' }}
              </td>
              <td>{{ item.problem_date || '-' }}<br>{{ item.problem_time || '' }}</td>
              <td>
                <div class="row-actions">
                  <RouterLink class="text-link" :to="`/staff/requests/${item.id}`">
                    <i class="fa-solid fa-eye"></i> ดู
                  </RouterLink>

                  <button
                    v-if="userRole === 'admin' && item.status === 'completed'"
                    class="text-danger"
                    type="button"
                    @click="deleteRequest(item)"
                  >
                    <i class="fa-solid fa-trash"></i> ลบ
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="!displayRequests.length">
              <td :colspan="columnCount" style="text-align: center; padding: 40px; color: #666;">
                <i class="fa-solid fa-folder-open" style="font-size: 24px; margin-bottom: 10px; color: #ccc; display: block;"></i>
                {{ loading ? 'กำลังโหลด...' : 'ไม่พบรายการ' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </StaffLayout>
</template>
