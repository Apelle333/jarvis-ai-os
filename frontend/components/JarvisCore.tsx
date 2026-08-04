'use client';

import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import type { Group, Mesh, Sprite } from 'three';
import type { JarvisVisualState } from '@/lib/jarvisState';
import { STATE_COLOR } from '@/lib/jarvisState';
import { useGlowTexture } from '@/lib/threeUtils';

interface Props {
  state: JarvisVisualState;
}

const FRAGMENT = /* glsl */ `
  uniform vec3 uColor;
  uniform float uIntensity;
  varying vec3 vNormal;
  varying vec3 vViewPosition;
  void main() {
    vec3 viewDir = normalize(vViewPosition);
    float fresnel = pow(1.0 - abs(dot(vNormal, viewDir)), 3.0);
    gl_FragColor = vec4(uColor, fresnel * uIntensity);
  }
`;

const VERTEX = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vViewPosition;
  void main() {
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    vViewPosition = -mvPosition.xyz;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

/**
 * The central JARVIS AI core: a breathing, distorted energy orb wrapped in
 * additive fresnel shells, orbit rings and a radial glow. Every state changes
 * the energy signature (speed, distortion, brightness).
 */
export default function JarvisCore({ state }: Props) {
  const rootRef = useRef<Group>(null);
  const orbRef = useRef<Mesh>(null);
  const innerRef = useRef<Mesh>(null);
  const shellRef = useRef<Mesh>(null);
  const glowRef = useRef<Sprite>(null);
  const ring1Ref = useRef<Mesh>(null);
  const ring2Ref = useRef<Mesh>(null);
  const ring3Ref = useRef<Mesh>(null);
  const scanRef = useRef<Mesh>(null);

  const glowTexture = useGlowTexture('rgba(34, 211, 238, 1)', 256);

  // keep shell/ring colors in sync with the current state
  useEffect(() => {
    const c = new THREE.Color(STATE_COLOR[state]);
    if (shellRef.current) {
      (shellRef.current.material as THREE.ShaderMaterial).uniforms.uColor.value = c;
    }
    if (scanRef.current) {
      (scanRef.current.material as THREE.MeshBasicMaterial).color = c;
    }
    if (ring1Ref.current) {
      (ring1Ref.current.material as THREE.MeshBasicMaterial).color = c;
    }
    if (ring2Ref.current) {
      (ring2Ref.current.material as THREE.MeshBasicMaterial).color = c;
    }
  }, [state]);

  useFrame((clockState) => {
    const t = clockState.clock.elapsedTime;
    const root = rootRef.current;
    const orb = orbRef.current;
    const inner = innerRef.current;
    const shell = shellRef.current;
    const glow = glowRef.current;

    if (!root || !orb || !inner || !shell || !glow) return;

    const energy =
      state === 'EXECUTING' ? 1.4 : state === 'THINKING' ? 1.1 : state === 'SPEAKING' ? 0.9 : 0.6;
    const breath = 0.055 * energy;

    // breathing core
    const scale = 1 + Math.sin(t * (0.6 + energy * 0.5)) * breath;
    orb.scale.setScalar(scale);

    // inner core pulses brighter on executing
    inner.scale.setScalar(1 + Math.sin(t * (4 + energy * 3)) * 0.12 * energy);
    (inner.material as THREE.MeshBasicMaterial).opacity = 0.55 + 0.35 * energy;

    // fresnel shell
    const shellMat = shell.material as THREE.ShaderMaterial;
    shellMat.uniforms.uIntensity.value = THREE.MathUtils.lerp(
      shellMat.uniforms.uIntensity.value,
      0.7 + energy * 0.9,
      0.05
    );
    shell.rotation.y = t * 0.1;

    // radial glow
    (glow.material as THREE.SpriteMaterial).opacity = 0.35 + energy * 0.35;
    glow.scale.setScalar(5.2 + Math.sin(t * (1 + energy)) * 0.4 * energy);

    // orbit rings
    const ringSpeed = 0.15 + energy * 0.35;
    if (ring1Ref.current) {
      ring1Ref.current.rotation.z = t * ringSpeed;
      ring1Ref.current.rotation.x = 1.15;
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.z = -t * ringSpeed * 0.8;
      ring2Ref.current.rotation.x = 0.45;
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.z = t * ringSpeed * 0.6;
      ring3Ref.current.rotation.y = 0.8;
    }
    if (scanRef.current) {
      scanRef.current.rotation.z = t * (0.9 + energy * 1.4);
      const scanMat = scanRef.current.material as THREE.MeshBasicMaterial;
      scanMat.opacity = 0.25 + 0.5 * energy;
    }
  });

  const color = STATE_COLOR[state];

  return (
    <group ref={rootRef}>
      {/* radial glow halo */}
      <sprite ref={glowRef} scale={[5.2, 5.2, 1]}>
        <spriteMaterial
          map={glowTexture}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          transparent
          opacity={0.5}
        />
      </sprite>

      {/* main energy orb */}
      <mesh ref={orbRef}>
        <sphereGeometry args={[1.15, 64, 64]} />
        <MeshDistortMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.7}
          roughness={0.15}
          metalness={0.9}
          distort={state === 'THINKING' ? 0.55 : state === 'EXECUTING' ? 0.5 : 0.28}
          speed={state === 'EXECUTING' ? 4.5 : state === 'THINKING' ? 3 : 1.5}
        />
      </mesh>

      {/* bright inner core */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshBasicMaterial
          color="#e0faff"
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* fresnel atmosphere shell */}
      <mesh ref={shellRef} scale={1.9}>
        <sphereGeometry args={[1, 48, 48]} />
        <shaderMaterial
          vertexShader={VERTEX}
          fragmentShader={FRAGMENT}
          uniforms={{
            uColor: { value: new THREE.Color(color) },
            uIntensity: { value: 0.6 }
          }}
          blending={THREE.AdditiveBlending}
          transparent
          depthWrite={false}
          side={THREE.FrontSide}
        />
      </mesh>

      {/* orbit rings */}
      <mesh ref={ring1Ref} rotation={[1.15, 0, 0]}>
        <torusGeometry args={[1.85, 0.012, 8, 96]} />
        <meshBasicMaterial color={color} transparent opacity={0.7} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
      <mesh ref={ring2Ref} rotation={[0.45, 0.4, 0]}>
        <torusGeometry args={[2.25, 0.01, 8, 96]} />
        <meshBasicMaterial color={color} transparent opacity={0.5} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
      <mesh ref={ring3Ref} rotation={[0.8, -0.6, 0.3]}>
        <torusGeometry args={[2.6, 0.008, 8, 96]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.4} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* fast scanning ring */}
      <mesh ref={scanRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.4, 0.035, 8, 64]} />
        <meshBasicMaterial color="#7dd3fc" transparent opacity={0.4} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
    </group>
  );
}
