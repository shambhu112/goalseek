import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'goalseek',
  tagline: 'Local-first, git-backed research loops for coding agents.',
  favicon: 'img/favicon.ico',
  future: {
    v4: true,
  },
  url: 'https://shambhu112.github.io',
  baseUrl: '/goalseek/',
  organizationName: 'shambhu112',
  projectName: 'goalseek',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,
  onBrokenLinks: 'throw',
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  themes: ['@docusaurus/theme-mermaid'],
  markdown: {
    mermaid: true,
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/shambhu112/goalseek/tree/main/docs-site/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/goal-seek.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'goalseek',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/getting-started/quickstart',
          label: 'Quickstart',
          position: 'left',
        },
        {
          to: '/docs/guides/kaggle-demo',
          label: 'Examples',
          position: 'left',
        },
        {
          to: '/docs/architecture/system-architecture',
          label: 'Architecture',
          position: 'left',
        },
        {
          to: '/docs/reference/cli-and-api',
          label: 'API & CLI',
          position: 'left',
        },
        {
          href: 'https://github.com/shambhu112/goalseek',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Overview',
              to: '/docs/intro',
            },
            {
              label: 'Quickstart',
              to: '/docs/getting-started/quickstart',
            },
          ],
        },
        {
          title: 'Architecture',
          items: [
            {
              label: 'System Architecture',
              to: '/docs/architecture/system-architecture',
            },
            {
              label: 'Loop Engine Phases',
              to: '/docs/architecture/loop-engine-phases',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/shambhu112/goalseek',
            },
            {
              label: 'Documentation Source',
              href: 'https://github.com/shambhu112/goalseek/tree/main/docs-site',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} goalseek contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.vsDark,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
