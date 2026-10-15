<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'

const route = useRoute()

function keepRoomQuery(path) {
  return {
    path,
    query: route.query.room
      ? { room: route.query.room }
      : {}
  }
}

const repairLink = computed(() => keepRoomQuery('/request/repair'))
const cleaningLink = computed(() => keepRoomQuery('/request/cleaning'))
</script>

<template>
  <div class="public-app home-page">
    <PublicHeader />

    <main>
      <section class="hero">
        <div class="hero-text">
          <span class="hero-label">CS Building Services</span>

          <h1>
            บริการอาคารเรียน<br>
            สะดวก รวดเร็ว ในที่เดียว
          </h1>

          <p>
            แจ้งซ่อม · แจ้งทำความสะอาด · ของหาย-ของได้คืน
          </p>
        </div>

        <div class="hero-image"></div>
      </section>

      <section class="home-services">
        <h2>เลือกบริการที่คุณต้องการ</h2>

        <div class="service-grid">
          <article class="service-card">
            <i class="fa-solid fa-wrench service-bg-icon"></i>

            <h3>แจ้งซ่อม</h3>

            <p>
              แจ้งซ่อมอาคาร<br>
              ระบบไฟฟ้า ประปา<br>
              แอร์ เฟอร์นิเจอร์<br>
              และอื่น ๆ
            </p>

            <RouterLink
              class="service-link"
              :to="repairLink"
            >
              <span>เริ่มต้น</span>

              <span class="service-link-icon">
                <i class="fa-solid fa-chevron-right"></i>
              </span>
            </RouterLink>
          </article>

          <article class="service-card">
            <i class="fa-solid fa-broom service-bg-icon"></i>

            <h3>
              แจ้งทำความ<br>
              สะอาด
            </h3>

            <p>
              แจ้งขอทำความสะอาด<br>
              ห้องเรียน ห้องน้ำ<br>
              ทางเดิน<br>
              หรือพื้นที่ส่วนกลาง
            </p>

            <RouterLink
              class="service-link"
              :to="cleaningLink"
            >
              <span>เริ่มต้น</span>

              <span class="service-link-icon">
                <i class="fa-solid fa-chevron-right"></i>
              </span>
            </RouterLink>
          </article>

          <article class="service-card">
            <i class="fa-solid fa-magnifying-glass service-bg-icon"></i>

            <h3>
              ของหาย-ของได้<br>
              คืน
            </h3>

            <p>
              แจ้งของที่เก็บได้<br>
              และค้นหารายการของ<br>
              ที่มีผู้พบแล้ว
            </p>

            <RouterLink
              class="service-link"
              to="/lost-found"
            >
              <span>เริ่มต้น</span>

              <span class="service-link-icon">
                <i class="fa-solid fa-chevron-right"></i>
              </span>
            </RouterLink>
          </article>
        </div>
      </section>
    </main>

    <PublicFooter />
  </div>
</template>
