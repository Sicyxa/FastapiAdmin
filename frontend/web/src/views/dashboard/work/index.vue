<template>
  <div class="workplace-page relative last:mb-0">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="workplace-hero">
        <div class="brand-heading">
          <div class="brand-mark">
            <FaSvgIcon icon="ri:shield-star-line" />
          </div>
          <h1>智能内容工作台</h1>
        </div>
        <p>文档、PPT、检索与校对集中处理，让日常材料生产更高效。</p>

        <div class="workbench-chat-entry">
          <FaChatInput :show-hint="false" @send="submitPrompt" />
        </div>
      </section>

      <section class="workplace-section">
        <div class="section-header">
          <h2>写长文神器</h2>
        </div>

        <div class="feature-grid">
          <article
            v-for="item in writingTools"
            :key="item.title"
            class="feature-card fa-card"
            :class="{ 'is-featured': item.featured }"
          >
            <div class="feature-card__top">
              <div class="feature-icon">
                <FaSvgIcon :icon="item.icon" />
              </div>
              <span v-if="item.badge" class="feature-badge">{{ item.badge }}</span>
            </div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>

            <div v-if="item.featured" class="document-preview">
              <div class="preview-paper">
                <span></span>
                <strong>根据主题一键长文写作</strong>
                <p></p>
                <p></p>
                <p></p>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="workplace-section">
        <div class="section-header">
          <h2>AI 工具箱</h2>
        </div>

        <div class="tool-grid">
          <article v-for="item in aiTools" :key="item.title" class="tool-card fa-card">
            <div class="tool-card__top">
              <FaSvgIcon :icon="item.icon" />
              <span v-if="item.badge">{{ item.badge }}</span>
            </div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";
import FaChatInput from "@/views/module_ai/chat/components/FaChatInput.vue";
import { savePendingChatPrompt } from "@/views/module_ai/chat/pendingPrompt";
import type { UploadedFile } from "@/views/module_ai/chat/types";

defineOptions({ name: "DashboardWorkbench" });

interface ToolItem {
  title: string;
  description: string;
  icon: string;
  badge?: string;
  featured?: boolean;
}

const loading = ref(true);
const router = useRouter();

const writingTools: ToolItem[] = [
  {
    title: "长文写作",
    description: "论文、文献综述、课题报告等",
    icon: "ri:edit-2-line",
    featured: true,
  },
  {
    title: "智能 PPT",
    description: "一句话生成 PPT，多风格可选",
    icon: "ri:slideshow-3-line",
    badge: "热门",
  },
  {
    title: "AI 内容检测",
    description: "文本检测、改写降重、AI 率识别",
    icon: "ri:file-search-line",
    badge: "上新",
  },
  {
    title: "校正润色",
    description: "纠错、写作建议一键获取",
    icon: "ri:spell-check-2",
  },
  {
    title: "学术搜索",
    description: "亿级专业资料库",
    icon: "ri:search-eye-line",
  },
  {
    title: "文档总结",
    description: "迅速总结要点",
    icon: "ri:list-check-3",
  },
  {
    title: "制作图表",
    description: "新增思维导图、流程图等类型",
    icon: "ri:bar-chart-grouped-line",
  },
  {
    title: "格式整理",
    description: "文档格式快捷调整",
    icon: "ri:article-line",
  },
  {
    title: "查重",
    description: "权威机构服务",
    icon: "ri:file-shield-2-line",
  },
];

const aiTools: ToolItem[] = [
  {
    title: "多文档合并",
    description: "总结合并多篇文档",
    icon: "ri:file-copy-2-line",
  },
  {
    title: "AI 思维导图",
    description: "助你发散工作思路",
    icon: "ri:mind-map",
    badge: "上线中",
  },
  {
    title: "AI 漫画",
    description: "智能辅助生成漫画",
    icon: "ri:layout-grid-line",
    badge: "上线中",
  },
  {
    title: "AI 有声画本",
    description: "一句话生成有声画本",
    icon: "ri:magic-line",
    badge: "上线中",
  },
  {
    title: "AI 写小红书",
    description: "一键生成爆款文案",
    icon: "ri:booklet-line",
    badge: "上线中",
  },
];

function submitPrompt(message: string, files?: UploadedFile[]): void {
  const content = message.trim();
  const hasFiles = Boolean(files?.length);
  if (!content && !hasFiles) return;

  savePendingChatPrompt(content || "请处理这些附件", files);
  router.push({ name: "DashboardAiAssistant" });
}

onMounted(() => {
  loading.value = false;
});
</script>

<style lang="scss" scoped>
.workplace-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-bottom: 8px;

  --work-card-shadow: 0 2px 6px rgb(15 23 42 / 6%), 0 14px 32px rgb(37 99 235 / 12%);
  --work-card-shadow-hover: 0 4px 10px rgb(15 23 42 / 8%), 0 20px 42px rgb(37 99 235 / 16%);
}

.workplace-hero {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  align-items: center;
  padding: 0;

  .brand-heading {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .brand-mark {
    display: flex;
    align-items: center;
    justify-content: center;
    width: clamp(52px, 4vw, 64px);
    height: clamp(52px, 4vw, 64px);
    font-size: clamp(28px, 2.3vw, 34px);
    color: var(--el-color-primary);
    background: var(--default-box-color);
    border: 1px solid var(--fa-card-border);
    border-radius: calc(var(--custom-radius) + 8px);
  }

  h1 {
    margin: 0;
    font-size: clamp(28px, 2.6vw, 34px);
    font-weight: 700;
    line-height: 1.2;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 6px 0 14px;
    font-size: clamp(15px, 1.4vw, 18px);
    color: var(--el-text-color-regular);
  }
}

.workbench-chat-entry {
  width: min(100%, 760px);

  :deep(.chat-input .input-wrapper) {
    max-width: none;
    padding: 0;
  }

  :deep(.chat-input .input-container) {
    min-height: 96px;
    padding: 16px 18px 12px;
    border-radius: 18px;
  }

  :deep(.chat-input .message-input .el-textarea__inner) {
    min-height: 62px !important;
  }
}

.workplace-section {
  display: flex;
  flex-direction: column;

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;

    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }
  }
}

.feature-grid,
.tool-grid {
  display: grid;
  gap: 14px;
}

.feature-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.tool-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.feature-card,
.tool-card {
  position: relative;
  min-height: 96px;
  padding: 14px 16px;
  overflow: hidden;
  cursor: pointer;
  background: var(--default-box-color);
  box-shadow: var(--work-card-shadow) !important;
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    transform 0.2s;

  &:hover {
    border-color: var(--el-color-primary-light-5) !important;
    box-shadow: var(--work-card-shadow-hover) !important;
    transform: translateY(-2px);
  }

  h3 {
    margin: 8px 0 6px;
    font-size: 15px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
    color: var(--el-text-color-secondary);
  }
}

.feature-card__top,
.tool-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.feature-icon,
.tool-card__top > .fa-svg-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.feature-badge,
.tool-card__top span {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  font-size: 12px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 0 0 0 calc(var(--custom-radius) + 2px);
}

.feature-card.is-featured {
  grid-row: span 2;
  min-height: 206px;
}

.document-preview {
  position: absolute;
  right: -10px;
  bottom: -12px;
  width: 138px;
  height: 98px;
  padding: 8px 0 0 8px;
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  border-radius: calc(var(--custom-radius) + 6px) 0 0;
}

.preview-paper {
  width: 116px;
  height: 90px;
  padding: 10px;
  background: var(--default-box-color);
  border: 1px solid var(--fa-card-border);
  border-radius: calc(var(--custom-radius) + 2px);
  box-shadow: 0 12px 28px rgb(0 0 0 / 8%);

  span {
    display: block;
    width: 58px;
    height: 5px;
    margin-bottom: 10px;
    background: var(--el-color-primary-light-5);
    border-radius: 999px;
  }

  strong {
    display: block;
    margin-bottom: 6px;
    font-size: 11px;
    line-height: 1.4;
    color: var(--el-text-color-primary);
  }

  p {
    width: 100%;
    height: 4px;
    margin: 6px 0 0;
    background: var(--el-fill-color);
    border-radius: 999px;

    &:last-child {
      width: 68%;
    }
  }
}

@media screen and (width <= 1200px) {
  .feature-grid,
  .tool-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media screen and (width <= 768px) {
  .workplace-hero {
    align-items: stretch;

    .brand-heading {
      align-self: center;
    }

    h1,
    > p {
      text-align: center;
    }

    h1 {
      font-size: 28px;
    }

    > p {
      font-size: 15px;
    }
  }

  .workbench-chat-entry {
    width: 100%;
  }

  .feature-grid,
  .tool-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media screen and (width <= 520px) {
  .feature-grid,
  .tool-grid {
    grid-template-columns: 1fr;
  }

  .feature-card.is-featured {
    grid-row: auto;
  }
}
</style>
