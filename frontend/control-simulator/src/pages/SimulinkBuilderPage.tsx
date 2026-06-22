import React, { useState, useCallback, useRef } from "react";
import Navbar from "../components/Navbar";
import Canvas from "../components/Canvas";
import EditModal from "../components/EditModal";
import { useBlocks } from "../hooks/useBlocks";
import { componentLibrary, BLOCK_W, BLOCK_H } from "../lib/data";

const SimulinkBuilderPage: React.FC = () => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    blocks,
    connections,
    addBlock,
    moveBlock,
    updateBlockValue,
    addConnection,
    deleteBlock,
    clearBlocks,
  } = useBlocks();

  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [tempValue, setTempValue] = useState("");

  // --- New block from palette (navbar drag) still works ---
  const handleDropBlock = useCallback(
    (type: string, x: number, y: number) => {
      let defaultVal = "";
      for (const category of Object.values(componentLibrary)) {
        const found = category.find((i) => i.type === type);
        if (found) {
          defaultVal = found.defaultVal;
          break;
        }
      }
      addBlock(type, x, y, defaultVal);
    },
    [addBlock],
  );

  const handleMoveBlock = useCallback(
    (id: number, x: number, y: number) => {
      moveBlock(id, x, y);
    },
    [moveBlock],
  );

  const openModal = useCallback(
    (id: number) => {
      const block = blocks.find((b) => b.id === id);
      if (block) {
        setEditingBlockId(id);
        setTempValue(block.value);
      }
    },
    [blocks],
  );

  const closeModal = useCallback(() => {
    setEditingBlockId(null);
    setTempValue("");
  }, []);

  const saveValue = useCallback(() => {
    if (editingBlockId !== null) {
      updateBlockValue(editingBlockId, tempValue);
      closeModal();
    }
  }, [editingBlockId, tempValue, updateBlockValue, closeModal]);

  const deleteCurrentBlock = useCallback(() => {
    if (editingBlockId !== null) {
      deleteBlock(editingBlockId);
      closeModal();
    }
  }, [editingBlockId, deleteBlock, closeModal]);

  // We no longer need handleAddConnectedBlock – we'll pass addConnection directly
  const handleConnect = useCallback(
    (
      fromId: number,
      toId: number,
      direction: "left" | "right" | "top" | "bottom",
    ) => {
      addConnection(fromId, toId, direction);
    },
    [addConnection],
  );

  const exportDiagram = useCallback(() => {
    const diagram = {
      metadata: {
        name: "Simulink Diagram",
        createdAt: new Date().toISOString(),
        blockCount: blocks.length,
      },
      blocks: blocks.map((block) => ({
        id: block.id,
        type: block.type,
        position: { x: block.x, y: block.y },
        parameters: { value: block.value, label: `${block.type}_${block.id}` },
      })),
      connections: blocks.slice(0, -1).map((block, i) => ({
        from: { blockId: block.id, port: 0 },
        to: { blockId: blocks[i + 1].id, port: 0 },
      })),
      simulationParams: { startTime: 0, endTime: 10, timeStep: 0.01 },
    };
    const dataStr = JSON.stringify(diagram, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "simulink_diagram.json";
    link.click();
    alert("Diagram exported as simulink_diagram.json");
  }, [blocks]);

  const handleImport = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileImport = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target?.result as string);

          // Validate structure
          if (!data.blocks || !data.connections) {
            alert("Invalid file format: missing 'blocks' or 'connections'.");
            return;
          }

          // Confirm if canvas is not empty
          if (
            blocks.length > 0 &&
            !window.confirm("Import will replace all current blocks. Continue?")
          ) {
            return;
          }

          // Clear existing diagram
          clearBlocks();

          // Map old IDs → new IDs
          const idMap: Record<number, number> = {};
          const positions = new Map<number, { x: number; y: number }>();

          // Add all blocks from the file
          for (const blockData of data.blocks) {
            const { id, type, position, parameters } = blockData;
            const value = parameters?.value || "";
            const newId = addBlock(type, position.x, position.y, value);
            idMap[id] = newId;
            positions.set(id, { x: position.x, y: position.y });
          }

          // Add connections (computing direction from positions)
          for (const conn of data.connections) {
            const fromOld = conn.from.blockId;
            const toOld = conn.to.blockId;
            const fromNew = idMap[fromOld];
            const toNew = idMap[toOld];
            if (fromNew === undefined || toNew === undefined) continue;

            const fromPos = positions.get(fromOld);
            const toPos = positions.get(toOld);
            if (!fromPos || !toPos) continue;

            // Determine direction based on relative positions
            let direction: "left" | "right" | "top" | "bottom";
            const dx = toPos.x - fromPos.x;
            const dy = toPos.y - fromPos.y;

            if (Math.abs(dx) >= Math.abs(dy)) {
              direction = dx > 0 ? "right" : "left";
            } else {
              direction = dy > 0 ? "bottom" : "top";
            }

            addConnection(fromNew, toNew, direction);
          }

          alert("Diagram imported successfully!");
        } catch (err) {
          alert("Failed to parse JSON file. Please check the format.");
          console.error(err);
        }
      };
      reader.readAsText(file);
      e.target.value = ""; // reset input
    },
    [blocks, clearBlocks, addBlock, addConnection],
  );

  const sendToBackend = useCallback(async () => {
    if (blocks.length === 0) {
      alert("Please add some blocks to simulate");
      return;
    }
    const diagram = {
      blocks: blocks.map((b) => ({
        id: b.id,
        type: b.type,
        position: { x: b.x, y: b.y },
        value: b.value,
      })),
      connections: blocks
        .slice(0, -1)
        .map((block, i) => ({ from: block.id, to: blocks[i + 1].id })),
      metadata: {
        totalBlocks: blocks.length,
        timestamp: new Date().toISOString(),
      },
    };
    console.log("Ready to send to backend:", diagram);
    alert(
      "Diagram structure ready for backend!\nCheck console for JSON structure.",
    );
  }, [blocks]);

  const handleClear = useCallback(() => {
    if (window.confirm("Clear all blocks?")) clearBlocks();
  }, [clearBlocks]);

  // --- New: add connected block from a handle ---
  const handleAddConnectedBlock = useCallback(
    (
      sourceId: number,
      direction: "left" | "right" | "top" | "bottom",
      type: string,
    ) => {
      const sourceBlock = blocks.find((b) => b.id === sourceId);
      if (!sourceBlock) return;

      let defaultVal = "";
      for (const category of Object.values(componentLibrary)) {
        const found = category.find((i) => i.type === type);
        if (found) {
          defaultVal = found.defaultVal;
          break;
        }
      }

      // Calculate position based on direction (gap of 30px)
      const gap = 30;
      let newX = sourceBlock.x,
        newY = sourceBlock.y;
      if (direction === "right") newX = sourceBlock.x + BLOCK_W + gap;
      else if (direction === "left") newX = sourceBlock.x - BLOCK_W - gap;
      else if (direction === "bottom") newY = sourceBlock.y + BLOCK_H + gap;
      else if (direction === "top") newY = sourceBlock.y - BLOCK_H - gap;

      const newId = addBlock(type, newX, newY, defaultVal);
      addConnection(sourceId, newId, direction); // ← pass direction
    },
    [blocks, addBlock, addConnection],
  );

  return (
    <div className="h-screen flex flex-col bg-black text-white font-sans overflow-hidden relative">
      <input
        type="file"
        accept=".json"
        ref={fileInputRef}
        onChange={handleFileImport}
        className="hidden"
      />
      <Navbar
        onExport={exportDiagram}
        onSendBackend={sendToBackend}
        onClear={handleClear}
        hasBlocks={blocks.length > 0}
        onImport={handleImport} // <-- new prop
      />
      <Canvas
        ref={canvasRef}
        blocks={blocks}
        connections={connections}
        onDropBlock={handleDropBlock}
        onMoveBlock={handleMoveBlock}
        onBlockClick={openModal}
        onConnect={handleConnect} // <- new prop
      />
      {editingBlockId !== null && (
        <EditModal
          value={tempValue}
          onValueChange={setTempValue}
          onSave={saveValue}
          onCancel={closeModal}
          onDelete={deleteCurrentBlock}
        />
      )}
    </div>
  );
};

export default SimulinkBuilderPage;
