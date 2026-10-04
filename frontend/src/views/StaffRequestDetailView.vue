<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import ImageLightbox from '../components/ImageLightbox.vue'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const history = ref([])
const statuses = ref({})
const note = ref('')
const imageViewerIndex = ref(-1)

const requestId = computed(() => route.params.id)

async function loadDetail() {
  const response = await fetch(`/api/staff/requests/${requestId.value}`)
  if (!response.ok) {
    router.replace('/staff/requests')
    return
  }

  const data = await response.json()
  item.value = data.request
  history.value = data.history || []
  statuses.value = data.statuses || {}
  note.value = item.value.staff_note || ''
}

function openImageViewer(index) {
  imageViewerIndex.value = index
}

function closeImageViewer() {
  imageViewerIndex.value = -1
}

async function updateStatus(status) {
  const response = await fetch(`/api/staff/requests/${requestId.value}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })

  if (response.ok) await loadDetail()
}

async function saveNote() {
  const response = await fetch(`/api/staff/requests/${requestId.value}/note`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ staff_note: note.value })
  })

  if (response.ok) await loadDetail()
}

async function deleteRequest() {
  if (item.value?.status !== 'completed') return
  if (!confirm(`ยืนยันลบคำขอ REQ-${String(item.value.id).padStart(6, '0')} ? การลบไม่สามารถย้อนกลับได้`)) return

  const response = await fetch(`/api/staff/requests/${requestId.value}`, {
    method: 'DELETE'
  })
  const data = await response.json()

  if (!response.ok) {
    alert(data.message || 'ไม่สามารถลบรายการได้')
    return
  }

  router.push('/staff/requests')
}

onMounted(loadDetail)
</script>

<template>
  <StaffLayout>
    <template v-if="item">
      <RouterLink class="back-link" to="/staff/requests">
        <i class="fa-solid fa-chevron-left"></i>
        กลับรายการคำขอ
      </RouterLink>

      <div class="staff-page-title">
        <h1>รายละเอียดคำขอ REQ-{{ String(item.id).padStart(6, '0') }}</h1>
      </div>

      <section class="card detail-card">
        <div class="detail-grid four">
          <div><span>ประเภทบริการ</span><strong>{{ item.service_type }}</strong></div>
          <div><span>ความเร่งด่วน</span><strong>{{ item.urgency }}</strong></div>
          <div>
            <span>สถานะ</span>
            <StatusBadge :status="item.status" :label="statuses[item.status] || item.status" />
          </div>
          <div><span>วันที่/เวลา</span><strong>{{ item.problem_date || '-' }} {{ item.problem_time || '' }}</strong></div>
        </div>

        <div class="detail-section">
          <h3>รายละเอียด</h3>
          <p>{{ item.description }}</p>
        </div>

        <div class="detail-section">
          <h3>ตำแหน่ง</h3>
          <p>อาคาร {{ item.building }} · ชั้น {{ item.floor }} · ห้อง {{ item.room }}</p>
        </div>

        <div class="detail-section">
          <h3>รูปภาพประกอบ</h3>

          <div
            v-if="item.images?.length"
            class="staff-image-grid"
          >
            <button
              v-for="(image, index) in item.images"
              :key="image"
              class="staff-image-button"
              type="button"
              @click="openImageViewer(index)"
            >
              <img
                class="detail-image"
                :src="`/uploads/${image}`"
                alt="รูปประกอบ"
              >
            </button>
          </div>

          <button
            v-else-if="item.image_path"
            class="staff-image-button single"
            type="button"
            @click="openImageViewer(0)"
          >
            <img
              class="detail-image"
              :src="`/uploads/${item.image_path}`"
              alt="รูปประกอบ"
            >
          </button>

          <p v-else class="muted">ไม่มีรูปภาพ</p>
        </div>
      </section>

      <section class="card">
        <h2>เปลี่ยนสถานะ</h2>
        <div class="button-row">
          <button
            v-for="(label, key) in statuses"
            :key="key"
            class="status-button"
            :class="{ active: item.status === key }"
            :disabled="item.status === key"
            @click="updateStatus(key)"
          >
            {{ label }}
          </button>
        </div>
      </section>

      <section v-if="item.status === 'completed'" class="card danger-card">
        <h2>ลบรายการที่เสร็จแล้ว</h2>
        <p class="muted">เมื่อลบแล้ว รายการนี้ ประวัติ และรูปประกอบจะถูกลบออกจากระบบ</p>
        <button class="btn-danger" @click="deleteRequest">
          <i class="fa-solid fa-trash"></i>
          ลบคำขอที่เสร็จแล้ว
        </button>
      </section>

      <section class="card">
        <h2>หมายเหตุเจ้าหน้าที่</h2>
        <textarea v-model="note" class="note-box" placeholder="เช่น รออะไหล่ / นัดช่างแล้ว"></textarea>
        <button class="btn-primary" @click="saveNote">บันทึกหมายเหตุ</button>
      </section>

      <section class="card">
        <h2>ประวัติการดำเนินการ</h2>
        <div class="history-list">
          <div v-for="entry in history" :key="entry.id">
            <strong>{{ entry.created_at }}</strong>
            <p>{{ entry.detail || entry.action }}</p>
          </div>
          <p v-if="!history.length" class="muted">ยังไม่มีประวัติ</p>
        </div>
      </section>
    </template>

    <ImageLightbox
      :images="item?.images?.length ? item.images : (item?.image_path ? [item.image_path] : [])"
      :index="imageViewerIndex"
      @update:index="imageViewerIndex = $event"
      @close="closeImageViewer"
    />
  </StaffLayout>
</template>
