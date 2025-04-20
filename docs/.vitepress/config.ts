import {defineConfig, type UserConfig} from 'vitepress'

const vitePressOptions: UserConfig = {
  lang: 'en-US',
  title: "uw-coursemap",
  description: "Explore the courses offered by the UW-Madison in a visual and interactive way.",
  themeConfig: {
    logo: 'https://uwcourses.com/uw-coursemap-logo.svg',
    siteTitle: 'UW Course Map',
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      {
        text: 'Home',
        link: '/'
      },
      {
        text: 'About',
        link: '/about'
      },
      {
        text: 'Live',
        link: 'https://uwcourses.com'
      },
    ],
    sidebar: [
      {
        text: 'Getting Started',
        items: [
          {
            text: 'About',
            link: '/about'
          },
          {
            text: 'Quickstart',
            link: '/getting-started/quickstart'
          },
          {
            text: 'Technical Writeup',
            link: '/getting-started/technical-writeup'
          }
        ]
      },
      {
        text: 'Concepts',
        items: [
          {
            text: 'Data Model',
            link: '/concepts/data-model'
          },
          {
            text: 'Architecture',
            link: '/concepts/architecture'
          }
        ]
      },
      {
        text: 'Codebase',
        items: [
          {
            text: 'Frontend',
            link: '/codebase/frontend'
          },
          {
            text: 'Backend',
            link: '/codebase/backend'
          },
          {
            text: 'Generation',
            link: '/codebase/generation'
          }
        ]
      },
      {
        text: 'Contributing',
        link: '/contributing'
      },
      {
        text: 'Team',
        link: '/team'
      },
      {
        text: 'Branding',
        link: '/branding'
      },
      {
        text: 'Advanced',
        link: '/advanced'
      }
    ],
    search: {
      provider: 'local'
    },
    socialLinks: [
      {
        icon: 'github',
        link: 'https://github.com/twangodev/uw-coursemap'
      }
    ],
    editLink: {
      pattern: 'https://github.com/twangodev/uw-coursemap/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },
    footer: {
      message: "UW Course Map is not affiliated with the University of Wisconsin-Madison.",
      copyright: `&copy; ${new Date().getFullYear()} James Ding`
    }
  },
  lastUpdated: true,
  sitemap: {
    hostname: 'https://docs.uwcourses.com'
  },
}

export default defineConfig(vitePressOptions);