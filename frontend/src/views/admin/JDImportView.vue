<template>
  <div class="jd-import-view">
    <div class="page-header">
      <h2>京东联盟商品导入</h2>
      <p class="subtitle">批量导入京东商品数据，或实时搜索预览</p>
    </div>

    <!-- API 配置状态 -->
    <el-alert
      v-if="statusLoaded && !apiConfigured"
      title="京东联盟 API 未配置"
      type="warning"
      description="请在后端 .env 文件中设置 JD_APP_KEY 和 JD_SECRET_KEY，申请地址: https://union.jd.com"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-else-if="statusLoaded && apiConfigured && !hasAccessToken"
      :title="`AppKey 已配置 (${appKeyPrefix}) — 缺少 AccessToken`"
      type="warning"
      description="京东联盟接口需要 access_token 才能调用。请在下方填入 AccessToken。"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-else-if="statusLoaded && apiConfigured && hasAccessToken"
      :title="`API 已就绪 (AppKey: ${appKeyPrefix})`"
      type="success"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-if="statusLoaded && apiConfigured && apiNote"
      title="权限说明"
      type="info"
      :description="apiNote"
      :closable="false"
      show-icon
      class="mb-4"
    />

    <!-- AccessToken 配置卡片 -->
    <el-card v-if="statusLoaded && apiConfigured" shadow="never" class="mb-4">
      <template #header>
        <div class="card-header-row">
          <span>AccessToken 配置</span>
          <el-tag v-if="hasAccessToken" type="success" size="small">
            已配置（{{ tokenSource === 'db' ? '数据库' : '.env' }}）
          </el-tag>
          <el-tag v-else-if="tokenExpired" type="danger" size="small">已过期</el-tag>
          <el-tag v-else type="warning" size="small">未配置</el-tag>
        </div>
      </template>

      <!-- 当前 Token 信息 -->
      <div v-if="tokenMasked || tokenExpiresAt" class="token-info mb-4">
        <div v-if="tokenMasked" class="token-row">
          <span class="token-label">当前 Token：</span>
          <el-tag type="info">{{ tokenMasked }}</el-tag>
        </div>
        <div v-if="tokenExpiresAt" class="token-row mt-2">
          <span class="token-label">过期时间：</span>
          <el-tag :type="tokenExpired ? 'danger' : 'success'">{{ formatExpiry(tokenExpiresAt) }}</el-tag>
        </div>
      </div>

      <!-- OAuth2 授权区域 -->
      <div class="oauth-actions">
        <el-button
          type="primary"
          :loading="authorizing"
          :disabled="!hasRedirectUri"
          @click="handleOAuthAuthorize"
        >
          京东 OAuth2 授权
        </el-button>
        <el-button
          v-if="hasAccessToken"
          :loading="refreshing"
          @click="handleRefreshToken"
        >
          刷新 Token
        </el-button>
        <el-button link @click="showManualInput = !showManualInput">
          {{ showManualInput ? '收起' : '手动填入（备用）' }}
        </el-button>
      </div>

      <el-alert
        v-if="!hasRedirectUri"
        type="warning"
        :closable="false"
        show-icon
        class="mt-3"
        title="OAuth2 回调地址未配置"
        description="请在后端 .env 中设置 JD_OAUTH_REDIRECT_URI，例如: http://yourdomain.com/api/v1/jd/oauth/callback"
      />

      <!-- 手动填入（备用） -->
      <el-collapse-transition>
        <div v-if="showManualInput" class="manual-input mt-4">
          <el-divider content-position="left">手动填入（备用）</el-divider>
          <el-form :model="tokenForm" label-width="120px" @submit.prevent="handleSaveToken">
            <el-form-item label="AccessToken">
              <el-input
                v-model="tokenForm.value"
                type="password"
                show-password
                placeholder="粘贴 AccessToken"
                clearable
                style="width: 420px"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="savingToken"
                :disabled="!tokenForm.value.trim()"
                @click="handleSaveToken"
              >
                保存
              </el-button>
              <span class="form-hint ml-2">保存后立即生效，无需重启服务</span>
            </el-form-item>
          </el-form>
        </div>
      </el-collapse-transition>
    </el-card>

    <el-tabs v-model="activeTab">
      <!-- 批量导入 -->
      <el-tab-pane label="批量导入" name="import">
        <el-card shadow="never" class="mt-4">
          <el-form :model="importForm" label-width="100px" @submit.prevent="handleImport">
            <el-form-item label="搜索关键词" required>
              <el-input
                v-model="importForm.keyword"
                placeholder="例如：内蒙古牛肉、草原奶酪"
                clearable
                style="width: 360px"
              />
            </el-form-item>
            <el-form-item label="最多拉取页数">
              <el-input-number
                v-model="importForm.max_pages"
                :min="1"
                :max="10"
                controls-position="right"
              />
              <span class="form-hint">每页 30 条，共最多 {{ importForm.max_pages * 30 }} 条</span>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="importing"
                :disabled="!apiConfigured || !importForm.keyword.trim()"
                @click="handleImport"
              >
                开始导入
              </el-button>
              <span class="form-hint ml-2">任务在后台执行，不会阻塞页面</span>
            </el-form-item>
          </el-form>

          <el-alert
            v-if="importMessage"
            :title="importMessage"
            type="success"
            show-icon
            :closable="false"
            class="mt-4"
          />
        </el-card>
      </el-tab-pane>

      <!-- 实时搜索预览 -->
      <el-tab-pane label="实时搜索预览" name="search">
        <el-card shadow="never" class="mt-4">
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="输入关键词搜索京东商品"
              clearable
              style="width: 360px"
              @keyup.enter="handleSearch(1)"
            >
              <template #append>
                <el-button
                  :loading="searching"
                  :disabled="!apiConfigured"
                  @click="handleSearch(1)"
                >
                  搜索
                </el-button>
              </template>
            </el-input>
          </div>

          <el-skeleton v-if="searching" :rows="4" animated class="mt-4" />

          <template v-else-if="searchDone">
            <el-alert
              v-if="searchError"
              :title="searchError"
              type="error"
              show-icon
              :closable="false"
              class="mt-4"
            />

            <el-alert
              v-if="searchWarning"
              :title="searchWarning"
              type="warning"
              show-icon
              :closable="true"
              class="mt-4"
            />

            <div v-if="searchResults.length > 0" class="results-grid mt-4">
              <div
                v-for="item in searchResults"
                :key="item.jd_sku_id"
                class="goods-card"
              >
                <div class="goods-image">
                  <img :src="item.image || '/default-product.jpg'" :alt="item.name" />
                </div>
                <div class="goods-info">
                  <p class="goods-name" :title="item.name">{{ item.name }}</p>
                  <p class="goods-category">{{ item.category }}{{ item.sub_category ? ' / ' + item.sub_category : '' }}</p>
                  <p class="goods-price">¥{{ item.price.toFixed(2) }}</p>
                  <p class="goods-shop">{{ item.shop_name }}</p>
                </div>
              </div>
            </div>

            <el-empty v-else-if="!searchError" description="未找到相关商品" class="mt-4" />
          </template>

          <div v-if="searchTotal > 0" class="pagination-container mt-4">
            <el-pagination
              v-model:current-page="searchPage"
              :page-size="searchPageSize"
              :total="searchTotal"
              layout="total, prev, pager, next"
              @current-change="handleSearch"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getJdStatus, getJdConfig, updateJdAccessToken, importFromJd, searchJdGoods,
  getJdOAuthUrl, refreshJdToken,
  type JdGoodsItem,
} from '@/api/jdImport'

const activeTab = ref('import')

// API 状态
const statusLoaded = ref(false)
const apiConfigured = ref(false)
const hasAccessToken = ref(false)
const tokenExpired = ref(false)
const tokenSource = ref<'db' | 'env' | null>(null)
const tokenMasked = ref<string | null>(null)
const tokenExpiresAt = ref<string | null>(null)
const appKeyPrefix = ref<string | null>(null)
const apiNote = ref<string | null>(null)
const hasRedirectUri = ref(false)

// AccessToken 配置
const showManualInput = ref(false)
const tokenForm = ref({ value: '' })
const savingToken = ref(false)
const authorizing = ref(false)
const refreshing = ref(false)

// 批量导入
const importing = ref(false)
const importMessage = ref('')
const importForm = ref({ keyword: '', max_pages: 3 })

// 实时搜索
const searching = ref(false)
const searchDone = ref(false)
const searchKeyword = ref('')
const searchResults = ref<JdGoodsItem[]>([])
const searchWarning = ref<string | null>(null)
const searchError = ref<string | null>(null)
const searchTotal = ref(0)
const searchPage = ref(1)
const searchPageSize = 20

const formatExpiry = (iso: string) => {
  try {
    return new Date(iso).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
  } catch {
    return iso
  }
}

const loadStatus = async () => {
  try {
    const status = await getJdStatus()
    apiConfigured.value = status.configured
    hasAccessToken.value = status.has_access_token
    tokenExpired.value = status.token_expired ?? false
    tokenSource.value = status.token_source
    appKeyPrefix.value = status.app_key_prefix
    apiNote.value = status.note ?? null
    hasRedirectUri.value = status.has_redirect_uri ?? false
    if (status.configured) {
      const cfg = await getJdConfig()
      tokenMasked.value = cfg.token_masked
      tokenExpiresAt.value = cfg.expires_at
    }
  } catch {
    // 非管理员或网络错误，静默处理
  } finally {
    statusLoaded.value = true
  }
}

onMounted(() => {
  loadStatus()
  window.addEventListener('message', onOAuthMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', onOAuthMessage)
})

const onOAuthMessage = (event: MessageEvent) => {
  if (event.data?.type === 'jd_oauth_success') {
    ElMessage.success('京东授权成功，正在刷新状态...')
    loadStatus()
  } else if (event.data?.type === 'jd_oauth_error') {
    ElMessage.error('京东授权失败，请重试')
  }
}

const handleOAuthAuthorize = async () => {
  authorizing.value = true
  try {
    const { auth_url } = await getJdOAuthUrl()
    window.open(auth_url, 'jd_oauth', 'width=900,height=650,scrollbars=yes')
  } catch (error: any) {
    ElMessage.error(error?.message || '获取授权链接失败')
  } finally {
    authorizing.value = false
  }
}

const handleRefreshToken = async () => {
  refreshing.value = true
  try {
    const res = await refreshJdToken()
    ElMessage.success(`Token 刷新成功，新过期时间: ${formatExpiry(res.expires_at)}`)
    await loadStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || 'Token 刷新失败')
  } finally {
    refreshing.value = false
  }
}

const handleSaveToken = async () => {
  const token = tokenForm.value.value.trim()
  if (!token) return
  savingToken.value = true
  try {
    await updateJdAccessToken(token)
    ElMessage.success('AccessToken 已保存，正在刷新状态...')
    tokenForm.value.value = ''
    showManualInput.value = false
    await loadStatus()
  } catch (error: any) {
    ElMessage.error(error?.message || '保存失败')
  } finally {
    savingToken.value = false
  }
}

const handleImport = async () => {
  if (!importForm.value.keyword.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  importing.value = true
  importMessage.value = ''
  try {
    const res = await importFromJd({
      keyword: importForm.value.keyword.trim(),
      max_pages: importForm.value.max_pages,
      page_size: 30,
    })
    importMessage.value = `导入任务已提交：「${res.keyword}」，正在后台处理，请稍后刷新产品列表查看结果`
  } catch (error: any) {
    ElMessage.error(error?.message || '提交导入任务失败')
  } finally {
    importing.value = false
  }
}

const handleSearch = async (page = searchPage.value) => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  searching.value = true
  searchDone.value = false
  searchError.value = null
  searchPage.value = page
  try {
    const res = await searchJdGoods(searchKeyword.value.trim(), page, searchPageSize)
    searchResults.value = res.items
    searchTotal.value = res.total
    searchWarning.value = res.warning ?? null
  } catch (error: any) {
    const detail = error?.response?.data?.detail || error?.message || '搜索失败'
    searchError.value = detail
    searchResults.value = []
    searchTotal.value = 0
  } finally {
    searching.value = false
    searchDone.value = true
  }
}
</script>

<style scoped lang="scss">
.jd-import-view {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;
    h2 { margin: 0 0 6px; font-size: 22px; font-weight: 600; }
    .subtitle { margin: 0; font-size: 14px; color: #909399; }
  }

  .mb-4 { margin-bottom: 16px; }
  .mt-4 { margin-top: 16px; }
  .ml-2 { margin-left: 8px; }

  .card-header-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .token-current {
    display: flex;
    align-items: center;
    gap: 8px;
    .token-label { font-size: 13px; color: #606266; }
  }

  .token-info {
    .token-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .token-label { font-size: 13px; color: #606266; }
  }

  .oauth-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .manual-input {
    background: #fafafa;
    border-radius: 6px;
    padding: 16px;
  }

  .mt-2 { margin-top: 8px; }
  .mt-3 { margin-top: 12px; }

  .form-hint {
    margin-left: 10px;
    font-size: 12px;
    color: #909399;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }

  .goods-card {
    border: 1px solid #ebeef5;
    border-radius: 8px;
    overflow: hidden;
    transition: box-shadow 0.2s;

    &:hover { box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); }

    .goods-image {
      width: 100%;
      aspect-ratio: 1;
      background: #f5f5f5;
      overflow: hidden;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .goods-info {
      padding: 10px;

      .goods-name {
        margin: 0 0 4px;
        font-size: 13px;
        font-weight: 500;
        color: #333;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .goods-category {
        margin: 0 0 4px;
        font-size: 11px;
        color: #909399;
      }

      .goods-price {
        margin: 0 0 4px;
        font-size: 16px;
        font-weight: 600;
        color: #e74c3c;
      }

      .goods-shop {
        margin: 0;
        font-size: 11px;
        color: #c0c4cc;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
  }
}
</style>
