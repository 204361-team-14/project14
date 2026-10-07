<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import StaffLayout from '../components/StaffLayout.vue'

const users = ref([])
const message = ref('')
const error = ref('')
const searchQuery = ref('')
const filterRole = ref('')
const currentUsername = ref('') 

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

function loadCurrentUser() {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      currentUsername.value = payload.username
    } catch (e) {
      console.error("Token ไม่ถูกต้อง")
    }
  }
}

const getHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}

async function loadUsers() {
  try {
    const response = await fetch('/api/staff/users', { headers: getHeaders() })
    const data = await response.json()
    if (response.ok) {
      users.value = data.users || []
    }
  } catch (err) {
    error.value = 'ไม่สามารถโหลดข้อมูลพนักงานได้'
  }
}

const filteredUsers = computed(() => {
  const filtered = users.value.filter(user => {
    const matchSearch = user.username.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                        (user.email && user.email.toLowerCase().includes(searchQuery.value.toLowerCase()))
    
    const matchRole = filterRole.value === '' || user.role === filterRole.value

    return matchSearch && matchRole
  })
  
  return filtered.sort((a, b) => {
    if (a.username === currentUsername.value) return -1 
    if (b.username === currentUsername.value) return 1  
    return a.id - b.id 
  })
})

async function createUser() {
  message.value = ''
  error.value = ''

  try {
    const response = await fetch('/api/staff/users', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(form)
    })
    const data = await response.json()

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
  } catch (err) {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
  }
}

async function handleRoleChange(user, event) {
  const newRole = event.target.value
  const oldRole = user.role

  if (user.username === currentUsername.value && newRole !== 'admin') {
    alert('คุณไม่สามารถลดสิทธิ์ตัวเองในขณะที่ใช้งานอยู่ได้')
    event.target.value = oldRole
    return
  }

  user.role = newRole
  await updateRole(user, oldRole)
}

async function updateRole(user, oldRole) {
  message.value = ''
  error.value = ''
  try {
    const response = await fetch(`/api/staff/users/${user.id}/role`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({ role: user.role })
    })

    if (response.ok) {
      message.value = `เปลี่ยนตำแหน่งของ ${user.username} เรียบร้อยแล้ว`
    } else {
      const data = await response.json()
      error.value = data.message || 'ไม่สามารถอัปเดตตำแหน่งได้'
      user.role = oldRole 
    }
  } catch (err) {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
    user.role = oldRole
  }
}

async function deleteUser(user) {
  if (user.username === currentUsername.value) {
    alert('ไม่สามารถลบบัญชีที่กำลังล็อกอินอยู่ได้')
    return
  }

  if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบบัญชี ${user.username}?`)) return

  try {
    const response = await fetch(`/api/staff/users/${user.id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })

    if (response.ok) {
      message.value = 'ลบบัญชีเรียบร้อยแล้ว'
      await loadUsers()
    } else {
      const data = await response.json()
      error.value = data.message || 'ไม่สามารถลบผู้ใช้งานได้'
    }
  } catch (err) {
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

async function saveEditUser() {
  message.value = ''
  error.value = ''
  
  try {

    const updateData = {
      username: editForm.username,
      email: editForm.email
    }
    // ถ้ามีการกรอกรหัสผ่านใหม่ ค่อยแนบไป
    if (editForm.password.trim() !== '') {
      updateData.password = editForm.password
    }

    const response = await fetch(`/api/staff/users/${editForm.id}`, {
      method: 'PUT', // หรือ PATCH ขึ้นอยู่กับ API ของคุณ
      headers: getHeaders(),
      body: JSON.stringify(updateData)
    })

    if (response.ok) {
      message.value = 'อัปเดตข้อมูลผู้ใช้งานเรียบร้อยแล้ว'
      closeEditUser()
      await loadUsers()
    } else {
      const data = await response.json()
      error.value = data.message || 'ไม่สามารถอัปเดตข้อมูลได้'
    }
  } catch (err) {
    error.value = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'
  }
}


function getRoleBadgeClass(role) {
  if (role === 'admin') return 'on' 
  if (role === 'technician') return 'off' 
  if (role === 'maid') return 'warning' 
  return ''
}

onMounted(() => {
  loadCurrentUser()
  loadUsers()
})
</script>

<template>
  <StaffLayout>
    <div class="staff-page-title">
      <h1>จัดการพนักงานและตำแหน่ง</h1>
      <p>เพิ่ม ลบ หรือแก้ไขตำแหน่ง (ช่าง, แม่บ้าน, ผู้ดูแลระบบ) เพื่อจำกัดสิทธิ์การเข้าถึงข้อมูล</p>
    </div>

    <p v-if="message" class="flash success">{{ message }}</p>
    <p v-if="error" class="flash error">{{ error }}</p>

    <div class="rooms-grid">
      <!-- ... ส่วนเพิ่มพนักงานใหม่ เหมือนเดิม ... -->
      <section class="card">
        <h2>เพิ่มพนักงานใหม่</h2>
        <form @submit.prevent="createUser">
          <div class="field">
            <label>ชื่อผู้ใช้งาน (Username) *</label>
            <input v-model="form.username" required placeholder="เช่น tech_01">
          </div>
          <div class="field">
            <label>อีเมล (Email)</label>
            <input type="email" v-model="form.email" placeholder="เช่น user@example.com">
          </div>
          <div class="field">
            <label>รหัสผ่าน *</label>
            <input type="password" v-model="form.password" required placeholder="กำหนดรหัสผ่าน">
          </div>
          <div class="field">
            <label>ตำแหน่ง *</label>
            <select v-model="form.role" required>
              <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <button type="submit" class="btn-primary">
            <i class="fa-solid fa-user-plus"></i> เพิ่มพนักงาน
          </button>
        </form>
      </section>

      <section class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h2 style="margin: 0;">บัญชีผู้ใช้งานทั้งหมด</h2>
          
          <div style="display: flex; gap: 0.5rem;">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="ค้นหาชื่อ หรือ อีเมล..." 
              style="padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px;"
            >
            <select v-model="filterRole" style="padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px;">
              <option value="">ทุกตำแหน่ง</option>
              <option value="admin">ผู้ดูแลระบบ</option>
              <option value="technician">ช่าง</option>
              <option value="maid">แม่บ้าน</option>
            </select>
          </div>
        </div>

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
                <td><strong>{{ user.username }}</strong></td>
                <td>{{ user.email || '-' }}</td>
                <td>
                  <select 
                    :value="user.role" 
                    @change="handleRoleChange(user, $event)" 
                    class="role-inline-select"
                    :class="getRoleBadgeClass(user.role)"
                    :disabled="user.username === currentUsername"
                  >
                    <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </td>
                <td>
                  <div class="row-actions wrap">
                    <!-- ปุ่มแก้ไข (เพิ่มเข้ามาใหม่) -->
                    <button
                      class="btn-soft"
                      @click="openEditUser(user)"
                    >
                      <i class="fa-solid fa-pen-to-square"></i> แก้ไข
                    </button>
                    <!-- ปุ่มลบ (ของเดิม) -->
                    <button
                      class="btn-soft danger"
                      @click="deleteUser(user)"
                      :disabled="user.username === currentUsername"
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
      style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;"
    >
      <div class="card" style="width: 100%; max-width: 400px; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <h2 style="margin-top: 0;">แก้ไขข้อมูลบัญชี</h2>
        <form @submit.prevent="saveEditUser">
          <div class="field">
            <label>ชื่อผู้ใช้งาน (Username) *</label>
            <input v-model="editForm.username" required>
          </div>
          <div class="field">
            <label>อีเมล (Email)</label>
            <input type="email" v-model="editForm.email">
          </div>
          <div class="field">
            <label>รหัสผ่านใหม่ (ไม่บังคับ)</label>
            <input type="password" v-model="editForm.password" placeholder="ปล่อยว่างไว้หากไม่ต้องการเปลี่ยน">
          </div>
          <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
            <button type="submit" class="btn-primary" style="flex: 1;">บันทึก</button>
            <button type="button" class="btn-soft" @click="closeEditUser" style="flex: 1;">ยกเลิก</button>
          </div>
        </form>
      </div>
    </div>

  </StaffLayout>
</template>