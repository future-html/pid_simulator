// components/CanvasBlock.tsx
import React from "react";
import BlockRenderer from "./BlockRenderer";
import { BLOCK_W, BLOCK_H, type SubsystemData } from "../lib/data";

interface CanvasBlockProps {
  id: number;
  type: string;
  x: number;
  y: number;
  value: string;
  onClick: (id: number) => void;
  onAddHandleClick: (
    id: number,
    direction: "left" | "right" | "top" | "bottom"
  ) => void;
  onSubsystemClick?: (id: number) => void;
  subsystemData?: SubsystemData;
}

const CanvasBlock: React.FC<CanvasBlockProps> = ({
  id,
  type,
  x,
  y,
  value,
  onClick,
  onAddHandleClick,
  onSubsystemClick,
  subsystemData,
}) => {
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", `move-${id}`);
    e.dataTransfer.setData("offsetX", e.nativeEvent.offsetX.toString());
    e.dataTransfer.setData("offsetY", e.nativeEvent.offsetY.toString());
  };

  const isSubsystem = type === "Subsystem";

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

      {/* Input port indicators (blue squares on left) */}
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

      {/* Output port indicators (green squares on right) */}
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