import { cloudflare } from '@cloudflare/vite-plugin';
import { readFileSync, mkdirSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import type { PluginOption } from 'vite';

/**
 * Checkout-local Sites adapter. The cloud skill's vendored adapter is not
 * available in this executor, so use the documented Cloudflare integration
 * and retain the Site identity in the deployment artifact.
 *
 * Runtime secrets are never read into the Vite configuration or client build.
 */
export function sites(): PluginOption {
  const root = process.cwd();
  const manifestPath = path.join(root, '.openai/hosting.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (typeof manifest.project_id !== 'string' || !manifest.project_id) {
    throw new Error('The Site project_id is missing from .openai/hosting.json.');
  }
  if (manifest.d1 || manifest.r2) {
    throw new Error('This client stores gameplay in the Mordor server; unused D1/R2 bindings must be null.');
  }
  return [
    cloudflare({
      config: {
        name: 'hollowdeep',
        main: path.join(root, 'worker/index.ts'),
        compatibility_date: '2026-05-15',
        compatibility_flags: ['nodejs_compat'],
        assets: { binding: 'ASSETS', not_found_handling: 'none' },
      },
      viteEnvironment: { name: 'rsc', childEnvironments: ['ssr'] },
      persistState: { path: path.join(root, '.wrangler/state') },
      remoteBindings: false,
      inspectorPort: false,
    }),
    {
      name: 'sites:hosting-manifest',
      apply: 'build',
      enforce: 'post',
      closeBundle() {
        const target = path.join(root, 'dist/.openai');
        mkdirSync(target, { recursive: true });
        copyFileSync(manifestPath, path.join(target, 'hosting.json'));
      },
    },
  ];
}
