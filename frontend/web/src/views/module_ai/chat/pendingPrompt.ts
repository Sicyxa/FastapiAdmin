import type { UploadedFile } from "./types";

const PENDING_CHAT_PROMPT_KEY = "fastapiadmin:ai-chat:pending-prompt";
const PENDING_CHAT_PROMPT_TTL = 5 * 60 * 1000;

export interface PendingChatPrompt {
  message: string;
  createdAt: number;
  files?: UploadedFile[];
}

let pendingPromptMemory: PendingChatPrompt | null = null;

export function savePendingChatPrompt(message: string, files?: UploadedFile[]): void {
  const payload: PendingChatPrompt = {
    message: message.trim(),
    createdAt: Date.now(),
    files,
  };

  pendingPromptMemory = payload;
  sessionStorage.setItem(
    PENDING_CHAT_PROMPT_KEY,
    JSON.stringify({
      message: payload.message,
      createdAt: payload.createdAt,
    })
  );
}

export function readPendingChatPrompt(): PendingChatPrompt | null {
  if (pendingPromptMemory && !isExpired(pendingPromptMemory)) {
    return pendingPromptMemory;
  }

  const raw = sessionStorage.getItem(PENDING_CHAT_PROMPT_KEY);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as PendingChatPrompt;

    if (isExpired(payload) || !payload.message?.trim()) {
      clearPendingChatPrompt();
      return null;
    }

    return {
      message: payload.message.trim(),
      createdAt: payload.createdAt,
    };
  } catch {
    clearPendingChatPrompt();
    return null;
  }
}

export function clearPendingChatPrompt(): void {
  pendingPromptMemory = null;
  sessionStorage.removeItem(PENDING_CHAT_PROMPT_KEY);
}

function isExpired(payload: PendingChatPrompt): boolean {
  return Date.now() - payload.createdAt > PENDING_CHAT_PROMPT_TTL;
}
