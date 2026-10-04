<template>
  <div class="staff-shell">
    <header class="staff-header">
      <div class="staff-brand">
        <strong>CS BUILDING SERVICES</strong>
        <small>ระบบบริหารจัดการงานบริการอาคารเรียน</small>
      </div>
    </header>

    <div class="staff-body">
      <aside class="staff-sidebar">
        <nav class="staff-menu">
          <RouterLink to="/staff/dashboard">
            <i class="fa-solid fa-chart-line"></i>
            แดชบอร์ด
          </RouterLink>

          <RouterLink to="/staff/requests">
            <i class="fa-solid fa-clipboard-list"></i>
            คำขอบริการ
          </RouterLink>

          <RouterLink to="/staff/lost-found">
            <i class="fa-solid fa-box"></i>
            ของหาย-ของได้คืน
          </RouterLink>

          <RouterLink to="/staff/rooms">
            <i class="fa-solid fa-door-open"></i>
            จัดการห้อง / QR
          </RouterLink>

          <RouterLink to="/">
            <i class="fa-solid fa-house"></i>
            หน้าผู้ใช้งาน
          </RouterLink>
        </nav>
      </aside>

      <main class="staff-main">
        <slot />
      </main>
    </div>
  </div>
</template>
