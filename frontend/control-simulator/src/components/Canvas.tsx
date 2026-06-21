import React, { useState, forwardRef } from 'react';
import CanvasBlock from './CanvasBlock';
import ComponentPickerPopup from './ComponentPickerPopup';
import { BLOCK_W, BLOCK_H, type BlockData, type ConnectionData, type componentLibrary } from '../lib/data';

interface CanvasProps {
  blocks: BlockData[];
  connections: ConnectionData[];
  onDropBlock: (type: string, x: number, y: number) => void;
  onMoveBlock: (id: number, x: number, y: number) => void;
  onBlockClick: (id: number) => void;
  onAddConnectedBlock: (sourceId: number, direction: 'left' | 'right' | 'top' | 'bottom', type: string) => void;
}


// Helper: generate orthogonal polyline points from a direction
function getConnectionPoints(
  fromBlock: BlockData,
  toBlock: BlockData,
  direction: 'left' | 'right' | 'top' | 'bottom'
): string {
  const fromCX = fromBlock.x + BLOCK_W / 2;
  const fromCY = fromBlock.y + BLOCK_H / 2;
  const toCX = toBlock.x + BLOCK_W / 2;
  const toCY = toBlock.y + BLOCK_H / 2;
  const gap = 20; // distance from edge before turning

  switch (direction) {
    case 'right':
      // Start from right centre → horizontal right → vertical → horizontal left into target
      return `${fromBlock.x + BLOCK_W},${fromCY} ${fromBlock.x + BLOCK_W + gap},${fromCY} ${fromBlock.x + BLOCK_W + gap},${toCY} ${toBlock.x},${toCY}`;
    case 'left':
      // Start from left centre → horizontal left → vertical → horizontal right into target
      return `${fromBlock.x},${fromCY} ${fromBlock.x - gap},${fromCY} ${fromBlock.x - gap},${toCY} ${toBlock.x + BLOCK_W},${toCY}`;
    case 'bottom':
      // Start from bottom centre → vertical down → horizontal → vertical up into target
      return `${fromCX},${fromBlock.y + BLOCK_H} ${fromCX},${fromBlock.y + BLOCK_H + gap} ${toCX},${fromBlock.y + BLOCK_H + gap} ${toCX},${toBlock.y}`;
    case 'top':
      // Start from top centre → vertical up → horizontal → vertical down into target
      return `${fromCX},${fromBlock.y} ${fromCX},${fromBlock.y - gap} ${toCX},${fromBlock.y - gap} ${toCX},${toBlock.y + BLOCK_H}`;
    default:
      return '';
  }
}

const Canvas = forwardRef<HTMLDivElement, CanvasProps>(
  ({ blocks, connections, onDropBlock, onMoveBlock, onBlockClick, onAddConnectedBlock }, ref) => {
    const [popup, setPopup] = useState<{
      sourceId: number;
      direction: 'left' | 'right' | 'top' | 'bottom';
      x: number;
      y: number;
    } | null>(null);

    const handleAddHandleClick = (id: number, direction: 'left' | 'right' | 'top' | 'bottom') => {
      const block = blocks.find(b => b.id === id);
      if (!block) return;
      // Position the popup to the right of the block by default, adjust for other directions
      let px = block.x + BLOCK_W + 10;
      let py = block.y;
      if (direction === 'left') px = block.x - 260; // rough width
      else if (direction === 'top') { px = block.x; py = block.y - 200; }
      else if (direction === 'bottom') { px = block.x; py = block.y + BLOCK_H + 10; }

      setPopup({ sourceId: id, direction, x: px, y: py });
    };

    const handleSelect = (type: string) => {
      if (!popup) return;
      onAddConnectedBlock(popup.sourceId, popup.direction, type);
      setPopup(null);
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const canvas = e.currentTarget;
      const canvasRect = canvas.getBoundingClientRect();
      const rawType = e.dataTransfer.getData('text/plain');
      if (rawType && !rawType.startsWith('move-')) {
        const x = e.clientX - canvasRect.left - BLOCK_W / 2;
        const y = e.clientY - canvasRect.top - BLOCK_H / 2;
        onDropBlock(rawType, x, y);
        return;
      }
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
        onClick={() => setPopup(null)} // close popup when clicking canvas
      >
        {blocks.map((block) => (
          <CanvasBlock
            key={block.id}
            {...block}
            onClick={onBlockClick}
            onAddHandleClick={handleAddHandleClick}
          />
        ))}

        {/* Orthogonal connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="white" />
            </marker>
          </defs>
          {connections.map((conn) => {
            const fromBlock = blocks.find(b => b.id === conn.from);
            const toBlock = blocks.find(b => b.id === conn.to);
            if (!fromBlock || !toBlock) return null;
            const points = getConnectionPoints(fromBlock, toBlock, conn.direction);
            return (
              <polyline
                key={`conn-${conn.from}-${conn.to}`}
                points={points}
                fill="none"
                stroke="#64748b"
                strokeWidth="2"
                markerEnd="url(#arrowhead)"
              />
            );
          })}
        </svg>

        {/* Popup */}
        {popup && (
          <ComponentPickerPopup
            x={popup.x}
            y={popup.y}
            onSelect={handleSelect}
            onClose={() => setPopup(null)}
          />
        )}

        {blocks.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-medium pointer-events-none select-none">
            <div className="text-center">
              <div className="text-xl text-gray-400 mb-2">📦 Drag components from the library above</div>
              <div className="text-sm text-gray-500">Or hover over a block and click the + to add connected blocks</div>
            </div>
          </div>
        )}
      </div>
    );
  }
);

Canvas.displayName = 'Canvas';
export default Canvas;