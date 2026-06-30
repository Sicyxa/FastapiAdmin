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

        <div class="prompt-panel fa-card">
          <ElInput
            v-model="promptText"
            type="textarea"
            resize="none"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="今天需要我做些什么？Shift + Enter 换行"
            class="prompt-input"
            @keyup.enter.exact="submitPrompt"
          />

          <div class="prompt-actions">
            <div class="model-list">
              <ElButton plain>
                <FaSvgIcon icon="ri:sparkling-2-line" />
                DeepSeek-R1 满血版
              </ElButton>
              <ElButton plain type="primary">
                <FaSvgIcon icon="ri:global-line" />
                联网搜索
              </ElButton>
            </div>
            <div class="tool-list">
              <FaIconButton icon="ri:box-3-line" />
              <FaIconButton icon="ri:upload-2-line" />
              <FaIconButton icon="ri:link-m" />
              <ElButton type="primary" class="send-btn" @click="submitPrompt">
                <FaSvgIcon icon="ri:send-plane-2-fill" />
              </ElButton>
            </div>
          </div>
        </div>

        <div class="prompt-tags">
          <button v-for="item in promptTags" :key="item" type="button" @click="usePrompt(item)">
            {{ item }}
          </button>
        </div>
      </section>

      <section class="workplace-section">
        <div class="section-header">
          <h2>写长文神器</h2>
          <ElButton text type="primary">
            查看全部
            <FaSvgIcon icon="ri:arrow-right-s-line" />
          </ElButton>
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
          <ElButton text type="primary">
            管理工具
            <FaSvgIcon icon="ri:settings-3-line" />
          </ElButton>
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
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";

defineOptions({ name: "DashboardWorkbench" });

interface ToolItem {
  title: string;
  description: string;
  icon: string;
  badge?: string;
  featured?: boolean;
}

const loading = ref(true);
const promptText = ref("");

const promptTags = [
  "做一个PPT分析人工智能的价值",
  "一文深究AI能否实现解码人类思想",
  "高校教育与文旅融合的相关文献资料",
  "以中国式现代化的出发点为主题的开题报告",
  "安史之乱为什么会发生？",
  "做一个分析生育率走低原因的PPT",
  "高铁座位为什么没有 E？",
  "图解近五年两会热门议题",
  "研究民营企业的发展方向",
];

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

function usePrompt(text: string): void {
  promptText.value = text;
}

function submitPrompt(): void {
  if (!promptText.value.trim()) {
    return;
  }
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
}

.workplace-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 0 0;

  .brand-heading {
    display: flex;
    gap: 14px;
    align-items: center;
  }

  .brand-mark {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    font-size: 34px;
    color: var(--el-color-primary);
    background: var(--default-box-color);
    border: 1px solid var(--fa-card-border);
    border-radius: calc(var(--custom-radius) + 10px);
  }

  h1 {
    margin: 0;
    font-size: 34px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 10px 0 26px;
    font-size: 18px;
    color: var(--el-text-color-regular);
  }
}

.prompt-panel {
  width: min(100%, 1120px);
  padding: 16px;
  background: var(--default-box-color);
}

.prompt-input {
  :deep(.el-textarea__inner) {
    min-height: 52px !important;
    padding: 0;
    color: var(--el-text-color-primary);
    background: transparent;
    border: 0;
    box-shadow: none;
  }
}

.prompt-actions {
  display: flex;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.model-list,
.tool-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.send-btn {
  width: 40px;
  padding: 0;
  font-size: 18px;
}

.prompt-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  width: min(100%, 1000px);
  margin-top: 16px;

  button {
    height: 34px;
    padding: 0 16px;
    font-size: 13px;
    color: var(--el-text-color-primary);
    cursor: pointer;
    background: var(--default-box-color);
    border: 1px solid transparent;
    border-radius: calc(var(--custom-radius) + 2px);
    transition: all 0.2s;

    &:hover {
      color: var(--el-color-primary);
      border-color: var(--el-color-primary-light-5);
      transform: translateY(-1px);
    }
  }
}

.workplace-section {
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }
  }
}

.feature-grid,
.tool-grid {
  display: grid;
  gap: 16px;
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
  min-height: 128px;
  padding: 18px 20px;
  overflow: hidden;
  cursor: pointer;
  background: var(--default-box-color);
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    transform 0.2s;

  &:hover {
    border-color: var(--el-color-primary-light-5) !important;
    box-shadow: 0 10px 24px rgb(0 0 0 / 6%);
    transform: translateY(-2px);
  }

  h3 {
    margin: 10px 0 8px;
    font-size: 16px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
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
  min-height: 268px;
}

.document-preview {
  position: absolute;
  right: -16px;
  bottom: -20px;
  width: 170px;
  height: 126px;
  padding: 12px 0 0 12px;
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  border-radius: calc(var(--custom-radius) + 8px) 0 0 0;
}

.preview-paper {
  width: 140px;
  height: 116px;
  padding: 14px;
  background: var(--default-box-color);
  border: 1px solid var(--fa-card-border);
  border-radius: calc(var(--custom-radius) + 2px);
  box-shadow: 0 12px 28px rgb(0 0 0 / 8%);

  span {
    display: block;
    width: 64px;
    height: 6px;
    margin-bottom: 12px;
    background: var(--el-color-primary-light-5);
    border-radius: 999px;
  }

  strong {
    display: block;
    margin-bottom: 10px;
    font-size: 12px;
    line-height: 1.4;
    color: var(--el-text-color-primary);
  }

  p {
    width: 100%;
    height: 5px;
    margin: 7px 0 0;
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

  .prompt-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .tool-list {
    justify-content: flex-end;
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
