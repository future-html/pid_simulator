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
  onDragStart: (e: React.DragEvent, id: number) => void;
  onDragEnd: (e: React.DragEvent) => void;
}

const CanvasBlock: React.FC<CanvasBlockProps> = ({
  id,
  type,
  x,
  y,
  value,
  onClick,
  onDragStart,
  onDragEnd,
}) => {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', `move-${id}`);
    e.dataTransfer.setData('offsetX', e.nativeEvent.offsetX.toString());
    e.dataTransfer.setData('offsetY', e.nativeEvent.offsetY.toString());
    onDragStart(e, id);
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onClick={() => onClick(id)}
      className="absolute cursor-move hover:z-20 transition-shadow group"
      style={{ left: x, top: y, width: BLOCK_W, height: BLOCK_H }}
    >
      <BlockRenderer type={type} value={value} />
      <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/10 transition-colors pointer-events-none rounded-sm border-2 border-transparent group-hover:border-blue-400 group-hover:border-dashed" />
    </div>
  );
};

export default CanvasBlock;