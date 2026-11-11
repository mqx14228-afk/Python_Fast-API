<!-- setup Vue3 语法糖 不用注册组件 不用 export default 直接在模板中使用 -->
<!-- composition API 组合式 API -->
<script setup lang="ts">
import FileUploader from "./components/FileUploader.vue";
</script>

<template>
  <div class="min-h-screen bg-gray-50 px-4 py-10">
    <FileUploader />
  </div>
</template>
