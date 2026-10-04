<script setup>
import { onMounted, ref } from 'vue'
import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'
import StatusBadge from '../components/StatusBadge.vue'

const q = ref('')
const items = ref([])
const statuses = ref({})
const message = ref('')
const submitting = ref(false)
const formRef = ref(null)
const foundImageFiles = ref([])
const foundImagePreviews = ref([])
const foundDate = ref('')

function setCurrentFoundDate() {
  const now = new Date()

  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')

  foundDate.value = `${year}-${month}-${day}`
}

function rebuildFoundImagePreviews() {
  foundImagePreviews.value.forEach((preview) => {
    URL.revokeObjectURL(preview.url)
  })

  foundImagePreviews.value = foundImageFiles.value.map((file) => ({
    name: file.name,
    url: URL.createObjectURL(file)
  }))
}

function clearFoundImagePreviews() {
  foundImagePreviews.value.forEach((preview) => {
    URL.revokeObjectURL(preview.url)
  })

  foundImageFiles.value = []
  foundImagePreviews.value = []
}

function onFoundImageChange(event) {
  const selected = Array.from(event.target.files || [])

  const existingKeys = new Set(
    foundImageFiles.value.map(
      (file) => `${file.name}-${file.size}-${file.lastModified}`
    )
  )

  for (const file of selected) {
    const key = `${file.name}-${file.size}-${file.lastModified}`

    if (!existingKeys.has(key) && foundImageFiles.value.length < 6) {
      foundImageFiles.value.push(file)
      existingKeys.add(key)
    }
  }

  rebuildFoundImagePreviews()
  event.target.value = ''
}

function removeFoundImage(index) {
  foundImageFiles.value.splice(index, 1)
  rebuildFoundImagePreviews()
}

async function loadItems() {
  const params = new URLSearchParams()
  if (q.value.trim()) params.set('q', q.value.trim())

  const response = await fetch(`/api/lost-found?${params}`)
  const data = await response.json()
  items.value = data.items || []
  statuses.value = data.statuses || {}
}

async function submitFoundItem(event) {
  message.value = ''
  submitting.value = true

  try {
    const formData = new FormData(event.currentTarget)

    formData.delete('images')
    foundImageFiles.value.forEach((file) => {
      formData.append('images', file)
    })

    const response = await fetch('/api/lost-found', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()

    if (!response.ok || !data.success) {
      message.value = data.message || 'ไม่สามารถบันทึกรายการได้'
      return
    }

    message.value = 'บันทึกรายการของที่เก็บได้เรียบร้อยแล้ว'
    event.currentTarget.reset()

    clearFoundImagePreviews()

    await loadItems()
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  setCurrentFoundDate()
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
              <label>ชื่อสิ่งของ *</label>
              <input name="item_name" required placeholder="เช่น กระเป๋าสตางค์">
            </div>

            <div class="field">
              <label>หมวดหมู่</label>
              <input name="category" placeholder="เช่น อุปกรณ์อิเล็กทรอนิกส์">
            </div>

            <div class="field">
              <label>วันที่พบ</label>
              <input v-model="foundDate" name="event_date" type="date">
            </div>

            <div class="field full">
              <label>สถานที่พบ</label>
              <input name="location" placeholder="เช่น CSB ชั้น 3 ห้อง 301">
            </div>

            <div class="field full">
              <label>รายละเอียด *</label>
              <textarea name="description" required placeholder="สี ลักษณะ จุดสังเกต..."></textarea>
            </div>

            <div class="field">
              <label>ชื่อผู้ติดต่อ</label>
              <input name="contact_name">
            </div>

            <div class="field">
              <label>ช่องทางติดต่อ</label>
              <input name="contact_info" placeholder="เบอร์โทร / Line / Email">
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
            </div>

            <div class="full">
              <button class="btn-primary" :disabled="submitting">
                {{ submitting ? 'กำลังบันทึก...' : 'แจ้งของที่เก็บได้' }}
              </button>
            </div>
          </form>

          <p v-if="message" class="form-message">{{ message }}</p>
        </section>

        <section class="card">
          <div class="list-header">
            <div>
              <h2>รายการของที่มีผู้พบ</h2>
              <p class="muted">ค้นหาจากชื่อสิ่งของ สถานที่ หรือรายละเอียด</p>
            </div>

            <form class="search-row" @submit.prevent="loadItems">
              <input v-model="q" placeholder="ค้นหา...">
              <button class="btn-primary">ค้นหา</button>
            </form>
          </div>

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

            <p v-if="!items.length" class="muted">ยังไม่มีรายการ</p>
          </div>
        </section>
      </div>
    </main>

    <PublicFooter />
  </div>
</template>
