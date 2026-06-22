// components/BlockRenderer.tsx
import React from 'react';

type BlockRendererProps = {
  type: string;
  value: string;
};

const BlockRenderer: React.FC<BlockRendererProps> = ({ type, value }) => {
  // Common wrapper for all blocks
  const Wrapper: React.FC<{ children: React.ReactNode; bg: string }> = ({ children, bg }) => (
    <div
      className={`w-full h-full flex items-center justify-center rounded-sm shadow-sm ${bg} border border-gray-600`}
    >
      {children}
    </div>
  );

  switch (type) {
    case 'Input':
    case 'Outport':
      return (
        <Wrapper bg="bg-blue-800">
          <span className="text-white font-mono text-sm">{value || '▶'}</span>
        </Wrapper>
      );
    case 'Step':
      return (
        <Wrapper bg="bg-indigo-800">
          <span className="text-white font-mono text-sm">Step</span>
        </Wrapper>
      );
    case 'Constant':
      return (
        <Wrapper bg="bg-emerald-800">
          <span className="text-white font-mono text-sm">{value || '0'}</span>
        </Wrapper>
      );
    case 'Scope':
      return (
        <Wrapper bg="bg-yellow-800">
          <span className="text-white font-mono text-sm">📊</span>
        </Wrapper>
      );
    case 'StopSimulation':
      return (
        <Wrapper bg="bg-red-800">
          <span className="text-white font-mono text-sm">⏹</span>
        </Wrapper>
      );
    case 'Integrator':
    case 'IntegratorLimited':
      return (
        <Wrapper bg="bg-purple-800">
          <span className="text-white font-mono text-sm">{value || '∫'}</span>
        </Wrapper>
      );
    case 'Sum':
      return (
        <Wrapper bg="bg-teal-800">
          <span className="text-white font-mono text-sm">{value || '∑'}</span>
        </Wrapper>
      );
    case 'Gain':
      return (
        <Wrapper bg="bg-orange-800">
          <span className="text-white font-mono text-sm">× {value || '1'}</span>
        </Wrapper>
      );
    case 'RelationalOp':
      return (
        <Wrapper bg="bg-cyan-800">
          <span className="text-white font-mono text-sm">{value || '<='}</span>
        </Wrapper>
      );
    case 'Subsystem':
      return (
        <Wrapper bg="bg-gray-700">
          <span className="text-white font-mono text-xs text-center px-1 break-words">
            {value || 'Subsystem'}
          </span>
        </Wrapper>
      );
    default:
      return (
        <Wrapper bg="bg-gray-800">
          <span className="text-white font-mono text-xs">{type}</span>
        </Wrapper>
      );
  }
};

export default BlockRenderer;