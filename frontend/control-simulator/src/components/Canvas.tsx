import React, { forwardRef } from 'react';
import CanvasBlock from './CanvasBlock';
import { BLOCK_W, BLOCK_H, type BlockData } from '../lib/data';

interface CanvasProps {
  blocks: BlockData[];
  onDropBlock: (type: string, x: number, y: number) => void;
  onMoveBlock: (id: number, x: number, y: number) => void;
  onBlockClick: (id: number) => void;
}

const Canvas = forwardRef<HTMLDivElement, CanvasProps>(
  ({ blocks, onDropBlock, onMoveBlock, onBlockClick }, ref) => {
    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const canvas = e.currentTarget; // the canvas div
      const canvasRect = canvas.getBoundingClientRect();
      const rawType = e.dataTransfer.getData('text/plain');

      // --- New block from palette ---
      if (rawType && !rawType.startsWith('move-')) {
        const x = e.clientX - canvasRect.left - BLOCK_W / 2;
        const y = e.clientY - canvasRect.top - BLOCK_H / 2;
        onDropBlock(rawType, x, y);
        return;
      }

      // --- Move existing block ---
      if (rawType.startsWith('move-')) {
        const id = parseInt(rawType.replace('move-', ''));
        const offsetX = parseInt(e.dataTransfer.getData('offsetX') || '0');
        const offsetY = parseInt(e.dataTransfer.getData('offsetY') || '0');
        const newX = e.clientX - canvasRect.left - offsetX;
        const newY = e.clientY - canvasRect.top - offsetY;
        onMoveBlock(id, newX, newY);
      }
    };

    return (
      <div
        ref={ref}
        className="flex-1 relative m-4 rounded-xl border-2 border-dashed border-gray-600 overflow-hidden"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        {blocks.map((block) => (
          <CanvasBlock
            key={block.id}
            {...block}
            onClick={onBlockClick}
            // No onDragEnd needed – the drop on the canvas does all the work
          />
        ))}

        {/* Orthogonal connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="white" />
            </marker>
          </defs>
          {blocks.slice(0, -1).map((block, i) => {
            const nextBlock = blocks[i + 1];
            const startX = block.x + BLOCK_W;
            const startY = block.y + BLOCK_H / 2;
            const endX = nextBlock.x;
            const endY = nextBlock.y + BLOCK_H / 2;
            const midX = startX + (endX - startX) / 2;
            return (
              <polyline
                key={`line-${block.id}`}
                points={`${startX},${startY} ${midX},${startY} ${midX},${endY} ${endX},${endY}`}
                fill="none"
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
  }
);

Canvas.displayName = 'Canvas';
export default Canvas;