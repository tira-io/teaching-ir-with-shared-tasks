<template>
  <v-card v-if="loading" flat class="my-5">
    <v-progress-linear color="red" indeterminate :height="9"></v-progress-linear>
  </v-card>
</template>

<script lang="ts">
  export default {
    name: "loading",
    props: ['loading'],
  }
</script>
