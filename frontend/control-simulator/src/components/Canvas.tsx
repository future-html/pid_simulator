// components/Canvas.tsx
import React, {
  useState,
  forwardRef,
  useEffect,
  useRef,
} from "react";
import CanvasBlock from "./CanvasBlock";
import {
  BLOCK_W,
  BLOCK_H,
  type BlockData,
  type ConnectionData,
} from "../lib/data";

interface CanvasProps {
  blocks: BlockData[];
  connections: ConnectionData[];
  onDropBlock: (type: string, x: number, y: number) => void;
  onMoveBlock: (id: number, x: number, y: number) => void;
  onBlockClick: (id: number) => void;
  onLabelChange?: (id: number, newLabel: string) => void; // NEW
  onSubsystemClick?: (id: number) => void;
  onConnect: (
    fromId: number,
    toId: number,
    direction: "left" | "right" | "top" | "bottom",
  ) => void;
  onDeleteConnection: (from: number, to: number) => void;
}

// Helper: generate orthogonal polyline points from a direction
function getConnectionPoints(
  fromBlock: BlockData,
  toBlock: BlockData,
  direction: "left" | "right" | "top" | "bottom",
): string {
  const fromCX = fromBlock.x + BLOCK_W / 2;
  const fromCY = fromBlock.y + BLOCK_H / 2;
  const toCX = toBlock.x + BLOCK_W / 2;
  const toCY = toBlock.y + BLOCK_H / 2;
  const gap = 20;

  switch (direction) {
    case "right":
      return `${fromBlock.x + BLOCK_W},${fromCY} ${fromBlock.x + BLOCK_W + gap},${fromCY} ${fromBlock.x + BLOCK_W + gap},${toCY} ${toBlock.x},${toCY}`;
    case "left":
      return `${fromBlock.x},${fromCY} ${fromBlock.x - gap},${fromCY} ${fromBlock.x - gap},${toCY} ${toBlock.x + BLOCK_W},${toCY}`;
    case "bottom":
      return `${fromCX},${fromBlock.y + BLOCK_H} ${fromCX},${fromBlock.y + BLOCK_H + gap} ${toCX},${fromBlock.y + BLOCK_H + gap} ${toCX},${toBlock.y}`;
    case "top":
      return `${fromCX},${fromBlock.y} ${fromCX},${fromBlock.y - gap} ${toCX},${fromBlock.y - gap} ${toCX},${toBlock.y + BLOCK_H}`;
    default:
      return "";
  }
}

const Canvas = forwardRef<HTMLDivElement, CanvasProps>(
  (
    {
      blocks,
      connections,
      onDropBlock,
      onMoveBlock,
      onBlockClick,
      onConnect,
      onDeleteConnection,
      onSubsystemClick, // new prop for opening modal
      onLabelChange, // new prop for label changes
    },
    ref,
  ) => {
    const canvasRef = useRef<HTMLDivElement>(null);

    // State for the connection being drawn
    const [drawing, setDrawing] = useState<{
      fromId: number;
      direction: "left" | "right" | "top" | "bottom";
      endX: number;
      endY: number;
    } | null>(null);

    // Start drawing when a + handle is clicked
    const handleAddHandleClick = (
      id: number,
      direction: "left" | "right" | "top" | "bottom",
    ) => {
      const block = blocks.find((b) => b.id === id);
      if (!block) return;
      setDrawing({
        fromId: id,
        direction,
        endX: block.x + BLOCK_W / 2,
        endY: block.y + BLOCK_H / 2,
      });
    };

    // Track mouse movement and release while drawing
    useEffect(() => {
      if (!drawing) return;

      const onMouseMove = (e: MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        setDrawing((prev) => (prev ? { ...prev, endX: x, endY: y } : null));
      };

      const onMouseUp = (e: MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas || !drawing) return;
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Find the block under the mouse
        let targetBlock: BlockData | null = null;
        for (const block of blocks) {
          if (
            mouseX >= block.x &&
            mouseX <= block.x + BLOCK_W &&
            mouseY >= block.y &&
            mouseY <= block.y + BLOCK_H
          ) {
            targetBlock = block;
            break;
          }
        }

        // If we hit a different block, create a connection
        if (targetBlock && targetBlock.id !== drawing.fromId) {
          onConnect(drawing.fromId, targetBlock.id, drawing.direction);
        }
        // Clear the drawing state (arrow disappears)
        setDrawing(null);
      };

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);

      return () => {
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      };
    }, [drawing, blocks, onConnect]);

    

    // Handle dropping new blocks or moving existing ones
    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const canvas = e.currentTarget;
      const canvasRect = canvas.getBoundingClientRect();
      const rawType = e.dataTransfer.getData("text/plain");

      if (rawType && !rawType.startsWith("move-")) {
        // New block from palette
        const x = e.clientX - canvasRect.left - BLOCK_W / 2;
        const y = e.clientY - canvasRect.top - BLOCK_H / 2;
        onDropBlock(rawType, x, y);
        return;
      }

      if (rawType.startsWith("move-")) {
        // Moving an existing block
        const id = parseInt(rawType.replace("move-", ""));
        const offsetX = parseInt(e.dataTransfer.getData("offsetX") || "0");
        const offsetY = parseInt(e.dataTransfer.getData("offsetY") || "0");
        const newX = e.clientX - canvasRect.left - offsetX;
        const newY = e.clientY - canvasRect.top - offsetY;
        onMoveBlock(id, newX, newY);
      }
    };

    // Compute preview line points from source block to current mouse position
    const getPreviewPoints = (): string | null => {
      if (!drawing) return null;
      const fromBlock = blocks.find((b) => b.id === drawing.fromId);
      if (!fromBlock) return null;

      const fromCX = fromBlock.x + BLOCK_W / 2;
      const fromCY = fromBlock.y + BLOCK_H / 2;
      const toX = drawing.endX;
      const toY = drawing.endY;
      const gap = 20;

      switch (drawing.direction) {
        case "right":
          return `${fromBlock.x + BLOCK_W},${fromCY} ${fromBlock.x + BLOCK_W + gap},${fromCY} ${fromBlock.x + BLOCK_W + gap},${toY} ${toX},${toY}`;
        case "left":
          return `${fromBlock.x},${fromCY} ${fromBlock.x - gap},${fromCY} ${fromBlock.x - gap},${toY} ${toX},${toY}`;
        case "bottom":
          return `${fromCX},${fromBlock.y + BLOCK_H} ${fromCX},${fromBlock.y + BLOCK_H + gap} ${toX},${fromBlock.y + BLOCK_H + gap} ${toX},${toY}`;
        case "top":
          return `${fromCX},${fromBlock.y} ${fromCX},${fromBlock.y - gap} ${toX},${fromBlock.y - gap} ${toX},${toY}`;
        default:
          return "";
      }
    };

    // Click on a connection → delete it
    const handleConnectionClick = (
      from: number,
      to: number,
      e: React.MouseEvent,
    ) => {
      e.stopPropagation();
      onDeleteConnection(from, to);
    };

    return (
      <div
        ref={(node) => {
          // Forward the ref to the parent, and store it locally
          if (typeof ref === "function") ref(node);
          else if (ref) ref.current = node;
          canvasRef.current = node;
        }}
        className="flex-1 relative m-4 rounded-xl border-2 border-dashed border-gray-600 overflow-hidden"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        {/* Render all blocks */}
        {blocks.map((block) => (
          <CanvasBlock
            key={block.id}
            {...block}
            onClick={onBlockClick}
            onAddHandleClick={handleAddHandleClick}
            onSubsystemClick={onSubsystemClick}
            onLabelChange={onLabelChange} // ADD THIS
          />
        ))}

        {/* SVG overlay for connections and preview */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
            </marker>
            <marker
              id="preview-arrow"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#60a5fa" />
            </marker>
          </defs>

          {/* Permanent connections – clickable to delete */}
          {connections.map((conn) => {
            const fromBlock = blocks.find((b) => b.id === conn.from);
            const toBlock = blocks.find((b) => b.id === conn.to);
            if (!fromBlock || !toBlock) return null;
            const points = getConnectionPoints(
              fromBlock,
              toBlock,
              conn.direction,
            );
            return (
              <polyline
                key={`conn-${conn.from}-${conn.to}`}
                points={points}
                fill="none"
                stroke="#64748b"
                strokeWidth="2"
                markerEnd="url(#arrowhead)"
                className="pointer-events-auto cursor-pointer hover:stroke-red-400 transition-colors"
                onClick={(e) => handleConnectionClick(conn.from, conn.to, e)}
              />
            );
          })}

          {/* Preview line while drawing */}
          {drawing && (
            <polyline
              points={getPreviewPoints() || ""}
              fill="none"
              stroke="#60a5fa"
              strokeWidth="2"
              strokeDasharray="6 4"
              markerEnd="url(#preview-arrow)"
            />
          )}
        </svg>

        {/* Empty state placeholder */}
        {blocks.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-medium pointer-events-none select-none">
            <div className="text-center">
              <div className="text-xl text-gray-400 mb-2">
                📦 Drag components from the library above
              </div>
              <div className="text-sm text-gray-500">
                Or hover over a block and click the{" "}
                <span className="font-mono">+</span> to connect it to another
                block
              </div>
            </div>
          </div>
        )}
      </div>
    );
  },
);

Canvas.displayName = "Canvas";
export default Canvas;
