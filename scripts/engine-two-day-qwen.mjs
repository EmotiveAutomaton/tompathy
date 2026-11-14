// Own one dedicated service for one explicitly invoked counted benchmark.
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import path from 'node:path';
import { startFixedQwen } from './fixed-qwen-session.mjs';

const args = process.argv.slice(2);
if (!args.includes('--task') || !['edits', 'human-edits', 'goals', 'choice-goals'].includes(args[args.indexOf('--task') + 1])) {
  throw Error('Specify one commissioned judgment task');
}
const service = await startFixedQwen();
if (!service) throw Error('Exact dedicated CPU service unavailable');
try {
  const childArgs = [...args];
  if (!childArgs.includes('--task-args')) childArgs.push('--task-args');
  childArgs.push('--url', service.url);
  const child = spawn(path.resolve('engine/.venv/Scripts/python.exe'), ['-B', 'scripts/engine-two-day-job.py', ...childArgs], {
    windowsHide: true, stdio: 'inherit',
    env: { ...process.env, OMP_NUM_THREADS: '2', MKL_NUM_THREADS: '2', OPENBLAS_NUM_THREADS: '2', NUMEXPR_NUM_THREADS: '2', CUDA_VISIBLE_DEVICES: '-1' },
  });
  const [code] = await once(child, 'exit');
  process.exitCode = code ?? 1;
} finally {
  await service.stop();
}
