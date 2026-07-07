<!-- 参数配置 -->
<template>
  <FaDrawer
    v-model="drawerVisible"
    title="AI 模型选项"
    :size="drawerSize"
    drawer-class="config-info-drawer"
    destroy-on-close
  >
    <div class="config-drawer-content">
      <ElTabs model-value="aiModel" type="border-card" class="config-tabs">
        <ElTabPane label="AI 模型" name="aiModel">
          <div class="config-panel-wrap">
            <FaAiModelConfigPanel />
          </div>
        </ElTabPane>
      </ElTabs>
    </div>
    <template #footer>
      <ElButton @click="handleCloseDialog">关闭</ElButton>
    </template>
  </FaDrawer>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import FaAiModelConfigPanel from "@/views/module_ai/chat/components/FaAiModelConfigPanel.vue";

defineOptions({ name: "FaConfigInfoDrawer" });

const drawerSize = "60%";

interface Props {
  modelValue: boolean;
}

const props = withDefaults(defineProps<Props>(), {});

interface Emits {
  (e: "update:modelValue", value: boolean): void;
}

const emit = defineEmits<Emits>();
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit("update:modelValue", val),
});

function handleCloseDialog() {
  drawerVisible.value = false;
}
</script>

<style lang="scss" scoped>
.config-drawer-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.config-tabs {
  display: flex;
  flex: 1;
  min-height: 0;
}

.config-panel-wrap {
  height: 100%;
  min-height: 0;
}

:deep(.config-info-drawer .el-drawer__body) {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

:deep(.config-tabs.el-tabs--border-card) {
  height: 100%;
}

:deep(.config-tabs .el-tabs__header) {
  flex-shrink: 0;
}

:deep(.config-tabs .el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

:deep(.config-tabs .el-tab-pane) {
  height: 100%;
}
</style>
