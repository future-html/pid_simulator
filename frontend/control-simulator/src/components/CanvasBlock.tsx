// components/CanvasBlock.tsx
import React, { useState } from "react";
import BlockRenderer from "./BlockRenderer";
import { BLOCK_W, BLOCK_H, type SubsystemData } from "../lib/data";

interface CanvasBlockProps {
  id: number;
  type: string;
  x: number;
  y: number;
  value: string;
  label?: string;  // NEW PROP
  onClick: (id: number) => void;
  onAddHandleClick: (
    id: number,
    direction: "left" | "right" | "top" | "bottom"
  ) => void;
  onSubsystemClick?: (id: number) => void;
  onLabelChange?: (id: number, newLabel: string) => void; // NEW PROP
  subsystemData?: SubsystemData;
}

const CanvasBlock: React.FC<CanvasBlockProps> = ({
  id,
  type,
  x,
  y,
  value,
  label,
  onClick,
  onAddHandleClick,
  onSubsystemClick,
  onLabelChange,
  subsystemData,
}) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [editedLabel, setEditedLabel] = useState(label || `${type}_${id}`);

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", `move-${id}`);
    e.dataTransfer.setData("offsetX", e.nativeEvent.offsetX.toString());
    e.dataTransfer.setData("offsetY", e.nativeEvent.offsetY.toString());
  };

  const isSubsystem = type === "Subsystem";

  // Handle label edit start
  const handleLabelClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditingLabel(true);
    setEditedLabel(label || `${type}_${id}`);
  };

  // Handle label save
  const handleLabelSave = () => {
    if (onLabelChange && editedLabel.trim()) {
      onLabelChange(id, editedLabel.trim());
    }
    setIsEditingLabel(false);
  };

  // Handle keyboard events in input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleLabelSave();
    } else if (e.key === "Escape") {
      setIsEditingLabel(false);
    }
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onClick={() => {
        if (isSubsystem && onSubsystemClick) {
          onSubsystemClick(id);
        } else {
          onClick(id);
        }
      }}
      className="absolute cursor-move group"
      style={{ left: x, top: y, width: BLOCK_W, height: BLOCK_H }}
    >
      <BlockRenderer 
        type={type} 
        value={value}
        subsystemData={subsystemData}
      />

      {/* Input port indicators */}
      {isSubsystem && subsystemData?.inputPorts && (
        <div className="absolute left-0 top-0 h-full flex flex-col justify-around pointer-events-none">
          {subsystemData.inputPorts.map((_, idx) => {
            const portY =
              ((idx + 1) / (subsystemData.inputPorts.length + 1)) * BLOCK_H;
            return (
              <div
                key={`in-port-${idx}`}
                className="w-2.5 h-2.5 bg-blue-400 border border-blue-300 -translate-x-1/2 rounded-sm shadow-md"
                style={{ top: portY }}
                title={`Input: ${subsystemData.inputPorts[idx]}`}
              />
            );
          })}
        </div>
      )}

      {/* Output port indicators */}
      {isSubsystem && subsystemData?.outputPorts && (
        <div className="absolute right-0 top-0 h-full flex flex-col justify-around pointer-events-none">
          {subsystemData.outputPorts.map((_, idx) => {
            const portY =
              ((idx + 1) / (subsystemData.outputPorts.length + 1)) * BLOCK_H;
            return (
              <div
                key={`out-port-${idx}`}
                className="w-2.5 h-2.5 bg-green-400 border border-green-300 translate-x-1/2 rounded-sm shadow-md"
                style={{ top: portY }}
                title={`Output: ${subsystemData.outputPorts[idx]}`}
              />
            );
          })}
        </div>
      )}

      {/* Hover highlight */}
      <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/10 transition-colors pointer-events-none rounded-sm border-2 border-transparent group-hover:border-blue-400 group-hover:border-dashed" />

      {/* Directional handles */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <button
          className="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 hover:bg-blue-400 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20 transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            onAddHandleClick(id, "right");
          }}
        >
          +
        </button>
        <button
          className="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 hover:bg-blue-400 rounded-full flex items-center justify-center text-white text-xs pointer-events-auto z-20 transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            onAddHandleClick(id, "left");
          }}
        >
          +
        </button>
      </div>

      {/* Editable Label (display name) - SEPARATE from value */}
      <div
        className="absolute left-0 right-0 flex justify-center pointer-events-auto select-none"
        style={{ top: BLOCK_H + 4 }}
      >
        {isEditingLabel ? (
          <input
            type="text"
            autoFocus
            value={editedLabel}
            onChange={(e) => setEditedLabel(e.target.value)}
            onBlur={handleLabelSave}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
            className="w-24 px-1.5 py-0.5 text-[10px] bg-gray-900 text-white border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 text-center"
            placeholder="Label..."
          />
        ) : (
          <span
            onClick={handleLabelClick}
            className="text-[10px] text-blue-300 bg-black/60 px-1.5 py-0.5 rounded whitespace-nowrap leading-tight cursor-text hover:bg-black/80 hover:text-blue-200 transition-colors"
          >
            {label || `${type}_${id}`}
          </span>
        )}
      </div>
    </div>
  );
};

export default CanvasBlock;