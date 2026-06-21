import React from 'react';

interface BlockRendererProps {
  type: string;
  value: string;
}

const BlockRenderer: React.FC<BlockRendererProps> = ({ type, value }) => {
  switch (type) {
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
    // ... (other cases remain identical)
    default:
      return (
        <div className="w-full h-full border-2 border-black bg-white flex items-center justify-center text-xs text-black">
          {type}
        </div>
      );
  }
};

export default BlockRenderer;