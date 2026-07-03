<template>
  <div class="document-page">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="document-header">
        <div>
          <h1>音视频转写</h1>
          <p>上传会议录音、访谈视频或课程素材，生成可编辑的文字稿与摘要。</p>
        </div>
        <ElButton type="primary">
          <FaSvgIcon icon="ri:add-line" />
          新建任务
        </ElButton>
      </section>

      <section class="document-grid">
        <div class="upload-card fa-card">
          <div class="card-title">
            <div>
              <h2>上传素材</h2>
              <p>支持 mp3、wav、m4a、mp4、mov 等常见格式。</p>
            </div>
            <FaSvgIcon icon="ri:upload-cloud-2-line" />
          </div>

          <ElUpload
            v-model:file-list="fileList"
            class="transcription-upload"
            drag
            action="#"
            :auto-upload="false"
            :limit="3"
          >
            <FaSvgIcon icon="ri:file-music-line" class="upload-icon" />
            <div class="upload-text">拖拽文件到此处，或点击选择文件</div>
            <template #tip>
              <div class="upload-tip">单个文件建议不超过 2GB，可在任务创建后继续补充素材。</div>
            </template>
          </ElUpload>
        </div>

        <div class="settings-card fa-card">
          <div class="card-title">
            <div>
              <h2>转写设置</h2>
              <p>按素材语言与输出场景选择处理方式。</p>
            </div>
            <FaSvgIcon icon="ri:equalizer-line" />
          </div>

          <ElForm label-position="top">
            <ElFormItem label="识别语言">
              <ElSelect v-model="form.language" class="w-full">
                <ElOption label="自动识别" value="auto" />
                <ElOption label="中文普通话" value="zh" />
                <ElOption label="英文" value="en" />
              </ElSelect>
            </ElFormItem>
          </ElForm>

          <ElButton type="primary" class="w-full" @click="createTask">
            <FaSvgIcon icon="ri:play-circle-line" />
            开始转写
          </ElButton>
        </div>
      </section>

      <section class="fa-card task-card">
        <div class="section-header">
          <div>
            <h2>最近任务</h2>
            <p>查看转写进度、下载文字稿或继续编辑。</p>
          </div>
          <ElButton text type="primary">
            刷新
            <FaSvgIcon icon="ri:refresh-line" />
          </ElButton>
        </div>

        <ElTable :data="tasks" class="document-table">
          <ElTableColumn prop="name" label="文件名称" min-width="180" />
          <ElTableColumn prop="duration" label="时长" width="100" />
          <ElTableColumn prop="language" label="语言" width="120" />
          <ElTableColumn label="状态" width="130">
            <template #default="{ row }">
              <ElTag :type="row.statusType">{{ row.status }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="updatedAt" label="更新时间" width="160" />
          <ElTableColumn label="操作" width="150" fixed="right">
            <template #default>
              <ElButton link type="primary">查看</ElButton>
              <ElButton link>下载</ElButton>
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

defineOptions({ name: "DashboardAudioVideoTranscription" });

const loading = ref(true);
const fileList = ref<UploadUserFile[]>([]);

const form = ref({
  language: "auto",
  outputs: ["transcript", "summary"],
  speakerDiarization: true,
});

const tasks = [
  {
    name: "产品需求评审会议.mp4",
    duration: "48:32",
    language: "中文",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 10:20",
  },
  {
    name: "客户访谈录音.m4a",
    duration: "32:15",
    language: "自动识别",
    status: "转写中",
    statusType: "warning",
    updatedAt: "2026-06-30 09:48",
  },
  {
    name: "培训课程片段.wav",
    duration: "18:06",
    language: "中文",
    status: "待处理",
    statusType: "info",
    updatedAt: "2026-06-29 17:12",
  },
];

function createTask(): void {
  if (fileList.value.length === 0) {
    ElMessage.warning("请先选择需要转写的音视频文件");
    return;
  }
  ElMessage.success("转写任务已创建");
}

onMounted(() => {
  loading.value = false;
});
</script>

<style lang="scss" scoped>
.document-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 8px;
}

.document-header {
  display: flex;
  gap: 16px;
  align-items: center;
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

.document-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
  align-items: start;
  gap: 14px;
}

.task-card {
  display: flex;
  flex-direction: column;
  padding: 18px;
  border-radius: 8px;
}

.upload-card,
.settings-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
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

.upload-card,
.settings-card {
  .card-title {
    margin-bottom: 12px;
  }
}

.transcription-upload {
  display: flex;

  :deep(.el-upload) {
    width: 100%;
    display: flex;
  }

  :deep(.el-upload-dragger) {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 104px;
    padding: 14px;
    border-radius: 12px;
  }
}

.upload-icon {
  margin-bottom: 8px;
  font-size: 32px;
  color: var(--el-color-primary);
}

.upload-text {
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.upload-tip {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.settings-card {
  :deep(.el-form) {
    flex: 1;
  }

  :deep(.el-form-item__label) {
    margin-bottom: 4px;
  }

  :deep(.el-form-item) {
    margin-bottom: 10px;
  }

  :deep(.el-checkbox-group) {
    gap: 14px;
  }

  > .el-button {
    min-height: 42px;
    margin-top: auto;
  }
}

.document-table {
  width: 100%;
}

@media screen and (width <= 960px) {
  .document-grid {
    grid-template-columns: 1fr;
  }
}

@media screen and (width <= 640px) {
  .document-header,
  .section-header {
    flex-direction: column;
  }
}
</style>
