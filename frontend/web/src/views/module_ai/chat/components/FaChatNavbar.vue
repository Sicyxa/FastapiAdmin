<template>
  <div class="chat-navbar">
    <div class="navbar-left">
      <button class="collapse-btn" @click="toggleSidebar">
        <FaSvgIcon
          v-if="!props.isSidebarCollapsed"
          :icon="resolveIconForFaSvgIcon('layout_leftbar_close_line')"
          class="size-6"
        />
        <FaSvgIcon
          v-else
          :icon="resolveIconForFaSvgIcon('layout_leftbar_open_line')"
          class="size-6"
        />
      </button>
      <span class="navbar-title">星宇智能助手</span>
    </div>

    <div class="navbar-right">
      <ElButton v-if="hasMessages" text :icon="Delete" @click="handleClearChat">
        清空对话
      </ElButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Delete } from "@element-plus/icons-vue";
import { resolveIconForFaSvgIcon } from "@utils";

interface Props {
  messageCount: number;
  isSidebarCollapsed?: boolean;
}

interface Emits {
  (e: "clear-chat"): void;
  (e: "toggle-sidebar"): void;
}

const props = withDefaults(defineProps<Props>(), {
  isSidebarCollapsed: false,
});
const emit = defineEmits<Emits>();

const hasMessages = computed(() => props.messageCount > 0);

const handleClearChat = () => emit("clear-chat");
const toggleSidebar = () => emit("toggle-sidebar");
</script>

<style lang="scss" scoped>
.chat-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background:
    linear-gradient(90deg, rgb(255 255 255 / 68%), rgb(255 255 255 / 46%)), var(--fa-surface-tint);

  .navbar-left {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .navbar-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--el-color-primary);
  }

  .navbar-right {
    display: flex;
    flex-wrap: nowrap;
    gap: 12px;
    align-items: center;

    :deep(.el-button) {
      margin: 0;
    }
  }
}

.collapse-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  transition:
    background-color 0.2s,
    color 0.2s;

  &:hover {
    color: var(--el-color-primary);
    background:
      linear-gradient(var(--fa-surface-elevated), var(--fa-surface-elevated)) padding-box,
      var(--fa-gradient-border) border-box;
    border-color: transparent;
    box-shadow: 0 6px 14px rgb(37 99 235 / 10%);
  }

  &:focus-visible {
    outline: 2px solid var(--el-color-primary);
    outline-offset: 2px;
  }

  & > div {
    color: inherit;
  }
}
</style>
