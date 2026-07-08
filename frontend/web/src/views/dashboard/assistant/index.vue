<template>
  <ChatWorkspace mode="user" />
</template>

<script setup lang="ts">
defineOptions({
  name: "DashboardAssistantPage",
  inheritAttrs: false,
});

import ChatWorkspace from "@/views/module_ai/chat/ChatWorkspace.vue";
</script>
