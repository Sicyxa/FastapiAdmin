<template>
  <div class="fa-full-height">
    <ElContainer class="main-chat">
      <ElAside class="sidebar-container" :class="{ collapsed: isSidebarCollapsed }">
        <FaSidebar
          ref="sidebarRef"
          :current-session-id="currentSessionId"
          :is-collapsed="isSidebarCollapsed"
          :title="assistantTitle"
          @select-session="handleSelectSession"
          @new-session="handleNewSession"
        />
      </ElAside>
      <ElContainer class="chat-container">
        <ElHeader class="chat-header">
          <FaChatNavbar
            :message-count="messages.length"
            :is-sidebar-collapsed="isSidebarCollapsed"
            :show-model-config-trigger="showModelConfigTrigger"
            :title="assistantTitle"
            @clear-chat="handleClearChat"
            @open-model-config="configDrawerVisible = true"
            @toggle-sidebar="toggleSidebar"
          />
        </ElHeader>
        <ElMain class="chat-main">
          <FaChatMessages
            ref="chatMessagesRef"
            :messages="messages"
            :error="error"
            :assistant-title="assistantTitle"
            :assistant-subtitle="assistantSubtitle"
            @prompt-click="handleSendMessage"
            @error-close="error = ''"
          />
        </ElMain>
        <ElFooter class="chat-footer">
          <FaChatInput :sending="sending" @send="handleSendMessage" @stop="handleStopMessage" />
        </ElFooter>
      </ElContainer>
    </ElContainer>
    <FaConfigInfoDrawer v-if="isAdminMode" v-model="configDrawerVisible" />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "ChatWorkspace",
  inheritAttrs: false,
});

import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import AiChatAPI, { ChatSession, type AiModelConfigList } from "@/api/module_ai/chat";
import { Auth } from "@utils/auth";
import type { ChatMessage, UploadedFile } from "./types";
import FaSidebar from "./components/FaSidebar.vue";
import FaChatNavbar from "./components/FaChatNavbar.vue";
import FaChatMessages from "./components/FaChatMessages.vue";
import FaChatInput from "./components/FaChatInput.vue";
import FaConfigInfoDrawer from "@/components/layouts/fa-header-bar/widgets/FaConfigInfoDrawer.vue";
import {
  clearPendingChatPrompt,
  readPendingChatPrompt,
  type PendingChatPrompt,
} from "./pendingPrompt";

interface Props {
  mode: "user" | "admin";
}

const props = defineProps<Props>();

const isAdminMode = computed(() => props.mode === "admin");
const assistantTitle = computed(() => (isAdminMode.value ? "AI智能助手" : "星宇智能助手"));
const assistantSubtitle = computed(() =>
  isAdminMode.value
    ? "管理员可在此统一管理模型配置并进行智能对话"
    : "我是您的专属AI助手，可以帮您回答问题、处理任务和进行智能对话"
);
const messages = ref<ChatMessage[]>([]);
const sending = ref(false);
const isConnected = ref(true);
const error = ref("");
const currentSessionId = ref<string | null>(null);
const isSidebarCollapsed = ref(false);
const configDrawerVisible = ref(false);
const pendingInitialPrompt = ref<PendingChatPrompt | null>(null);
const canManageModels = ref(false);
const showModelConfigTrigger = computed(() => isAdminMode.value && canManageModels.value);

const chatMessagesRef = ref<{ scrollToBottom: () => void }>();
const sidebarRef = ref<{ loadSessions: () => void }>();

let ws: WebSocket | null = null;
let isUnmounting = false;
let connectionPromptVisible = false;
let pendingPromptSending = false;
const WS_URL = import.meta.env.VITE_APP_WS_ENDPOINT;

const loadModelConfigAbility = async () => {
  try {
    const res = await AiChatAPI.getModelConfig();
    if (res.data?.code === 0 && res.data.data) {
      const data: AiModelConfigList = res.data.data;
      canManageModels.value = !!data.can_manage;
    }
  } catch {
    canManageModels.value = false;
  }
};

const connectWebSocket = () => {
  if (ws?.readyState === WebSocket.OPEN) return;

  error.value = "";

  try {
    const url = new URL("/api/v1/ai/chat/ws", WS_URL);
    const token = Auth.getAccessToken();
    if (token) url.searchParams.append("token", token);

    ws = new WebSocket(url.toString());

    ws.onopen = () => {
      isConnected.value = true;
      handlePendingInitialMessage();
    };

    ws.onmessage = (event) => handleWebSocketMessage(event.data);

    ws.onclose = () => {
      ws = null;
      finishLoadingMessages();
      if (!isUnmounting) {
        handleDisconnected();
      }
    };

    ws.onerror = () => {
      finishLoadingMessages();
      handleDisconnected();
    };
  } catch {
    handleDisconnected();
  }
};

const disconnectWebSocket = () => {
  if (ws) {
    ws.close(1000, "用户主动断开");
    ws = null;
  }
  finishLoadingMessages();
};

const handleDisconnected = () => {
  if (isUnmounting) return;
  isConnected.value = false;
  showConnectionPrompt();
};

const showConnectionPrompt = () => {
  if (connectionPromptVisible) return;
  connectionPromptVisible = true;
  ElMessageBox.alert("当前未连接到服务器，请检查服务状态后刷新页面重试。", "连接提示", {
    confirmButtonText: "我知道了",
    type: "warning",
  }).finally(() => {
    connectionPromptVisible = false;
  });
};

const handleWebSocketMessage = (data: string) => {
  const text = data || "";

  if (text === "[DONE]") {
    finishLoadingMessages();
    sending.value = false;
    return;
  }

  if (text === "[STOPPED]") {
    finishLoadingMessages();
    sending.value = false;
    ElMessage.info("已停止生成");
    return;
  }

  const lastMessage = messages.value[messages.value.length - 1];

  if (lastMessage?.type === "assistant" && lastMessage.loading) {
    lastMessage.content += text;
  } else {
    addMessage("assistant", text);
  }

  chatMessagesRef.value?.scrollToBottom();
};

const addMessage = (type: "user" | "assistant", content: string, files?: UploadedFile[]) => {
  messages.value.push({
    id: generateId(),
    type,
    content,
    timestamp: Date.now(),
    collapsed: false,
    files,
    loading: type === "assistant",
  });
};

const finishLoadingMessages = () => {
  messages.value.forEach((msg) => {
    if (msg.type === "assistant" && msg.loading) {
      msg.loading = false;
      msg.collapsed = false;
    }
  });
};

const generateId = () => Date.now().toString(36) + Math.random().toString(36).slice(2);

const appendHistoryMessage = (role: "user" | "assistant", content: string, createdAt?: number | null) => {
  messages.value.push({
    id: generateId(),
    type: role,
    content: content || "",
    timestamp: typeof createdAt === "number" ? createdAt * 1000 : Date.now(),
    collapsed: false,
    loading: false,
  });
};

const normalizeSessionMessages = (sessionData: any) => {
  const historyMessages = Array.isArray(sessionData?.messages) ? sessionData.messages : [];
  if (historyMessages.length > 0) {
    return historyMessages;
  }

  const runs = Array.isArray(sessionData?.runs) ? sessionData.runs : [];
  return runs.flatMap((run: any) => (Array.isArray(run?.messages) ? run.messages : []));
};

const uploadChatFiles = async (files?: UploadedFile[]) => {
  if (!files?.length) return [];

  const uploadedFiles: Array<Record<string, any>> = [];
  for (const file of files) {
    if (file.file_path && file.file_url) {
      uploadedFiles.push({
        name: file.name,
        size: file.size,
        type: file.type,
        file_path: file.file_path,
        file_url: file.file_url,
      });
      continue;
    }

    if (!file.file) {
      uploadedFiles.push({
        name: file.name,
        size: file.size,
        type: file.type,
      });
      continue;
    }

    const formData = new FormData();
    formData.append("file", file.file);
    const response = await AiChatAPI.uploadChatFile(formData);
    if (response.data?.code !== 0 || !response.data.data) {
      throw new Error(response.data?.msg || "附件上传失败");
    }

    uploadedFiles.push({
      name: file.name,
      size: file.size,
      type: file.type,
      file_path: response.data.data.file_path,
      file_url: response.data.data.file_url,
    });
  }

  return uploadedFiles;
};

const handleSendMessage = async (message: string, files?: UploadedFile[]): Promise<boolean> => {
  if ((!message && !files) || sending.value) return false;
  if (!isConnected.value || ws?.readyState !== WebSocket.OPEN) {
    handleDisconnected();
    return false;
  }

  finishLoadingMessages();

  if (!currentSessionId.value) {
    const success = await createNewSession(message);
    if (!success) return false;
  }

  addMessage("user", message, files);
  messages.value.push({
    id: generateId(),
    type: "assistant",
    content: "",
    timestamp: Date.now(),
    loading: true,
  });

  sending.value = true;
  chatMessagesRef.value?.scrollToBottom();

  try {
    const uploadedFiles = await uploadChatFiles(files);
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          message,
          session_id: currentSessionId.value,
          files: uploadedFiles,
        })
      );
      return true;
    }
    throw new Error("WebSocket 连接未建立");
  } catch {
    messages.value.pop();
    error.value = "发送消息失败，请检查连接状态";
    sending.value = false;
    return false;
  }
};

const handlePendingInitialMessage = async () => {
  if (pendingPromptSending || !pendingInitialPrompt.value) return;
  if (ws?.readyState !== WebSocket.OPEN) return;

  pendingPromptSending = true;
  const prompt = pendingInitialPrompt.value;
  const sent = await handleSendMessage(prompt.message, prompt.files);

  if (sent) {
    pendingInitialPrompt.value = null;
    clearPendingChatPrompt();
  }

  pendingPromptSending = false;
};

const handleStopMessage = () => {
  if (ws?.readyState !== WebSocket.OPEN) return;
  try {
    ws.send(
      JSON.stringify({
        action: "stop",
        session_id: currentSessionId.value,
      })
    );
  } catch {
    ElMessage.error("停止指令发送失败");
  }
};

const createNewSession = async (firstMessage: string): Promise<boolean> => {
  try {
    const title = firstMessage.slice(0, 20) + (firstMessage.length > 20 ? "..." : "");
    const res = await AiChatAPI.createSession({ title });

    if (res.data?.code === 0 || res.data?.success) {
      currentSessionId.value = res.data.data?.id ?? null;
      sidebarRef.value?.loadSessions();
      return true;
    }
    throw new Error("创建会话失败");
  } catch {
    return false;
  }
};

const handleSelectSession = async (session: ChatSession) => {
  currentSessionId.value = session.id;
  messages.value = [];

  try {
    const response = await AiChatAPI.getSessionDetail(session.id);
    if (response.data?.code !== 0) return;

    const sessionData = response.data.data || {};
    const historyMessages = normalizeSessionMessages(sessionData);

    historyMessages.forEach((msg: any) => {
      if (msg?.role === "user" || msg?.role === "assistant") {
        appendHistoryMessage(msg.role, String(msg.content ?? ""), msg.created_at ?? null);
      }
    });

    finishLoadingMessages();
    chatMessagesRef.value?.scrollToBottom();
    ElMessage.success(`已切换到会话：${session.title}`);
  } catch {
    ElMessage.error("获取会话详情失败");
  }
};

const handleNewSession = () => {
  currentSessionId.value = null;
  messages.value = [];
  ElMessage.success("已开启新对话");
};

const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm("确定要清空当前对话吗？此操作不可恢复。", "确认清空", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    messages.value = [];
    ElMessage.success("对话已清空");
  } catch {
    ElMessage.info("已取消清空对话");
  }
};

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

onMounted(() => {
  pendingInitialPrompt.value = readPendingChatPrompt();
  loadModelConfigAbility();
  connectWebSocket();
});

onUnmounted(() => {
  isUnmounting = true;
  disconnectWebSocket();
});
</script>

<style lang="scss" scoped>
.main-chat {
  --chat-shell-outline: color-mix(in srgb, var(--el-color-primary) 13%, rgb(255 255 255 / 80%));
  --chat-divider: color-mix(in srgb, var(--el-color-primary) 16%, transparent);
  --chat-divider-soft: color-mix(in srgb, var(--fa-brand-cyan) 9%, transparent);

  flex: 1;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgb(255 255 255 / 90%), rgb(255 255 255 / 96%)) padding-box,
    var(--fa-gradient-border) border-box;
  border: 1px solid transparent;
  border-radius: 12px;
  box-shadow:
    0 16px 36px rgb(37 99 235 / 8%),
    0 0 0 1px var(--chat-shell-outline) inset,
    0 1px 0 rgb(255 255 255 / 72%) inset;

  .sidebar-container {
    position: relative;
    width: 200px;
    background:
      linear-gradient(180deg, rgb(255 255 255 / 74%), rgb(255 255 255 / 56%)),
      linear-gradient(
        180deg,
        color-mix(in srgb, var(--el-color-primary-light-9) 84%, white),
        color-mix(in srgb, var(--fa-brand-cyan) 7%, transparent)
      );
    transition: width 0.3s ease;

    &::after {
      position: absolute;
      top: 14px;
      right: 0;
      bottom: 14px;
      width: 1px;
      content: "";
      background: linear-gradient(
        180deg,
        transparent,
        var(--chat-divider),
        var(--chat-divider-soft),
        transparent
      );
      opacity: 0.86;
      pointer-events: none;
    }

    &.collapsed {
      width: 64px;
    }
  }

  .chat-container {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
  }

  .chat-header {
    height: auto;
    padding: 0;
  }

  .chat-main {
    display: flex;
    flex: 1;
    min-height: 0;
    padding: 0;
  }

  .chat-footer {
    height: auto;
    padding: 0;
    background: transparent;
  }
}
</style>
