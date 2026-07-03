<template>
  <div class="fa-full-height">
    <ElContainer class="main-chat">
      <ElAside class="sidebar-container" :class="{ collapsed: isSidebarCollapsed }">
        <FaSidebar
          ref="sidebarRef"
          :current-session-id="currentSessionId"
          :is-collapsed="isSidebarCollapsed"
          @select-session="handleSelectSession"
          @new-session="handleNewSession"
          @open-config="configDrawerVisible = true"
        />
      </ElAside>
      <ElContainer class="chat-container">
        <ElHeader class="chat-header">
          <FaChatNavbar
            :message-count="messages.length"
            :is-sidebar-collapsed="isSidebarCollapsed"
            @clear-chat="handleClearChat"
            @toggle-sidebar="toggleSidebar"
          />
        </ElHeader>
        <ElMain class="chat-main">
          <FaChatMessages
            ref="chatMessagesRef"
            :messages="messages"
            :error="error"
            @prompt-click="handleSendMessage"
            @error-close="error = ''"
          />
        </ElMain>
        <ElFooter class="chat-footer">
          <FaChatInput :sending="sending" @send="handleSendMessage" @stop="handleStopMessage" />
        </ElFooter>
      </ElContainer>
    </ElContainer>

    <FaConfigInfoDrawer v-model="configDrawerVisible" />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "Chat",
  inheritAttrs: false,
});

import { ref, onMounted, onUnmounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import AiChatAPI, { ChatSession } from "@/api/module_ai/chat";
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

// 状态
const messages = ref<ChatMessage[]>([]);
const sending = ref(false);
const isConnected = ref(true);
const error = ref("");
const currentSessionId = ref<string | null>(null);
const isSidebarCollapsed = ref(false);
const configDrawerVisible = ref(false);
const pendingInitialPrompt = ref<PendingChatPrompt | null>(null);

// Refs
const chatMessagesRef = ref<{ scrollToBottom: () => void }>();
const sidebarRef = ref<{ loadSessions: () => void }>();

// WebSocket
let ws: WebSocket | null = null;
let isUnmounting = false;
let connectionPromptVisible = false;
let pendingPromptSending = false;
const WS_URL = import.meta.env.VITE_APP_WS_ENDPOINT;
// ============ WebSocket 操作 ============
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

// ============ 消息处理 ============
const handleWebSocketMessage = (data: string) => {
  const text = data || "";

  // 服务端结束标记
  if (text === "[DONE]") {
    finishLoadingMessages();
    sending.value = false;
    return;
  }

  // 服务端停止确认标记
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
    collapsed: content.length > 200,
    files,
    loading: type === "assistant" ? true : false,
  });
};

const finishLoadingMessages = () => {
  messages.value.forEach((msg) => {
    if (msg.type === "assistant" && msg.loading) {
      msg.loading = false;
      msg.collapsed = msg.content.length > 200;
    }
  });
};

const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
};

// ============ 发送消息 ============
const handleSendMessage = async (message: string, files?: UploadedFile[]): Promise<boolean> => {
  if ((!message && !files) || sending.value) return false;
  if (!isConnected.value || ws?.readyState !== WebSocket.OPEN) {
    handleDisconnected();
    return false;
  }

  // 结束上一个加载中的消息
  finishLoadingMessages();

  // 创建新会话（如果没有）
  if (!currentSessionId.value) {
    const success = await createNewSession(message);
    if (!success) return false;
  }

  // 添加用户消息
  addMessage("user", message, files);

  // 添加加载中的助手消息
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
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          message,
          session_id: currentSessionId.value,
          files: files?.map((f) => ({ name: f.name, type: f.type, size: f.size })),
        })
      );
      // 注意：sending 状态保持为 true，等待 [DONE] / [STOPPED] 标记清除
      return true;
    } else {
      throw new Error("WebSocket 连接未建立");
    }
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

// 停止当前生成
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

// ============ 会话操作 ============
const handleSelectSession = async (session: ChatSession) => {
  currentSessionId.value = session.id;
  messages.value = [];

  try {
    const response = await AiChatAPI.getSessionDetail(session.id);
    if (response.data?.code !== 0) {
      return;
    }

    const sessionData = response.data.data || {};
    const runs = sessionData.runs || [];

    runs.forEach((run: any) => {
      const runMessages = run.messages || [];
      runMessages.forEach((msg: any) => {
        if (msg.role === "user" || msg.role === "assistant") {
          addMessage(msg.role, msg.content);
        }
      });
    });

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

// ============ 生命周期 ============
onMounted(() => {
  pendingInitialPrompt.value = readPendingChatPrompt();
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

  /* 与右侧同一表面色；与内容区的分界交给 Sidebar 的竖线即可 */
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
    height: 100%;
    overflow: hidden;
  }

  .chat-header {
    position: relative;
    height: auto;
    padding: 0;
    background:
      linear-gradient(90deg, rgb(255 255 255 / 80%), rgb(255 255 255 / 66%)),
      linear-gradient(
        90deg,
        color-mix(in srgb, var(--el-color-primary-light-9) 84%, white),
        color-mix(in srgb, var(--fa-brand-cyan) 6%, transparent)
      );

    &::after {
      position: absolute;
      right: 18px;
      bottom: 0;
      left: 18px;
      height: 1px;
      content: "";
      background: linear-gradient(
        90deg,
        transparent,
        var(--chat-divider),
        var(--chat-divider-soft),
        transparent
      );
      opacity: 0.88;
      pointer-events: none;
    }
  }

  .chat-main {
    flex: 1;
    overflow: hidden;
    background:
      linear-gradient(180deg, rgb(255 255 255 / 60%), rgb(255 255 255 / 82%)),
      var(--fa-surface-tint);
  }

  .chat-footer {
    position: relative;
    height: auto;
    min-height: 80px;
    padding: 0;
    background:
      linear-gradient(90deg, rgb(255 255 255 / 84%), rgb(255 255 255 / 70%)),
      linear-gradient(
        90deg,
        color-mix(in srgb, var(--el-color-primary-light-9) 82%, white),
        color-mix(in srgb, var(--fa-brand-cyan) 6%, transparent)
      );

    &::before {
      position: absolute;
      top: 0;
      right: 18px;
      left: 18px;
      height: 1px;
      content: "";
      background: linear-gradient(
        90deg,
        transparent,
        var(--chat-divider),
        var(--chat-divider-soft),
        transparent
      );
      opacity: 0.88;
      pointer-events: none;
    }
  }
}

html.dark .main-chat {
  background:
    linear-gradient(180deg, rgb(23 26 33 / 90%), rgb(18 20 26 / 96%)) padding-box,
    var(--fa-gradient-border) border-box;

  .sidebar-container,
  .chat-header,
  .chat-footer,
  .chat-main {
    background: var(--el-bg-color-overlay);
  }
}
</style>
