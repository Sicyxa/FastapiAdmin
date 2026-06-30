<template>
  <div class="conversion-page">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="conversion-header">
        <div>
          <h1>AI文档转换</h1>
          <p>将 PDF、Word、图片或 Markdown 转换为结构化文档、PPT 大纲与知识库素材。</p>
        </div>
        <ElButton type="primary">
          <FaSvgIcon icon="ri:add-line" />
          新建转换
        </ElButton>
      </section>

      <section class="conversion-layout">
        <div class="fa-card converter-card">
          <div class="card-title">
            <div>
              <h2>转换任务</h2>
              <p>选择源文件与目标格式，AI 会自动清理版式并保留语义结构。</p>
            </div>
            <FaSvgIcon icon="ri:file-transfer-line" />
          </div>

          <ElUpload
            v-model:file-list="fileList"
            class="document-upload"
            drag
            action="#"
            :auto-upload="false"
            :limit="5"
          >
            <FaSvgIcon icon="ri:file-upload-line" class="upload-icon" />
            <div class="upload-text">选择或拖入需要转换的文档</div>
            <template #tip>
              <div class="upload-tip">支持 pdf、docx、xlsx、pptx、md、png、jpg。</div>
            </template>
          </ElUpload>

          <div class="format-grid">
            <button
              v-for="item in formats"
              :key="item.value"
              type="button"
              class="format-item"
              :class="{ 'is-active': form.target === item.value }"
              @click="form.target = item.value"
            >
              <FaSvgIcon :icon="item.icon" />
              <span>{{ item.label }}</span>
            </button>
          </div>

          <ElForm label-position="top" class="conversion-form">
            <ElFormItem label="处理模式">
              <ElRadioGroup v-model="form.mode">
                <ElRadioButton label="保留版式" value="layout" />
                <ElRadioButton label="重组内容" value="semantic" />
                <ElRadioButton label="提取要点" value="summary" />
              </ElRadioGroup>
            </ElFormItem>
            <ElFormItem label="附加能力">
              <ElCheckboxGroup v-model="form.options">
                <ElCheckbox label="OCR识别" value="ocr" />
                <ElCheckbox label="表格解析" value="table" />
                <ElCheckbox label="图片说明" value="imageCaption" />
              </ElCheckboxGroup>
            </ElFormItem>
          </ElForm>

          <ElButton type="primary" class="w-full" @click="createConversion">
            <FaSvgIcon icon="ri:magic-line" />
            开始转换
          </ElButton>
        </div>

        <aside class="fa-card preview-card">
          <div class="card-title">
            <div>
              <h2>输出预览</h2>
              <p>转换后将生成可编辑文件与结构化片段。</p>
            </div>
            <FaSvgIcon icon="ri:article-line" />
          </div>

          <div class="preview-paper">
            <div class="paper-line is-title"></div>
            <div class="paper-line"></div>
            <div class="paper-line short"></div>
            <div class="paper-block">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div class="paper-line"></div>
            <div class="paper-line medium"></div>
          </div>

          <div class="summary-list">
            <div v-for="item in summaries" :key="item.title" class="summary-item">
              <FaSvgIcon :icon="item.icon" />
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.description }}</p>
              </div>
            </div>
          </div>
        </aside>
      </section>

      <section class="fa-card history-card">
        <div class="section-header">
          <div>
            <h2>转换记录</h2>
            <p>最近创建的文档转换任务。</p>
          </div>
          <ElButton text type="primary">
            查看全部
            <FaSvgIcon icon="ri:arrow-right-s-line" />
          </ElButton>
        </div>

        <ElTable :data="records" class="conversion-table">
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
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import type { UploadUserFile } from "element-plus";
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";

defineOptions({ name: "DashboardAiDocumentConversion" });

interface FormatItem {
  label: string;
  value: string;
  icon: string;
}

const loading = ref(true);
const fileList = ref<UploadUserFile[]>([]);

const form = ref({
  target: "docx",
  mode: "semantic",
  options: ["ocr", "table"],
});

const formats: FormatItem[] = [
  { label: "Word", value: "docx", icon: "ri:file-word-line" },
  { label: "PPT大纲", value: "ppt", icon: "ri:slideshow-3-line" },
  { label: "Markdown", value: "markdown", icon: "ri:markdown-line" },
  { label: "知识库片段", value: "knowledge", icon: "ri:database-2-line" },
];

const summaries = [
  {
    title: "结构化段落",
    description: "自动识别标题、正文、列表与引用。",
    icon: "ri:list-check-2",
  },
  {
    title: "表格与图片解析",
    description: "将复杂版面转换为可编辑内容。",
    icon: "ri:table-2",
  },
  {
    title: "智能摘要",
    description: "同步生成要点、关键词与章节摘要。",
    icon: "ri:mind-map",
  },
];

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
];

function createConversion(): void {
  if (fileList.value.length === 0) {
    ElMessage.warning("请先选择需要转换的文档");
    return;
  }
  ElMessage.success("转换任务已创建");
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
    margin: 8px 0 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.conversion-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 20px;
}

.converter-card,
.preview-card,
.history-card {
  padding: 20px;
  border-radius: 8px;
}

.card-title,
.section-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;

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

.document-upload {
  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    border-radius: 8px;
  }
}

.upload-icon {
  margin-bottom: 12px;
  font-size: 42px;
  color: var(--el-color-primary);
}

.upload-text {
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.upload-tip {
  margin-top: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.format-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 18px 0;
}

.format-item {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;

  .fa-svg-icon {
    font-size: 18px;
  }

  &.is-active {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary-light-5);
  }
}

.preview-paper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}

.paper-line {
  width: 100%;
  height: 10px;
  background: var(--el-border-color);
  border-radius: 999px;

  &.is-title {
    width: 58%;
    height: 16px;
    background: var(--el-color-primary-light-5);
  }

  &.short {
    width: 46%;
  }

  &.medium {
    width: 72%;
  }
}

.paper-block {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;

  span {
    height: 48px;
    background: var(--default-box-color);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
  }
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 18px;
}

.summary-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;

  .fa-svg-icon {
    flex: 0 0 auto;
    margin-top: 2px;
    font-size: 20px;
    color: var(--el-color-primary);
  }

  strong {
    font-size: 14px;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 4px 0 0;
    font-size: 12px;
    line-height: 1.5;
    color: var(--el-text-color-secondary);
  }
}

.conversion-form {
  margin-top: 2px;
}

.conversion-table {
  width: 100%;
}

@media screen and (width <= 1100px) {
  .conversion-layout {
    grid-template-columns: 1fr;
  }
}

@media screen and (width <= 720px) {
  .conversion-header {
    flex-direction: column;
  }

  .format-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
