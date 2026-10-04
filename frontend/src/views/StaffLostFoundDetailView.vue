<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StaffLayout from '../components/StaffLayout.vue'
import StatusBadge from '../components/StatusBadge.vue'
import ImageLightbox from '../components/ImageLightbox.vue'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const statuses = ref({})
const imageViewerIndex = ref(-1)

async function loadDetail() {
  const response = await fetch(`/api/staff/lost-found/${route.params.id}`)
  if (!response.ok) {
    router.replace('/staff/lost-found')
    return
  }

  const data = await response.json()
  item.value = data.item
  statuses.value = data.statuses || {}
}

function openImageViewer(index) {
  imageViewerIndex.value = index
}

function closeImageViewer() {
  imageViewerIndex.value = -1
}

async function updateStatus(status) {
  const response = await fetch(`/api/staff/lost-found/${route.params.id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })

  if (response.ok) await loadDetail()
}

onMounted(loadDetail)
</script>

<template>
  <StaffLayout>
    <template v-if="item">
      <RouterLink class="back-link" to="/staff/lost-found">
        <i class="fa-solid fa-chevron-left"></i>
        กลับรายการของหาย-ของได้คืน
      </RouterLink>

      <div class="staff-page-title">
        <h1>รายละเอียดของที่เก็บได้ LF-{{ String(item.id).padStart(6, '0') }}</h1>
        <p>ข้อมูลสิ่งของที่มีผู้พบและแจ้งเข้ามาในระบบ</p>
      </div>

      <section class="card detail-card">
        <div class="detail-grid three">
          <div><span>ชื่อสิ่งของ</span><strong>{{ item.item_name }}</strong></div>
          <div><span>หมวดหมู่</span><strong>{{ item.category || '-' }}</strong></div>
          <div>
            <span>สถานะ</span>
            <StatusBadge :status="item.status" :label="statuses[item.status] || item.status" />
          </div>
          <div><span>สถานที่พบ</span><strong>{{ item.location || '-' }}</strong></div>
          <div><span>วันที่พบ</span><strong>{{ item.event_date || '-' }}</strong></div>
          <div><span>วันที่แจ้ง</span><strong>{{ item.created_at || '-' }}</strong></div>
        </div>

        <div class="detail-section">
          <h3>รายละเอียด</h3>
          <p>{{ item.description }}</p>
        </div>

        <div class="detail-section">
          <h3>ข้อมูลผู้แจ้ง</h3>
          <div class="detail-grid two">
            <div><span>ชื่อผู้ติดต่อ</span><strong>{{ item.contact_name || '-' }}</strong></div>
            <div><span>ช่องทางติดต่อ</span><strong>{{ item.contact_info || '-' }}</strong></div>
          </div>
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
                alt="รูปสิ่งของ"
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
              alt="รูปสิ่งของ"
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
    </template>

    <ImageLightbox
      :images="item?.images?.length ? item.images : (item?.image_path ? [item.image_path] : [])"
      :index="imageViewerIndex"
      @update:index="imageViewerIndex = $event"
      @close="closeImageViewer"
    />
  </StaffLayout>
</template>
