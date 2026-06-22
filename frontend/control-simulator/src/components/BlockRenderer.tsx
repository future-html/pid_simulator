// components/BlockRenderer.tsx
import React from 'react';
import { type SubsystemData } from '../lib/data';

type BlockRendererProps = {
  type: string;
  value: string;
  subsystemData?: SubsystemData;
};

const BlockRenderer: React.FC<BlockRendererProps> = ({ type, value, subsystemData }) => {
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
      return (
        <Wrapper bg="bg-blue-800">
          <div className="flex items-center gap-1">
            <span className="text-white font-mono text-sm">▶</span>
            <span className="text-white text-xs">{value || 'In'}</span>
          </div>
        </Wrapper>
      );

    case 'Outport':
      return (
        <Wrapper bg="bg-green-800">
          <div className="flex items-center gap-1">
            <span className="text-white text-xs">{value || 'Out'}</span>
            <span className="text-white font-mono text-sm">◀</span>
          </div>
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
        <div className="relative w-full h-full">
          <Wrapper bg="bg-gray-700">
            <div className="flex flex-col items-center gap-1">
              <span className="text-white font-mono text-xs font-bold">
                {value || 'Subsystem'}
              </span>
              {subsystemData && (
                <span className="text-gray-300 text-[9px]">
                  [{subsystemData.inputPorts.length}×{subsystemData.outputPorts.length}]
                </span>
              )}
            </div>
          </Wrapper>

          {/* Input ports labels on left */}
          {subsystemData?.inputPorts && subsystemData.inputPorts.length > 0 && (
            <div className="absolute left-0 top-0 h-full flex flex-col justify-around pointer-events-none">
              {subsystemData.inputPorts.map((label, idx) => (
                <div
                  key={`in-label-${idx}`}
                  className="text-[8px] text-blue-300 -ml-12 whitespace-nowrap"
                >
                  {label}
                </div>
              ))}
            </div>
          )}

          {/* Output ports labels on right */}
          {subsystemData?.outputPorts && subsystemData.outputPorts.length > 0 && (
            <div className="absolute right-0 top-0 h-full flex flex-col justify-around pointer-events-none">
              {subsystemData.outputPorts.map((label, idx) => (
                <div
                  key={`out-label-${idx}`}
                  className="text-[8px] text-green-300 ml-1 whitespace-nowrap"
                >
                  {label}
                </div>
              ))}
            </div>
          )}
        </div>
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