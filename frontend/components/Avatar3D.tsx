'use client';

import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

function JarvisHead() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.005;
      groupRef.current.rotation.x = Math.sin(Date.now() * 0.0005) * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial color="#64b5f6" />
      </mesh>

      <group>
        <mesh position={[-0.3, 0.2, 0.6]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#ffffff" />
        </mesh>
        <mesh position={[0.3, 0.2, 0.6]}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#ffffff" />
        </mesh>
      </group>

      <group>
        <mesh position={[-0.35, 0.25, 0.7]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial color="#000000" />
        </mesh>
        <mesh position={[0.25, 0.25, 0.7]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial color="#000000" />
        </mesh>
      </group>

      <mesh position={[0, 0, 0.6]}>
        <sphereGeometry args={[0.1, 12, 12]} />
        <meshStandardMaterial color="#ffccbc" />
      </mesh>

      <mesh position={[0, -0.2, 0.5]}>
        <torusGeometry args={[0.2, 0.04, 8, 16]} />
        <meshStandardMaterial color="#ff6b6b" />
      </mesh>
    </group>
  );
}

export default function Avatar3D({ className = '' }: { className?: string }) {
  return (
    <div className={`${className} w-64 h-64`}>
      <Canvas camera={{ position: [0, 0, 5], fov: 35 }} style={{ height: '100%', width: '100%' }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <spotLight position={[0, 10, 10]} angle={0.15} penumbra={1} intensity={2} />
        <pointLight position={[-10, 0, 10]} intensity={0.5} />

        <JarvisHead />

        <mesh position={[0, -1.2, 0]}>
          <cylinderGeometry args={[1.2, 1.2, 0.2, 32]} />
          <meshStandardMaterial color="#424242" />
        </mesh>

        <mesh>
          <sphereGeometry args={[1.1, 32, 32]} />
          <meshBasicMaterial
            color="#64b5f6"
            opacity={0.1}
            transparent
            depthWrite={false}
          />
        </mesh>

        <OrbitControls enablePan={false} enableZoom={false} maxPolarAngle={Math.PI / 2 - 0.1} />
      </Canvas>
    </div>
  );
}
