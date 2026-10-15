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

const userRole = ref('')
const currentUserId = ref(null)
const message = ref('')
const error = ref('')

const staffList = ref([])
const selectedStaffId = ref('')
const completionFile = ref(null)

const requestId = computed(() => route.params.id)

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

async function loadDetail() {
  const response = await fetch(`/api/staff/requests/${requestId.value}`, {
    headers: getHeaders()
  })
  if (!response.ok) {
    router.replace('/staff/requests')
    return
  }

  const data = await response.json()
  item.value = data.request
  history.value = data.history || []
  statuses.value = data.statuses || {}
  note.value = item.value.staff_note || ''
  selectedStaffId.value = item.value.assigned_to || ''
}

async function loadStaffList() {
  const response = await fetch('/api/staff/list', { headers: getHeaders() })
  if (response.ok) {
    const data = await response.json()
    staffList.value = data.staff || []
  }
}

const availableStaff = computed(() => {
  if (!item.value) return []
  if (item.value.service_type === 'แจ้งทำความสะอาด') {
    return staffList.value.filter(s => s.role === 'maid')
  } else {
    return staffList.value.filter(s => s.role === 'technician')
  }
})

const allImages = computed(() => {
  if (!item.value) return []
  const imgs = item.value.images?.length ? [...item.value.images] : (item.value.image_path ? [item.value.image_path] : [])
  if (item.value.completion_image_path) {
    imgs.push(item.value.completion_image_path)
  }
  return imgs
})

const isAssignedToMe = computed(() => item.value && item.value.assigned_to == currentUserId.value)
const canManageTask = computed(() => userRole.value === 'admin' || isAssignedToMe.value)

async function assignStaff() {
  message.value = ''
  error.value = ''

  const response = await fetch(`/api/staff/requests/${requestId.value}/assign`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify({ staff_id: selectedStaffId.value || null })
  })
  
  if (response.ok) {
    message.value = 'อัปเดตผู้รับผิดชอบเรียบร้อยแล้ว'
    await loadDetail()
    setTimeout(() => { message.value = '' }, 3000)
  } else {
    const data = await response.json().catch(() => ({}))
    error.value = data.message || 'เกิดข้อผิดพลาดในการจ่ายงาน'
  }
}

function onFileChange(event) {
  completionFile.value = event.target.files[0]
}

async function completeWithImage() {
  if (!completionFile.value) {
    alert('กรุณาแนบรูปภาพหลักฐานการทำงานเสร็จสิ้น')
    return
  }

  const formData = new FormData()
  formData.append('images', completionFile.value)

  const token = localStorage.getItem('token')
  const response = await fetch(`/api/staff/requests/${requestId.value}/complete`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  })

  if (response.ok) {
    alert('บันทึกงานเสร็จสิ้นและส่งรูปหลักฐานเรียบร้อยแล้ว')
    completionFile.value = null
    await loadDetail()
  } else {
    const data = await response.json()
    alert(data.message || 'เกิดข้อผิดพลาดในการอัปโหลด')
  }
}

function openImageViewer(index) {
  imageViewerIndex.value = index
}

function closeImageViewer() {
  imageViewerIndex.value = -1
}

async function updateStatus(status) {
  const statusLabel = statuses.value[status] || status;

  if (status === 'completed') {
    if (!confirm(`ยืนยันเปลี่ยนสถานะเป็น "${statusLabel}" ใช่หรือไม่?\n(เมื่อเสร็จสิ้นแล้วจะไม่สามารถเปลี่ยนสถานะกลับมาได้อีก)`)) {
      return; 
    }
  } else {
    if (!confirm(`ยืนยันการเปลี่ยนสถานะเป็น "${statusLabel}" ใช่หรือไม่?`)) {
      return;
    }
  }

  const response = await fetch(`/api/staff/requests/${requestId.value}/status`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify({ status })
  })
  
  if (response.ok) await loadDetail()
}

async function saveNote() {
  const response = await fetch(`/api/staff/requests/${requestId.value}/note`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify({ staff_note: note.value })
  })
  if (response.ok) await loadDetail()
}

async function deleteRequest() {
  if (item.value?.status !== 'completed') return
  if (!confirm(`ยืนยันลบคำขอ REQ-${String(item.value.id).padStart(6, '0')} ? การลบไม่สามารถย้อนกลับได้`)) return

  const response = await fetch(`/api/staff/requests/${requestId.value}`, {
    method: 'DELETE',
    headers: getHeaders()
  })

  const data = await response.json()
  if (!response.ok) {
    alert(data.message || 'ไม่สามารถลบรายการได้')
    return
  }
  router.push('/staff/requests')
}

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    const payload = JSON.parse(atob(token.split('.')[1]))
    userRole.value = payload.role
    currentUserId.value = payload.user_id 
  }
  
  loadDetail()
  if (userRole.value === 'admin') {
    loadStaffList()
  }
})
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

      <p v-if="message" class="flash success">{{ message }}</p>
      <p v-if="error" class="flash error">{{ error }}</p>

      <section class="card detail-card">
        <div class="detail-grid detail-grid-auto">
          <div><span>ประเภทบริการ</span><strong>{{ item.service_type }}</strong></div>
          <div><span>ความเร่งด่วน</span><strong>{{ item.urgency }}</strong></div>
          <div>
            <span>สถานะ</span>
            <StatusBadge :status="item.status" :label="statuses[item.status] || item.status" />
          </div>
          <div><span>วันที่/เวลา</span><strong>{{ item.problem_date || '-' }} {{ item.problem_time || '' }}</strong></div>
          <div>
            <span>ผู้รับผิดชอบ</span>
            <strong :class="{'text-primary': item.assigned_to_name}">
              {{ item.assigned_to_name || 'ยังไม่มี (รอแอดมินจ่ายงาน)' }}
            </strong>
          </div>
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
          <h3>รูปภาพประกอบ (ผู้แจ้ง)</h3>
          <div v-if="item.images?.length" class="staff-image-grid">
            <button v-for="(image, index) in item.images" :key="image" class="staff-image-button" type="button" @click="openImageViewer(index)">
              <img class="detail-image" :src="`/uploads/${image}`" alt="รูปประกอบ">
            </button>
          </div>
          <button v-else-if="item.image_path" class="staff-image-button single" type="button" @click="openImageViewer(0)">
            <img class="detail-image" :src="`/uploads/${item.image_path}`" alt="รูปประกอบ">
          </button>
          <p v-else class="muted">ไม่มีรูปภาพ</p>
        </div>

        <div class="detail-section" v-if="item.completion_image_path">
          <h3 class="completion-title">รูปภาพหลักฐาน (ตอนเสร็จงาน)</h3>
          <button class="staff-image-button single completion-image-button" type="button" @click="openImageViewer(allImages.length - 1)">
            <img class="detail-image" :src="`/uploads/${item.completion_image_path}`" alt="รูปหลักฐานเสร็จงาน">
          </button>
        </div>
      </section>

      <section class="card" v-if="userRole === 'admin' && item.status !== 'completed' && item.status !== 'cancelled'">
        <h2>จ่ายงาน (มอบหมายผู้รับผิดชอบ)</h2>
        <div class="assign-staff-row">
          <select v-model="selectedStaffId" class="assign-staff-select">
            <option value="">-- ยังไม่ระบุ / ยกเลิกการมอบหมาย --</option>
            <option v-for="staff in availableStaff" :key="staff.id" :value="staff.id">
              {{ staff.username }} ({{ staff.role === 'maid' ? 'แม่บ้าน' : 'ช่าง' }})
            </option>
          </select>
          <button class="btn-primary" @click="assignStaff">บันทึกการจ่ายงาน</button>
        </div>
      </section>

      <section class="card" v-if="userRole !== 'admin' && isAssignedToMe && item.status !== 'completed' && item.status !== 'cancelled'">
        <h2>ส่งงาน (เสร็จสิ้นภารกิจ)</h2>
        <p class="muted">กรุณาแนบรูปภาพหลักฐานการทำงาน เพื่อเปลี่ยนสถานะเป็นเสร็จสิ้น</p>
        <div class="complete-task-row">
          <input type="file" accept="image/*" @change="onFileChange" class="completion-file-input">
          <button class="btn-primary complete-task-button" @click="completeWithImage">
            <i class="fa-solid fa-check"></i> ส่งรูปและเสร็จสิ้นงาน
          </button>
        </div>
      </section>

      <section class="card" v-if="userRole !== 'admin' && !isAssignedToMe">
        <h2 class="not-assigned-title">คุณไม่ได้เป็นผู้รับผิดชอบงานนี้</h2>
        <p class="muted not-assigned-text">สามารถดูรายละเอียดได้อย่างเดียว ไม่สามารถจัดการแก้ไขได้</p>
      </section>

      <template v-if="canManageTask">
        <section class="card" v-if="item.status !== 'completed'">
          <h2>เปลี่ยนสถานะ (Manual)</h2>
          <div class="button-row">
            <button
              v-for="(label, key) in statuses"
              :key="key"
              v-show="userRole === 'admin' || (key !== 'cancelled' && key !== 'completed')"
              class="status-button"
              :class="{ active: item.status === key }"
              :disabled="item.status === key"
              @click="updateStatus(key)"
            >
              {{ label }}
            </button>
          </div>
        </section>

        <section v-if="userRole === 'admin' && item.status === 'completed'" class="card danger-card">
          <h2>ลบรายการที่เสร็จแล้ว</h2>
          <button class="btn-danger" @click="deleteRequest">
            <i class="fa-solid fa-trash"></i> ลบคำขอที่เสร็จแล้ว
          </button>
        </section>

        <section class="card">
          <h2>หมายเหตุเจ้าหน้าที่</h2>
          <textarea v-model="note" class="note-box" placeholder="เช่น รออะไหล่ / นัดช่างแล้ว" :disabled="item.status === 'completed'"></textarea>
          <button class="btn-primary" @click="saveNote" v-if="item.status !== 'completed'">บันทึกหมายเหตุ</button>
        </section>
      </template>

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
      :images="allImages"
      :index="imageViewerIndex"
      @update:index="imageViewerIndex = $event"
      @close="closeImageViewer"
    />
  </StaffLayout>
</template>
