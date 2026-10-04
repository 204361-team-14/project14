import { createRouter, createWebHistory } from 'vue-router'

import HomeView from './views/HomeView.vue'
import LostFoundView from './views/LostFoundView.vue'
import LostFoundDetailView from './views/LostFoundDetailView.vue'
import ServiceRequestView from './views/ServiceRequestView.vue'
import StaffDashboardView from './views/StaffDashboardView.vue'
import StaffRequestsView from './views/StaffRequestsView.vue'
import StaffRequestDetailView from './views/StaffRequestDetailView.vue'
import StaffLostFoundView from './views/StaffLostFoundView.vue'
import StaffLostFoundDetailView from './views/StaffLostFoundDetailView.vue'
import StaffRoomsView from './views/StaffRoomsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/request/repair',
      name: 'request-repair',
      component: ServiceRequestView,
      meta: { serviceType: 'แจ้งซ่อม' }
    },
    {
      path: '/request/cleaning',
      name: 'request-cleaning',
      component: ServiceRequestView,
      meta: { serviceType: 'แจ้งทำความสะอาด' }
    },
    { path: '/lost-found', name: 'lost-found', component: LostFoundView },
    { path: '/lost-found/:id', name: 'lost-found-detail', component: LostFoundDetailView },
    { path: '/staff', redirect: '/staff/dashboard' },
    { path: '/staff/dashboard', name: 'staff-dashboard', component: StaffDashboardView },
    { path: '/staff/requests', name: 'staff-requests', component: StaffRequestsView },
    { path: '/staff/requests/:id', name: 'staff-request-detail', component: StaffRequestDetailView },
    { path: '/staff/lost-found', name: 'staff-lost-found', component: StaffLostFoundView },
    { path: '/staff/lost-found/:id', name: 'staff-lost-found-detail', component: StaffLostFoundDetailView },
    { path: '/staff/rooms', name: 'staff-rooms', component: StaffRoomsView }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
