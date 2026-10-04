<template>
  <header class="public-header">
    <RouterLink class="public-brand" to="/">
      CS BUILDING SERVICES
    </RouterLink>

    <nav class="public-nav">
      <RouterLink to="/">
        <i class="fa-solid fa-house"></i>
        หน้าหลัก
      </RouterLink>

      <RouterLink to="/lost-found">
        <i class="fa-solid fa-magnifying-glass"></i>
        ของหาย-ของได้คืน
      </RouterLink>

      <RouterLink class="staff-entry" to="/staff/dashboard">
        สำหรับเจ้าหน้าที่
      </RouterLink>
    </nav>
  </header>
</template>
