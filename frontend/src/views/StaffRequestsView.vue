<script setup>
import { onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'

const requests = ref([])
const statuses = ref({})
const stats = reactive({ all: 0, pending: 0, in_progress: 0, completed: 0 })
const filters = reactive({ q: '', status: '', service_type: '', urgency: '' })

function urgencyClass(value) {
  if (value === 'เร่งด่วน') return 'urgent'
  if (value === 'ไม่เร่งด่วน') return 'noturgent'
  return 'normal'
}

async function loadRequests() {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })

  const response = await fetch(`/api/staff/requests?${params}`)
  const data = await response.json()

  requests.value = data.requests || []
  statuses.value = data.statuses || {}
  Object.assign(stats, data.stats || {})
}

async function deleteRequest(item) {
  if (item.status !== 'completed') return
  if (!confirm(`ยืนยันลบคำขอ REQ-${String(item.id).padStart(6, '0')} ?`)) return

  const response = await fetch(`/api/staff/requests/${item.id}`, {
    method: 'DELETE'
  })

  const data = await response.json()
  if (!response.ok) {
    alert(data.message || 'ไม่สามารถลบรายการได้')
    return
  }

  await loadRequests()
}

onMounted(loadRequests)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>คำขอบริการ</h1>
      <p>ค้นหา กรอง และติดตามสถานะคำขอทั้งหมด</p>
    </div>

    <section class="stats-grid four">
      <article class="stat-card"><span>ทั้งหมด</span><strong>{{ stats.all }}</strong></article>
      <article class="stat-card"><span>รอดำเนินการ</span><strong>{{ stats.pending }}</strong></article>
      <article class="stat-card"><span>กำลังดำเนินการ</span><strong>{{ stats.in_progress }}</strong></article>
      <article class="stat-card"><span>เสร็จสิ้น</span><strong>{{ stats.completed }}</strong></article>
    </section>

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
              <th>สถานะ</th>
              <th>วันที่พบ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in requests" :key="item.id">
              <td>REQ-{{ String(item.id).padStart(6, '0') }}</td>
              <td>{{ item.service_type }}</td>
              <td>{{ item.building }} ชั้น {{ item.floor }} ห้อง {{ item.room }}</td>
              <td class="description-cell">{{ item.description }}</td>
              <td><span class="badge" :class="urgencyClass(item.urgency)">{{ item.urgency }}</span></td>
              <td>
                <StatusBadge
                  :status="item.status || 'pending'"
                  :label="statuses[item.status || 'pending'] || item.status"
                />
              </td>
              <td>{{ item.problem_date || '-' }} {{ item.problem_time || '' }}</td>
              <td>
                <div class="row-actions">
                  <RouterLink class="text-link" :to="`/staff/requests/${item.id}`">
                    <i class="fa-solid fa-eye"></i> ดู
                  </RouterLink>

                  <button
                    v-if="item.status === 'completed'"
                    class="text-danger"
                    type="button"
                    @click="deleteRequest(item)"
                  >
                    <i class="fa-solid fa-trash"></i> ลบ
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="!requests.length">
              <td colspan="8">ไม่พบรายการ</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </StaffLayout>
</template>
