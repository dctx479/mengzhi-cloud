<template>
  <div class="users-view">
    <el-card>
      <template #header>
        <div class="header">
          <span>用户管理</span>
          <el-input
            v-model="search"
            placeholder="搜索用户"
            style="width: 200px"
            clearable
            @input="onSearchInput"
            @clear="onSearchInput"
          />
        </div>
      </template>

      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag
              :type="row.role === 'admin' ? 'danger' : row.role === 'enterprise_admin' ? '' : 'info'"
              size="small"
            >
              {{ row.role === 'admin' ? '系统管理员' : row.role === 'enterprise_admin' ? '企业管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-popconfirm
              title="确认删除该用户？此操作不可恢复。"
              confirm-button-text="确认删除"
              cancel-button-text="取消"
              @confirm="deleteUser(row.id)"
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
        @change="loadUsers"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="系统管理员" value="admin" />
            <el-option label="企业管理员" value="enterprise_admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
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
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import type { User } from '@/types/admin'

const users = ref<User[]>([])
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const dialogVisible = ref(false)
const editForm = ref<Partial<User>>({})
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null

const onSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadUsers()
  }, 300)
}

const loadUsers = async () => {
  loading.value = true
  try {
    const result = await adminApi.getUsers({
      search: search.value,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    users.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const editUser = (user: User) => {
  editForm.value = { ...user }
  dialogVisible.value = true
}

const saveUser = async () => {
  saving.value = true
  try {
    await adminApi.updateUser(editForm.value.id!, editForm.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
  } finally {
    saving.value = false
  }
}

const deleteUser = async (id: number) => {
  try {
    await adminApi.deleteUser(id)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.users-view {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
