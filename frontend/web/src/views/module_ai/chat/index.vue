<template>
  <ChatWorkspace mode="admin" />
</template>

<script setup lang="ts">
defineOptions({
  name: "ChatAdminPage",
  inheritAttrs: false,
});

import ChatWorkspace from "./ChatWorkspace.vue";
</script>
