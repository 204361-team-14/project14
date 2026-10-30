<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'
import { apiFetch, getAuth } from '../composables/useAuth'
import { alertDialog, confirmDialog } from '../composables/useDialog'

const MIN_PASSWORD_LENGTH = 8

const auth = getAuth()
const currentUserId = auth?.userId ?? null

const users = ref([])
const message = ref('')
const error = ref('')
const searchQuery = ref('')
const filterRole = ref('')
const creating = ref(false)
const saving = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  role: 'technician'
})

const editingUser = ref(null)
const editForm = reactive({
  id: null,
  username: '',
  email: '',
  password: ''
})

const roleOptions = [
  { value: 'admin', label: 'ผู้ดูแลระบบ (Admin)' },
  { value: 'technician', label: 'ช่าง (Technician)' },
  { value: 'maid', label: 'แม่บ้าน (Maid)' }
]

function isSelf(user) {
  return currentUserId !== null && Number(user.id) === Number(currentUserId)
}

async function loadUsers() {
  try {
    const response = await apiFetch('/api/staff/users')
    if (!response.ok) throw new Error('load failed')

    const data = await response.json()
    users.value = data.users || []
  } catch {
    error.value = 'ไม่สามารถโหลดข้อมูลพนักงานได้'
  }
}

const filteredUsers = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()

  return users.value
    .filter((user) => {
      const matchSearch = !keyword ||
        user.username.toLowerCase().includes(keyword) ||
        (user.email && user.email.toLowerCase().includes(keyword))

      const matchRole = filterRole.value === '' || user.role === filterRole.value

      return matchSearch && matchRole
    })
    .sort((a, b) => {
      if (isSelf(a)) return -1
      if (isSelf(b)) return 1
      return a.id - b.id
    })
})

async function createUser() {
  if (creating.value) return

  message.value = ''
  error.value = ''

  if (form.password.length < MIN_PASSWORD_LENGTH) {
    error.value = `รหัสผ่านต้องมีอย่างน้อย ${MIN_PASSWORD_LENGTH} ตัวอักษร`
    return
  }

  creating.value = true

  try {
    const response = await apiFetch('/api/staff/users', {
      method: 'POST',
      body: JSON.stringify({ ...form, username: form.username.trim() })
    })
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      error.value = data.message || 'ไม่สามารถเพิ่มพนักงานได้'
      return
    }

    message.value = 'เพิ่มพนักงานเรียบร้อยแล้ว'
    form.username = ''
    form.email = ''
    form.password = ''
    form.role = 'technician'
    await loadUsers()
  } catch {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
  } finally {
    creating.value = false
  }
}

async function handleRoleChange(user, event) {
  const newRole = event.target.value
  const oldRole = user.role

  if (isSelf(user) && newRole !== 'admin') {
    event.target.value = oldRole
    await alertDialog('คุณไม่สามารถลดสิทธิ์ตัวเองในขณะที่ใช้งานอยู่ได้', { title: 'ไม่สามารถเปลี่ยนตำแหน่งได้' })
    return
  }

  user.role = newRole
  await updateRole(user, oldRole, event)
}

async function updateRole(user, oldRole, event) {
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(`/api/staff/users/${user.id}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role: user.role })
    })

    if (response.ok) {
      message.value = `เปลี่ยนตำแหน่งของ ${user.username} เรียบร้อยแล้ว`
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถอัปเดตตำแหน่งได้'
      user.role = oldRole
      event.target.value = oldRole
    }
  } catch {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
    user.role = oldRole
    event.target.value = oldRole
  }
}

async function deleteUser(user) {
  if (isSelf(user)) {
    await alertDialog('ไม่สามารถลบบัญชีที่กำลังล็อกอินอยู่ได้', { title: 'ไม่สามารถลบบัญชีได้' })
    return
  }

  const ok = await confirmDialog(`ต้องการลบบัญชี "${user.username}" ใช่หรือไม่?\nการลบไม่สามารถย้อนกลับได้`, {
    title: 'ลบบัญชีผู้ใช้งาน',
    confirmText: 'ลบบัญชี',
    variant: 'danger'
  })
  if (!ok) return

  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(`/api/staff/users/${user.id}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      message.value = 'ลบบัญชีเรียบร้อยแล้ว'
      await loadUsers()
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถลบผู้ใช้งานได้'
    }
  } catch {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
  }
}

function openEditUser(user) {
  editingUser.value = user
  editForm.id = user.id
  editForm.username = user.username
  editForm.email = user.email || ''
  editForm.password = ''
}

function closeEditUser() {
  editingUser.value = null
}

function onKeydown(event) {
  if (event.key === 'Escape' && editingUser.value) closeEditUser()
}

async function saveEditUser() {
  if (saving.value) return

  message.value = ''
  error.value = ''

  const newPassword = editForm.password.trim()

  if (newPassword !== '' && newPassword.length < MIN_PASSWORD_LENGTH) {
    error.value = `รหัสผ่านใหม่ต้องมีอย่างน้อย ${MIN_PASSWORD_LENGTH} ตัวอักษร`
    return
  }

  saving.value = true

  try {
    const updateData = {
      username: editForm.username.trim(),
      email: editForm.email.trim()
    }

    // แนบรหัสผ่านเฉพาะเมื่อกรอกใหม่
    if (newPassword !== '') {
      updateData.password = editForm.password
    }

    const response = await apiFetch(`/api/staff/users/${editForm.id}`, {
      method: 'PUT', 
      body: JSON.stringify(updateData)
    })

    if (response.ok) {
      message.value = 'อัปเดตข้อมูลผู้ใช้งานเรียบร้อยแล้ว'
      closeEditUser()
      await loadUsers()
    } else {
      const data = await response.json().catch(() => ({}))
      error.value = data.message || 'ไม่สามารถอัปเดตข้อมูลได้'
    }
  } catch {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
  } finally {
    saving.value = false
  }
}

function onSearchSubmit() {
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
}

function getRoleClass(role) {
  if (role === 'admin') return 'role-admin'
  if (role === 'technician') return 'role-technician'
  if (role === 'maid') return 'role-maid'
  return ''
}

onMounted(() => {
  loadUsers()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>จัดการพนักงานและตำแหน่ง</h1>
      <p>เพิ่ม ลบ หรือแก้ไขตำแหน่ง (ช่าง, แม่บ้าน, ผู้ดูแลระบบ) เพื่อจำกัดสิทธิ์การเข้าถึงข้อมูล</p>
    </div>

    <p v-if="message" class="flash success" role="status">{{ message }}</p>
    <p v-if="error" class="flash error" role="alert">{{ error }}</p>

    <div class="rooms-grid">
      <section class="card">
        <h2>เพิ่มพนักงานใหม่</h2>
        <form @submit.prevent="createUser">
          <div class="field">
            <label for="new-username">ชื่อผู้ใช้งาน (Username) *</label>
            <input id="new-username" v-model="form.username" required placeholder="เช่น tech_01" autocomplete="off">
          </div>
          <div class="field">
            <label for="new-email">อีเมล (Email)</label>
            <input id="new-email" type="email" v-model="form.email" placeholder="เช่น user@example.com" autocomplete="off">
          </div>
          <div class="field">
            <label for="new-password">รหัสผ่าน * (อย่างน้อย {{ MIN_PASSWORD_LENGTH }} ตัวอักษร)</label>
            <input
              id="new-password"
              type="password"
              v-model="form.password"
              required
              :minlength="MIN_PASSWORD_LENGTH"
              placeholder="กำหนดรหัสผ่าน"
              autocomplete="new-password"
            >
          </div>
          <div class="field">
            <label for="new-role">ตำแหน่ง *</label>
            <select id="new-role" v-model="form.role" required>
              <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <button type="submit" class="btn-primary" :disabled="creating">
            <i class="fa-solid fa-user-plus"></i>
            {{ creating ? 'กำลังเพิ่ม...' : 'เพิ่มพนักงาน' }}
          </button>
        </form>
      </section>

      <section class="card">
        <h2>บัญชีผู้ใช้งานทั้งหมด</h2>

        <form class="filter-grid users" @submit.prevent="onSearchSubmit">
          <input
            v-model="searchQuery"
            type="search"
            placeholder="ค้นหาชื่อ หรือ อีเมล..."
            aria-label="ค้นหา"
          >

          <select v-model="filterRole" aria-label="กรองตามตำแหน่ง">
            <option value="">ทุกตำแหน่ง</option>
            <option value="admin">ผู้ดูแลระบบ</option>
            <option value="technician">ช่าง</option>
            <option value="maid">แม่บ้าน</option>
          </select>

          <button class="btn-primary">ค้นหา</button>
        </form>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ชื่อผู้ใช้งาน</th>
                <th>อีเมล</th>
                <th>ตำแหน่ง</th>
                <th>จัดการ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td>
                  <strong>{{ user.username }}</strong>
                  <small v-if="isSelf(user)" class="muted"> (คุณ)</small>
                </td>
                <td>{{ user.email || '-' }}</td>
                <td>
                  <select
                    :value="user.role"
                    class="role-inline-select"
                    :class="getRoleClass(user.role)"
                    :disabled="isSelf(user)"
                    :aria-label="`ตำแหน่งของ ${user.username}`"
                    @change="handleRoleChange(user, $event)"
                  >
                    <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </td>
                <td>
                  <div class="row-actions wrap">
                    <button
                      type="button"
                      class="btn-soft"
                      @click="openEditUser(user)"
                    >
                      <i class="fa-solid fa-pen-to-square"></i> แก้ไข
                    </button>
                    <button
                      type="button"
                      class="btn-soft danger"
                      :disabled="isSelf(user)"
                      @click="deleteUser(user)"
                    >
                      <i class="fa-solid fa-trash"></i>
                      ลบ
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredUsers.length">
                <td colspan="4" style="text-align: center;">ไม่พบข้อมูลผู้ใช้งานที่ค้นหา</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <div
      v-if="editingUser"
      class="modal-backdrop"
      @click.self="closeEditUser"
    >
      <div
        class="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-user-title"
      >
        <h2 id="edit-user-title">แก้ไขข้อมูลบัญชี</h2>
        <form @submit.prevent="saveEditUser">
          <div class="field">
            <label for="edit-username">ชื่อผู้ใช้งาน (Username) *</label>
            <input id="edit-username" v-model="editForm.username" required autofocus>
          </div>
          <div class="field">
            <label for="edit-email">อีเมล (Email)</label>
            <input id="edit-email" type="email" v-model="editForm.email">
          </div>
          <div class="field">
            <label for="edit-password">รหัสผ่านใหม่ (ไม่บังคับ)</label>
            <input
              id="edit-password"
              type="password"
              v-model="editForm.password"
              placeholder="ปล่อยว่างไว้หากไม่ต้องการเปลี่ยน"
              autocomplete="new-password"
            >
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeEditUser">ยกเลิก</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'กำลังบันทึก...' : 'บันทึก' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </StaffLayout>
</template>

<style scoped>
.filter-grid.users {
  grid-template-columns: 2fr 1fr auto;
}

@media (max-width: 960px) {
  .filter-grid.users {
    grid-template-columns: 1fr 1fr auto;
  }
}

@media (max-width: 700px) {
  .filter-grid.users {
    grid-template-columns: 1fr;
  }
}

.role-admin {
  border-color: #2563eb;
  color: #1d4ed8;
}

.role-technician {
  border-color: #0d9488;
  color: #0f766e;
}

.role-maid {
  border-color: #d97706;
  color: #b45309;
}
</style>
