<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useImageUploader } from '../composables/useImageUploader'
import { todayString } from '../utils/format'

const route = useRoute()
const q = ref('')
const items = ref([])
const statuses = ref({})
const message = ref('')
const listError = ref('')
const submitting = ref(false)
const formRef = ref(null)
const foundDate = ref('')
const maxDate = todayString()

const foundLocation = ref('')
let qrLocationText = ''

async function prefillLocationFromRoom() {
  const code = String(route.query.room || '').trim()
  if (!code) return

  try {
    const response = await fetch(`/api/rooms/resolve/${encodeURIComponent(code)}`)
    if (!response.ok) return

    const { room } = await response.json()
    qrLocationText = `${room.building} ชั้น ${room.floor} ห้อง ${room.room_number}`
    if (room.room_name) qrLocationText += ` (${room.room_name})`

    if (!foundLocation.value.trim()) foundLocation.value = qrLocationText
  } catch {
  }
}

const {
  previews: foundImagePreviews,
  files: foundImageFiles,
  notice: imageNotice,
  onChange: onFoundImageChange,
  remove: removeFoundImage,
  clear: clearFoundImages
} = useImageUploader(6)

function setCurrentFoundDate() {
  foundDate.value = todayString()
}

async function loadItems() {
  listError.value = ''

  try {
    const params = new URLSearchParams()
    if (q.value.trim()) params.set('q', q.value.trim())

    const response = await fetch(`/api/lost-found?${params}`)
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()
    items.value = data.items || []
    statuses.value = data.statuses || {}
  } catch {
    listError.value = 'ไม่สามารถโหลดรายการได้ กรุณาลองใหม่อีกครั้ง'
  }
}

async function submitFoundItem() {
  if (submitting.value) return

  message.value = ''
  submitting.value = true

  try {
    // อ่าน form จาก ref แทน event.currentTarget (ซึ่งเป็น null หลัง await)
    const form = formRef.value
    const formData = new FormData(form)

    formData.delete('images')
    foundImageFiles.value.forEach((file) => {
      formData.append('images', file)
    })

    const response = await fetch('/api/lost-found', {
      method: 'POST',
      body: formData
    })
    const data = await response.json().catch(() => ({}))

    if (!response.ok || !data.success) {
      message.value = data.message || 'ไม่สามารถบันทึกรายการได้'
      return
    }

    form.reset()
    setCurrentFoundDate()
    
    form.elements.event_date.value = foundDate.value
    clearFoundImages()

    foundLocation.value = qrLocationText
    form.elements.location.value = qrLocationText

    message.value = 'บันทึกรายการของที่เก็บได้เรียบร้อยแล้ว'
    await loadItems()
  } catch {
    message.value = 'ไม่สามารถเชื่อมต่อกับระบบได้'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  setCurrentFoundDate()
  prefillLocationFromRoom()
  loadItems()
})
</script>

<template>
  <div class="public-app">
    <PublicHeader />

    <main class="public-content">
      <RouterLink class="back-link public-back-link" to="/">
        <i class="fa-solid fa-chevron-left"></i>
        กลับหน้าหลัก
      </RouterLink>

      <div class="page-title">
        <span class="eyebrow">LOST & FOUND</span>
        <h1>ของหาย-ของได้คืน</h1>
        <p>
          ระบบนี้รับแจ้งเฉพาะผู้ที่พบสิ่งของ ส่วนเจ้าของสามารถค้นหารายการที่มีผู้พบไว้ได้
        </p>
      </div>

      <div class="lost-found-grid">
        <section class="card">
          <h2>แจ้งของที่เก็บได้</h2>

          <form ref="formRef" class="form-grid" @submit.prevent="submitFoundItem">
            <div class="field">
              <label for="lf-item-name">ชื่อสิ่งของ *</label>
              <input id="lf-item-name" name="item_name" required placeholder="เช่น กระเป๋าสตางค์">
            </div>

            <div class="field">
              <label for="lf-category">หมวดหมู่</label>
              <input id="lf-category" name="category" placeholder="เช่น อุปกรณ์อิเล็กทรอนิกส์">
            </div>

            <div class="field">
              <label for="lf-date">วันที่พบ</label>
              <input
                id="lf-date"
                v-model="foundDate"
                name="event_date"
                type="date"
                :max="maxDate"
              >
            </div>

            <div class="field full">
              <label for="lf-location">สถานที่พบ</label>
              <input id="lf-location" v-model="foundLocation" name="location" placeholder="เช่น CSB ชั้น 3 ห้อง 301">
            </div>

            <div class="field full">
              <label for="lf-description">รายละเอียด *</label>
              <textarea
                id="lf-description"
                name="description"
                required
                placeholder="สี ลักษณะ จุดสังเกต..."
              ></textarea>
            </div>

            <div class="field">
              <label for="lf-contact-name">ชื่อผู้ติดต่อ</label>
              <input id="lf-contact-name" name="contact_name">
            </div>

            <div class="field">
              <label for="lf-contact-info">ช่องทางติดต่อ</label>
              <input id="lf-contact-info" name="contact_info" placeholder="เบอร์โทร / Line / Email">
            </div>

            <div class="field full">
              <label>รูปภาพ</label>

              <label class="multi-upload-box lost-found-upload">
                <input
                  class="upload-input"
                  name="images"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  multiple
                  @change="onFoundImageChange"
                >

                <i class="fa-solid fa-cloud-arrow-up"></i>
                <span>เพิ่มรูปภาพ</span>
                <small>เลือกได้สูงสุด 6 รูป</small>
              </label>

              <div
                v-if="foundImagePreviews.length"
                class="image-preview-grid"
              >
                <article
                  v-for="(preview, index) in foundImagePreviews"
                  :key="preview.url"
                  class="image-preview-card"
                >
                  <img :src="preview.url" :alt="preview.name">

                  <button
                    class="image-remove-btn"
                    type="button"
                    aria-label="ลบรูป"
                    @click="removeFoundImage(index)"
                  >
                    <i class="fa-solid fa-xmark"></i>
                  </button>

                  <span>{{ preview.name }}</span>
                </article>
              </div>

              <small
                v-if="foundImagePreviews.length"
                class="multi-image-count"
              >
                เลือกแล้ว {{ foundImagePreviews.length }}/6 รูป
                สามารถกด “เพิ่มรูปภาพ” เพื่อเพิ่มทีละชุดได้
              </small>

              <small v-if="imageNotice" class="multi-image-count" role="alert">
                {{ imageNotice }}
              </small>
            </div>

            <div class="full">
              <button class="btn-primary" :disabled="submitting">
                {{ submitting ? 'กำลังบันทึก...' : 'แจ้งของที่เก็บได้' }}
              </button>
            </div>
          </form>

          <p v-if="message" class="form-message" role="status">{{ message }}</p>
        </section>

        <section class="card">
          <div class="list-header">
            <div>
              <h2>รายการของที่มีผู้พบ</h2>
              <p class="muted">ค้นหาจากชื่อสิ่งของ สถานที่ หรือรายละเอียด</p>
            </div>

            <form class="search-row" @submit.prevent="loadItems">
              <input v-model="q" placeholder="ค้นหา..." aria-label="ค้นหา">
              <button class="btn-primary">ค้นหา</button>
            </form>
          </div>

          <p v-if="listError" class="form-message" role="alert">{{ listError }}</p>

          <div class="found-items">
            <article v-for="item in items" :key="item.id" class="found-item">
              <img
                v-if="item.images?.length || item.image_path"
                class="found-thumb"
                :src="`/uploads/${item.images?.[0] || item.image_path}`"
                alt="รูปสิ่งของ"
              >
              <div v-else class="found-thumb empty-thumb">
                <i class="fa-regular fa-image"></i>
              </div>

              <div>
                <div class="found-title">ของที่เก็บได้ · {{ item.item_name }}</div>
                <p>{{ item.description }}</p>
                <p class="muted">{{ item.location || '-' }} · {{ item.event_date || '-' }}</p>
                <StatusBadge
                  :status="item.status"
                  :label="statuses[item.status] || item.status"
                />

                <RouterLink
                  class="found-detail-link"
                  :to="`/lost-found/${item.id}`"
                >
                  ดูรายละเอียด
                  <i class="fa-solid fa-chevron-right"></i>
                </RouterLink>
              </div>
            </article>

            <p v-if="!items.length && !listError" class="muted">ยังไม่มีรายการ</p>
          </div>
        </section>
      </div>
    </main>

    <PublicFooter />
  </div>
</template> 