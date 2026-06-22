// import React from 'react';
// import { componentLibrary } from '../lib/data';

// interface ComponentPickerPopupProps {
//   x: number;
//   y: number;
//   onSelect: (type: string) => void;
//   onClose: () => void;
// }

// const ComponentPickerPopup: React.FC<ComponentPickerPopupProps> = ({ x, y, onSelect, onClose }) => {
//   return (
//     <div
//       className="absolute z-50 bg-gray-800 border border-gray-600 rounded-lg shadow-xl p-2 w-60"
//       style={{ left: x, top: y }}
//     >
//       <div className="flex justify-between items-center mb-2">
//         <span className="text-sm font-bold text-white">Add Block</span>
//         <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
//       </div>
//       {Object.entries(componentLibrary).map(([category, items]) => (
//         <div key={category} className="mb-2 last:mb-0">
//           <div className="text-xs font-semibold text-gray-400 uppercase mb-1">{category}</div>
//           <div className="grid grid-cols-2 gap-1">
//             {items.map((item) => (
//               <button
//                 key={item.type}
//                 onClick={() => onSelect(item.type)}
//                 className="text-left text-xs text-gray-200 hover:bg-gray-700 px-2 py-1 rounded flex items-center gap-1"
//               >
//                 <span className="text-gray-400">{item.label}</span>
//               </button>
//             ))}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };

// export default ComponentPickerPopup;
// can use later if needed, but for now, we will use the palette in the navbar instead of a popup.