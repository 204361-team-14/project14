<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const statuses = ref({})
const activeImage = ref('')

async function loadDetail() {
  const response = await fetch(`/api/lost-found/${route.params.id}`)

  if (!response.ok) {
    router.replace('/lost-found')
    return
  }

  const data = await response.json()
  item.value = data.item
  statuses.value = data.statuses || {}

  const images = item.value.images || []
  activeImage.value = images[0] || item.value.image_path || ''
}

onMounted(loadDetail)
</script>

<template>
  <div class="public-app public-page-shell">
    <PublicHeader />

    <main class="public-content">
      <RouterLink class="back-link public-back-link" to="/lost-found">
        <i class="fa-solid fa-chevron-left"></i>
        กลับรายการของหาย-ของได้คืน
      </RouterLink>

      <template v-if="item">
        <div class="page-title">
          <span class="eyebrow">LOST & FOUND</span>
          <h1>{{ item.item_name }}</h1>
          <p>รายละเอียดสิ่งของที่มีผู้พบและแจ้งเข้ามาในระบบ</p>
        </div>

        <div class="public-found-detail">
          <section class="card public-found-gallery">
            <div
              v-if="activeImage"
              class="public-found-main-image"
            >
              <img
                :src="`/uploads/${activeImage}`"
                :alt="item.item_name"
              >
            </div>

            <div v-else class="public-found-no-image">
              <i class="fa-regular fa-image"></i>
              <span>ไม่มีรูปภาพ</span>
            </div>

            <div
              v-if="item.images?.length > 1"
              class="public-found-thumbnails"
            >
              <button
                v-for="image in item.images"
                :key="image"
                type="button"
                :class="{ active: activeImage === image }"
                @click="activeImage = image"
              >
                <img
                  :src="`/uploads/${image}`"
                  :alt="item.item_name"
                >
              </button>
            </div>
          </section>

          <section class="card public-found-info">
            <div class="found-detail-title-row">
              <div>
                <span class="eyebrow">ของที่เก็บได้</span>
                <h2>{{ item.item_name }}</h2>
              </div>

              <StatusBadge
                :status="item.status"
                :label="statuses[item.status] || item.status"
              />
            </div>

            <div class="public-found-info-grid">
              <div>
                <span>หมวดหมู่</span>
                <strong>{{ item.category || '-' }}</strong>
              </div>

              <div>
                <span>วันที่พบ</span>
                <strong>{{ item.event_date || '-' }}</strong>
              </div>

              <div class="full">
                <span>สถานที่พบ</span>
                <strong>{{ item.location || '-' }}</strong>
              </div>
            </div>

            <div class="detail-section">
              <h3>รายละเอียด</h3>
              <p>{{ item.description }}</p>
            </div>

            <div class="detail-section">
              <h3>ข้อมูลสำหรับติดต่อ</h3>

              <div class="public-found-info-grid">
                <div>
                  <span>ผู้แจ้ง</span>
                  <strong>{{ item.contact_name || '-' }}</strong>
                </div>

                <div>
                  <span>ช่องทางติดต่อ</span>
                  <strong>{{ item.contact_info || '-' }}</strong>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>
    </main>

    <PublicFooter />
  </div>
</template>
