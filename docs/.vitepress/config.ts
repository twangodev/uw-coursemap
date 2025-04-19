import { defineConfig } from 'vitepress'
import {withSidebar} from "vitepress-sidebar";
import type {VitePressSidebarOptions} from "vitepress-sidebar/types";

const vitePressSidebarOptions: VitePressSidebarOptions  = {
  documentRootPath: '/docs',
  collapsed: false,
  capitalizeFirst: true,
  capitalizeEachWords: true,
  hyphenToSpace: true,
  useTitleFromFileHeading: true,
  useFolderTitleFromIndexFile: true,
};

const vitePressOptions = {
  title: "uw-coursemap",
  description: "Explore the courses offered by the UW-Madison in a visual and interactive way.",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ]
  }
}

export default defineConfig(withSidebar(vitePressOptions, vitePressSidebarOptions));