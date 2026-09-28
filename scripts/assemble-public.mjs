import {cp,mkdir} from 'node:fs/promises';
// Keep the existing full application and its API available beside the public presentation.
await mkdir('site-dist/workbench',{recursive:true});
await cp('dist/index.html','site-dist/workbench/index.html');
await cp('dist/assets','site-dist/assets',{recursive:true});
console.log('Public presentation: / | Full workbench: /workbench/');
