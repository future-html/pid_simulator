import { useState, useCallback } from 'react';
import {  type BlockData } from '../lib/data';

export function useBlocks() {
  const [blocks, setBlocks] = useState<BlockData[]>([]);

  const addBlock = useCallback((type: string, x: number, y: number, defaultVal: string) => {
    setBlocks(prev => [...prev, {
      id: Date.now(),
      type,
      x,
      y,
      value: defaultVal,
    }]);
  }, []);

  const moveBlock = useCallback((id: number, newX: number, newY: number) => {
    setBlocks(prev =>
      prev.map(b => (b.id === id ? { ...b, x: newX, y: newY } : b))
    );
  }, []);

  const updateBlockValue = useCallback((id: number, value: string) => {
    setBlocks(prev =>
      prev.map(b => (b.id === id ? { ...b, value } : b))
    );
  }, []);

  const deleteBlock = useCallback((id: number) => {
    setBlocks(prev => prev.filter(b => b.id !== id));
  }, []);

  const clearBlocks = useCallback(() => {
    setBlocks([]);
  }, []);

  return { blocks, addBlock, moveBlock, updateBlockValue, deleteBlock, clearBlocks };
}