<template>
    <v-container class="text-center">
      <v-img class="mx-auto" height="300px" max-width="100%" width="300px" src="https://temir.org/img/index-cover-modified.png"/>
      <section>
        <h1 class="text-h3 text-sm-h3 py-4">
          Teaching IR with Shared Tasks
        </h1>
        <p class="mx-auto py-4 tira-explanation">
        This page contains resources coupled to  <a href="https://arxiv.org/pdf/2103.02280.pdf" target="_blank">ir_datasets</a> and <a href="https://webis.de/publications.html?q=tira#froebe_2023e" target="_blank">TIREx</a> for brainstorming in IR courses that focus their hands-on labs on shared tasks (previously in  <a href="https://tira-io.github.io/ir-lab-sose-23/" target="_blank">summer 23</a>, <a href="https://tira-io.github.io/ir-lab-ws-23/" target="_blank">winter 23/24</a>, and <a href="https://tira-io.github.io/ir-lab-sose-24/" target="_blank">summer 24</a>).
        </p>
        <v-row class="d-flex justify-center py-4">
          <v-col cols="auto">
            <v-btn color="primary" href="https://webis.de/publications.html?q=shared+task#elstner_2023" target="_blank"  min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
              <v-icon icon="mdi-speedometer" size="large" start/>
              Why
            </v-btn>
          </v-col>
          <v-col cols="auto text-primary">
            <v-btn href="https://tira.io" target="_blank"  min-width="228"  rel="noopener noreferrer" size="x-large" variant="outlined">
              <v-icon size="large" start>
                <v-img src="../logo.svg" />
              </v-icon>
              TIRA
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn class="home-button" href="https://github.com/tira-io/teaching-ir-with-shared-tasks" target="_blank" min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
              <v-icon icon="mdi-github" size="large" start/>
              GitHub
            </v-btn>
          </v-col>
        </v-row>
      </section>
    </v-container>
    <component-overview />
  </template>

<script lang="ts">
import ComponentOverview from "@/components/ComponentOverview.vue";

export default {
  name: "landing-page",
  components: {ComponentOverview},
}
</script>

<style scoped>
  .tira-explanation {
    font-size: 1.25rem;
    font-weight: 300;
    max-width: 525px;
  }
  .home-button {
    color: #fff;
    background: #000;
  }
  .home-button:hover {
    color: #fff;
    background: #000;
  }
  .home-button:visited {
    color: #fff;
    background: #000;
  }
</style>
