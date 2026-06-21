// Dimensions shared across the app
export const BLOCK_W = 100;
export const BLOCK_H = 50;

// Core component library
export const componentLibrary = {
  'Sources (Inputs)': [
    { type: 'Input', defaultVal: 'In1', label: 'Inport' },
    { type: 'Constant', defaultVal: '5', label: 'Constant' },
    { type: 'Step', defaultVal: '', label: 'Step' },
  ],
  'Math Operations': [
    { type: 'Sum', defaultVal: '+', label: 'Sum' },
    { type: 'Gain', defaultVal: 'K', label: 'Gain' },
    { type: 'Product', defaultVal: '×', label: 'Product' },
    { type: 'Divide', defaultVal: '÷', label: 'Divide' },
  ],
  'Continuous (Dynamics)': [
    { type: 'Integrator', defaultVal: '1/s', label: 'Integrator' },
    { type: 'Derivative', defaultVal: 'ds/dt', label: 'Derivative' },
  ],
  'Signal Routing': [
    { type: 'Multiplexer', defaultVal: '', label: 'Mux' },
    { type: 'Demultiplexer', defaultVal: '', label: 'Demux' },
  ],
  'Logic & Comparison': [
    { type: 'RelationalOp', defaultVal: '<=', label: 'Relational Op' },
    { type: 'LogicalOp', defaultVal: '&&', label: 'Logical Op' },
  ],
  'Sinks (Outputs)': [
    { type: 'Output', defaultVal: 'Out1', label: 'Outport' },
    { type: 'Scope', defaultVal: '', label: 'Scope' },
    { type: 'Stop', defaultVal: '', label: 'Stop Sim' },
  ],
  'Subsystems': [
    { type: 'Subsystem', defaultVal: 'Sub1', label: 'Subsystem' },
  ],
};

export interface BlockData {
  id: number;
  type: string;
  x: number;
  y: number;
  value: string;
}