
interface BlockRendererProps {
  type: string;
  value: string;
}
// --- Visual Renderers for Simulink Blocks ---
const BlockRenderer = ({ type, value }: BlockRendererProps) => {
  switch (type) {
    // ===== BASIC INPUT/OUTPUT BLOCKS =====
    case 'Input':
      return (
        <div className="w-full h-full flex items-center justify-center">
          <svg width="100%" height="100%" viewBox="0 0 100 50">
            <ellipse cx="50" cy="25" rx="45" ry="22" fill="white" stroke="black" strokeWidth="2" />
            <text x="50" y="30" fontSize="12" fontFamily="sans-serif" fill="black" textAnchor="middle" fontWeight="bold">
              {value || 'In1'}
            </text>
          </svg>
        </div>
      );

    case 'Output':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center">
          <span className="font-bold text-black text-[11px]">
            {value || 'Out'}
          </span>
        </div>
      );

    // ===== SIGNAL GENERATION =====
    case 'Step':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm overflow-hidden">
          <svg width="80%" height="60%" viewBox="0 0 100 40">
            <polyline points="10,30 40,30 40,10 90,10" fill="none" stroke="black" strokeWidth="2" />
          </svg>
          <span className="text-[8px] font-bold text-black mt-1">Step</span>
        </div>
      );

    case 'Constant':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm">
          <span className="font-bold text-sm text-black">{value || 'K'}</span>
          <span className="text-[8px] text-gray-600">Const</span>
        </div>
      );

    // ===== MATHEMATICAL OPERATIONS =====
    case 'Sum':
      return (
        <div className="w-full h-full rounded-full border-2 border-black bg-white flex items-center justify-center text-lg font-bold text-black shadow-sm">
          {value || '+'}
        </div>
      );

    case 'Gain':
      return (
        <div className="relative w-full h-full flex items-center justify-center">
          <svg width="100%" height="100%" viewBox="0 0 100 50">
            <polygon points="10,0 100,25 10,50" fill="white" stroke="black" strokeWidth="2" />
            <text x="55" y="28" fontSize="12" fontFamily="sans-serif" fill="black" textAnchor="middle" fontWeight="bold">
              {value || 'K'}
            </text>
          </svg>
        </div>
      );

    case 'Product':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center shadow-sm">
          <span className="font-bold text-black text-[14px]">×</span>
        </div>
      );

    case 'Divide':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center shadow-sm">
          <span className="font-bold text-black text-[14px]">÷</span>
        </div>
      );

    // ===== DYNAMICS =====
    case 'Integrator':
      return (
        <div className="relative w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm">
          <span className="text-sm font-bold text-black leading-3">1</span>
          <div className="w-5 bg-black my-0.5"></div>
          <span className="text-sm font-bold text-black leading-3">s</span>
        </div>
      );

    case 'Derivative':
      return (
        <div className="relative w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm">
          <span className="text-sm font-bold text-black leading-3">ds</span>
          <div className="w-5  bg-black my-0.5"></div>
          <span className="text-sm font-bold text-black leading-3">dt</span>
        </div>
      );

    // ===== COMPARISON & LOGIC =====
    case 'RelationalOp':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center shadow-sm">
          <span className="font-bold text-black text-[12px]">
            {value || '<='}
          </span>
        </div>
      );

    case 'LogicalOp':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center shadow-sm">
          <span className="font-bold text-black text-[11px]">
            {value || '&&'}
          </span>
        </div>
      );

    // ===== VISUALIZATION =====
    case 'Scope':
      return (
        <div className="relative w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm overflow-hidden">
          <svg width="70%" height="60%" viewBox="0 0 100 50">
            <rect x="0" y="0" width="100" height="50" fill="#f8fafc" />
            <polyline points="10,40 25,20 40,25 55,15 70,35 85,10" fill="none" stroke="#3b82f6" strokeWidth="2" />
          </svg>
          <span className="text-[8px] font-bold text-black">Scope</span>
        </div>
      );

    // ===== SUBSYSTEMS =====
    case 'Subsystem':
      return (
        <div className="w-full h-full border-2 border-black bg-white flex flex-col items-center justify-center shadow-sm">
          <span className="text-[10px] font-bold text-black text-center">
            {value || 'Sub'}
          </span>
          <svg width="60%" height="30%" viewBox="0 0 40 20" className="mt-1">
            <circle cx="8" cy="10" r="2" fill="#3b82f6" />
            <line x1="10" y1="10" x2="30" y2="10" stroke="#3b82f6" strokeWidth="1" />
            <circle cx="32" cy="10" r="2" fill="#3b82f6" />
          </svg>
        </div>
      );

    case 'Stop':
      return (
        <div className="w-full h-full border-2 border-red-500 bg-white flex items-center justify-center shadow-sm">
          <span className="font-bold text-black text-sm">STOP</span>
        </div>
      );

    case 'Multiplexer':
      return (
        <div className="w-full h-full bg-white border-2 border-black flex items-center justify-center shadow-sm">
          <svg width="60%" height="80%" viewBox="0 0 30 50">
            <polygon points="5,5 25,15 25,35 5,45" fill="white" stroke="black" strokeWidth="1" />
            <line x1="5" y1="20" x2="25" y2="20" stroke="black" strokeWidth="1" />
            <line x1="5" y1="30" x2="25" y2="30" stroke="black" strokeWidth="1" />
          </svg>
        </div>
      );

    case 'Demultiplexer':
      return (
        <div className="w-full h-full bg-white border-2 border-black flex items-center justify-center shadow-sm">
          <svg width="60%" height="80%" viewBox="0 0 30 50">
            <polygon points="5,15 25,5 25,45 5,35" fill="white" stroke="black" strokeWidth="1" />
            <line x1="5" y1="20" x2="25" y2="20" stroke="black" strokeWidth="1" />
            <line x1="5" y1="30" x2="25" y2="30" stroke="black" strokeWidth="1" />
          </svg>
        </div>
      );

    default:
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center text-xs text-black">
          {type}
        </div>
      );
  }
};

export default BlockRenderer;