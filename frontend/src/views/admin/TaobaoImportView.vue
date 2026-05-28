<template>
  <div class="taobao-import-view">
    <div class="page-header">
      <h2>淘宝联盟商品导入</h2>
      <p class="subtitle">通过淘宝联盟开放平台批量导入商品数据，或实时搜索预览</p>
    </div>

    <!-- API 未配置 -->
    <el-alert
      v-if="statusLoaded && !apiConfigured"
      title="淘宝联盟 API 未配置"
      type="warning"
      description="请在后端 .env 文件中设置 TAOBAO_APP_KEY 和 TAOBAO_APP_SECRET，申请地址: https://open.taobao.com"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-else-if="statusLoaded && apiConfigured && !hasSession"
      :title="`AppKey 已配置 (${appKeyPrefix}) — 缺少 Session`"
      type="warning"
      description="淘宝联盟接口需要 OAuth2 授权后的 session 才能调用。请点击下方「淘宝授权」按钮完成授权。"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-else-if="statusLoaded && apiConfigured && sessionExpired"
      title="Session 已过期"
      type="error"
      description="淘宝 session 有效期仅 1 天。请点击「刷新 Session」或重新授权。"
      :closable="false"
      show-icon
      class="mb-4"
    />
    <el-alert
      v-else-if="statusLoaded && apiConfigured && hasSession"
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

    <!-- Session 配置卡片 -->
    <el-card v-if="statusLoaded && apiConfigured" shadow="never" class="mb-4">
      <template #header>
        <div class="card-header-row">
          <span>Session 配置</span>
          <el-tag v-if="hasSession && !sessionExpired" type="success" size="small">
            已授权（{{ sessionSource === 'db' ? '数据库' : '.env' }}）
          </el-tag>
          <el-tag v-else-if="sessionExpired" type="danger" size="small">已过期</el-tag>
          <el-tag v-else type="warning" size="small">未授权</el-tag>
        </div>
      </template>

      <!-- 当前 Session 信息 -->
      <div v-if="sessionMasked || sessionExpiresAt" class="token-info mb-4">
        <div v-if="sessionMasked" class="token-row">
          <span class="token-label">当前 Session：</span>
          <el-tag type="info">{{ sessionMasked }}</el-tag>
        </div>
        <div v-if="sessionExpiresAt" class="token-row mt-2">
          <span class="token-label">过期时间：</span>
          <el-tag :type="sessionExpired ? 'danger' : 'success'">{{ formatExpiry(sessionExpiresAt) }}</el-tag>
          <span class="token-hint">（淘宝 session 有效期 1 天，系统每 20 小时自动刷新）</span>
        </div>
        <div v-if="taobaoUserId" class="token-row mt-2">
          <span class="token-label">淘宝用户 ID：</span>
          <el-tag type="info">{{ taobaoUserId }}</el-tag>
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
          淘宝 OAuth2 授权
        </el-button>
        <el-button
          v-if="hasSession"
          :loading="refreshing"
          @click="handleRefreshSession"
        >
          刷新 Session
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
        description="请在后端 .env 中设置 TAOBAO_OAUTH_REDIRECT_URI=https://shushang.online/api/v1/taobao/oauth/callback，并在淘宝开放平台应用设置中填写该地址。"
      />

      <!-- 手动填入（备用） -->
      <el-collapse-transition>
        <div v-if="showManualInput" class="manual-input mt-4">
          <el-divider content-position="left">手动填入（备用）</el-divider>
          <el-form :model="sessionForm" label-width="120px" @submit.prevent="handleSaveSession">
            <el-form-item label="Session">
              <el-input
                v-model="sessionForm.value"
                type="password"
                show-password
                placeholder="粘贴淘宝联盟 OAuth2 Session"
                clearable
                style="width: 420px"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="savingSession"
                :disabled="!sessionForm.value.trim()"
                @click="handleSaveSession"
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
          <el-form :model="importForm" label-width="120px" @submit.prevent="handleImport">
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
              <span class="form-hint">每页 40 条，共最多 {{ importForm.max_pages * 40 }} 条</span>
            </el-form-item>
            <el-form-item label="推广位 ID">
              <el-input
                v-model="importForm.adzone_id"
                placeholder="可选，用于佣金追踪"
                clearable
                style="width: 240px"
              />
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
              placeholder="输入关键词搜索淘宝联盟商品"
              clearable
              style="width: 320px"
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
            <el-input
              v-model="searchAdzoneId"
              placeholder="推广位 ID（可选）"
              clearable
              style="width: 180px"
            />
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
                :key="item.tb_num_iid"
                class="goods-card"
              >
                <div class="goods-image">
                  <img :src="item.image || '/default-product.jpg'" :alt="item.name" />
                </div>
                <div class="goods-info">
                  <p class="goods-name" :title="item.name">{{ item.name }}</p>
                  <p class="goods-meta">
                    <el-tag size="small" type="info">{{ item.provcity || '未知地区' }}</el-tag>
                    <el-tag v-if="item.volume" size="small" type="success" class="ml-1">
                      月销 {{ item.volume }}
                    </el-tag>
                  </p>
                  <p class="goods-price">¥{{ item.price.toFixed(2) }}</p>
                  <p class="goods-shop">{{ item.shop_title }}</p>
                  <a
                    v-if="item.item_url"
                    :href="item.item_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="goods-link"
                  >
                    查看商品
                  </a>
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
  getTaobaoStatus, getTaobaoConfig, updateTaobaoSession,
  importFromTaobao, searchTaobaoItems, getTaobaoOAuthUrl, refreshTaobaoSession,
  type TaobaoItem,
} from '@/api/taobaoImport'

const activeTab = ref('import')
const statusLoaded = ref(false)
const apiConfigured = ref(false)
const hasSession = ref(false)
const sessionExpired = ref(false)
const sessionSource = ref<'db' | 'env' | null>(null)
const sessionMasked = ref<string | null>(null)
const sessionExpiresAt = ref<string | null>(null)
const taobaoUserId = ref<string | null>(null)
const appKeyPrefix = ref<string | null>(null)
const apiNote = ref<string | null>(null)
const hasRedirectUri = ref(false)
const showManualInput = ref(false)
const sessionForm = ref({ value: '' })
const savingSession = ref(false)
const authorizing = ref(false)
const refreshing = ref(false)
const importing = ref(false)
const importMessage = ref('')
const importForm = ref({ keyword: '', max_pages: 3, adzone_id: '' })
const searching = ref(false)
const searchDone = ref(false)
const searchKeyword = ref('')
const searchAdzoneId = ref('')
const searchResults = ref<TaobaoItem[]>([])
const searchWarning = ref<string | null>(null)
const searchError = ref<string | null>(null)
const searchTotal = ref(0)
const searchPage = ref(1)
const searchPageSize = 20

const formatExpiry = (iso: string) => {
  try { return new Date(iso).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }) }
  catch { return iso }
}

const loadStatus = async () => {
  try {
    const s = await getTaobaoStatus()
    apiConfigured.value = s.configured
    hasSession.value = s.has_session
    sessionExpired.value = s.session_expired ?? false
    sessionSource.value = s.session_source
    appKeyPrefix.value = s.app_key_prefix
    apiNote.value = s.note ?? null
    hasRedirectUri.value = s.has_redirect_uri ?? false
    if (s.configured) {
      const cfg = await getTaobaoConfig()
      sessionMasked.value = cfg.session_masked
      sessionExpiresAt.value = cfg.expires_at
      taobaoUserId.value = cfg.taobao_user_id
    }
  } catch { /* silent */ } finally { statusLoaded.value = true }
}

const onOAuthMessage = (event: MessageEvent) => {
  if (event.data?.type === 'taobao_oauth_success') { ElMessage.success('淘宝授权成功，正在刷新状态...'); loadStatus() }
  else if (event.data?.type === 'taobao_oauth_error') { ElMessage.error('淘宝授权失败，请重试') }
}

onMounted(() => { loadStatus(); window.addEventListener('message', onOAuthMessage) })
onUnmounted(() => { window.removeEventListener('message', onOAuthMessage) })

const handleOAuthAuthorize = async () => {
  authorizing.value = true
  try {
    const { auth_url } = await getTaobaoOAuthUrl()
    window.open(auth_url, 'taobao_oauth', 'width=900,height=650,scrollbars=yes')
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || e?.message || '获取授权链接失败') }
  finally { authorizing.value = false }
}

const handleRefreshSession = async () => {
  refreshing.value = true
  try {
    const res = await refreshTaobaoSession()
    ElMessage.success('Session 刷新成功，新过期时间: ' + formatExpiry(res.expires_at))
    await loadStatus()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || e?.message || 'Session 刷新失败') }
  finally { refreshing.value = false }
}

const handleSaveSession = async () => {
  const session = sessionForm.value.value.trim()
  if (!session) return
  savingSession.value = true
  try {
    await updateTaobaoSession(session)
    ElMessage.success('Session 已保存，正在刷新状态...')
    sessionForm.value.value = ''; showManualInput.value = false
    await loadStatus()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败') }
  finally { savingSession.value = false }
}

const handleImport = async () => {
  if (!importForm.value.keyword.trim()) { ElMessage.warning('请输入搜索关键词'); return }
  importing.value = true; importMessage.value = ''
  try {
    const res = await importFromTaobao({
      keyword: importForm.value.keyword.trim(),
      max_pages: importForm.value.max_pages,
      page_size: 40,
      adzone_id: importForm.value.adzone_id.trim() || undefined,
    })
    importMessage.value = '导入任务已提交：「' + res.keyword + '」，正在后台处理，请稍后刷新产品列表查看结果'
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || e?.message || '提交导入任务失败') }
  finally { importing.value = false }
}

const handleSearch = async (page = searchPage.value) => {
  if (!searchKeyword.value.trim()) { ElMessage.warning('请输入搜索关键词'); return }
  searching.value = true; searchDone.value = false; searchError.value = null; searchPage.value = page
  try {
    const res = await searchTaobaoItems(
      searchKeyword.value.trim(), page, searchPageSize,
      searchAdzoneId.value.trim() || undefined,
    )
    searchResults.value = res.items; searchTotal.value = res.total; searchWarning.value = res.warning ?? null
  } catch (e: any) {
    searchError.value = e?.response?.data?.detail || e?.message || '搜索失败'
    searchResults.value = []; searchTotal.value = 0
  } finally { searching.value = false; searchDone.value = true }
}
</script>

<style scoped lang="scss">
.taobao-import-view {
  padding: 20px;
  .page-header { margin-bottom: 20px; h2 { margin: 0 0 6px; font-size: 22px; font-weight: 600; } .subtitle { margin: 0; font-size: 14px; color: #909399; } }
  .mb-4 { margin-bottom: 16px; } .mt-4 { margin-top: 16px; } .mt-3 { margin-top: 12px; } .mt-2 { margin-top: 8px; } .ml-1 { margin-left: 4px; } .ml-2 { margin-left: 8px; }
  .card-header-row { display: flex; align-items: center; gap: 10px; }
  .token-info { .token-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; } .token-label { font-size: 13px; color: #606266; white-space: nowrap; } .token-hint { font-size: 12px; color: #909399; } }
  .oauth-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .manual-input { background: #fafafa; border-radius: 6px; padding: 16px; }
  .form-hint { margin-left: 10px; font-size: 12px; color: #909399; }
  .search-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
  .goods-card {
    border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; transition: box-shadow 0.2s;
    &:hover { box-shadow: 0 2px 12px rgba(0,0,0,.1); }
    .goods-image { width: 100%; aspect-ratio: 1; background: #f5f5f5; overflow: hidden; img { width: 100%; height: 100%; object-fit: cover; } }
    .goods-info {
      padding: 10px;
      .goods-name { margin: 0 0 6px; font-size: 13px; font-weight: 500; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .goods-meta { margin: 0 0 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
      .goods-price { margin: 0 0 4px; font-size: 16px; font-weight: 600; color: #e74c3c; }
      .goods-shop { margin: 0 0 6px; font-size: 11px; color: #c0c4cc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .goods-link { font-size: 12px; color: #ff6600; text-decoration: none; &:hover { text-decoration: underline; } }
    }
  }
  .pagination-container { display: flex; justify-content: center; }
}
</style>
