import { cpSync, mkdirSync } from 'node:fs';

// 把数据复制到 public/data，供前端以 /data/*.json 拉取
mkdirSync('public/data', { recursive: true });
for (const f of ['papers.json', 'publications.json', 'meta.json', 'latest.json']) {
  try {
    cpSync(`data/${f}`, `public/data/${f}`);
  } catch (e) {
    console.warn(`[copy-data] 跳过 ${f}: ${e.message}`);
  }
}
console.log('[copy-data] data -> public/data 完成');
