<template>
  <div class="advanced-filters">
    <el-card class="filter-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon class="icon"><Filter /></el-icon>
            高级筛选
          </span>
          <el-button text @click="handleToggleExpand">
            {{ isExpanded ? '收起' : '展开' }}
            <el-icon class="expand-icon" :class="{ expanded: isExpanded }">
              <ArrowDown />
            </el-icon>
          </el-button>
        </div>
      </template>

      <el-collapse-transition>
        <div v-show="isExpanded" class="filter-content">
          <el-form :model="filters" label-width="100px">
            <!-- 分类筛选 -->
            <el-form-item label="产品分类">
              <el-tree
                ref="treeRef"
                :data="categoryTree"
                :props="{ children: 'children', label: 'label' }"
                node-key="id"
                show-checkbox
                :check-on-click-node="true"
                :default-checked-keys="selectedCategories"
                @check="handleCategoryChange"
              />
            </el-form-item>

            <!-- 价格范围 -->
            <el-form-item label="价格范围">
              <div v-if="filters.priceRange" class="price-input-group">
                <el-input-number
                  v-model="filters.priceRange[0]"
                  :min="0"
                  :max="filters.priceRange[1]"
                  placeholder="最低价格"
                />
                <span class="separator">-</span>
                <el-input-number
                  v-model="filters.priceRange[1]"
                  :min="filters.priceRange[0]"
                  :max="10000"
                  placeholder="最高价格"
                />
              </div>
              <el-slider
                v-model="filters.priceRange"
                range
                :min="0"
                :max="10000"
                :step="50"
                :format-tooltip="formatPriceTooltip"
                style="margin-top: 12px"
              />
            </el-form-item>

            <!-- 产地筛选 -->
            <el-form-item label="产地">
              <el-select
                v-model="filters.regions"
                multiple
                clearable
                filterable
                placeholder="选择产地"
                style="width: 100%"
              >
                <el-option label="锡林郭勒盟" value="xilin" />
                <el-option label="呼伦贝尔市" value="hulun" />
                <el-option label="赤峰市" value="chifeng" />
                <el-option label="通辽市" value="tongliao" />
                <el-option label="乌兰察布市" value="wulanchabu" />
                <el-option label="包头市" value="baotou" />
                <el-option label="呼和浩特市" value="huhhot" />
              </el-select>
            </el-form-item>

            <!-- 文化标签 -->
            <el-form-item label="文化标签">
              <div class="tags-filter">
                <el-checkbox-group v-model="filters.culturalTags">
                  <el-checkbox
                    v-for="tag in culturalTags"
                    :key="tag.id"
                    :label="tag.id"
                    border
                  >
                    {{ tag.icon }} {{ tag.name }}
                  </el-checkbox>
                </el-checkbox-group>
              </div>
            </el-form-item>

            <!-- 认证标识 -->
            <el-form-item label="认证">
              <el-checkbox-group v-model="filters.certifications">
                <el-checkbox label="organic" border>🌿 有机认证</el-checkbox>
                <el-checkbox label="geo" border>🗺️ 地理标志</el-checkbox>
                <el-checkbox label="quality" border>⭐ 质量认证</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <!-- 排序方式 -->
            <el-form-item label="排序">
              <el-select v-model="filters.sortBy" style="width: 100%">
                <el-option label="综合推荐" value="recommend" />
                <el-option label="价格从低到高" value="price_asc" />
                <el-option label="价格从高到低" value="price_desc" />
                <el-option label="最新上架" value="newest" />
                <el-option label="销量最高" value="sales" />
              </el-select>
            </el-form-item>

            <!-- 操作按钮 -->
            <el-form-item>
              <el-button type="primary" @click="handleApplyFilters">
                <el-icon><Search /></el-icon>
                应用筛选
              </el-button>
              <el-button @click="handleResetFilters">
                <el-icon><RefreshRight /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-collapse-transition>

      <!-- 已选筛选条件标签 -->
      <div v-if="hasActiveFilters" class="active-filters">
        <span class="label">已选条件：</span>
        <el-tag
          v-for="(tag, index) in activeFilterTags"
          :key="index"
          closable
          @close="removeFilter(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
import { Filter, ArrowDown, Search, RefreshRight } from '@element-plus/icons-vue'
import type { AdvancedFilters, CulturalTag } from '@/types/product'

interface Props {
  modelValue: AdvancedFilters
  categories: any[]
  culturalTags?: CulturalTag[]
}

const props = withDefaults(defineProps<Props>(), {
  culturalTags: () => [
    { id: 'mongolian', name: '蒙古族', icon: '🐴' },
    { id: 'dairy', name: '乳文化', icon: '🥛' },
    { id: 'grassland', name: '草原', icon: '🌾' },
    { id: 'nomadic', name: '游牧文化', icon: '🏕️' },
    { id: 'traditional', name: '传统工艺', icon: '🎨' },
    { id: 'heritage', name: '非遗传承', icon: '👑' },
  ],
})

const emit = defineEmits<{
  'update:modelValue': [value: AdvancedFilters]
  apply: [filters: AdvancedFilters]
}>()

const isExpanded = ref(false)
const treeRef = ref()
const selectedCategories = ref<string[]>([])

const filters = reactive<AdvancedFilters>({
  category: [],
  priceRange: [0, 10000],
  regions: [],
  culturalTags: [],
  certifications: [],
  sortBy: 'recommend',
})

// 构建分类树
const categoryTree = computed(() => {
  const buildTree = (items: any[]): any[] => {
    return items.map((item) => ({
      id: item.id,
      label: item.name,
      children: item.children ? buildTree(item.children) : [],
    }))
  }
  return buildTree(props.categories)
})

// 已激活的筛选条件标签
const activeFilterTags = computed(() => {
  const tags: string[] = []

  if (filters.priceRange && (filters.priceRange[0] > 0 || filters.priceRange[1] < 10000)) {
    tags.push(`¥${filters.priceRange[0]} - ¥${filters.priceRange[1]}`)
  }

  if (filters.regions && filters.regions.length > 0) {
    tags.push(...filters.regions)
  }

  if (filters.culturalTags && filters.culturalTags.length > 0) {
    tags.push(...filters.culturalTags)
  }

  if (filters.certifications && filters.certifications.length > 0) {
    const certMap: Record<string, string> = {
      organic: '有机认证',
      geo: '地理标志',
      quality: '质量认证',
    }
    tags.push(...filters.certifications.map((c) => certMap[c] || c))
  }

  if (filters.sortBy && filters.sortBy !== 'recommend') {
    const sortMap: Record<string, string> = {
      price_asc: '价格低到高',
      price_desc: '价格高到低',
      newest: '最新上架',
      sales: '销量最高',
    }
    tags.push(sortMap[filters.sortBy] || filters.sortBy)
  }

  return tags
})

const hasActiveFilters = computed(() => activeFilterTags.value.length > 0)

const formatPriceTooltip = (val: number) => `¥${val}`

const handleCategoryChange = (_data: any, _checked: boolean, _node: any) => {
  if (treeRef.value) {
    selectedCategories.value = treeRef.value.getCheckedKeys() as string[]
    filters.category = selectedCategories.value
  }
}

const handleToggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleApplyFilters = () => {
  emit('update:modelValue', filters)
  emit('apply', filters)
}

const handleResetFilters = () => {
  filters.category = []
  filters.priceRange = [0, 10000]
  filters.regions = []
  filters.culturalTags = []
  filters.certifications = []
  filters.sortBy = 'recommend'
  selectedCategories.value = []
  if (treeRef.value) {
    treeRef.value.setCheckedKeys([])
  }
  emit('update:modelValue', filters)
  emit('apply', filters)
}

const removeFilter = (tag: string) => {
  // 根据标签类型移除对应的筛选条件
  if (tag.startsWith('¥')) {
    filters.priceRange = [0, 10000]
  } else if (filters.regions?.includes(tag)) {
    filters.regions = filters.regions.filter((r: string) => r !== tag)
  } else if (filters.culturalTags?.includes(tag)) {
    filters.culturalTags = filters.culturalTags.filter((c: string) => c !== tag)
  } else {
    const certMap: Record<string, string> = {
      '有机认证': 'organic',
      '地理标志': 'geo',
      '质量认证': 'quality',
    }
    const cert = certMap[tag]
    if (cert) {
      filters.certifications = filters.certifications?.filter((c: string) => c !== cert) || []
    }
  }
  emit('update:modelValue', filters)
}

// 监听外部模型值变化
watch(
  () => props.modelValue,
  (newVal) => {
    Object.assign(filters, newVal)
  },
  { deep: true }
)
</script>

<style scoped lang="scss">
.advanced-filters {
  margin-bottom: 24px;

  .filter-card {
    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid #ebeef5;
    }

    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 16px;
    }

    .expand-icon {
      transition: transform 0.3s;

      &.expanded {
        transform: rotate(180deg);
      }
    }
  }

  .filter-content {
    :deep(.el-form-item) {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    :deep(.el-form-item__label) {
      color: #333;
      font-weight: 500;
    }

    :deep(.el-tree) {
      background: transparent;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      padding: 8px;
    }

    .price-input-group {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;

      :deep(.el-input-number) {
        flex: 1;
      }

      .separator {
        color: #909399;
      }
    }

    .tags-filter {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      :deep(.el-checkbox) {
        margin: 4px;
      }
    }
  }

  .active-filters {
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;

    .label {
      font-weight: 500;
      color: #333;
      white-space: nowrap;
    }

    :deep(.el-tag) {
      margin: 4px 0;
    }
  }
}

@media (max-width: 768px) {
  .advanced-filters {
    .filter-card {
      :deep(.el-card__header) {
        padding: 12px 16px;
      }

      :deep(.el-card__body) {
        padding: 16px;
      }
    }

    .filter-content {
      :deep(.el-form-item__label) {
        width: 80px !important;
      }
    }
  }
}
</style>
