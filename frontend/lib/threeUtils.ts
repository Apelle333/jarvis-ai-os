'use client';

import * as THREE from 'three';
import { useMemo } from 'react';

export function createGlowTexture(
  color = 'rgba(34, 211, 238, 1)',
  size = 256
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  const gradient = ctx.createRadialGradient(
    size / 2,
    size / 2,
    0,
    size / 2,
    size / 2,
    size / 2
  );
  gradient.addColorStop(0, color);
  gradient.addColorStop(0.25, color.replace('1)', '0.35)'));
  gradient.addColorStop(1, color.replace('1)', '0)'));
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

export function useGlowTexture(
  color = 'rgba(34, 211, 238, 1)',
  size = 256
): THREE.CanvasTexture {
  return useMemo(() => createGlowTexture(color, size), [color, size]);
}

export const damp = THREE.MathUtils.damp;
