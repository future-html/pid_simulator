import React from 'react';
import CanvasBlock from './CanvasBlock';
import {  BLOCK_W, BLOCK_H, type BlockData } from '../lib/data';

interface CanvasProps {
  blocks: BlockData[];
  onDropNew: (e: React.DragEvent<HTMLDivElement>) => void;
  onMoveBlock: (e: React.DragEvent<HTMLDivElement>, id: number) => void;
  onBlockClick: (id: number) => void;
}

const Canvas: React.FC<CanvasProps> = ({ blocks, onDropNew, onMoveBlock, onBlockClick }) => {
  return (
    <div
      className="flex-1 relative m-4 rounded-xl border-2 border-dashed border-gray-600 overflow-hidden"
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDropNew}
    >
      {blocks.map((block) => (
        <CanvasBlock
          key={block.id}
          {...block}
          onClick={onBlockClick}
          onDragStart={(e) => {
            // We'll handle move logic in the parent via onDragEnd, but we pass the event upward.
            // The actual move is triggered onDragEnd using the parent's handler.
            // For simplicity, we let the parent define onMoveBlock and call it onDragEnd.
          }}
          onDragEnd={(e) => onMoveBlock(e, block.id)}
        />
      ))}

      {/* SVG connections */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="white" />
          </marker>
        </defs>
        {blocks.slice(0, -1).map((block, i) => {
          const nextBlock = blocks[i + 1];
          const x1 = block.x + BLOCK_W;
          const y1 = block.y + BLOCK_H / 2;
          const x2 = nextBlock.x;
          const y2 = nextBlock.y + BLOCK_H / 2;
          return (
            <line
              key={`line-${block.id}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#64748b"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
          );
        })}
      </svg>

      {blocks.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-medium pointer-events-none select-none">
          <div className="text-center">
            <div className="text-xl text-gray-400 mb-2">📦 Drag components from the library above</div>
            <div className="text-sm text-gray-500">Drop them here to build your diagram</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Canvas;