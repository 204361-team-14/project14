<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import { apiFetch } from '../composables/useAuth'

const rooms = ref([])
const message = ref('')
const error = ref('')
const loading = ref(true)
const submitting = ref(false)
const form = reactive({
  building: '',
  floor: '',
  room_number: '',
  room_name: ''
})

// เก็บ blob URL ของ QR ทั้งหมดไว้ เพื่อ revoke ตอนโหลดใหม่ / ออกจากหน้า
let qrObjectUrls = []

function revokeQrUrls() {
  qrObjectUrls.forEach((url) => URL.revokeObjectURL(url))
  qrObjectUrls = []
}

// ดึงรูป QR ด้วย Authorization header แทนการแนบ token ใน URL
async function loadQr(room) {
  try {
    const response = await apiFetch(`/api/staff/rooms/${room.id}/qr`)
    if (!response.ok) return

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    qrObjectUrls.push(url)
    room.qrUrl = url
  } catch {
    // ไม่แสดง QR ของห้องนี้ แต่ห้องอื่นยังใช้งานได้
  }
}

async function loadRooms() {
  error.value = ''

  try {
    const response = await apiFetch('/api/staff/rooms')
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()

    revokeQrUrls()
    rooms.value = (data.rooms || []).map((room) => ({ ...room, qrUrl: '' }))

    // rooms.value เป็น reactive proxy ใช้ตัวที่อยู่ใน array เพื่อให้ qrUrl อัปเดตหน้าจอ
    await Promise.all(rooms.value.map((room) => loadQr(room)))
  } catch {
    error.value = 'ไม่สามารถโหลดข้อมูลห้องได้'
  } finally {
    loading.value = false
  }
}

async function createRoom() {
  if (submitting.value) return

  message.value = ''
  error.value = ''
  submitting.value = true

  try {
    const response = await apiFetch('/api/staff/rooms', {
      method: 'POST',
      body: JSON.stringify({
        building: form.building.trim(),
        floor: form.floor.trim(),
        room_number: form.room_number.trim(),
        room_name: form.room_name.trim()
      })
    })
    const data = await response.json().catch(() => ({}))

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
  } catch {
    error.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  } finally {
    submitting.value = false
  }
}

async function toggleRoom(room) {
  error.value = ''

  try {
    const response = await apiFetch(`/api/staff/rooms/${room.id}/toggle`, {
      method: 'PATCH'
    })

    if (response.ok) {
      await loadRooms()
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถเปลี่ยนสถานะห้องได้'
    }
  } catch {
    error.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  }
}

function qrFileName(room) {
  const safe = (value) => String(value).replace(/[^\w.-]+/g, '_')
  return `qr-${safe(room.building)}-${safe(room.floor)}-${safe(room.room_number)}.png`
}

onMounted(loadRooms)
onBeforeUnmount(revokeQrUrls)
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>จัดการข้อมูลห้องและ QR Code</h1>
      <p>
        QR Code จะใส่ตำแหน่งห้องเป็นค่าเริ่มต้นให้ผู้ใช้ และผู้ใช้ยังสามารถแก้ไขห้องก่อนส่งคำขอได้
      </p>
    </div>

    <p v-if="message" class="flash success" role="status">{{ message }}</p>
    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <div class="rooms-grid">
      <section class="card">
        <h2>เพิ่มห้องใหม่</h2>

        <form @submit.prevent="createRoom">
          <div class="field">
            <label for="room-building">อาคาร *</label>
            <input id="room-building" v-model="form.building" required placeholder="เช่น CSB">
          </div>

          <div class="field">
            <label for="room-floor">ชั้น *</label>
            <input id="room-floor" v-model="form.floor" required placeholder="เช่น 3">
          </div>

          <div class="field">
            <label for="room-number">เลขห้อง *</label>
            <input id="room-number" v-model="form.room_number" required placeholder="เช่น 301">
          </div>

          <div class="field">
            <label for="room-name">ชื่อห้อง</label>
            <input id="room-name" v-model="form.room_name" placeholder="เช่น ห้องปฏิบัติการคอมพิวเตอร์ 1">
          </div>

          <button class="btn-primary" :disabled="submitting">
            <i class="fa-solid fa-plus"></i>
            {{ submitting ? 'กำลังเพิ่ม...' : 'เพิ่มห้อง' }}
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
                  <a v-if="room.qrUrl" :href="room.qrUrl" target="_blank" rel="noopener">
                    <img
                      class="qr-image"
                      :src="room.qrUrl"
                      :alt="`QR ห้อง ${room.room_number}`"
                    >
                  </a>
                  <span v-else class="muted">กำลังโหลด...</span>
                </td>
                <td>
                  <div class="row-actions wrap">
                    <a
                      v-if="room.qrUrl"
                      class="btn-soft"
                      :href="room.qrUrl"
                      :download="qrFileName(room)"
                    >
                      <i class="fa-solid fa-download"></i>
                      ดาวน์โหลด QR
                    </a>

                    <button
                      class="btn-soft"
                      type="button"
                      :class="{ danger: room.is_active }"
                      @click="toggleRoom(room)"
                    >
                      {{ room.is_active ? 'ปิดใช้งาน' : 'เปิดใช้งาน' }}
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-if="!rooms.length">
                <td colspan="5">{{ loading ? 'กำลังโหลด...' : 'ยังไม่มีข้อมูลห้อง' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </StaffLayout>
</template>
