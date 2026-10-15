<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'

const requests = ref([])
const statuses = ref({})
const userRole = ref('')
const currentUserId = ref(null)
const currentTab = ref('my_tasks')
const stats = reactive({ all: 0, pending: 0, in_progress: 0, completed: 0 })
const filters = reactive({ q: '', status: '', service_type: '', urgency: '' })

function urgencyClass(value) {
  if (value === 'เร่งด่วน') return 'urgent'
  if (value === 'ไม่เร่งด่วน') return 'noturgent'
  return 'normal'
}

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

async function loadRequests() {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })

  const response = await fetch(`/api/staff/requests?${params.toString()}`, {
    headers: getHeaders()
  })
  const data = await response.json()

  requests.value = data.requests || []
  statuses.value = data.statuses || {}
  Object.assign(stats, data.stats || {})
}

async function deleteRequest(item) {
  if (item.status !== 'completed') return
  if (!confirm(`ยืนยันลบคำขอ REQ-${String(item.id).padStart(6, '0')} ?`)) return

  const response = await fetch(`/api/staff/requests/${item.id}`, {
    method: 'DELETE',
    headers: getHeaders()
  })

  const data = await response.json()
  if (!response.ok) {
    alert(data.message || 'ไม่สามารถลบรายการได้')
    return
  }

  await loadRequests()
}

const displayRequests = computed(() => {
  if (userRole.value === 'admin') {
    return requests.value 
  }

  if (currentTab.value === 'my_tasks') {
    return requests.value.filter(r => r.assigned_to == currentUserId.value)
  } else if (currentTab.value === 'unassigned') {
    return requests.value.filter(r => !r.assigned_to)
  }
  
  return requests.value 
})

const currentStats = computed(() => {
  return {
    all: displayRequests.value.length,
    pending: displayRequests.value.filter(r => r.status === 'pending').length,
    in_progress: displayRequests.value.filter(r => r.status === 'in_progress').length,
    completed: displayRequests.value.filter(r => r.status === 'completed').length,
  }
})

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    const payload = JSON.parse(atob(token.split('.')[1]))
    userRole.value = payload.role
    currentUserId.value = payload.user_id
  }
  loadRequests()
})
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>คำขอบริการ</h1>
      <p>ค้นหา กรอง และติดตามสถานะคำขอทั้งหมด</p>
    </div>

    <section class="stats-grid four">
      <article class="stat-card"><span>ทั้งหมด</span><strong>{{ currentStats.all }}</strong></article>
      <article class="stat-card"><span>รอดำเนินการ</span><strong>{{ currentStats.pending }}</strong></article>
      <article class="stat-card"><span>กำลังดำเนินการ</span><strong>{{ currentStats.in_progress }}</strong></article>
      <article class="stat-card"><span>เสร็จสิ้น</span><strong>{{ currentStats.completed }}</strong></article>
    </section>

    <div v-if="userRole !== 'admin'" style="display: flex; gap: 10px; margin-bottom: 20px;">
      <button 
        :class="currentTab === 'my_tasks' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'my_tasks'"
      >
        <i class="fa-solid fa-user-check"></i> งานของฉัน
      </button>
      
      <button 
        :class="currentTab === 'unassigned' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'unassigned'"
      >
        <i class="fa-solid fa-inbox"></i> งานใหม่ (รอรับ)
      </button>

      <button 
        :class="currentTab === 'all' ? 'btn-primary' : 'btn-soft'"
        @click="currentTab = 'all'"
      >
        <i class="fa-solid fa-list"></i> งานทั้งหมด
      </button>
    </div>

    <section class="card">
      <form class="filter-grid requests" @submit.prevent="loadRequests">
        <input v-model="filters.q" placeholder="ค้นหาเลขคำขอ รายละเอียด ห้อง...">

        <select v-model="filters.status">
          <option value="">ทุกสถานะ</option>
          <option v-for="(label, key) in statuses" :key="key" :value="key">{{ label }}</option>
        </select>

        <select v-model="filters.service_type">
          <option value="">ทุกประเภท</option>
          <option>แจ้งซ่อม</option>
          <option>แจ้งทำความสะอาด</option>
        </select>

        <select v-model="filters.urgency">
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
              <th>สถานที่</th>
              <th>รายละเอียด</th>
              <th>ความเร่งด่วน</th>
              <th v-if="userRole === 'admin'">ผู้รับผิดชอบ</th>
              <th>สถานะ</th>
              <th>วันที่พบ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in displayRequests" :key="item.id">
              <td>REQ-{{ String(item.id).padStart(6, '0') }}</td>
              <td>
                {{ item.service_type }}<br>
                <span class="badge" :class="urgencyClass(item.urgency)" style="margin-top: 5px;">{{ item.urgency }}</span>
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
              <td colspan="9" style="text-align: center; padding: 40px; color: #666;">
                <i class="fa-solid fa-folder-open" style="font-size: 24px; margin-bottom: 10px; color: #ccc; display: block;"></i>
                ไม่พบรายการ
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </StaffLayout>
</template>
