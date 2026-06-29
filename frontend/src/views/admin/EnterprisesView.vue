<template>
  <div class="enterprises-view">
    <el-card>
      <template #header>
        <div class="header">
          <span>企业管理</span>
          <div style="display: flex; gap: 12px; align-items: center">
            <el-input
              v-model="search"
              placeholder="搜索企业"
              style="width: 200px"
              clearable
              @input="onSearchInput"
              @clear="onSearchInput"
            />
            <el-button type="primary" @click="openCreateDialog">新增企业</el-button>
          </div>
        </div>
      </template>

      <el-table :data="enterprises" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="企业名称" />
        <el-table-column prop="contact_name" label="联系人" />
        <el-table-column prop="contact_email" label="邮箱" />
        <el-table-column prop="verify_status" label="认证状态">
          <template #default="{ row }">
            <el-tag :type="row.verify_status === 'verified' ? 'success' : row.verify_status === 'rejected' ? 'danger' : 'warning'">
              {{ row.verify_status === 'verified' ? '已认证' : row.verify_status === 'rejected' ? '已拒绝' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="plan_type" label="套餐" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ planLabels[row.plan_type] || row.plan_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editEnterprise(row)">编辑</el-button>
            <el-popconfirm
              title="确认删除该企业？此操作不可恢复。"
              confirm-button-text="确认删除"
              cancel-button-text="取消"
              @confirm="deleteEnterprise(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; display: flex; justify-content: flex-end"
        @change="loadEnterprises"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑企业' : '新增企业'" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="企业名称" required>
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item v-if="!isEditing" label="营业执照号" required>
          <el-input v-model="editForm.license_no" placeholder="如 91150100..." />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.contact_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.contact_email" />
        </el-form-item>
        <el-form-item label="认证状态" v-if="isEditing">
          <el-select v-model="editForm.verify_status">
            <el-option label="待审核" value="pending" />
            <el-option label="已认证" value="verified" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐" v-if="isEditing">
          <el-select v-model="editForm.plan_type">
            <el-option label="免费版" value="free" />
            <el-option label="基础版" value="basic" />
            <el-option label="专业版" value="pro" />
            <el-option label="企业版" value="enterprise" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEnterprise">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import type { Enterprise } from '@/types/admin'

const planLabels: Record<string, string> = {
  free: '免费版',
  basic: '基础版',
  pro: '专业版',
  enterprise: '企业版',
}

const enterprises = ref<Enterprise[]>([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const dialogVisible = ref(false)
const editForm = ref<Record<string, unknown>>({})
const isEditing = computed(() => Boolean(editForm.value.id))
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null

const onSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadEnterprises()
  }, 300)
}

const loadEnterprises = async () => {
  loading.value = true
  try {
    const result = await adminApi.getEnterprises({
      search: search.value,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    enterprises.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载企业列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editForm.value = {}
  dialogVisible.value = true
}

const editEnterprise = (enterprise: Enterprise) => {
  editForm.value = { ...enterprise } as Record<string, unknown>
  dialogVisible.value = true
}

const saveEnterprise = async () => {
  saving.value = true
  try {
    if (isEditing.value) {
      await adminApi.updateEnterprise(editForm.value.id as number, editForm.value as Partial<Enterprise>)
      ElMessage.success('保存成功')
    } else {
      if (!editForm.value.name || !editForm.value.license_no) {
        ElMessage.warning('企业名称和营业执照号为必填项')
        saving.value = false
        return
      }
      await adminApi.createEnterprise(editForm.value as Partial<Enterprise>)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadEnterprises()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '操作失败')
  } finally {
    saving.value = false
  }
}

const deleteEnterprise = async (id: number) => {
  try {
    await adminApi.deleteEnterprise(id)
    ElMessage.success('删除成功')
    await loadEnterprises()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

onMounted(loadEnterprises)
</script>

<style scoped>
.enterprises-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
