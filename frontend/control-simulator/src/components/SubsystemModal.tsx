import React, { useState, useCallback, useEffect } from "react";
import Canvas from "./Canvas";
import EditModal from "./EditModal";
import { componentLibrary, type SubsystemData } from "../lib/data";
import { useBlocks } from "../hooks/useBlocks";

interface SubsystemModalProps {
  isOpen: boolean;
  initialData: SubsystemData;
  onSave: (data: SubsystemData) => void;
  onClose: () => void;
}

const SubsystemModal: React.FC<SubsystemModalProps> = ({
  isOpen,
  initialData,
  onSave,
  onClose,
}) => {
  const {
    blocks: internalBlocks,
    connections: internalConnections,
    addBlock,
    moveBlock,
    addConnection,
    deleteConnection,
    updateBlockValue,
    deleteBlock,
    clearBlocks,
  } = useBlocks();

  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [tempValue, setTempValue] = useState("");
  const [hasLoaded, setHasLoaded] = useState(false);

   // Reset hasLoaded when modal closes
  useEffect(() => {
    if (!isOpen) {
      setHasLoaded(false);
    }
  }, [isOpen]);

  // Load initial data when modal opens
  useEffect(() => {
    if (isOpen && !hasLoaded) {
      clearBlocks();
      initialData.blocks.forEach((b) => {
        addBlock(b.type, b.x, b.y, b.value);
      });
      initialData.connections.forEach((c) => {
        addConnection(c.from, c.to, c.direction);
      });
      setHasLoaded(true);
    }
  }, [isOpen, initialData, clearBlocks, addBlock, addConnection, hasLoaded]);

  
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

  const handleBlockClick = useCallback(
    (id: number) => {
      const block = internalBlocks.find((b) => b.id === id);
      if (block) {
        setEditingBlockId(id);
        setTempValue(block.value);
      }
    },
    [internalBlocks],
  );

  const handleConnect = useCallback(
    (fromId: number, toId: number, direction: string) => {
      addConnection(fromId, toId, direction as any);
    },
    [addConnection],
  );

  const handleDeleteConnection = useCallback(
    (from: number, to: number) => {
      deleteConnection(from, to);
    },
    [deleteConnection],
  );

  const handleSave = () => {
    const inputBlocks = internalBlocks.filter((b) => b.type === "Input");
    const outputBlocks = internalBlocks.filter((b) => b.type === "Outport");
    inputBlocks.sort((a, b) => a.y - b.y);
    outputBlocks.sort((a, b) => a.y - b.y);

    const inputPorts = inputBlocks.map(
      (b) => b.value || `In${inputBlocks.indexOf(b) + 1}`,
    );
    const outputPorts = outputBlocks.map(
      (b) => b.value || `Out${outputBlocks.indexOf(b) + 1}`,
    );

    const subsystemData: SubsystemData = {
      inputPorts,
      outputPorts,
      blocks: internalBlocks.map((b) => ({ ...b })),
      connections: internalConnections.map((c) => ({ ...c })),
    };
    onSave(subsystemData);
  };

  const closeEditModal = useCallback(() => {
    setEditingBlockId(null);
    setTempValue("");
  }, []);

  const saveEditValue = useCallback(() => {
    if (editingBlockId !== null) {
      updateBlockValue(editingBlockId, tempValue);
      closeEditModal();
    }
  }, [editingBlockId, tempValue, updateBlockValue, closeEditModal]);

  const deleteCurrentBlock = useCallback(() => {
    if (editingBlockId !== null) {
      deleteBlock(editingBlockId);
      closeEditModal();
    }
  }, [editingBlockId, deleteBlock, closeEditModal]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-[90%] h-[90%] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-white font-semibold">Edit Subsystem</h2>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white"
            >
              Save & Close
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
            >
              Cancel
            </button>
          </div>
        </div>

        {/* Palette – same as main Navbar */}
        <div className="p-2 border-b border-gray-700 overflow-x-auto">
          {Object.entries(componentLibrary).map(([category, items]) => (
            <div key={category} className="inline-block mr-4">
              <span className="text-xs font-bold text-gray-400 uppercase block mb-1">
                {category}
              </span>
              <div className="flex gap-2">
                {items.map((item) => (
                  <div
                    key={item.type}
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData("text/plain", item.type);
                      e.dataTransfer.effectAllowed = "copy";
                    }}
                    className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded cursor-grab text-xs text-white"
                  >
                    {item.label}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex-1 relative flex flex-col">
          <Canvas
            ref={null}
            blocks={internalBlocks}
            connections={internalConnections}
            onDropBlock={handleDropBlock}
            onMoveBlock={handleMoveBlock}
            onBlockClick={handleBlockClick}
            onConnect={handleConnect}
            onDeleteConnection={handleDeleteConnection}
          />
        </div>
        {/* Local EditModal */}
        {editingBlockId !== null && (
          <EditModal
            value={tempValue}
            onValueChange={setTempValue}
            onSave={saveEditValue}
            onCancel={closeEditModal}
            onDelete={deleteCurrentBlock}
          />
        )}
      </div>
    </div>
  );
};

export default SubsystemModal;
