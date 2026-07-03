<template>
  <div class="conversion-page">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="conversion-header">
        <div>
          <h1>AI文档转换</h1>
          <p>将 PDF、Word、图片或 Markdown 转换为结构化文档、PPT 大纲与知识库素材。</p>
        </div>
      </section>

      <section class="conversion-layout">
        <div class="fa-card converter-card">
          <div class="card-title">
            <div>
              <h2>转换任务</h2>
              <p>选择源文件后，AI 会自动清理版式并输出目标格式内容。</p>
            </div>
            <FaSvgIcon icon="ri:file-transfer-line" />
          </div>

          <input
            ref="fileInputRef"
            class="hidden-file-input"
            type="file"
            accept=".pdf,.doc,.docx,.xlsx,.ppt,.pptx,.md,.markdown,.csv,.png,.jpg,.jpeg,.txt"
            @change="handleFileChange"
          />

          <div
            v-if="!selectedFile"
            class="upload-stage"
            @click="openFilePicker"
            @dragover.prevent
            @drop.prevent="handleFileDrop"
          >
            <div class="upload-stage__icon">
              <FaSvgIcon icon="ri:file-upload-line" />
            </div>
            <div class="upload-stage__title">选择或拖入需要转换的文档</div>
            <p class="upload-stage__desc">支持 pdf、docx、xlsx、pptx、md、png、jpg、txt。</p>
          </div>

          <div v-else class="conversion-workbench">
            <div class="file-flow">
              <div class="selected-file-card">
                <div class="selected-file-card__meta">
                  <FaSvgIcon icon="ri:file-text-line" />
                  <span>{{ selectedFile.name }}</span>
                </div>
                <button type="button" class="file-action-button" @click="clearSelectedFile">
                  <FaSvgIcon icon="ri:delete-bin-line" />
                </button>
              </div>

              <div class="flow-arrow">
                <FaSvgIcon icon="ri:arrow-right-line" />
              </div>

              <div class="target-badge">
                {{ form.target }}
              </div>
            </div>

            <div class="target-grid">
              <button
                v-for="item in formats"
                :key="item"
                type="button"
                class="target-chip"
                :class="{ 'is-active': form.target === item }"
                @click="form.target = item"
              >
                {{ item }}
              </button>
            </div>

            <div class="action-row">
              <ElButton class="action-row__secondary" @click="openFilePicker">
                <FaSvgIcon icon="ri:refresh-line" />
                更换文件
              </ElButton>
              <ElButton type="primary" class="action-row__primary" @click="createConversion">
                转换
                <FaSvgIcon icon="ri:arrow-right-line" />
              </ElButton>
            </div>
          </div>
        </div>
      </section>

      <section class="fa-card history-card">
        <div class="section-header">
          <div>
            <h2>转换记录</h2>
            <p>最近创建的文档转换任务。</p>
          </div>
          <ElInput
            v-model.trim="searchKeyword"
            class="history-search"
            clearable
            :prefix-icon="Search"
            placeholder="搜索文档名称"
          />
        </div>

        <ElTable :data="paginatedRecords" class="conversion-table">
          <ElTableColumn prop="name" label="文档名称" min-width="180" />
          <ElTableColumn prop="target" label="目标格式" width="130" />
          <ElTableColumn label="状态" width="120">
            <template #default="{ row }">
              <ElTag :type="row.statusType">{{ row.status }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="updatedAt" label="更新时间" width="160" />
          <ElTableColumn label="操作" width="150" fixed="right">
            <template #default>
              <ElButton link type="primary">预览</ElButton>
              <ElButton link>导出</ElButton>
            </template>
          </ElTableColumn>
        </ElTable>

        <div class="table-pagination">
          <div class="table-pagination__summary">
            共 {{ filteredRecords.length }} 条数据，当前第 {{ displayCurrentPage }} /
            {{ totalPages }} 页
          </div>
          <ElPagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="filteredRecords.length"
            background
            layout="sizes, prev, pager, next"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";

defineOptions({ name: "DashboardAiDocumentConversion" });

const loading = ref(true);
const fileInputRef = ref<HTMLInputElement | null>(null);
const searchKeyword = ref("");
const currentPage = ref(1);
const pageSize = ref(10);

const form = ref({
  target: "PDF",
});

const formats = [
  "DOCM",
  "DOCX",
  "DOCXF",
  "DOTM",
  "DOTX",
  "EPUB",
  "FB2",
  "HTML",
  "HWP",
  "HWPX",
  "ODT",
  "OTT",
  "PAGES",
  "PDF",
  "PDFA",
  "RTF",
  "TXT",
  "PNG",
  "JPG",
  "BMP",
  "GIF",
];
const selectedFile = ref<File | null>(null);

const records = [
  {
    name: "项目实施方案.pdf",
    target: "Word",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 11:02",
  },
  {
    name: "行业研究报告.pptx",
    target: "Markdown",
    status: "转换中",
    statusType: "warning",
    updatedAt: "2026-06-30 10:36",
  },
  {
    name: "扫描合同.jpg",
    target: "知识库片段",
    status: "待处理",
    statusType: "info",
    updatedAt: "2026-06-29 16:44",
  },
  {
    name: "扫描合同.jpg",
    target: "知识库片段",
    status: "待处理",
    statusType: "info",
    updatedAt: "2026-06-29 16:44",
  },
  {
    name: "扫描合同.jpg",
    target: "知识库片段",
    status: "待处理",
    statusType: "info",
    updatedAt: "2026-06-29 16:44",
  },
  {
    name: "扫描合同.jpg",
    target: "知识库片段",
    status: "待处理",
    statusType: "info",
    updatedAt: "2026-06-29 16:44",
  },
];

const filteredRecords = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return records;
  return records.filter((item) => item.name.toLowerCase().includes(keyword));
});

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredRecords.value.slice(start, start + pageSize.value);
});

const totalPages = computed(() => {
  if (filteredRecords.value.length === 0) return 0;
  return Math.ceil(filteredRecords.value.length / pageSize.value);
});

const displayCurrentPage = computed(() => {
  if (filteredRecords.value.length === 0) return 0;
  return Math.min(currentPage.value, totalPages.value);
});

watch([searchKeyword, pageSize], () => {
  currentPage.value = 1;
});

watch([filteredRecords, totalPages], () => {
  if (totalPages.value === 0) {
    currentPage.value = 1;
    return;
  }
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
});

function openFilePicker(): void {
  fileInputRef.value?.click();
}

function applySelectedFile(file: File | null): void {
  selectedFile.value = file;
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  applySelectedFile(file);
}

function handleFileDrop(event: DragEvent): void {
  const file = event.dataTransfer?.files?.[0] ?? null;
  if (!file) return;
  applySelectedFile(file);
}

function clearSelectedFile(): void {
  selectedFile.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
}

function createConversion(): void {
  if (!selectedFile.value) {
    ElMessage.warning("请先选择需要转换的文档");
    return;
  }
  ElMessage.success(`已创建 ${selectedFile.value.name} -> ${form.value.target} 的转换任务`);
}

onMounted(() => {
  loading.value = false;
});
</script>

<style lang="scss" scoped>
.conversion-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 8px;
}

.conversion-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 6px 0 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.conversion-layout {
  display: block;
}

.hidden-file-input {
  display: none;
}

.converter-card,
.history-card {
  display: flex;
  flex-direction: column;
  padding: 18px;
  border-radius: 8px;
}

.card-title,
.section-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;

  h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 650;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 6px 0 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  > .fa-svg-icon {
    flex: 0 0 auto;
    font-size: 24px;
    color: var(--el-color-primary);
  }
}

.history-search {
  flex: 0 0 240px;
  max-width: 100%;
}

.upload-stage {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  min-height: 176px;
  padding: 22px;
  text-align: center;
  cursor: pointer;
  background:
    linear-gradient(135deg, rgb(46 109 240 / 6%), rgb(18 166 210 / 3%)), var(--el-bg-color);
  border: 1px dashed var(--el-color-primary-light-5);
  border-radius: 14px;
  transition:
    border-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;

  &:hover {
    border-color: var(--el-color-primary);
    box-shadow: 0 12px 28px rgb(46 109 240 / 10%);
    transform: translateY(-1px);
  }
}

.upload-stage__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  font-size: 30px;
  color: var(--el-color-primary);
  background: linear-gradient(135deg, rgb(46 109 240 / 14%), rgb(18 166 210 / 10%));
  border-radius: 18px;
}

.upload-stage__title {
  font-size: 16px;
  font-weight: 650;
  color: var(--el-text-color-primary);
}

.upload-stage__desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.conversion-workbench {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 14px;
  align-items: center;
}

.selected-file-card {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  padding: 14px 16px;
  background: var(--el-bg-color);
  border: 1px dashed var(--el-border-color);
  border-radius: 12px;
}

.selected-file-card__meta {
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;
  color: var(--el-text-color-primary);

  .fa-svg-icon {
    flex: 0 0 auto;
    font-size: 20px;
    color: var(--el-text-color-regular);
  }

  span {
    overflow: hidden;
    font-size: 15px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.file-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  background: transparent;
  border: 0;
  border-radius: 10px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;

  .fa-svg-icon {
    font-size: 18px;
  }

  &:hover {
    color: var(--el-color-danger);
    background: var(--el-color-danger-light-9);
  }
}

.flow-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary-dark-2);

  .fa-svg-icon {
    font-size: 28px;
  }
}

.target-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 98px;
  min-height: 48px;
  padding: 0 18px;
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.04em;
  background: linear-gradient(180deg, rgb(255 255 255 / 96%), rgb(239 245 255 / 98%));
  border: 1px solid var(--el-border-color);
  border-radius: 14px;
  box-shadow: 0 10px 24px rgb(32 84 187 / 8%);
}

.target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(72px, 1fr));
  gap: 8px;
}

.target-chip {
  min-width: 0;
  min-height: 36px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background: var(--el-fill-color-light);
  border: 1px solid transparent;
  border-radius: 10px;
  transition: all 0.2s ease;

  &:hover {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary-light-5);
  }

  &.is-active {
    color: white;
    background: linear-gradient(135deg, var(--el-color-primary), #ff7a3d);
    border-color: transparent;
    box-shadow: 0 10px 20px rgb(46 109 240 / 18%);
  }
}

.action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.action-row__secondary,
.action-row__primary {
  min-height: 46px;
  font-size: 15px;
  font-weight: 650;
  border-radius: 12px;
}

.action-row__secondary {
  color: var(--el-text-color-primary);
  background: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.action-row__primary {
  border: 0;
  background: linear-gradient(135deg, var(--el-color-primary), #ff7a3d);
  box-shadow: 0 14px 28px rgb(46 109 240 / 18%);
}

.action-row :deep(.el-button) {
  margin: 0;
}

.conversion-table {
  width: 100%;
}

.table-pagination {
  display: flex;
  flex-shrink: 0;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.table-pagination__summary {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.table-pagination :deep(.el-pagination) {
  margin-left: auto;
}

.table-pagination :deep(.el-pagination__sizes) {
  margin-right: 8px;
}

@media screen and (width <= 960px) {
  .file-flow {
    grid-template-columns: 1fr;
  }

  .flow-arrow {
    justify-self: center;

    .fa-svg-icon {
      transform: rotate(90deg);
    }
  }
}

@media screen and (width <= 720px) {
  .conversion-header {
    flex-direction: column;
  }

  .action-row {
    grid-template-columns: 1fr;
  }

  .target-badge {
    justify-self: flex-start;
  }

  .section-header {
    flex-direction: column;
  }

  .history-search {
    flex-basis: auto;
    width: 100%;
  }

  .table-pagination {
    align-items: flex-start;
  }

  .table-pagination :deep(.el-pagination) {
    margin-left: 0;
  }
}
</style>
