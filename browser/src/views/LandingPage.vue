<template>
    <v-container class="text-center">
      <v-img class="mx-auto" height="300px" max-width="100%" width="300px" src="https://temir.org/img/index-cover-modified.png"/>
      <section>
        <h1 class="text-h3 text-sm-h3 py-4">
          Teaching IR with Shared Tasks
        </h1>
        <p class="mx-auto py-4 tira-explanation">
        

This contains a set of resources to x y practical part of , 
ir_datasets and <a href="https://webis.de/publications.html?q=tira#froebe_2023e" target="_blank">TIREx</a>
links to previous iterations 
        </p>
        <v-row class="d-flex justify-center py-4">
          <v-col cols="auto">
            <v-btn color="primary" href="https://webis.de/publications.html?q=shared+task#elstner_2023" target="_blank"  min-width="228" rel="noopener noreferrer" size="x-large" variant="flat">
              <v-icon icon="mdi-speedometer" size="large" start/>
              Why
            </v-btn>
          </v-col>
          <v-col cols="auto text-primary">
            <v-btn href="https://www.tira.io/task-overview/ir-lab-jena-leipzig-wise-2023" target="_blank"  min-width="228"  rel="noopener noreferrer" size="x-large" variant="outlined">
              <v-icon size="large" start>
                <v-img src="https://www.tira.io/public/tira/frontend-vuetify/assets-public/logo.svg" />
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

    <p>modern technology research oriented tools and industry xy. Stuff like people will learn docker, devcontainer.</p>
  </template>
  
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