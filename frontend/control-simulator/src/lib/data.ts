// lib/data.ts

export const BLOCK_W = 80;
export const BLOCK_H = 40;
export interface BlockData {
  id: number;
  type: string;
  x: number;
  y: number;
  value: string;        // The parameter value
  label?: string;       // The display name (NEW)
  subsystemData?: SubsystemData; // present only for type === 'Subsystem'
}

export interface SubsystemData {
  inputPorts: string[];   // e.g. ['In1', 'In2']
  outputPorts: string[];  // e.g. ['Out1']
  blocks: BlockData[];
  connections: ConnectionData[];
}

export interface ConnectionData {
  from: number;
  to: number;
  direction: 'left' | 'right' | 'top' | 'bottom';
  fromPortIndex?: number; // output port index (for subsystems)
  toPortIndex?: number;   // input port index (for subsystems)
}

export const componentLibrary = {
  Sources: [
    { type: 'Input', label: 'Inport', defaultVal: 'In1' },
    { type: 'Step', label: 'Step', defaultVal: '' },
    { type: 'Constant', label: 'Constant', defaultVal: '0' },
  ],
  Sinks: [
    { type: 'Scope', label: 'Scope', defaultVal: '' },
    { type: 'StopSimulation', label: 'Stop Simulation', defaultVal: '' },
    { type: 'Outport', label: 'Outport', defaultVal: 'Out1' },
  ],
  Continuous: [
    { type: 'Integrator', label: 'Integrator', defaultVal: '1/s' },
    { type: 'IntegratorLimited', label: 'Integrator Limited', defaultVal: '1/s' },
  ],
  MathOperations: [
    { type: 'Sum', label: 'Sum', defaultVal: '++' },
    { type: 'Gain', label: 'Gain', defaultVal: '1' },
  ],
  Logic: [
    { type: 'RelationalOp', label: 'Relational Operator', defaultVal: '<=' },
  ],
  Subsystems: [
    { type: 'Subsystem', label: 'Subsystem', defaultVal: 'Subsystem' },
  ],
};