import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      items: ['getting-started/quickstart'],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/baseline-and-iterations',
        'guides/kaggle-demo',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture/system-architecture',
        'architecture/loop-engine-phases',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/cli-and-api',
        'reference/manifest-and-project-layout',
      ],
    },
    {
      type: 'category',
      label: 'Maintainers',
      items: ['maintainers/design-notes'],
    },
  ],
};

export default sidebars;
