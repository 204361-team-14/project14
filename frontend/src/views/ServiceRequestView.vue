<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'

const route = useRoute()
const router = useRouter()

const step = ref(1)
const description = ref('')
const urgency = ref('ปกติ')
const problemDate = ref('')
const problemTime = ref('')
const imageFiles = ref([])
const imagePreviews = ref([])
const submitting = ref(false)
const message = ref('')
const successId = ref(null)
const showLocationEditor = ref(false)

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

const qrRoom = reactive({
  building: 'CSB',
  floor: '3',
  room: '301',
  room_name: ''
})

const location = reactive({
  building: 'CSB',
  floor: '3',
  room: '301',
  room_name: ''
})

const editLocation = reactive({
  building: '',
  floor: '',
  room: ''
})

function setCurrentDateTime() {
  const now = new Date()

  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hour = String(now.getHours()).padStart(2, '0')
  const minute = String(now.getMinutes()).padStart(2, '0')

  problemDate.value = `${year}-${month}-${day}`
  problemTime.value = `${hour}:${minute}`
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

function setUrgency(value) {
  urgency.value = value
}

function openLocationEditor() {
  editLocation.building = location.building
  editLocation.floor = location.floor
  editLocation.room = location.room
  showLocationEditor.value = true
}

function saveLocation() {
  if (
    !editLocation.building.trim() ||
    !editLocation.floor.trim() ||
    !editLocation.room.trim()
  ) {
    alert('กรุณาระบุอาคาร ชั้น และห้องให้ครบ')
    return
  }

  location.building = editLocation.building.trim()
  location.floor = editLocation.floor.trim()
  location.room = editLocation.room.trim()

  location.room_name = (
    location.building === qrRoom.building &&
    location.floor === qrRoom.floor &&
    location.room === qrRoom.room
  ) ? qrRoom.room_name : ''

  showLocationEditor.value = false
}

function rebuildImagePreviews() {
  imagePreviews.value.forEach((preview) => {
    URL.revokeObjectURL(preview.url)
  })

  imagePreviews.value = imageFiles.value.map((file) => ({
    name: file.name,
    url: URL.createObjectURL(file)
  }))
}

function onImageChange(event) {
  const selected = Array.from(event.target.files || [])

  const existingKeys = new Set(
    imageFiles.value.map(
      (file) => `${file.name}-${file.size}-${file.lastModified}`
    )
  )

  for (const file of selected) {
    const key = `${file.name}-${file.size}-${file.lastModified}`

    if (!existingKeys.has(key) && imageFiles.value.length < 6) {
      imageFiles.value.push(file)
      existingKeys.add(key)
    }
  }

  rebuildImagePreviews()
  event.target.value = ''
}

function removeImage(index) {
  imageFiles.value.splice(index, 1)
  rebuildImagePreviews()
}

function validateStepOne() {
  message.value = ''

  if (!description.value.trim() || !problemDate.value) {
    message.value = 'กรุณากรอกรายละเอียดและวันที่พบปัญหาให้ครบ'
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
  form.append('building', location.building)
  form.append('floor', location.floor)
  form.append('room', location.room)

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

    const data = await response.json()

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

  if (!qrCode) return

  try {
    const response = await fetch(
      `/api/rooms/resolve/${encodeURIComponent(qrCode)}`
    )

    if (!response.ok) return

    const data = await response.json()
    const room = data.room

    qrRoom.building = room.building
    qrRoom.floor = room.floor
    qrRoom.room = room.room_number
    qrRoom.room_name = room.room_name || ''

    location.building = room.building
    location.floor = room.floor
    location.room = room.room_number
    location.room_name = room.room_name || ''
  } catch {
    // ผู้ใช้ยังสามารถแก้ไขห้องเองได้
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

      <!-- STEP 1 -->
      <section v-if="step === 1" class="request-main-layout">
        <div class="card request-form-card">
          <h2>ข้อมูลคำขอ</h2>

          <div class="request-form-grid">
            <div class="field">
              <label>ประเภทบริการ <span class="required">*</span></label>

              <select
                v-model="serviceChoice"
                @change="changeServiceType"
              >
                <option value="แจ้งซ่อม">แจ้งซ่อม</option>
                <option value="แจ้งทำความสะอาด">แจ้งทำความสะอาด</option>
              </select>
            </div>

            <div class="field">
              <label>รายละเอียดคำขอ <span class="required">*</span></label>

              <textarea
                v-model="description"
                :placeholder="descriptionPlaceholder"
                required
              ></textarea>
            </div>

            <div class="field full">
              <label>ระดับความเร่งด่วน <span class="required">*</span></label>

              <div class="urgency-options">
                <button
                  type="button"
                  class="urgency-option urgent"
                  :class="{ selected: urgency === 'เร่งด่วน' }"
                  @click="setUrgency('เร่งด่วน')"
                >
                  <span></span>
                  เร่งด่วน
                </button>

                <button
                  type="button"
                  class="urgency-option normal"
                  :class="{ selected: urgency === 'ปกติ' }"
                  @click="setUrgency('ปกติ')"
                >
                  <span></span>
                  ปกติ
                </button>

                <button
                  type="button"
                  class="urgency-option noturgent"
                  :class="{ selected: urgency === 'ไม่เร่งด่วน' }"
                  @click="setUrgency('ไม่เร่งด่วน')"
                >
                  <span></span>
                  ไม่เร่งด่วน
                </button>
              </div>
            </div>

            <div class="field">
              <label>วันที่พบปัญหา <span class="required">*</span></label>
              <input v-model="problemDate" type="date" required>
            </div>

            <div class="field">
              <label>เวลาที่พบปัญหา</label>
              <input v-model="problemTime" type="time">
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

          <p v-if="message" class="form-message">{{ message }}</p>
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

              <div>
                <strong>อาคาร {{ location.building }}</strong>
                <span>ชั้น {{ location.floor }}</span>
                <span>ห้อง {{ location.room }}</span>
                <small v-if="location.room_name">{{ location.room_name }}</small>
              </div>
            </div>

            <button
              class="btn-outline location-edit-btn"
              type="button"
              @click="openLocationEditor"
            >
              <i class="fa-solid fa-pen"></i>
              แก้ไขห้อง
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
                อาคาร {{ location.building }}
                · ชั้น {{ location.floor }}
                · ห้อง {{ location.room }}
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
            <button class="btn-secondary" @click="backToForm">
              ย้อนกลับ
            </button>

            <button
              class="btn-primary"
              :disabled="submitting"
              @click="submitRequest"
            >
              {{ submitting ? 'กำลังส่ง...' : 'ยืนยันส่งคำขอ' }}
            </button>
          </div>

          <p v-if="message" class="form-message">{{ message }}</p>
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
            REQ-{{ String(successId).padStart(6, '0') }}
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
      @click.self="showLocationEditor = false"
    >
      <div class="modal-card">
        <h2>แก้ไขตำแหน่งห้อง</h2>

        <p class="muted">
          ข้อมูลจาก QR เป็นค่าเริ่มต้นเท่านั้น
          สามารถเปลี่ยนตำแหน่งได้ก่อนส่งคำขอ
        </p>

        <div class="form-grid">
          <div class="field">
            <label>อาคาร</label>
            <input v-model="editLocation.building">
          </div>

          <div class="field">
            <label>ชั้น</label>
            <input v-model="editLocation.floor">
          </div>

          <div class="field full">
            <label>ห้อง</label>
            <input v-model="editLocation.room">
          </div>
        </div>

        <div class="modal-actions">
          <button
            class="btn-secondary"
            @click="showLocationEditor = false"
          >
            ยกเลิก
          </button>

          <button class="btn-primary" @click="saveLocation">
            บันทึกตำแหน่ง
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
