<!-- 按钮组件 -->
<template>
  <div
    class="fa-icon-button size-8.5 inline-flex items-center justify-center cursor-pointer text-g-600 dark:text-g-800 text-xl rounded transition duration-300 hover:bg-hover-color"
    :class="{ 'rounded-full': circle }"
  >
    <FaSvgIcon :icon="icon"></FaSvgIcon>
    <slot></slot>
  </div>
</template>

<script lang="ts" setup>
defineOptions({ name: "FaIconButton" });

interface Props {
  /** 图标名称 */
  icon: string;
  /** 圆角按钮 */
  circle?: boolean;
}

withDefaults(defineProps<Props>(), {});
</script>

<style lang="scss" scoped>
.fa-icon-button {
  border: 1px solid transparent;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;

  &:hover {
    color: var(--el-color-primary);
    background:
      linear-gradient(var(--fa-surface-elevated), var(--fa-surface-elevated)) padding-box,
      var(--fa-gradient-border) border-box !important;
    border-color: transparent;
    box-shadow: 0 8px 18px rgb(37 99 235 / 12%);
    transform: translateY(-1px);
  }

  &:hover :deep(.fa-svg-icon) {
    color: var(--el-color-primary);
  }
}
</style>
