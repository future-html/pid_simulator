import React, { useState, useCallback, useRef } from 'react';
import Navbar from '../components/Navbar';
import Canvas from '../components/Canvas';
import EditModal from '../components/EditModal';
import { useBlocks } from '../hooks/useBlocks';
import { componentLibrary, BLOCK_W, BLOCK_H  } from '../lib/data';

const SimulinkBuilderPage: React.FC = () => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const { blocks, connections,  addBlock, moveBlock, updateBlockValue, addConnection,  deleteBlock, clearBlocks } = useBlocks();

  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [tempValue, setTempValue] = useState('');

   // --- New block from palette (navbar drag) still works ---
  const handleDropBlock = useCallback(
    (type: string, x: number, y: number) => {
      let defaultVal = '';
      for (const category of Object.values(componentLibrary)) {
        const found = category.find(i => i.type === type);
        if (found) { defaultVal = found.defaultVal; break; }
      }
      addBlock(type, x, y, defaultVal);
    },
    [addBlock]
  );

  const handleMoveBlock = useCallback((id: number, x: number, y: number) => {
    moveBlock(id, x, y);
  }, [moveBlock]);

  const openModal = useCallback(
    (id: number) => {
      const block = blocks.find(b => b.id === id);
      if (block) {
        setEditingBlockId(id);
        setTempValue(block.value);
      }
    },
    [blocks]
  );

  const closeModal = useCallback(() => {
    setEditingBlockId(null);
    setTempValue('');
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

  const exportDiagram = useCallback(() => {
    const diagram = {
      metadata: { name: 'Simulink Diagram', createdAt: new Date().toISOString(), blockCount: blocks.length },
      blocks: blocks.map(block => ({
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
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'simulink_diagram.json';
    link.click();
    alert('Diagram exported as simulink_diagram.json');
  }, [blocks]);

  const sendToBackend = useCallback(async () => {
    if (blocks.length === 0) { alert('Please add some blocks to simulate'); return; }
    const diagram = {
      blocks: blocks.map(b => ({ id: b.id, type: b.type, position: { x: b.x, y: b.y }, value: b.value })),
      connections: blocks.slice(0, -1).map((block, i) => ({ from: block.id, to: blocks[i + 1].id })),
      metadata: { totalBlocks: blocks.length, timestamp: new Date().toISOString() },
    };
    console.log('Ready to send to backend:', diagram);
    alert('Diagram structure ready for backend!\nCheck console for JSON structure.');
  }, [blocks]);

  const handleClear = useCallback(() => {
    if (window.confirm('Clear all blocks?')) clearBlocks();
  }, [clearBlocks]);


   // --- New: add connected block from a handle ---
  const handleAddConnectedBlock = useCallback(
    (sourceId: number, direction: 'left' | 'right' | 'top' | 'bottom', type: string) => {
      const sourceBlock = blocks.find(b => b.id === sourceId);
      if (!sourceBlock) return;

      let defaultVal = '';
      for (const category of Object.values(componentLibrary)) {
        const found = category.find(i => i.type === type);
        if (found) { defaultVal = found.defaultVal; break; }
      }

      // Calculate position based on direction (gap of 30px)
      const gap = 30;
      let newX = sourceBlock.x, newY = sourceBlock.y;
      if (direction === 'right') newX = sourceBlock.x + BLOCK_W + gap;
      else if (direction === 'left') newX = sourceBlock.x - BLOCK_W - gap;
      else if (direction === 'bottom') newY = sourceBlock.y + BLOCK_H + gap;
      else if (direction === 'top') newY = sourceBlock.y - BLOCK_H - gap;

      const newId = addBlock(type, newX, newY, defaultVal);
       addConnection(sourceId, newId, direction);   // ← pass direction
    },
    [blocks, addBlock, addConnection]
  );

  return (
    <div className="h-screen flex flex-col bg-black text-white font-sans overflow-hidden relative">
      <Navbar
        onExport={exportDiagram}
        onSendBackend={sendToBackend}
        onClear={handleClear}
        hasBlocks={blocks.length > 0}
      />
      <Canvas
        ref={canvasRef}
        blocks={blocks}
        connections={connections}
        onDropBlock={handleDropBlock}
        onMoveBlock={handleMoveBlock}
        onBlockClick={openModal}
        onAddConnectedBlock={handleAddConnectedBlock}
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