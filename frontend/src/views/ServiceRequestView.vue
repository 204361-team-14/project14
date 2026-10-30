<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'
import { useImageUploader } from '../composables/useImageUploader'
import { formatId, timeString, todayString } from '../utils/format'

const route = useRoute()
const router = useRouter()

const step = ref(1)
const description = ref('')
const urgency = ref('ปกติ')
const problemDate = ref('')
const problemTime = ref('')
const submitting = ref(false)
const message = ref('')
const successId = ref(null)
const showLocationEditor = ref(false)
const editorError = ref('')
const maxDate = todayString()

const {
  previews: imagePreviews,
  files: imageFiles,
  notice: imageNotice,
  onChange: onImageChange,
  remove: removeImage
} = useImageUploader(6)

const serviceChoice = ref(
  route.meta.serviceType === 'แจ้งทำความสะอาด'
    ? 'แจ้งทำความสะอาด'
    : 'แจ้งซ่อม'
)

const serviceType = computed(() => serviceChoice.value)

const pageSubtitle = computed(() => (
  serviceType.value === 'แจ้งทำความสะอาด'
    ? 'กรอกรายละเอียดพื้นที่และงานที่ต้องการให้เจ้าหน้าที่ดำเนินการ'
    : 'กรอกรายละเอียดให้ครบถ้วน เพื่อให้เจ้าหน้าที่ดำเนินการได้อย่างรวดเร็ว'
))

const descriptionPlaceholder = computed(() => (
  serviceType.value === 'แจ้งทำความสะอาด'
    ? 'อธิบายพื้นที่ ลักษณะงาน หรือสิ่งที่ต้องการให้ดำเนินการ'
    : 'อธิบายรายละเอียด เช่น อาการของปัญหา สิ่งที่ต้องการให้ดำเนินการ'
))

// ค่าเริ่มต้นเป็นว่าง: ถ้าไม่ได้สแกน QR ผู้ใช้ต้องระบุห้องเอง
// (เดิม hardcode เป็น CSB/3/301 ทำให้คำขอไปผิดห้องโดยไม่รู้ตัว)
// สถานะการสแกน QR: '' (ไม่ได้สแกน) | 'found' | 'notfound' | 'error'
const qrStatus = ref('')

const qrRoom = reactive({
  building: '',
  floor: '',
  room: '',
  room_name: ''
})

// เปลี่ยนชื่อจาก location เพื่อไม่ให้บัง window.location
const roomLocation = reactive({
  building: '',
  floor: '',
  room: '',
  room_name: ''
})

const editLocation = reactive({
  building: '',
  floor: '',
  room: ''
})

const hasLocation = computed(() => (
  Boolean(
    roomLocation.building.trim() &&
    roomLocation.floor.trim() &&
    roomLocation.room.trim()
  )
))

function setCurrentDateTime() {
  const now = new Date()
  problemDate.value = todayString(now)
  problemTime.value = timeString(now)
}

function changeServiceType() {
  const targetPath = serviceChoice.value === 'แจ้งทำความสะอาด'
    ? '/request/cleaning'
    : '/request/repair'

  router.replace({
    path: targetPath,
    query: route.query.room
      ? { room: route.query.room }
      : {}
  })
}

// ไปหน้าของหาย-ของได้คืนโดยพกรหัสห้องจาก QR ไปด้วย
const lostFoundLink = computed(() => ({
  path: '/lost-found',
  query: route.query.room ? { room: route.query.room } : {}
}))

function setUrgency(value) {
  urgency.value = value
}

function openLocationEditor() {
  editLocation.building = roomLocation.building
  editLocation.floor = roomLocation.floor
  editLocation.room = roomLocation.room
  editorError.value = ''
  showLocationEditor.value = true
}

function closeLocationEditor() {
  showLocationEditor.value = false
}

function saveLocation() {
  if (
    !editLocation.building.trim() ||
    !editLocation.floor.trim() ||
    !editLocation.room.trim()
  ) {
    editorError.value = 'กรุณาระบุอาคาร ชั้น และห้องให้ครบ'
    return
  }

  roomLocation.building = editLocation.building.trim()
  roomLocation.floor = editLocation.floor.trim()
  roomLocation.room = editLocation.room.trim()

  roomLocation.room_name = (
    roomLocation.building === qrRoom.building &&
    roomLocation.floor === qrRoom.floor &&
    roomLocation.room === qrRoom.room
  ) ? qrRoom.room_name : ''

  editorError.value = ''
  showLocationEditor.value = false
}

function validateStepOne() {
  message.value = ''

  if (!description.value.trim() || !problemDate.value) {
    message.value = 'กรุณากรอกรายละเอียดและวันที่พบปัญหาให้ครบ'
    return false
  }

  if (problemDate.value > maxDate) {
    message.value = 'วันที่พบปัญหาต้องไม่เป็นวันในอนาคต'
    return false
  }

  if (!hasLocation.value) {
    message.value = 'กรุณาระบุตำแหน่ง (อาคาร ชั้น ห้อง) ก่อนดำเนินการต่อ'
    return false
  }

  return true
}

function goToReview() {
  if (!validateStepOne()) return
  step.value = 2
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function backToForm() {
  step.value = 1
  message.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function submitRequest() {
  if (submitting.value) return

  if (!validateStepOne()) {
    step.value = 1
    return
  }

  const form = new FormData()
  form.append('service_type', serviceType.value)
  form.append('description', description.value.trim())
  form.append('urgency', urgency.value)
  form.append('problem_date', problemDate.value)
  form.append('problem_time', problemTime.value)
  form.append('building', roomLocation.building)
  form.append('floor', roomLocation.floor)
  form.append('room', roomLocation.room)

  imageFiles.value.forEach((file) => {
    form.append('images', file)
  })

  submitting.value = true
  message.value = ''

  try {
    const response = await fetch('/api/requests', {
      method: 'POST',
      body: form
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok || !data.success) {
      message.value = data.message || 'ไม่สามารถส่งคำขอได้'
      return
    }

    successId.value = data.request_id
    step.value = 3
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch {
    message.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  } finally {
    submitting.value = false
  }
}

async function resolveQrRoom() {
  const qrCode = String(route.query.room || '').trim()

  if (!qrCode) {
    qrStatus.value = ''
    return
  }

  try {
    const response = await fetch(
      `/api/rooms/resolve/${encodeURIComponent(qrCode)}`
    )

    if (!response.ok) {
      qrStatus.value = response.status === 404 ? 'notfound' : 'error'
      return
    }

    const data = await response.json()
    const room = data.room

    qrRoom.building = room.building
    qrRoom.floor = room.floor
    qrRoom.room = room.room_number
    qrRoom.room_name = room.room_name || ''

    roomLocation.building = room.building
    roomLocation.floor = room.floor
    roomLocation.room = room.room_number
    roomLocation.room_name = room.room_name || ''
    qrStatus.value = 'found'
  } catch {
    // ผู้ใช้ยังสามารถระบุห้องเองได้
    qrStatus.value = 'error'
  }
}

watch(
  () => route.query.room,
  () => resolveQrRoom()
)

watch(
  () => route.meta.serviceType,
  (value) => {
    serviceChoice.value = value === 'แจ้งทำความสะอาด'
      ? 'แจ้งทำความสะอาด'
      : 'แจ้งซ่อม'
  }
)

onMounted(() => {
  setCurrentDateTime()
  resolveQrRoom()
})
</script>

<template>
  <div class="public-app request-flow-page">
    <PublicHeader />

    <main class="request-flow-container">
      <RouterLink class="back-link request-back" to="/">
        <i class="fa-solid fa-chevron-left"></i>
        กลับหน้าหลัก
      </RouterLink>

      <section class="request-flow-top">
        <div class="request-heading">
          <div class="request-heading-icon">
            <i class="fa-solid fa-file-lines"></i>
          </div>

          <div>
            <h1>ส่งคำขอบริการ</h1>
            <p>{{ pageSubtitle }}</p>
          </div>
        </div>

        <div class="request-progress" aria-label="ขั้นตอนการส่งคำขอ">
          <div
            class="progress-step"
            :class="{ active: step === 1, done: step > 1 }"
          >
            <span class="progress-circle">1</span>
            <span>กรอกข้อมูล</span>
          </div>

          <div
            class="progress-step"
            :class="{ active: step === 2, done: step > 2 }"
          >
            <span class="progress-circle">2</span>
            <span>ตรวจสอบข้อมูล</span>
          </div>

          <div
            class="progress-step"
            :class="{ active: step === 3 }"
          >
            <span class="progress-circle">3</span>
            <span>เสร็จสิ้น</span>
          </div>
        </div>
      </section>

      <!-- แจ้งผลการสแกน QR (เฉพาะขั้นกรอกข้อมูล) -->
      <template v-if="step === 1">
        <p v-if="qrStatus === 'found'" class="flash success" role="status">
          <i class="fa-solid fa-qrcode"></i>
          ตรวจพบห้องจาก QR:
          อาคาร {{ qrRoom.building }} · ชั้น {{ qrRoom.floor }} · ห้อง {{ qrRoom.room }}
          <template v-if="qrRoom.room_name">({{ qrRoom.room_name }})</template>
        </p>

        <p v-else-if="qrStatus === 'notfound'" class="flash error" role="alert">
          ไม่พบห้องจาก QR นี้ กรุณากด “ระบุห้อง” เพื่อกรอกตำแหน่งเอง
        </p>

        <p v-else-if="qrStatus === 'error'" class="flash error" role="alert">
          โหลดข้อมูลห้องจาก QR ไม่สำเร็จ กรุณากด “ระบุห้อง” เพื่อกรอกตำแหน่งเอง
        </p>
      </template>

      <!-- STEP 1 -->
      <section v-if="step === 1" class="request-main-layout">
        <div class="card request-form-card">
          <h2>ข้อมูลคำขอ</h2>

          <div class="request-form-grid">
            <div class="field">
              <label for="req-service">ประเภทบริการ <span class="required">*</span></label>

              <select
                id="req-service"
                v-model="serviceChoice"
                @change="changeServiceType"
              >
                <option value="แจ้งซ่อม">แจ้งซ่อม</option>
                <option value="แจ้งทำความสะอาด">แจ้งทำความสะอาด</option>
              </select>

              <RouterLink class="btn-outline lost-found-shortcut" :to="lostFoundLink">
                <i class="fa-solid fa-magnifying-glass"></i>
                ของหาย-ของได้คืน
              </RouterLink>
            </div>

            <div class="field">
              <label for="req-description">รายละเอียดคำขอ <span class="required">*</span></label>

              <textarea
                id="req-description"
                v-model="description"
                :placeholder="descriptionPlaceholder"
              ></textarea>
            </div>

            <div class="field full">
              <label id="req-urgency-label">ระดับความเร่งด่วน <span class="required">*</span></label>

              <div class="urgency-options" role="group" aria-labelledby="req-urgency-label">
                <button
                  type="button"
                  class="urgency-option urgent"
                  :class="{ selected: urgency === 'เร่งด่วน' }"
                  :aria-pressed="urgency === 'เร่งด่วน'"
                  @click="setUrgency('เร่งด่วน')"
                >
                  <span></span>
                  เร่งด่วน
                </button>

                <button
                  type="button"
                  class="urgency-option normal"
                  :class="{ selected: urgency === 'ปกติ' }"
                  :aria-pressed="urgency === 'ปกติ'"
                  @click="setUrgency('ปกติ')"
                >
                  <span></span>
                  ปกติ
                </button>

                <button
                  type="button"
                  class="urgency-option noturgent"
                  :class="{ selected: urgency === 'ไม่เร่งด่วน' }"
                  :aria-pressed="urgency === 'ไม่เร่งด่วน'"
                  @click="setUrgency('ไม่เร่งด่วน')"
                >
                  <span></span>
                  ไม่เร่งด่วน
                </button>
              </div>
            </div>

            <div class="field">
              <label for="req-date">วันที่พบปัญหา <span class="required">*</span></label>
              <input id="req-date" v-model="problemDate" type="date" :max="maxDate">
            </div>

            <div class="field">
              <label for="req-time">เวลาที่พบปัญหา</label>
              <input id="req-time" v-model="problemTime" type="time">
            </div>

            <div class="field full">
              <label>แนบรูปภาพ (ถ้ามี)</label>

              <label class="multi-upload-box">
                <input
                  class="upload-input"
                  name="images"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  multiple
                  @change="onImageChange"
                >

                <i class="fa-solid fa-cloud-arrow-up"></i>
                <span>เพิ่มรูปภาพ</span>
                <small>เลือกได้สูงสุด 6 รูป</small>
              </label>

              <div
                v-if="imagePreviews.length"
                class="image-preview-grid"
              >
                <article
                  v-for="(preview, index) in imagePreviews"
                  :key="preview.url"
                  class="image-preview-card"
                >
                  <img :src="preview.url" :alt="preview.name">

                  <button
                    class="image-remove-btn"
                    type="button"
                    aria-label="ลบรูป"
                    @click="removeImage(index)"
                  >
                    <i class="fa-solid fa-xmark"></i>
                  </button>

                  <span>{{ preview.name }}</span>
                </article>
              </div>

              <small
                v-if="imagePreviews.length"
                class="multi-image-count"
              >
                เลือกแล้ว {{ imagePreviews.length }}/6 รูป
                สามารถกด “เพิ่มรูปภาพ” เพื่อเพิ่มทีละชุดได้
              </small>

              <small v-if="imageNotice" class="multi-image-count" role="alert">
                {{ imageNotice }}
              </small>
            </div>
          </div>

          <div class="request-form-actions">
            <button
              class="btn-secondary"
              type="button"
              @click="router.push('/')"
            >
              ยกเลิก
            </button>

            <button
              class="btn-primary"
              type="button"
              @click="goToReview"
            >
              ถัดไป
            </button>
          </div>

          <p v-if="message" class="form-message" role="alert">{{ message }}</p>
        </div>

        <aside class="request-side-column">
          <section class="card request-location-panel">
            <h3>
              <i class="fa-solid fa-location-dot"></i>
              ตำแหน่งปัจจุบัน
            </h3>

            <div class="location-summary">
              <div class="location-building-icon">
                <i class="fa-solid fa-building"></i>
              </div>

              <div v-if="hasLocation">
                <strong>อาคาร {{ roomLocation.building }}</strong>
                <span>ชั้น {{ roomLocation.floor }}</span>
                <span>ห้อง {{ roomLocation.room }}</span>
                <small v-if="roomLocation.room_name">{{ roomLocation.room_name }}</small>
              </div>

              <div v-else>
                <strong>ยังไม่ได้ระบุตำแหน่ง</strong>
                <span>สแกน QR ที่ห้อง หรือกด “ระบุห้อง”</span>
              </div>
            </div>

            <button
              class="btn-outline location-edit-btn"
              type="button"
              @click="openLocationEditor"
            >
              <i class="fa-solid fa-pen"></i>
              {{ hasLocation ? 'แก้ไขห้อง' : 'ระบุห้อง' }}
            </button>

            <p class="location-note">
              QR Code ใช้เป็นค่าเริ่มต้นเท่านั้น
              คุณสามารถแก้ไขห้องก่อนส่งคำขอได้
            </p>
          </section>

          <section class="card request-help-card">
            <h3>
              <i class="fa-solid fa-lightbulb"></i>
              คำแนะนำ
            </h3>

            <ul>
              <li>
                <i class="fa-solid fa-camera"></i>
                ถ่ายรูปให้ชัดเจนเห็นปัญหา
              </li>
              <li>
                <i class="fa-solid fa-location-dot"></i>
                ระบุรายละเอียดสถานที่เกิดเหตุให้ชัดเจน
              </li>
              <li>
                <i class="fa-solid fa-clipboard-list"></i>
                ให้ข้อมูลครบถ้วนเพื่อความรวดเร็วในการดำเนินการ
              </li>
              <li>
                <i class="fa-regular fa-clock"></i>
                ฝ่ายอาคารสถานที่จะดำเนินการโดยเร็วที่สุด
              </li>
            </ul>
          </section>
        </aside>
      </section>

      <!-- STEP 2 -->
      <section v-else-if="step === 2" class="request-review-layout">
        <div class="card review-card">
          <h2>ตรวจสอบข้อมูลก่อนส่ง</h2>

          <div class="review-grid">
            <div>
              <span>ประเภทบริการ</span>
              <strong>{{ serviceType }}</strong>
            </div>

            <div>
              <span>ความเร่งด่วน</span>
              <strong>{{ urgency }}</strong>
            </div>

            <div class="full">
              <span>รายละเอียดคำขอ</span>
              <strong>{{ description }}</strong>
            </div>

            <div>
              <span>วันที่พบปัญหา</span>
              <strong>{{ problemDate || '-' }}</strong>
            </div>

            <div>
              <span>เวลา</span>
              <strong>{{ problemTime || '-' }}</strong>
            </div>

            <div class="full">
              <span>ตำแหน่ง</span>
              <strong>
                อาคาร {{ roomLocation.building }}
                · ชั้น {{ roomLocation.floor }}
                · ห้อง {{ roomLocation.room }}
              </strong>
            </div>

            <div v-if="imagePreviews.length" class="full">
              <span>รูปภาพ</span>

              <div class="review-image-grid">
                <img
                  v-for="preview in imagePreviews"
                  :key="preview.url"
                  :src="preview.url"
                  :alt="preview.name"
                >
              </div>
            </div>
          </div>

          <div class="request-form-actions">
            <button class="btn-secondary" type="button" @click="backToForm">
              ย้อนกลับ
            </button>

            <button
              class="btn-primary"
              type="button"
              :disabled="submitting"
              @click="submitRequest"
            >
              {{ submitting ? 'กำลังส่ง...' : 'ยืนยันส่งคำขอ' }}
            </button>
          </div>

          <p v-if="message" class="form-message" role="alert">{{ message }}</p>
        </div>
      </section>

      <!-- STEP 3 -->
      <section v-else class="request-success-wrap">
        <div class="card request-success-card">
          <div class="success-icon">
            <i class="fa-solid fa-check"></i>
          </div>

          <h2>ส่งคำขอเรียบร้อยแล้ว</h2>

          <p>
            ระบบได้รับคำขอของคุณแล้ว
            เจ้าหน้าที่จะตรวจสอบและดำเนินการต่อไป
          </p>

          <div v-if="successId" class="request-number">
            {{ formatId('REQ', successId) }}
          </div>

          <RouterLink class="btn-primary" to="/">
            กลับหน้าหลัก
          </RouterLink>
        </div>
      </section>
    </main>

    <PublicFooter />

    <div
      v-if="showLocationEditor"
      class="modal-backdrop"
      @click.self="closeLocationEditor"
      @keydown.esc="closeLocationEditor"
    >
      <div
        class="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="location-editor-title"
      >
        <h2 id="location-editor-title">แก้ไขตำแหน่งห้อง</h2>

        <p class="muted">
          ข้อมูลจาก QR เป็นค่าเริ่มต้นเท่านั้น
          สามารถเปลี่ยนตำแหน่งได้ก่อนส่งคำขอ
        </p>

        <div class="form-grid">
          <div class="field">
            <label for="edit-building">อาคาร</label>
            <input id="edit-building" v-model="editLocation.building" autofocus>
          </div>

          <div class="field">
            <label for="edit-floor">ชั้น</label>
            <input id="edit-floor" v-model="editLocation.floor">
          </div>

          <div class="field full">
            <label for="edit-room">ห้อง</label>
            <input id="edit-room" v-model="editLocation.room">
          </div>
        </div>

        <p v-if="editorError" class="form-message" role="alert">{{ editorError }}</p>

        <div class="modal-actions">
          <button
            class="btn-secondary"
            type="button"
            @click="closeLocationEditor"
          >
            ยกเลิก
          </button>

          <button class="btn-primary" type="button" @click="saveLocation">
            บันทึกตำแหน่ง
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lost-found-shortcut {
  margin-top: 10px;
  padding: 8px 12px;
  font-size: 13px;
}
</style>