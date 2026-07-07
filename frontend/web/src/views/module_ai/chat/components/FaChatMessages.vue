<template>
  <ElScrollbar ref="messagesContainer" class="chat-messages">
    <WelcomeScreen
      v-if="messages.length === 0"
      :title="assistantTitle"
      :subtitle="assistantSubtitle"
      @prompt-click="handlePromptClick"
    />
    <div v-else class="messages-list">
      <FaMessageItem
        v-for="message in messages"
        :key="message.id"
        :message="message"
        @toggle-fold="handleToggleFold(message)"
      />
    </div>
    <div v-if="error" class="error-banner">
      <ElAlert :title="error" type="error" :closable="true" show-icon @close="handleErrorClose" />
    </div>
  </ElScrollbar>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from "vue";
import { ElScrollbar } from "element-plus";
import WelcomeScreen from "./FaWelcomeScreen.vue";
import FaMessageItem from "./FaMessageItem.vue";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  error: string;
  assistantTitle?: string;
  assistantSubtitle?: string;
}

interface Emits {
  (e: "prompt-click", prompt: string): void;
  (e: "error-close"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const messagesContainer = ref<InstanceType<typeof ElScrollbar>>();

const scrollToBottom = () => {
  nextTick(() => {
    const wrap = messagesContainer.value?.wrapRef;
    if (wrap) wrap.scrollTop = wrap.scrollHeight;
  });
};

watch(
  () => props.messages,
  () => {
    scrollToBottom();
  },
  { deep: true }
);

const handlePromptClick = (prompt: string) => {
  emit("prompt-click", prompt);
};

const handleToggleFold = (message: ChatMessage) => {
  message.collapsed = !message.collapsed;
};

const handleErrorClose = () => {
  emit("error-close");
};

defineExpose({
  scrollToBottom,
});
</script>

<style lang="scss" scoped>
.chat-messages {
  /* 与 index chat-main 同底，避免 disabled 灰 + page 色打架 */
  display: block;
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  background: transparent;

  :deep(.el-scrollbar__view) {
    width: 100%;
    min-height: 100%;
  }

  .messages-list {
    max-width: 800px;
    padding: 24px;
    margin: 0 auto;
  }

  .error-banner {
    position: fixed;
    bottom: 140px;
    left: 50%;
    z-index: 1000;
    padding: 0 24px;
    transform: translateX(-50%);
  }
}
</style>
