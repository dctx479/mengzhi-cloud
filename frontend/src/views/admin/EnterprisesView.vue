<template>
  <div class="enterprises-view">
    <el-card>
      <template #header>
        <div class="header">
          <span>企业管理</span>
          <el-input
            v-model="search"
            placeholder="搜索企业"
            style="width: 200px"
            clearable
            @input="onSearchInput"
            @clear="onSearchInput"
          />
        </div>
      </template>

      <el-table :data="enterprises" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="企业名称" />
        <el-table-column prop="contactPerson" label="联系人" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" />
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

    <el-dialog v-model="dialogVisible" title="编辑企业" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="企业名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.contactPerson" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="激活" value="active" />
            <el-option label="禁用" value="inactive" />
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
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import type { Enterprise } from '@/types/admin'

const enterprises = ref<Enterprise[]>([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const dialogVisible = ref(false)
const editForm = ref<Partial<Enterprise>>({})
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

const editEnterprise = (enterprise: Enterprise) => {
  editForm.value = { ...enterprise }
  dialogVisible.value = true
}

const saveEnterprise = async () => {
  saving.value = true
  try {
    await adminApi.updateEnterprise(editForm.value.id!, editForm.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadEnterprises()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
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
