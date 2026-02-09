<template>
  <div class="loading-container">
    <el-spin :spinning="true" size="large">
      <template #default>
        <div class="loading-content">
          <div class="spinner"></div>
          <p class="loading-text">{{ message }}</p>
        </div>
      </template>
    </el-spin>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
  fullscreen?: boolean
}

withDefaults(defineProps<Props>(), {
  message: '加载中...',
  fullscreen: false,
})
</script>

<style scoped lang="scss">
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 200px;

  .loading-content {
    text-align: center;

    .spinner {
      width: 50px;
      height: 50px;
      border: 4px solid #f3f3f3;
      border-top: 4px solid #409eff;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }

    .loading-text {
      color: #606266;
      font-size: 14px;
      margin: 0;
    }
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
