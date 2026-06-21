import React from 'react';
import BlockRenderer from './BlockRenderer';
import { BLOCK_W, BLOCK_H } from '../lib/data';

interface CanvasBlockProps {
  id: number;
  type: string;
  x: number;
  y: number;
  value: string;
  onClick: (id: number) => void;
  onAddHandleClick: (id: number, direction: 'left' | 'right' | 'top' | 'bottom') => void;
}

const CanvasBlock: React.FC<CanvasBlockProps> = ({ id, type, x, y, value, onClick, onAddHandleClick }) => {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', `move-${id}`);
    e.dataTransfer.setData('offsetX', e.nativeEvent.offsetX.toString());
    e.dataTransfer.setData('offsetY', e.nativeEvent.offsetY.toString());
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onClick={() => onClick(id)}
      className="absolute cursor-move group"
      style={{ left: x, top: y, width: BLOCK_W, height: BLOCK_H }}
    >
      <BlockRenderer type={type} value={value} />

      {/* Hover highlight */}
      <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/10 transition-colors pointer-events-none rounded-sm border-2 border-transparent group-hover:border-blue-400 group-hover:border-dashed" />

      {/* Directional handles */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <button
          className="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20"
          onClick={(e) => { e.stopPropagation(); onAddHandleClick(id, 'right'); }}
        >+</button>
        <button
          className="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20"
          onClick={(e) => { e.stopPropagation(); onAddHandleClick(id, 'left'); }}
        >+</button>
        <button
          className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20"
          onClick={(e) => { e.stopPropagation(); onAddHandleClick(id, 'top'); }}
        >+</button>
        <button
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20"
          onClick={(e) => { e.stopPropagation(); onAddHandleClick(id, 'bottom'); }}
        >+</button>
      </div>

      {/* Value label below the block */}
      <div
        className="absolute left-0 right-0 flex justify-center pointer-events-none select-none"
        style={{ top: BLOCK_H + 4 }}
      >
        <span className="text-[10px] text-gray-300 bg-black/60 px-1.5 py-0.5 rounded whitespace-nowrap leading-tight">
          {type}
        </span>
      </div>
    </div>
  );
};

export default CanvasBlock;