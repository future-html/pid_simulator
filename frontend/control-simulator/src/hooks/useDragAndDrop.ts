import { useCallback } from 'react';
import { BLOCK_W, BLOCK_H, componentLibrary,  type BlockData } from '../lib/data';

export function useDragAndDrop(
  addBlock: (type: string, x: number, y: number, defaultVal: string) => void,
  moveBlock: (id: number, x: number, y: number) => void
) {
  const handleDropNew = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const type = e.dataTransfer.getData('text/plain');
      if (!type || type.startsWith('move-')) return;

      const canvasRect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - canvasRect.left - BLOCK_W / 2;
      const y = e.clientY - canvasRect.top - BLOCK_H / 2;

      // Find default value from library
      let defaultVal = '';
      for (const category of Object.values(componentLibrary)) {
        const found = category.find(i => i.type === type);
        if (found) {
          defaultVal = found.defaultVal;
          break;
        }
      }

      addBlock(type, x, y, defaultVal);
    },
    [addBlock]
  );

  const handleMoveBlock = useCallback(
    (e: React.DragEvent<HTMLDivElement>, id: number) => {
      const raw = e.dataTransfer.getData('text/plain');
      if (raw !== `move-${id}`) return;

      const canvasRect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      const offsetX = parseInt(e.dataTransfer.getData('offsetX'));
      const offsetY = parseInt(e.dataTransfer.getData('offsetY'));

      const newX = e.clientX - canvasRect.left - offsetX;
      const newY = e.clientY - canvasRect.top - offsetY;

      moveBlock(id, newX, newY);
    },
    [moveBlock]
  );

  return { handleDropNew, handleMoveBlock };
}