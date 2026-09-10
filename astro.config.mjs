import { defineConfig } from 'astro/config';

// GitHub Pages 部署：在 Actions 里通过 BASE_PATH 环境变量传入仓库名
// 本地开发/预览保持默认 '/' 即可
export default defineConfig({
  site: process.env.SITE_URL || 'https://example.github.io',
  base: process.env.BASE_PATH || '/',
});
