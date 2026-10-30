<script setup>
import { onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { apiFetch } from '../composables/useAuth'
import { formatId } from '../utils/format'

const stats = reactive({
  all: 0,
  pending: 0,
  in_progress: 0,
  completed: 0,
  lost_found_open: 0
})
const latestRequests = ref([])
const latestLostFound = ref([])
const requestStatuses = ref({})
const lostFoundStatuses = ref({})
const loading = ref(true)
const error = ref('')

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    const response = await apiFetch('/api/staff/dashboard')
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()

    Object.assign(stats, data.stats || {})
    latestRequests.value = data.latest_requests || []
    latestLostFound.value = data.latest_lost_found || []
    requestStatuses.value = data.request_statuses || {}
    lostFoundStatuses.value = data.lost_found_statuses || {}
  } catch {
    error.value = 'ไม่สามารถโหลดข้อมูลแดชบอร์ดได้'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>แดชบอร์ด</h1>
      <p>ภาพรวมสถานะงานบริการอาคาร</p>
    </div>

    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <section class="stats-grid five">
      <article class="stat-card">
        <span>คำขอทั้งหมด</span>
        <strong>{{ stats.all }}</strong>
      </article>
      <article class="stat-card">
        <span>รอดำเนินการ</span>
        <strong>{{ stats.pending }}</strong>
      </article>
      <article class="stat-card">
        <span>กำลังดำเนินการ</span>
        <strong>{{ stats.in_progress }}</strong>
      </article>
      <article class="stat-card">
        <span>เสร็จสิ้น</span>
        <strong>{{ stats.completed }}</strong>
      </article>
      <article class="stat-card">
        <span>ของที่พบที่ยังเปิด</span>
        <strong>{{ stats.lost_found_open }}</strong>
      </article>
    </section>

    <div class="dashboard-grid">
      <section class="card">
        <h2>คำขอล่าสุด</h2>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>เลขคำขอ</th>
                <th>ประเภท</th>
                <th>สถานะ</th>
                <th>เวลา</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in latestRequests" :key="item.id">
                <td>{{ formatId('REQ', item.id) }}</td>
                <td>{{ item.service_type }}</td>
                <td>
                  <StatusBadge
                    :status="item.status || 'pending'"
                    :label="requestStatuses[item.status || 'pending'] || item.status"
                  />
                </td>
                <td>{{ item.created_at }}</td>
                <td>
                  <RouterLink class="text-link" :to="`/staff/requests/${item.id}`">ดู</RouterLink>
                </td>
              </tr>
              <tr v-if="!latestRequests.length">
                <td colspan="5">{{ loading ? 'กำลังโหลด...' : 'ยังไม่มีข้อมูล' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h2>ของที่เก็บได้ล่าสุด</h2>

        <div v-for="item in latestLostFound" :key="item.id" class="compact-item">
          <strong>{{ item.item_name }}</strong>
          <p class="muted">{{ item.location || '-' }}</p>
          <StatusBadge
            :status="item.status"
            :label="lostFoundStatuses[item.status] || item.status"
          />
          <RouterLink class="text-link" :to="`/staff/lost-found/${item.id}`">
            ดูรายละเอียด
          </RouterLink>
        </div>

        <p v-if="!latestLostFound.length" class="muted">
          {{ loading ? 'กำลังโหลด...' : 'ยังไม่มีรายการ' }}
        </p>
      </section>
    </div>
  </StaffLayout>
</template>
