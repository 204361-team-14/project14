<script setup>
import { onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'

const rooms = ref([])
const message = ref('')
const error = ref('')
const form = reactive({
  building: '',
  floor: '',
  room_number: '',
  room_name: ''
})

<<<<<<< Updated upstream
const currentToken = localStorage.getItem('token')
const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
=======
// เก็บ blob URL ของ QR ทั้งหมดไว้ เพื่อ revoke ตอนโหลดใหม่ / ออกจากหน้า
let qrObjectUrls = []

function revokeQrUrls() {
  qrObjectUrls.forEach((url) => URL.revokeObjectURL(url))
  qrObjectUrls = []
}

// QR หนึ่งอันต่อห้อง เปิดหน้าแจ้งซ่อมพร้อมใส่ห้องให้ (เปลี่ยนเป็น 'cleaning' ถ้าต้องการให้เปิดหน้าทำความสะอาด)
// ผู้ใช้สลับประเภทบริการได้ในฟอร์มโดยห้องไม่หาย
const QR_SERVICE = 'repair'

// ดึงรูป QR ด้วย Authorization header แทนการแนบ token ใน URL
async function loadQr(room) {
  try {
    const response = await apiFetch(`/api/staff/rooms/${room.id}/qr?service=${QR_SERVICE}`)
    if (!response.ok) return

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    qrObjectUrls.push(url)
    room.qrUrl = url
  } catch {
    // ไม่แสดง QR ของห้องนี้ แต่ห้องอื่นยังใช้งานได้
>>>>>>> Stashed changes
  }
}

async function loadRooms() {
  const response = await fetch('/api/staff/rooms', {
    headers: getHeaders()
  })
  const data = await response.json()
  rooms.value = data.rooms || []
}

async function createRoom() {
  message.value = ''
  error.value = ''

  const response = await fetch('/api/staff/rooms', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(form)
  })
  const data = await response.json()

  if (!response.ok) {
    error.value = data.message || 'ไม่สามารถเพิ่มห้องได้'
    return
  }

  message.value = 'เพิ่มห้องเรียบร้อยแล้ว'
  form.building = ''
  form.floor = ''
  form.room_number = ''
  form.room_name = ''
  await loadRooms()
}

<<<<<<< Updated upstream
async function toggleRoom(room) {
  const response = await fetch(`/api/staff/rooms/${room.id}/toggle`, {
    method: 'PATCH',
    headers: getHeaders()
  })

  if (response.ok) await loadRooms()
=======
function qrFileName(room) {
  const safe = (value) => String(value).replace(/[^\w.-]+/g, '_')
  return `qr-${safe(room.building)}-${safe(room.floor)}-${safe(room.room_number)}-${QR_SERVICE}.png`
>>>>>>> Stashed changes
}

onMounted(loadRooms)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>จัดการข้อมูลห้องและ QR Code</h1>
      <p>
        QR Code จะใส่ตำแหน่งห้องเป็นค่าเริ่มต้นให้ผู้ใช้ และผู้ใช้ยังสามารถแก้ไขห้องก่อนส่งคำขอได้
      </p>
    </div>

    <p v-if="message" class="flash success">{{ message }}</p>
    <p v-if="error" class="flash error">{{ error }}</p>

    <div class="rooms-grid">
      <section class="card">
        <h2>เพิ่มห้องใหม่</h2>

        <form @submit.prevent="createRoom">
          <div class="field">
            <label>อาคาร *</label>
            <input v-model="form.building" required placeholder="เช่น CSB">
          </div>

          <div class="field">
            <label>ชั้น *</label>
            <input v-model="form.floor" required placeholder="เช่น 3">
          </div>

          <div class="field">
            <label>เลขห้อง *</label>
            <input v-model="form.room_number" required placeholder="เช่น 301">
          </div>

          <div class="field">
            <label>ชื่อห้อง</label>
            <input v-model="form.room_name" placeholder="เช่น ห้องปฏิบัติการคอมพิวเตอร์ 1">
          </div>

          <button class="btn-primary">
            <i class="fa-solid fa-plus"></i>
            เพิ่มห้อง
          </button>
        </form>
      </section>

      <section class="card">
        <h2>ห้องทั้งหมด</h2>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ห้อง</th>
                <th>ชื่อห้อง</th>
                <th>สถานะ</th>
                <th>QR Code</th>
                <th>จัดการ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="room in rooms" :key="room.id">
                <td>
                  <strong>{{ room.building }}</strong><br>
                  ชั้น {{ room.floor }} · ห้อง {{ room.room_number }}
                </td>
                <td>{{ room.room_name || '-' }}</td>
                <td>
                  <span class="badge" :class="room.is_active ? 'on' : 'off'">
                    {{ room.is_active ? 'ใช้งาน' : 'ปิดใช้งาน' }}
                  </span>
                </td>
                <td>
                  <a :href="`/api/staff/rooms/${room.id}/qr?token=${currentToken}`" target="_blank">
                    <img
                      class="qr-image"
                      :src="`/api/staff/rooms/${room.id}/qr?token=${currentToken}`"
                      :alt="`QR ห้อง ${room.room_number}`"
                    >
                  </a>
                </td>
                <td>
                  <div class="row-actions wrap">
                    <a
                      class="btn-soft"
                      :href="`/api/staff/rooms/${room.id}/qr?download=1&token=${currentToken}`"
                    >
                      <i class="fa-solid fa-download"></i>
                      ดาวน์โหลด QR
                    </a>

                    <button
                      class="btn-soft"
                      :class="{ danger: room.is_active }"
                      @click="toggleRoom(room)"
                    >
                      {{ room.is_active ? 'ปิดใช้งาน' : 'เปิดใช้งาน' }}
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-if="!rooms.length">
                <td colspan="5">ยังไม่มีข้อมูลห้อง</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </StaffLayout>
</template>