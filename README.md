<div align="center">
  <h1>uw-coursemap</h1>
  <p>
    <strong>Course exploration, made easy</strong></p>
  <div>
    <img src=".github/assets/course.png" alt="Preview" width="80%"/>
  </div>
</div>

<p align="center">
  <a href="https://github.com/twangodev/uw-coursemap/actions/workflows/node.js.yml" target="_blank"><img alt="Node.js CI" src="https://github.com/twangodev/uw-coursemap/actions/workflows/node.js.yml/badge.svg"></a>
  <a href="https://cheesehacks.webdevuw.com/" target="_blank"><img alt="Cheesehacks 2024" src="https://img.shields.io/badge/Cheesehacks-2024-fec732"/></a>
  <a href="https://cern-ohl.web.cern.ch/"><img alt="GitHub License" src="https://img.shields.io/github/license/twangodev/uw-coursemap"/></a>
  <img alt="Repository Size" src="https://img.shields.io/github/repo-size/twangodev/uw-coursemap"/>
</p>

<p align="center">
  Explore the courses offered by <a href="https://wisc.edu" target="_blank">UW-Madison</a> in a visual and interactive way.
</p>

## About

This project provides a comprehensive view of course information at the University of Wisconsin-Madison, utilizing a requirement Directed Acyclic Graph (DAG) to visualize course dependencies. The tool also offers historical grade distributions, professor ratings, and insights from Rate My Professor (RMP) comments to help students make informed decisions about their coursework.

> This project won 4th place at [Cheesehacks 2024](https://cheesehacks.webdevuw.com/) and is not affiliated with the University of Wisconsin-Madison.

### Features

- Course Requirement DAG: Displays course prerequisites and dependencies in a visual format.
- Historical Grade Distributions: Cumulative grade distributions for each course.
- Professor Ratings: Integrates data from Rate My Professor to show professor ratings and comments.
- Search Functionality: Easily search for courses, professors, and departments.

### Tech Stack
- **Frontend**: Svelte, shadcn-svelte, Tailwind CSS
- **Backend**: Python, NGINX (TODO, currently using GitHub CDN)


