// components/SimulinkBuilderPage.tsx
import React, { useState, useCallback, useRef } from "react";
import Navbar from "../components/Navbar";
import Canvas from "../components/Canvas";
import EditModal from "../components/EditModal";
import { useBlocks } from "../hooks/useBlocks";
import {
  componentLibrary,
  type SubsystemData,
  type BlockData,
} from "../lib/data";
import SubsystemModal from "../components/SubsystemModal";

interface ExportBlockData extends BlockData {
  subsystemData?: SubsystemData & {
    blocks: ExportBlockData[];
    connections: any[];
  };
}

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
    deleteConnection,
    updateSubsystem,
  } = useBlocks();

  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [tempValue, setTempValue] = useState("");
  const [editingSubsystemId, setEditingSubsystemId] = useState<number | null>(
    null,
  );

  // Helper function to recursively build nested block structure
  const buildNestedBlocks = (blockList: BlockData[]): ExportBlockData[] => {
    return blockList.map((block) => {
      const exportBlock: ExportBlockData = {
        id: block.id,
        type: block.type,
        x: block.x,
        y: block.y,
        value: block.value,
      };

      // If it's a subsystem, include nested data
      if (block.type === "Subsystem" && block.subsystemData) {
        exportBlock.subsystemData = {
          ...block.subsystemData,
          blocks: buildNestedBlocks(block.subsystemData.blocks),
          connections: block.subsystemData.connections,
        };
      }

      return exportBlock;
    });
  };

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
    const nestedBlocks = buildNestedBlocks(blocks);

    const diagram = {
      metadata: {
        name: "Simulink Diagram",
        createdAt: new Date().toISOString(),
        blockCount: blocks.length,
        version: "1.0",
      },
      blocks: nestedBlocks,
      connections: connections.map((conn) => ({
        from: conn.from,
        to: conn.to,
        direction: conn.direction,
      })),
      simulationParams: {
        startTime: 0,
        endTime: 10,
        timeStep: 0.01,
      },
    };

    const dataStr = JSON.stringify(diagram, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "simulink_diagram.json";
    link.click();
    alert("Diagram exported as simulink_diagram.json");
  }, [blocks, connections]);

  const handleImport = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Add this helper function first
  const computeDirection = (
    fromPos: { x: number; y: number },
    toPos: { x: number; y: number },
  ): "left" | "right" | "top" | "bottom" => {
    const dx = toPos.x - fromPos.x;
    const dy = toPos.y - fromPos.y;

    if (Math.abs(dx) >= Math.abs(dy)) {
      return dx > 0 ? "right" : "left";
    } else {
      return dy > 0 ? "bottom" : "top";
    }
  };

  const handleFileImport = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target?.result as string);

          if (!data.blocks || !data.connections) {
            alert("Invalid file format: missing 'blocks' or 'connections'.");
            return;
          }

          if (
            blocks.length > 0 &&
            !window.confirm("Import will replace all current blocks. Continue?")
          ) {
            return;
          }

          // IMPORTANT: Clear first to reset idCounter
          clearBlocks();

          const idMap: Record<number, number> = {};
          const positionMap: Record<number, { x: number; y: number }> = {};

          console.log("=== Starting Import ===");
          console.log("Blocks to import:", data.blocks);

          // Step 1: Add all blocks
          for (const blockData of data.blocks) {
            const { id, type, x, y, value, subsystemData } = blockData;

            const newId = addBlock(type, x, y, value);
            idMap[id] = newId;
            positionMap[id] = { x, y };

            console.log(
              `Block added: ${type} | Old ID: ${id} → New ID: ${newId} | Pos: (${x}, ${y})`,
            );

            // Handle subsystem
            if (type === "Subsystem" && subsystemData) {
              updateSubsystem(newId, subsystemData);
              console.log(`Subsystem ${newId} updated with nested data`);
            }
          }

          console.log("ID Mapping:", idMap);

          // Step 2: Add connections
          console.log("Connections to create:", data.connections);

          for (const conn of data.connections) {
            const fromNewId = idMap[conn.from];
            const toNewId = idMap[conn.to];

            console.log(
              `Mapping connection: ${conn.from} → ${conn.to} = ${fromNewId} → ${toNewId}`,
            );

            if (fromNewId === undefined || toNewId === undefined) {
              console.error(`❌ Connection failed: IDs not in map`);
              continue;
            }

            const direction = conn.direction || "right";
            addConnection(fromNewId, toNewId, direction);
            console.log(
              `✓ Connection created: ${fromNewId} → ${toNewId} (${direction})`,
            );
          }

          console.log("=== Import Complete ===");
          alert("✓ Diagram imported successfully!");
        } catch (err) {
          alert("Failed to parse JSON file. Check console for details.");
          console.error("Import error:", err);
        }
      };
      reader.readAsText(file);
      e.target.value = "";
    },
    [blocks, clearBlocks, addBlock, addConnection, updateSubsystem],
  );
  const sendToBackend = useCallback(async () => {
    if (blocks.length === 0) {
      alert("Please add some blocks to simulate");
      return;
    }

    const nestedBlocks = buildNestedBlocks(blocks);

    const diagram = {
      blocks: nestedBlocks,
      connections: connections.map((conn) => ({
        from: conn.from,
        to: conn.to,
        direction: conn.direction,
      })),
      metadata: {
        totalBlocks: blocks.length,
        timestamp: new Date().toISOString(),
        version: "1.0",
      },
    };

    console.log("Ready to send to backend:", diagram);

    // Uncomment to actually send to backend
    // try {
    //   const response = await fetch("http://your-backend/api/simulate", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify(diagram),
    //   });
    //   const result = await response.json();
    //   console.log("Backend response:", result);
    //   alert("Simulation submitted successfully!");
    // } catch (error) {
    //   console.error("Error sending to backend:", error);
    //   alert("Failed to send to backend");
    // }

    alert(
      "Diagram structure ready for backend!\nCheck console for JSON structure.",
    );
  }, [blocks, connections]);

  const handleClear = useCallback(() => {
    if (window.confirm("Clear all blocks?")) clearBlocks();
  }, [clearBlocks]);

  const handleDeleteConnection = useCallback(
    (from: number, to: number) => {
      deleteConnection(from, to);
    },
    [deleteConnection],
  );

  const openSubsystem = useCallback((id: number) => {
    setEditingSubsystemId(id);
  }, []);

  const closeSubsystem = useCallback(() => {
    setEditingSubsystemId(null);
  }, []);

  const saveSubsystem = useCallback(
    (subsystemData: SubsystemData) => {
      if (editingSubsystemId !== null) {
        updateSubsystem(editingSubsystemId, subsystemData);
        closeSubsystem();
      }
    },
    [editingSubsystemId, updateSubsystem, closeSubsystem],
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
        onImport={handleImport}
      />
      <Canvas
        ref={canvasRef}
        blocks={blocks}
        connections={connections}
        onDropBlock={handleDropBlock}
        onMoveBlock={handleMoveBlock}
        onBlockClick={openModal}
        onConnect={handleConnect}
        onDeleteConnection={handleDeleteConnection}
        onSubsystemClick={openSubsystem}
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

      {editingSubsystemId !== null && (
        <SubsystemModal
          isOpen={true}
          initialData={
            blocks.find((b) => b.id === editingSubsystemId)?.subsystemData || {
              inputPorts: ["In1"],
              outputPorts: ["Out1"],
              blocks: [],
              connections: [],
            }
          }
          onSave={saveSubsystem}
          onClose={closeSubsystem}
        />
      )}
    </div>
  );
};

export default SimulinkBuilderPage;
