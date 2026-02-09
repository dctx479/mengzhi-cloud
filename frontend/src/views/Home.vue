<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-content">
        <h1>欢迎来到 AI赋能云平台</h1>
        <p class="subtitle">智能推荐 · 云端服务 · 高效便捷</p>
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
        <div class="placeholder-image">AI平台</div>
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
    padding: 40px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;

    .hero-content {
      flex: 1;

      h1 {
        font-size: 40px;
        font-weight: 700;
        margin: 0 0 16px 0;
        line-height: 1.2;
      }

      .subtitle {
        font-size: 18px;
        margin: 0 0 32px 0;
        opacity: 0.9;
      }

      .hero-buttons {
        display: flex;
        gap: 16px;

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
        background: rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: rgba(255, 255, 255, 0.8);
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
    }

    .feature-card {
      padding: 24px;
      background: white;
      border-radius: 8px;
      text-align: center;
      transition: all 0.3s;
      border: 1px solid #f0f0f0;

      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transform: translateY(-4px);
      }

      .feature-icon {
        font-size: 40px;
        margin-bottom: 16px;
      }

      h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
      }

      p {
        color: #666;
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
      margin-bottom: 24px;
    }

    .section-footer {
      text-align: center;
      margin-top: 32px;
    }
  }

  .cta-section {
    padding: 60px 40px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;
    text-align: center;

    h2 {
      font-size: 32px;
      font-weight: 600;
      margin-bottom: 16px;
    }

    p {
      font-size: 18px;
      margin-bottom: 32px;
      opacity: 0.9;
    }
  }
}

@media (max-width: 768px) {
  .home-page {
    .hero-section {
      flex-direction: column;
      gap: 20px;
      padding: 24px 12px;
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
        margin-bottom: 24px;
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
