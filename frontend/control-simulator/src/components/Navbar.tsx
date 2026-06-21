import React from 'react';
import PaletteItem from './PaletteItem';
import { componentLibrary } from '../lib/data';

interface NavbarProps {
  onExport: () => void;
  onSendBackend: () => void;
  onClear: () => void;
  hasBlocks: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ onExport, onSendBackend, onClear, hasBlocks }) => {
  return (
    <div className="border-b border-gray-700 shadow-lg shadow-black/20 overflow-x-auto">
      <div className="flex items-center gap-4 p-4">
        <div className="flex-1 overflow-x-auto">
          {Object.entries(componentLibrary).map(([category, items]) => (
            <div key={category} className="inline-block mr-8">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">
                {category}
              </span>
              <div className="flex gap-3">
                {items.map((item) => (
                  <PaletteItem key={item.type} {...item} />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 flex-shrink-0 border-l border-gray-700 pl-4">
          <button
            onClick={onExport}
            className="px-3 py-2 bg-cyan-400 text-white text-sm rounded hover:bg-cyan-600 transition font-medium"
            title="Export diagram as JSON"
          >
            📥 Export
          </button>
          <button
            onClick={onSendBackend}
            className="px-3 py-2 bg-white text-cyan-400 text-sm rounded hover:bg-cyan-600 hover:text-white transition font-medium"
            title="Send to backend for simulation"
          >
            🔗 Backend
          </button>
          {hasBlocks && (
            <button
              onClick={onClear}
              className="px-3 py-2 bg-rose-500 text-white text-sm rounded hover:bg-rose-600 transition font-medium"
              title="Clear diagram"
            >
              🗑️ Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navbar;