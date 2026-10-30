<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import ImageLightbox from '../components/ImageLightbox.vue'
import { apiFetch, getAuth } from '../composables/useAuth'
import { alertDialog, confirmDialog } from '../composables/useDialog'
import { useImageUploader } from '../composables/useImageUploader'
import { formatId, sameId } from '../utils/format'

const route = useRoute()
const router = useRouter()

const auth = getAuth()
const userRole = auth?.role ?? ''
const currentUserId = auth?.userId ?? null

const item = ref(null)
const history = ref([])
const statuses = ref({})
const note = ref('')
const imageViewerIndex = ref(-1)

const message = ref('')
const error = ref('')

const staffList = ref([])
const selectedStaffId = ref('')
const {
  previews: completionPreviews,
  files: completionFiles,
  notice: completionNotice,
  onChange: onCompletionImageChange,
  remove: removeCompletionImage,
  clear: clearCompletionImages
} = useImageUploader(1)

const completing = ref(false)
const savingNote = ref(false)
const assigning = ref(false)

const requestId = computed(() => route.params.id)

function showMessage(text) {
  error.value = ''
  message.value = text
  setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 3000)
}

async function loadDetail() {
  try {
    const response = await apiFetch(`/api/staff/requests/${requestId.value}`)
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
  } catch {
    error.value = 'ไม่สามารถโหลดรายละเอียดคำขอได้'
  }
}

async function loadStaffList() {
  try {
    const response = await apiFetch('/api/staff/list')
    if (response.ok) {
      const data = await response.json()
      staffList.value = data.staff || []
    }
  } catch {
  }
}

const availableStaff = computed(() => {
  if (!item.value) return []
  const role = item.value.service_type === 'แจ้งทำความสะอาด' ? 'maid' : 'technician'
  return staffList.value.filter((s) => s.role === role)
})

const allImages = computed(() => {
  if (!item.value) return []

  const imgs = item.value.images?.length
    ? [...item.value.images]
    : (item.value.image_path ? [item.value.image_path] : [])

  if (item.value.completion_image_path) {
    imgs.push(item.value.completion_image_path)
  }

  return imgs
})

const isOpen = computed(() => (
  item.value && item.value.status !== 'completed' && item.value.status !== 'cancelled'
))
const isAssignedToMe = computed(() => (
  Boolean(item.value) && sameId(item.value.assigned_to, currentUserId)
))
const canManageTask = computed(() => userRole === 'admin' || isAssignedToMe.value)

async function assignStaff() {
  if (assigning.value) return

  assigning.value = true
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(`/api/staff/requests/${requestId.value}/assign`, {
      method: 'PATCH',
      body: JSON.stringify({ staff_id: selectedStaffId.value || null })
    })

    if (response.ok) {
      await loadDetail()
      showMessage('อัปเดตผู้รับผิดชอบเรียบร้อยแล้ว')
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'เกิดข้อผิดพลาดในการจ่ายงาน'
    }
  } catch {
    error.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  } finally {
    assigning.value = false
  }
}

async function completeWithImage() {
  if (completing.value) return

  if (!completionFiles.value.length) {
    await alertDialog('กรุณาแนบรูปภาพหลักฐานการทำงานเสร็จสิ้น', { title: 'ยังไม่ได้แนบรูปภาพ' })
    return
  }

  completing.value = true

  try {
    const formData = new FormData()
    formData.append('images', completionFiles.value[0])

    const response = await apiFetch(`/api/staff/requests/${requestId.value}/complete`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      clearCompletionImages()
      await loadDetail()
      showMessage('บันทึกงานเสร็จสิ้นและส่งรูปหลักฐานเรียบร้อยแล้ว')
    } else {
      const data = await response.json().catch(() => ({}))
      await alertDialog(data.message || 'เกิดข้อผิดพลาดในการอัปโหลด', { title: 'อัปโหลดไม่สำเร็จ', variant: 'error' })
    }
  } catch {
    await alertDialog('ไม่สามารถเชื่อมต่อกับระบบได้', { title: 'เกิดข้อผิดพลาด', variant: 'error' })
  } finally {
    completing.value = false
  }
}

function openImageViewer(index) {
  imageViewerIndex.value = index
}

function closeImageViewer() {
  imageViewerIndex.value = -1
}

async function updateStatus(status) {
  const statusLabel = statuses.value[status] || status

  const confirmText = status === 'completed'
    ? `ยืนยันเปลี่ยนสถานะเป็น "${statusLabel}" ใช่หรือไม่?\n(เมื่อเสร็จสิ้นแล้วจะไม่สามารถเปลี่ยนสถานะกลับมาได้อีก)`
    : `ยืนยันการเปลี่ยนสถานะเป็น "${statusLabel}" ใช่หรือไม่?`

  const ok = await confirmDialog(confirmText, {
    title: 'เปลี่ยนสถานะคำขอ',
    confirmText: 'ยืนยัน',
    variant: status === 'completed' ? 'warning' : 'default'
  })
  if (!ok) return

  try {
    const response = await apiFetch(`/api/staff/requests/${requestId.value}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    })

    if (response.ok) {
      await loadDetail()
      showMessage('เปลี่ยนสถานะเรียบร้อยแล้ว')
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถเปลี่ยนสถานะได้'
    }
  } catch {
    error.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  }
}

async function saveNote() {
  if (savingNote.value) return

  savingNote.value = true

  try {
    const response = await apiFetch(`/api/staff/requests/${requestId.value}/note`, {
      method: 'PATCH',
      body: JSON.stringify({ staff_note: note.value })
    })

    if (response.ok) {
      await loadDetail()
      showMessage('บันทึกหมายเหตุเรียบร้อยแล้ว')
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถบันทึกหมายเหตุได้'
    }
  } catch {
    error.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  } finally {
    savingNote.value = false
  }
}

async function deleteRequest() {
  if (item.value?.status !== 'completed') return
  const ok = await confirmDialog(
    `ต้องการลบคำขอ ${formatId('REQ', item.value.id)} ใช่หรือไม่?\nการลบไม่สามารถย้อนกลับได้`,
    { title: 'ลบคำขอ', confirmText: 'ลบ', variant: 'danger' }
  )
  if (!ok) return

  try {
    const response = await apiFetch(`/api/staff/requests/${requestId.value}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      await alertDialog(data.message || 'ไม่สามารถลบรายการได้', { title: 'ลบไม่สำเร็จ', variant: 'error' })
      return
    }

    router.push('/staff/requests')
  } catch {
    await alertDialog('ไม่สามารถเชื่อมต่อกับระบบได้', { title: 'เกิดข้อผิดพลาด', variant: 'error' })
  }
}

// เปลี่ยนคำขอ (เช่นกดลิงก์ไปคำขออื่น) ให้โหลดใหม่
watch(requestId, loadDetail)

onMounted(() => {
  loadDetail()
  if (userRole === 'admin') loadStaffList()
})
</script>

<template>
  <StaffLayout>
    <p v-if="message" class="flash success" role="status">{{ message }}</p>
    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <template v-if="item">
      <RouterLink class="back-link" to="/staff/requests">
        <i class="fa-solid fa-chevron-left"></i>
        กลับรายการคำขอ
      </RouterLink>

      <div class="staff-page-title">
        <h1>รายละเอียดคำขอ {{ formatId('REQ', item.id) }}</h1>
      </div>

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
            <button
              v-for="(image, index) in item.images"
              :key="image"
              class="staff-image-button"
              type="button"
              @click="openImageViewer(index)"
            >
              <img class="detail-image" :src="`/uploads/${image}`" alt="รูปประกอบ">
            </button>
          </div>
          <button
            v-else-if="item.image_path"
            class="staff-image-button single"
            type="button"
            @click="openImageViewer(0)"
          >
            <img class="detail-image" :src="`/uploads/${item.image_path}`" alt="รูปประกอบ">
          </button>
          <p v-else class="muted">ไม่มีรูปภาพ</p>
        </div>

        <div class="detail-section" v-if="item.completion_image_path">
          <h3 class="completion-title">รูปภาพหลักฐาน (ตอนเสร็จงาน)</h3>
          <button
            class="staff-image-button single completion-image-button"
            type="button"
            @click="openImageViewer(allImages.length - 1)"
          >
            <img class="detail-image" :src="`/uploads/${item.completion_image_path}`" alt="รูปหลักฐานเสร็จงาน">
          </button>
        </div>
      </section>

      <section class="card" v-if="userRole === 'admin' && isOpen">
        <h2>จ่ายงาน (มอบหมายผู้รับผิดชอบ)</h2>
        <div class="assign-staff-row">
          <select v-model="selectedStaffId" class="assign-staff-select" aria-label="เลือกผู้รับผิดชอบ">
            <option value="">-- ยังไม่ระบุ / ยกเลิกการมอบหมาย --</option>
            <option v-for="staff in availableStaff" :key="staff.id" :value="staff.id">
              {{ staff.username }} ({{ staff.role === 'maid' ? 'แม่บ้าน' : 'ช่าง' }})
            </option>
          </select>
          <button class="btn-primary" :disabled="assigning" @click="assignStaff">
            {{ assigning ? 'กำลังบันทึก...' : 'บันทึกการจ่ายงาน' }}
          </button>
        </div>
      </section>

      <section class="card" v-if="userRole !== 'admin' && isAssignedToMe && isOpen">
        <h2>ส่งงาน (เสร็จสิ้นภารกิจ)</h2>
        <p class="muted">กรุณาแนบรูปภาพหลักฐานการทำงาน เพื่อเปลี่ยนสถานะเป็นเสร็จสิ้น</p>

        <label class="multi-upload-box">
          <input
            class="upload-input"
            name="images"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            @change="onCompletionImageChange"
          >

          <i class="fa-solid fa-cloud-arrow-up"></i>
          <span>เพิ่มรูปภาพ</span>
          <small>แนบรูปหลักฐาน 1 รูป</small>
        </label>

        <div v-if="completionPreviews.length" class="image-preview-grid">
          <article
            v-for="(preview, index) in completionPreviews"
            :key="preview.url"
            class="image-preview-card"
          >
            <img :src="preview.url" :alt="preview.name">

            <button
              class="image-remove-btn"
              type="button"
              aria-label="ลบรูป"
              @click="removeCompletionImage(index)"
            >
              <i class="fa-solid fa-xmark"></i>
            </button>

            <span>{{ preview.name }}</span>
          </article>
        </div>

        <small v-if="completionNotice" class="multi-image-count" role="alert">
          {{ completionNotice }}
        </small>

        <div class="complete-task-row">
          <button
            class="btn-primary complete-task-button"
            :disabled="completing"
            @click="completeWithImage"
          >
            <i class="fa-solid fa-check"></i>
            {{ completing ? 'กำลังอัปโหลด...' : 'ส่งรูปและเสร็จสิ้นงาน' }}
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
          <textarea
            v-model="note"
            class="note-box"
            placeholder="เช่น รออะไหล่ / นัดช่างแล้ว"
            aria-label="หมายเหตุเจ้าหน้าที่"
            :disabled="item.status === 'completed'"
          ></textarea>
          <button
            v-if="item.status !== 'completed'"
            class="btn-primary"
            :disabled="savingNote"
            @click="saveNote"
          >
            {{ savingNote ? 'กำลังบันทึก...' : 'บันทึกหมายเหตุ' }}
          </button>
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
