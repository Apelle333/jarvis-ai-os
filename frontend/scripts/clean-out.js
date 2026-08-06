const fs = require('fs');
const path = require('path');

const frontendRoot = path.resolve(__dirname, '..');
const outDir = path.join(frontendRoot, 'out');

if (fs.existsSync(outDir)) {
  fs.rmSync(outDir, { recursive: true, force: true });
}

