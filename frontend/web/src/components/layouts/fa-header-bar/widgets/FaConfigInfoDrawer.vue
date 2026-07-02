<!-- 参数配置 -->
<template>
  <FaDrawer v-model="drawerVisible" title="配置中心" :size="drawerSize" destroy-on-close>
    <ElTabs model-value="aiModel" type="border-card" class="config-tabs">
      <ElTabPane label="AI 模型" name="aiModel">
        <FaAiModelConfigPanel />
      </ElTabPane>
    </ElTabs>
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
.config-tabs {
  min-height: 100%;
}
</style>
