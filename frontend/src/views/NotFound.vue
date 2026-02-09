<template>
  <div class="not-found-page">
    <div class="not-found-container">
      <div class="error-code">404</div>
      <h1 class="error-title">页面不存在</h1>
      <p class="error-description">抱歉，您访问的页面不存在或已删除</p>
      <router-link to="/">
        <el-button type="primary" size="large">返回首页</el-button>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
// 404 页面组件
</script>

<style scoped lang="scss">
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .not-found-container {
    text-align: center;
    color: white;

    .error-code {
      font-size: 120px;
      font-weight: 700;
      margin-bottom: 24px;
      opacity: 0.8;
    }

    .error-title {
      font-size: 32px;
      font-weight: 600;
      margin-bottom: 16px;
    }

    .error-description {
      font-size: 18px;
      margin-bottom: 32px;
      opacity: 0.9;
    }
  }
}
</style>
