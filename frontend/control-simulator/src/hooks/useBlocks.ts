import { useState, useCallback, useRef } from "react";
import { type BlockData, type ConnectionData, type SubsystemData } from "../lib/data";

export function useBlocks() {
  const [blocks, setBlocks] = useState<BlockData[]>([]);
  const [connections, setConnections] = useState<ConnectionData[]>([]);
  const idCounter = useRef(0);

  const addBlock = useCallback(
    (type: string, x: number, y: number, defaultVal: string) => {
      const id = ++idCounter.current;
      const newBlock: BlockData = {
        id,
        type,
        x,
        y,
        value: defaultVal,
        subsystemData: type === "Subsystem" ? {
          inputPorts: ["In1"],
          outputPorts: ["Out1"],
          blocks: [],
          connections: [],
        } : undefined,
      };
      setBlocks((prev) => [...prev, newBlock]);
      return id;
    },
    []
  );

  const addConnection = useCallback(
    (
      from: number,
      to: number,
      direction: "left" | "right" | "top" | "bottom"
    ) => {
      setConnections((prev) => [...prev, { from, to, direction }]);
    },
    []
  );

  const moveBlock = useCallback((id: number, x: number, y: number) => {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, x, y } : b)));
  }, []);

  const updateBlockValue = useCallback((id: number, value: string) => {
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, value } : b)));
  }, []);

  const deleteBlock = useCallback((id: number) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
    setConnections((prev) => prev.filter((c) => c.from !== id && c.to !== id));
  }, []);

  const clearBlocks = useCallback(() => {
    setBlocks([]);
    setConnections([]);
    idCounter.current = 0; // RESET counter for fresh IDs
  }, []);

  const deleteConnection = useCallback((from: number, to: number) => {
    setConnections((prev) =>
      prev.filter((c) => !(c.from === from && c.to === to))
    );
  }, []);

  const updateSubsystem = useCallback((id: number, subsystemData: SubsystemData) => {
    setBlocks((prev) =>
      prev.map((b) =>
        b.id === id && b.type === "Subsystem"
          ? { ...b, subsystemData }
          : b
      )
    );
  }, []);

  return {
    blocks,
    connections,
    addBlock,
    addConnection,
    moveBlock,
    updateBlockValue,
    deleteBlock,
    clearBlocks,
    deleteConnection,
    updateSubsystem,
  };
}