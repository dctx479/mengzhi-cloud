<template>
  <div class="enterprises-view">
    <el-card>
      <template #header>
        <div class="header">
          <span>企业管理</span>
          <el-input v-model="search" placeholder="搜索企业" style="width: 200px" @input="loadEnterprises" clearable />
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
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editEnterprise(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteEnterprise(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
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
        <el-button type="primary" @click="saveEnterprise">保存</el-button>
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
const search = ref('')
const dialogVisible = ref(false)
const editForm = ref<Partial<Enterprise>>({})

const loadEnterprises = async () => {
  loading.value = true
  try {
    const enterprises_data = await adminApi.getEnterprises({ search: search.value })
    enterprises.value = enterprises_data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const editEnterprise = (enterprise: Enterprise) => {
  editForm.value = { ...enterprise }
  dialogVisible.value = true
}

const saveEnterprise = async () => {
  try {
    await adminApi.updateEnterprise(editForm.value.id!, editForm.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadEnterprises()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteEnterprise = async (id: number) => {
  try {
    await adminApi.deleteEnterprise(id)
    ElMessage.success('删除成功')
    loadEnterprises()
  } catch (error) {
    ElMessage.error('删除失败')
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
