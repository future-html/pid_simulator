import React from 'react';
import BlockRenderer from './BlockRenderer';
import { BLOCK_W, BLOCK_H } from '../lib/data';

interface PaletteItemProps {
  type: string;
  defaultVal: string;
  label: string;
}

const PaletteItem: React.FC<PaletteItemProps> = ({ type, defaultVal, label }) => {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', type);
    e.dataTransfer.effectAllowed = 'copy';
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className="cursor-grab active:cursor-grabbing hover:opacity-80 transition-opacity"
      style={{ width: BLOCK_W, height: BLOCK_H }}
    >
      <BlockRenderer type={type} value={defaultVal} />
      <div className="text-[10px] text-center mt-1 text-gray-400 font-medium whitespace-nowrap">{label}</div>
    </div>
  );
};

export default PaletteItem;