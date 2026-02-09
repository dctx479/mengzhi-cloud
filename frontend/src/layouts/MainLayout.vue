<template>
  <div class="main-layout">
    <Header />
    <div class="layout-content">
      <Sidebar />
      <main class="main-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/Header.vue'
import Sidebar from '@/components/Sidebar.vue'
</script>

<style scoped lang="scss">
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f7fa;

  .layout-content {
    display: flex;
    flex: 1;

    .main-area {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }
  }
}

@media (max-width: 768px) {
  .main-layout {
    .layout-content {
      flex-direction: column;

      .main-area {
        padding: 12px;
      }
    }
  }
}
</style>
