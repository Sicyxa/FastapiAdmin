<template>
  <div class="chat-input" :class="{ 'chat-input--disabled': disabled }">
    <div class="input-wrapper">
      <div v-if="uploadedFiles.length > 0" class="uploaded-files">
        <div v-for="file in uploadedFiles" :key="file.id" class="file-item">
          <ElIcon class="file-icon"><Document /></ElIcon>
          <span class="file-name">{{ file.name }}</span>
          <ElIcon class="file-remove" @click="removeFile(file.id)"><Close /></ElIcon>
        </div>
      </div>
      <div class="input-container">
        <ElInput
          v-model="inputMessage"
          type="textarea"
          placeholder="向星宇智能助手发送消息..."
          :disabled="disabled || sending"
          :autosize="{ minRows: 1, maxRows: 6 }"
          resize="none"
          class="message-input"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.shift.enter.exact="handleShiftEnter"
        />
        <div class="input-footer">
          <div class="input-footer-left">
            <ElDropdown
              trigger="click"
              placement="top-start"
              @command="handleSelectModel"
              @visible-change="handleDropdownVisible"
            >
              <div class="model-switcher" :class="{ 'is-active': dropdownVisible }">
                <ElIcon class="model-icon"><Cpu /></ElIcon>
                <span class="model-name" :title="activeModelName">
                  {{ activeModelName }}
                </span>
                <ElIcon class="model-arrow" :class="{ expanded: dropdownVisible }">
                  <ArrowDown />
                </ElIcon>
              </div>
              <template #dropdown>
                <ElDropdownMenu>
                  <ElDropdownItem command="__default__" :class="{ 'is-active': !activeId }">
                    <ElIcon class="dropdown-icon"><MagicStick /></ElIcon>
                    <span class="dropdown-label">系统默认</span>
                    <ElTag v-if="!activeId" type="success" size="small" effect="plain">
                      使用中
                    </ElTag>
                  </ElDropdownItem>
                  <template v-if="items.length > 0">
                    <ElDropdownItem
                      v-for="item in items"
                      :key="item.id"
                      :command="item.id"
                      :class="{ 'is-active': item.id === activeId }"
                      :disabled="switching"
                    >
                      <ElIcon class="dropdown-icon"><ChatLineSquare /></ElIcon>
                      <div class="dropdown-content">
                        <div class="dropdown-label">{{ item.name }}</div>
                        <div class="dropdown-meta">{{ item.model_id }}</div>
                      </div>
                      <ElTag v-if="item.id === activeId" type="success" size="small" effect="plain">
                        使用中
                      </ElTag>
                    </ElDropdownItem>
                  </template>
                  <ElDropdownItem v-if="items.length === 0" disabled>
                    <span class="dropdown-empty"
                      >暂未配置模型，请到"星宇智能助手 → 设置 → 配置中心"添加</span
                    >
                  </ElDropdownItem>
                </ElDropdownMenu>
              </template>
            </ElDropdown>
          </div>
          <div class="input-actions">
            <ElUpload
              v-if="enableUpload"
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              :accept="acceptTypes"
              :multiple="true"
            >
              <ElButton :icon="Paperclip" class="upload-btn" circle />
            </ElUpload>
            <ElButton
              v-if="sending"
              class="send-button"
              type="danger"
              circle
              title="停止生成"
              @click="handleStop"
            >
              <ElIcon><VideoPause /></ElIcon>
            </ElButton>
            <ElButton
              v-else
              :disabled="(!inputMessage.trim() && uploadedFiles.length === 0) || disabled"
              class="send-button"
              type="primary"
              circle
              @click="handleSend"
            >
              <ElIcon><Promotion /></ElIcon>
            </ElButton>
          </div>
        </div>
      </div>
      <div v-if="showHint" class="input-hint">
        <span>按 Enter 发送消息，Shift + Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Promotion,
  Paperclip,
  Document,
  Close,
  VideoPause,
  Cpu,
  ArrowDown,
  ChatLineSquare,
  MagicStick,
} from "@element-plus/icons-vue";
import type { UploadFile } from "element-plus";
import type { UploadedFile } from "../types";
import AiChatAPI, { type AiModelConfigItem, type AiModelConfigList } from "@/api/module_ai/chat";

interface Props {
  disabled?: boolean;
  sending?: boolean;
  enableUpload?: boolean;
  showHint?: boolean;
}

interface Emits {
  (e: "send", message: string, files?: UploadedFile[]): void;
  (e: "stop"): void;
  (e: "model-changed"): void;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  sending: false,
  enableUpload: true,
  showHint: true,
});

const emit = defineEmits<Emits>();

// ============ 模型选择器 ============ //
const dropdownVisible = ref(false);
const items = ref<AiModelConfigItem[]>([]);
const activeId = ref<string | null>(null);
const switching = ref(false);

const activeModelName = computed(() => {
  if (!activeId.value) return "系统默认";
  const item = items.value.find((i) => i.id === activeId.value);
  return item?.name || "系统默认";
});

const loadModels = async () => {
  try {
    const res = await AiChatAPI.getModelConfig();
    if (res.data?.code === 0 && res.data.data) {
      const data: AiModelConfigList = res.data.data;
      items.value = data.items || [];
      activeId.value = data.active_id;
    }
  } catch {
    /* 静默失败 */
  }
};

const handleDropdownVisible = (visible: boolean) => {
  dropdownVisible.value = visible;
  if (visible) loadModels();
};

const handleSelectModel = async (command: string) => {
  dropdownVisible.value = false;
  if (command === activeId.value) return;
  switching.value = true;
  try {
    const res = await AiChatAPI.activateModelConfig(command === "__default__" ? "" : command);
    if (res.data?.code === 0) {
      activeId.value = command === "__default__" ? null : command;
      const newName =
        command === "__default__" ? "系统默认" : items.value.find((i) => i.id === command)?.name;
      ElMessage.success(`已切换到：${newName}`);
      emit("model-changed");
    } else {
      ElMessage.error(res.data?.msg || "切换失败");
    }
  } catch {
    ElMessage.error("切换模型失败");
  } finally {
    switching.value = false;
  }
};

onMounted(loadModels);

const inputMessage = ref("");
const uploadedFiles = ref<UploadedFile[]>([]);

const acceptTypes = computed(() => {
  return ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.mp3,.wav,.mp4,.avi,.mov";
});

const handleFileChange = (uploadFile: UploadFile) => {
  const file = uploadFile.raw;
  if (!file) return;

  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    alert("文件大小不能超过10MB");
    return;
  }

  const uploadedFile: UploadedFile = {
    id: Date.now().toString() + Math.random().toString(36).substr(2),
    name: file.name,
    size: file.size,
    type: file.type,
    file,
  };

  uploadedFiles.value.push(uploadedFile);
};

const removeFile = (id: string) => {
  const index = uploadedFiles.value.findIndex((f) => f.id === id);
  if (index > -1) {
    uploadedFiles.value.splice(index, 1);
  }
};

const handleSend = () => {
  const message = inputMessage.value.trim();
  if ((!message && uploadedFiles.value.length === 0) || props.disabled || props.sending) {
    return;
  }
  emit("send", message, uploadedFiles.value.length > 0 ? [...uploadedFiles.value] : undefined);
  inputMessage.value = "";
  uploadedFiles.value = [];
};

const handleStop = () => {
  if (!props.sending) return;
  emit("stop");
};

const handleShiftEnter = () => {
  inputMessage.value += "\n";
};

defineExpose({
  refresh: loadModels,
  focus: () => {
    const input = document.querySelector(".message-input textarea") as HTMLTextAreaElement;
    input?.focus();
  },
});
</script>

<style lang="scss" scoped>
.chat-input {
  .input-wrapper {
    max-width: 800px;
    padding: 20px;
    margin: 0 auto;

    @media (width <= 640px) {
      padding: 12px 16px;
    }

    .uploaded-files {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;

      .file-item {
        display: flex;
        gap: 6px;
        align-items: center;
        padding: 8px 14px;
        font-size: 13px;
        background:
          linear-gradient(var(--fa-surface-elevated), var(--fa-surface-elevated)) padding-box,
          var(--fa-gradient-border) border-box;
        border: 1px solid transparent;
        border-radius: 8px;
        transition: all 0.2s ease;

        &:hover {
          background: var(--el-color-primary-light-9);
          border-color: var(--el-color-primary-light-7);
        }

        .file-icon {
          font-size: 16px;
          color: var(--el-color-primary);
        }

        .file-name {
          max-width: 180px;
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 13px;
          white-space: nowrap;

          @media (width <= 640px) {
            max-width: 120px;
            font-size: 12px;
          }
        }

        .file-remove {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          cursor: pointer;
          transition: color 0.2s ease;

          &:hover {
            color: var(--el-color-danger);
          }
        }
      }
    }

    .input-container {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 20px;
      background:
        linear-gradient(180deg, rgb(255 255 255 / 97%), rgb(255 255 255 / 90%)) padding-box,
        var(--fa-gradient-border) border-box;
      border: 1px solid transparent;
      border-radius: 18px;
      box-shadow:
        0 14px 30px rgb(37 99 235 / 8%),
        0 0 0 1px color-mix(in srgb, var(--el-color-primary) 8%, rgb(255 255 255 / 74%)) inset;
      transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        transform 0.2s ease;

      &:hover {
        box-shadow:
          0 16px 34px rgb(31 45 61 / 9%),
          0 0 0 1px color-mix(in srgb, var(--el-color-primary) 10%, rgb(255 255 255 / 78%)) inset;
        transform: translateY(-1px);
      }

      &:focus-within {
        box-shadow:
          0 16px 34px rgb(31 45 61 / 9%),
          0 0 0 1px color-mix(in srgb, var(--el-color-primary) 12%, rgb(255 255 255 / 80%)) inset;
      }

      .message-input {
        flex: 1;
        min-width: 0;
        min-height: 84px;

        :deep(.el-textarea__wrapper) {
          display: flex;
          align-items: stretch;
          padding: 0;
          background: transparent !important;
          box-shadow: none !important;
          border: none !important;
        }

        :deep(.el-textarea) {
          width: 100%;
          padding: 0;
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
        }

        :deep(.el-textarea__inner) {
          min-height: 84px !important;
          padding: 2px 0 0 !important;
          font-size: 15px;
          line-height: 1.6;
          color: var(--el-text-color-primary);
          resize: none;
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          outline: none !important;
          appearance: none;
          -webkit-appearance: none;
        }

        :deep(textarea) {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          outline: none !important;
          appearance: none;
          -webkit-appearance: none;
        }

        :deep(.el-textarea__inner::placeholder) {
          color: color-mix(in srgb, var(--el-text-color-secondary) 88%, white);
        }

        :deep(.el-textarea:hover .el-textarea__inner),
        :deep(.el-textarea__inner:hover),
        :deep(.el-textarea__inner:focus),
        :deep(.el-textarea__inner:focus-visible) {
          border: none !important;
          box-shadow: none !important;
          outline: none !important;
        }
      }

      .input-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 8px;

        .input-footer-left {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .model-switcher {
          display: flex;
          gap: 6px;
          align-items: center;
          height: 30px;
          padding: 0 10px;
          font-size: 13px;
          color: var(--el-text-color-regular);
          cursor: pointer;
          background:
            linear-gradient(var(--el-fill-color-blank), var(--el-fill-color-blank)) padding-box,
            var(--fa-gradient-border) border-box;
          border: 1px solid color-mix(in srgb, var(--fa-line-strong) 35%, transparent);
          border-radius: 6px;
          transition: all 0.2s;

          &:hover {
            color: var(--el-color-primary);
            background: var(--el-color-primary-light-9);
            border-color: var(--el-color-primary-light-5);
          }

          &.is-active {
            color: var(--el-color-primary);
            background: var(--el-color-primary-light-9);
            border-color: var(--el-color-primary);
          }

          .model-icon {
            font-size: 14px;
          }

          .model-name {
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            font-weight: 500;
            white-space: nowrap;

            @media (width <= 640px) {
              max-width: 80px;
            }
          }

          .model-arrow {
            font-size: 12px;
            transition: transform 0.2s;

            &.expanded {
              transform: rotate(180deg);
            }
          }
        }

        .input-actions {
          display: flex;
          gap: 10px;
          align-items: center;

          .upload-btn {
            font-size: 18px;
            color: var(--el-text-color-secondary);
            border-color: var(--el-color-primary-light-7);
            transition: all 0.2s ease;

            &:hover {
              color: var(--el-color-primary);
              transform: scale(1.05);
            }
          }

          .send-button {
            flex-shrink: 0;
            border-radius: 50%;
            box-shadow: 0 10px 22px rgb(64 158 255 / 22%);
            transition: all 0.2s ease;

            &:hover {
              box-shadow: var(--el-box-shadow);
              transform: translateY(-1px);
            }

            &:active {
              transform: translateY(0);
            }
          }
        }
      }
    }

    .input-hint {
      margin-top: 12px;
      font-size: 12px;
      font-weight: 400;
      color: var(--el-text-color-secondary);
      text-align: center;
      letter-spacing: 0.5px;
    }
  }

  &.chat-input--disabled .input-wrapper .input-container {
    opacity: 0.72;
    filter: grayscale(0.06);

    &:hover {
      border-color: var(--el-border-color-light);
      box-shadow: var(--el-box-shadow-light);
      transform: none;
    }

    &:focus-within {
      border-color: var(--el-border-color-light);
      box-shadow: var(--el-box-shadow-light);
    }
  }
}

:global(html.dark) .chat-input {
  .input-wrapper {
    .uploaded-files .file-item,
    .input-container {
      background:
        linear-gradient(180deg, var(--fa-surface-elevated), var(--default-box-color)) padding-box,
        var(--fa-gradient-border) border-box;
      box-shadow: 0 16px 38px rgb(0 0 0 / 26%);
    }
  }
}
</style>

<style lang="scss">
/* 下拉菜单项样式 - 因为 scoped 限制无法直接覆盖命令项 */
.el-dropdown-menu {
  min-width: 240px;
  max-width: calc(100vw - 20px);

  @media (width <= 640px) {
    width: 90vw;
    min-width: 200px;
  }

  .el-dropdown-menu__item {
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 8px 12px;

    &.is-active {
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }

    .dropdown-icon {
      flex-shrink: 0;
      font-size: 14px;
    }

    .dropdown-content {
      flex: 1;
      min-width: 0;
    }

    .dropdown-label {
      font-size: 14px;
      font-weight: 500;
    }

    .dropdown-meta {
      max-width: 160px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      white-space: nowrap;
    }

    .dropdown-empty {
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }

    .el-tag {
      flex-shrink: 0;
      margin-left: auto;
    }
  }
}
</style>
