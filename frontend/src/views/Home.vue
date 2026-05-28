<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-content">
        <h1>欢迎来到 蒙智云</h1>
        <p class="subtitle">内蒙古优质农畜产品 · AI智能推荐 · 产地直供</p>
        <div class="hero-buttons">
          <router-link to="/products">
            <el-button type="primary" size="large">浏览产品</el-button>
          </router-link>
          <router-link to="/chat">
            <el-button size="large">开始对话</el-button>
          </router-link>
        </div>
      </div>
      <div class="hero-image">
        <div class="placeholder-image">蒙智云</div>
      </div>
    </section>

    <section class="features-section">
      <h2>平台特性</h2>
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3>智能推荐</h3>
            <p>基于 AI 的智能推荐系统，为您推荐最适合的产品</p>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="feature-card">
            <div class="feature-icon">☁️</div>
            <h3>云端服务</h3>
            <p>全面的云端服务，随时随地访问您的数据</p>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>高效便捷</h3>
            <p>简洁的界面设计，让您轻松完成各种操作</p>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <h3>安全可靠</h3>
            <p>企业级安全保护，让您的数据更加安全</p>
          </div>
        </el-col>
      </el-row>
    </section>

    <section class="hot-products-section">
      <h2>热门产品</h2>
      <el-skeleton v-if="loading" :rows="1" animated />
      <el-row v-else :gutter="20">
        <el-col
          v-for="product in hotProducts"
          :key="product.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <ProductCard :product="product" />
        </el-col>
      </el-row>
      <div class="section-footer">
        <router-link to="/products">
          <el-button text>查看所有产品 →</el-button>
        </router-link>
      </div>
    </section>

    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好开始了吗？</h2>
        <p>加入数百万用户，体验智能云平台的魅力</p>
        <router-link to="/register">
          <el-button type="primary" size="large">立即注册</el-button>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useProductStore } from '@/stores/product'
import ProductCard from '@/components/ProductCard.vue'

const productStore = useProductStore()
const loading = ref(false)

const hotProducts = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    if (productStore.categories.length === 0) {
      await productStore.fetchCategories()
    }
    // 获取热门产品
    const products = await import('@/api/products').then((m) =>
      m.getPopularProducts(8)
    )
    hotProducts.value = products
  } catch (error) {
    console.error('Failed to load hot products:', error)
    ElMessage.error('加载热门商品失败，请稍后重试')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.home-page {
  max-width: 1400px;
  margin: 0 auto;

  .hero-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 40px;
    margin-bottom: 60px;
    padding: 40px $spacing-lg;
    background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
    border-radius: $radius-lg;
    color: white;

    .hero-content {
      flex: 1;

      h1 {
        font-size: 40px;
        font-weight: 700;
        margin: 0 0 $spacing-md 0;
        line-height: 1.2;
      }

      .subtitle {
        font-size: 18px;
        margin: 0 0 $spacing-xl 0;
        opacity: 0.9;
      }

      .hero-buttons {
        display: flex;
        gap: $spacing-md;

        a {
          text-decoration: none;
        }
      }
    }

    .hero-image {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 300px;

      .placeholder-image {
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.15);
        border-radius: $radius-md;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.8);
        letter-spacing: 4px;
        backdrop-filter: blur(4px);
      }
    }
  }

  .features-section {
    margin-bottom: 60px;

    h2 {
      font-size: 28px;
      font-weight: 600;
      text-align: center;
      margin-bottom: 40px;
      color: $color-text-primary;
    }

    .feature-card {
      padding: $spacing-lg;
      background: $color-bg-card;
      border-radius: $radius-md;
      text-align: center;
      transition: all 0.3s;
      border: 1px solid $color-border-light;

      &:hover {
        box-shadow: $shadow-lg;
        transform: translateY(-4px);
      }

      .feature-icon {
        font-size: 40px;
        margin-bottom: $spacing-md;
      }

      h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
        color: $color-text-primary;
      }

      p {
        color: $color-text-regular;
        font-size: 14px;
        margin: 0;
        line-height: 1.6;
      }
    }
  }

  .hot-products-section {
    margin-bottom: 60px;

    h2 {
      font-size: 28px;
      font-weight: 600;
      margin-bottom: $spacing-lg;
      color: $color-text-primary;
    }

    .section-footer {
      text-align: center;
      margin-top: $spacing-xl;
    }
  }

  .cta-section {
    padding: 60px 40px;
    background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
    border-radius: $radius-lg;
    color: white;
    text-align: center;

    h2 {
      font-size: 32px;
      font-weight: 600;
      margin-bottom: $spacing-md;
    }

    p {
      font-size: 18px;
      margin-bottom: $spacing-xl;
      opacity: 0.9;
    }
  }
}

@media (max-width: 768px) {
  .home-page {
    .hero-section {
      flex-direction: column;
      gap: 20px;
      padding: $spacing-lg $spacing-md;
      margin-bottom: 40px;

      .hero-content {
        h1 {
          font-size: 24px;
        }

        .subtitle {
          font-size: 14px;
        }

        .hero-buttons {
          flex-direction: column;

          :deep(.el-button) {
            width: 100%;
          }
        }
      }

      .hero-image {
        height: 200px;
      }
    }

    .features-section,
    .hot-products-section {
      margin-bottom: 40px;

      h2 {
        font-size: 20px;
        margin-bottom: $spacing-lg;
      }
    }

    .cta-section {
      padding: 40px 20px;

      h2 {
        font-size: 20px;
      }

      p {
        font-size: 14px;
      }
    }
  }
}
</style>
