<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import PublicFooter from '../components/PublicFooter.vue'
import { getAuth } from '../composables/useAuth'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

async function handleLogin() {
  if (isLoading.value) return

  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok || !data.token) {
      errorMessage.value = data.message || 'ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง'
      return
    }

    localStorage.setItem('token', data.token)

    // ใช้ตัวถอดรหัสกลางที่รองรับ base64url
    const auth = getAuth()

    if (!auth) {
      localStorage.removeItem('token')
      errorMessage.value = 'ได้รับข้อมูลเข้าสู่ระบบที่ไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง'
      return
    }

    router.push(auth.role === 'admin' ? '/staff/dashboard' : '/staff/requests')
  } catch {
    errorMessage.value = 'ไม่สามารถเชื่อมต่อระบบได้ กรุณาลองใหม่อีกครั้ง'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="public-app login-page">
    <PublicHeader />

    <main class="login-main">
      <section class="login-section">
        <div class="login-card service-card">
          <div class="login-header">
            <i class="fa-solid fa-user-shield login-icon"></i>
            <h2>สำหรับเจ้าหน้าที่</h2>
            <p>กรุณาเข้าสู่ระบบเพื่อจัดการคำขอบริการ</p>
          </div>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label for="username">ชื่อผู้ใช้งาน</label>
              <div class="input-wrapper">
                <i class="fa-solid fa-user input-icon"></i>
                <input
                  type="text"
                  id="username"
                  v-model="username"
                  placeholder="กรอกชื่อผู้ใช้งาน"
                  autocomplete="username"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label for="password">รหัสผ่าน</label>
              <div class="input-wrapper">
                <i class="fa-solid fa-lock input-icon"></i>
                <input
                  type="password"
                  id="password"
                  v-model="password"
                  placeholder="กรอกรหัสผ่าน"
                  autocomplete="current-password"
                  required
                />
              </div>
            </div>

            <div v-if="errorMessage" class="error-alert" role="alert">
              <i class="fa-solid fa-circle-exclamation"></i>
              {{ errorMessage }}
            </div>

            <button type="submit" class="login-submit-btn" :disabled="isLoading">
              <span v-if="!isLoading">เข้าสู่ระบบ</span>
              <span v-else>กำลังเข้าสู่ระบบ...</span>
              <i class="fa-solid fa-arrow-right-to-bracket" v-if="!isLoading"></i>
            </button>
          </form>
        </div>
      </section>
    </main>

    <PublicFooter />
  </div>
</template>
