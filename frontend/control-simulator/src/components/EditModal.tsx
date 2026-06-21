import React from 'react';

interface EditModalProps {
  value: string;
  onValueChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
}

const EditModal: React.FC<EditModalProps> = ({
  value,
  onValueChange,
  onSave,
  onCancel,
  onDelete,
}) => {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-xl shadow-2xl w-[400px] border border-gray-700">
        <h2 className="text-lg font-bold text-white mb-2">Edit Block Parameter</h2>
        <p className="text-sm text-gray-400 mb-4">Modify the block's value or label</p>

        <label className="block text-sm font-medium text-gray-300 mb-1">Parameter Value</label>
        <input
          type="text"
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-6 placeholder-gray-500"
          autoFocus
        />

        <div className="flex justify-between gap-3">
          <button
            onClick={onDelete}
            className="px-4 py-2 bg-red-900 text-red-200 rounded hover:bg-red-800 transition"
          >
            Delete
          </button>
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition"
            >
              Cancel
            </button>
            <button
              onClick={onSave}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition shadow-sm"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditModal;