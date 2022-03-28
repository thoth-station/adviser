---
name: Deliver Container Image
about: build a git tag and push it as a container image to quay
title: Deliver Container Image
assignees: sesheta
labels: "bot, priority/critical-urgent"
---

Hey, AICoE-CI!

Please build and deliver the following git tag:

Tag: x.y.z


**IMPORTANT NOTES**

- _If the tag exists and [AICoE CI GitHub App](https://github.com/apps/aicoe-ci) is installed, this issue will retrigger the pipeline to build from tag and push image container image. It should be used if the pipeline triggered with the {major|minor|patch} release failed for any reason._
