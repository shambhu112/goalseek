import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const workflowSteps = [
  {
    label: 'Baseline',
    copy: 'Measure the current project without changing code and capture the retained metric.',
  },
  {
    label: 'Iterate',
    copy: 'Plan, apply, verify, and commit one focused change per loop iteration.',
  },
  {
    label: 'Keep or Revert',
    copy: 'Promote improvements and automatically roll back regressions with git-backed auditability.',
  },
];

const featureList = [
  {
    title: 'Git-backed',
    copy: 'Every candidate change becomes a real commit, and rejected changes are reverted with history intact.',
  },
  {
    title: 'Local-first',
    copy: 'Projects, manifests, logs, and experiment artifacts stay on disk in a layout you can inspect and version.',
  },
  {
    title: 'Provider-agnostic',
    copy: 'Swap between Codex, Claude Code, Gemini, OpenCode, or a fake provider through a consistent loop engine.',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  const heroImage = useBaseUrl('/img/goal-seek.png');
  return (
    <header className={clsx(styles.heroBanner)}>
      <div className={clsx('container', styles.heroGrid)}>
        <div className={styles.heroCopy}>
          <div className={styles.eyebrow}>Python package</div>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <p className={styles.heroDetail}>
            goalseek orchestrates disciplined research loops for coding agents with manifests,
            mechanical verification, and a durable local artifact trail.
          </p>
          <div className={styles.buttons}>
            <Link
              className={clsx('button button--primary button--lg', styles.primaryButton)}
              to="/docs/getting-started/quickstart">
              Quickstart
            </Link>
            <Link
              className={clsx('button button--secondary button--lg', styles.secondaryButton)}
              to="/docs/architecture/system-architecture">
              Architecture
            </Link>
            <Link
              className={clsx('button button--secondary button--lg', styles.secondaryButton)}
              to="/docs/guides/kaggle-demo">
              Kaggle Demo
            </Link>
          </div>
        </div>
        <div className={styles.heroVisual}>
          <img
            className={styles.heroImage}
            src={heroImage}
            alt="goalseek experiment lifecycle overview"
          />
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description="Developer documentation for goalseek, a local-first research loop orchestrator for coding agents.">
      <HomepageHeader />
      <main>
        <section className={styles.band}>
          <div className="container">
            <div className={styles.sectionHeading}>
              <div className={styles.sectionLabel}>Workflow</div>
              <Heading as="h2" className={styles.sectionTitle}>
                The loop is simple on purpose
              </Heading>
            </div>
            <div className={styles.workflowGrid}>
              {workflowSteps.map((step) => (
                <article key={step.label} className={styles.workflowItem}>
                  <div className={styles.stepLabel}>{step.label}</div>
                  <p className={styles.stepCopy}>{step.copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className={clsx(styles.band, styles.bandMuted)}>
          <div className="container">
            <div className={styles.sectionHeading}>
              <div className={styles.sectionLabel}>Why it works</div>
              <Heading as="h2" className={styles.sectionTitle}>
                Built for inspection, not magic
              </Heading>
            </div>
            <div className={styles.featureGrid}>
              {featureList.map((feature) => (
                <article key={feature.title} className={styles.featureItem}>
                  <Heading as="h3" className={styles.featureTitle}>
                    {feature.title}
                  </Heading>
                  <p className={styles.featureCopy}>{feature.copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
