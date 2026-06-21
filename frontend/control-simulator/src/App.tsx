
import "./App.css";
import React from 'react';

// Reusable Block Component
const Block = ({ x, y, width, height, children, className = "" }) => {
  return (
    <div
      className={`absolute border-2 border-gray-700 bg-white flex flex-col items-center justify-center text-center shadow-sm select-none ${className}`}
      style={{ left: x, top: y, width, height }}
    >
      {children}
    </div>
  );
};

// Reusable Fraction Component (for 1/s blocks)
const Fraction = ({ num, den, label }) => (
  <div className="flex flex-col items-center justify-center">
    <span className="text-sm font-bold">{num}</span>
    <div className="w-4 h-[2px] bg-black my-0.5"></div>
    <span className="text-sm font-bold">{den}</span>
    <span className="text-[9px] mt-1">{label}</span>
  </div>
);

export default function App() {
  return (
    <div className="w-full h-screen flex items-center justify-center bg-gray-50 p-8 overflow-auto">
      {/* Canvas Container with Scale to fit typical screens */}
      <div className="relative w-[900px] h-[700px] bg-white border border-gray-300 shadow-xl rounded-lg overflow-hidden font-sans text-[10px] transform scale-90 origin-top-left">
        
        {/* SVG Layer for connecting lines and arrows */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
            </marker>
            <marker id="arrow-down" viewBox="0 0 10 10" refX="5" refY="9" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 0 L 10 0 L 5 10 z" fill="#374151" />
            </marker>
          </defs>
          
          {/* Paths / Connections */}
          <g stroke="#374151" strokeWidth="1.5" fill="none">
            {/* Top Left Input Paths */}
            <path d="M 90 165 L 120 165 L 120 180 L 140 180" markerEnd="url(#arrow)" />
            <path d="M 90 270 L 120 270 L 120 185 L 140 185" markerEnd="url(#arrow)" />
            
            {/* Top Horizontal Paths */}
            <path d="M 200 180 L 240 180" markerEnd="url(#arrow)" />
            <path d="M 310 180 L 350 180" markerEnd="url(#arrow)" />
            <path d="M 440 180 L 480 180" markerEnd="url(#arrow)" />
            
            {/* Top Right Logic Paths */}
            <path d="M 525 165 L 525 115 L 570 115" markerEnd="url(#arrow)" />
            <path d="M 550 115 L 570 115" markerEnd="url(#arrow)" />
            <path d="M 640 115 L 660 115" markerEnd="url(#arrow)" />

            {/* Feedback Branches */}
            <path d="M 395 210 L 395 295 L 350 295" markerEnd="url(#arrow)" />
            <path d="M 290 380 L 290 295 L 350 295" markerEnd="url(#arrow)" />
            
            {/* Bottom Translational Paths */}
            <path d="M 430 475 L 480 475" markerEnd="url(#arrow)" />
            <path d="M 560 470 L 610 470" markerEnd="url(#arrow)" />
            <path d="M 690 470 L 740 470" markerEnd="url(#arrow)" />
            <path d="M 570 180 L 600 180" markerEnd="url(#arrow)" />
            
            {/* Slip Calculator Inputs */}
            <path d="M 520 490 L 520 580 L 480 580" markerEnd="url(#arrow)" />
            <path d="M 525 195 L 525 595 L 480 595" markerEnd="url(#arrow)" />
            <path d="M 390 310 L 450 310 L 450 610 L 480 610" markerEnd="url(#arrow)" />
            
            {/* Slip Calculator Outputs */}
            <path d="M 570 595 L 620 595" markerEnd="url(#arrow)" />
            <path d="M 570 615 L 620 615" markerEnd="url(#arrow)" />
            
            {/* Long Outer Feedback Loop */}
            <path d="M 680 605 L 750 605 L 750 400 L 270 400" markerEnd="url(#arrow)" />
          </g>
        </svg>

        {/* --------------------------------------------------- */}
        {/* Top Left Corner                                        */}
        <Block x={30} y={150} width={60} height={30} className="bg-gray-100">
          <span className="font-bold text-xs">In1</span>
        </Block>
        <Block x={30} y={250} width={60} height={40}>
          <span className="font-bold text-xs">Step</span>
        </Block>
        
        {/* Sum Block */}
        <Block x={140} y={150} width={60} height={60} className="rounded-full z-20 border-2 border-gray-700">
          <span className="font-bold text-xl leading-none">+</span>
          <span className="absolute -top-1 right-0 text-xs font-bold">-</span>
        </Block>

        {/* Top Path Blocks */}
        <Block x={240} y={165} width={70} height={30}>
          <span className="font-bold">1/J</span>
          <span className="text-[9px]">Gain3</span>
        </Block>
        <Block x={350} y={150} width={90} height={60} className="bg-gray-50">
          <Fraction num="1" den="s" label="Integrator" />
          <div className="text-[8px] absolute bottom-1">Limited</div>
        </Block>
        <Block x={480} y={165} width={90} height={30}>
          <span className="font-bold">Angular Velocity</span>
        </Block>

        {/* Top Right Logic */}
        <Block x={480} y={100} width={70} height={30}>
          <span className="font-bold">5</span>
          <span className="text-[9px]">Constant</span>
        </Block>
        <Block x={570} y={100} width={70} height={30}>
          <span className="font-bold text-xs">&lt;=</span>
          <span className="text-[8px]">Relational</span>
        </Block>
        <Block x={660} y={100} width={90} height={30} className="bg-red-100 border-red-500">
          <span className="font-bold text-red-600">STOP</span>
          <span className="text-[9px] text-red-500">Simulation</span>
        </Block>
        
        {/* Scopes */}
        <Block x={600} y={195} width={60} height={40} className="bg-gray-50">
          <span className="font-bold">Vel</span>
        </Block>
        <Block x={740} y={450} width={80} height={40} className="bg-gray-50">
          <span className="font-bold text-[9px]">Stopping_Distance</span>
        </Block>

        {/* --------------------------------------------------- */}
        {/* Middle Forces Section                                */}
        <Block x={180} y={335} width={80} height={60}>
          <div className="flex flex-col items-center">
            <span className="text-[8px]">In1</span>
            <span className="text-[8px]">In2</span>
          </div>
          <span className="font-bold text-[11px] mt-1">Friction</span>
          <span className="font-bold text-[9px] -mt-1">Calculator</span>
          <div className="flex flex-col items-center absolute right-1 top-0">
             <span className="text-[8px]">Out1</span>
          </div>
        </Block>
        
        <Block x={290} y={330} width={60} height={40} className="bg-gray-50">
          <span className="font-bold text-[10px]">Scope1</span>
        </Block>
        
        <Block x={270} y={380} width={40} height={40} className="bg-gray-100">
          <span className="font-bold text-lg">FN</span>
        </Block>
        <div className="absolute top-[380px] left-[320px] w-[60px] flex items-center justify-center z-10">
            <span className="bg-white px-1 text-[9px] text-gray-700 font-medium">Normal force</span>
        </div>

        {/* Block R and Mass */}
        <Block x={350} y={280} width={80} height={30}>
          <span className="font-bold">R</span>
          <span className="text-[8px]">Wheel Radius</span>
        </Block>
        <Block x={350} y={460} width={80} height={30}>
          <span className="font-bold">-K</span>
          <span className="text-[9px]">Mass</span>
        </Block>

        {/* Bottom Translational Paths */}
        <Block x={480} y={450} width={80} height={40} className="bg-gray-50">
          <Fraction num="1" den="s" label="Velocity" />
        </Block>
        <Block x={610} y={450} width={80} height={40} className="bg-gray-50">
          <Fraction num="1" den="s" label="Stopping" />
          <span className="text-[8px] -mt-1">Distance</span>
        </Block>

        {/* --------------------------------------------------- */}
        {/* Slip Calculator                                      */}
        <Block x={480} y={580} width={90} height={50}>
          <div className="flex justify-between w-full px-1 absolute top-0 text-[8px]">
             <span>In1</span>
             <span className="font-bold mt-2">slip</span>
          </div>
          <div className="flex justify-between w-full px-1 absolute top-3 text-[8px]">
             <span>In2</span>
          </div>
          <div className="flex justify-between w-full px-1 absolute top-6 text-[8px]">
             <span>In3</span>
             <span className="mt-1">slip rate</span>
          </div>
          <div className="absolute bottom-0 w-full text-[9px] font-medium">Slip calculator</div>
        </Block>

        <Block x={620} y={590} width={60} height={30}>
           <span className="font-bold">Slip</span>
        </Block>
        <Block x={620} y={640} width={60} height={30}>
           <span className="font-bold text-[9px]">Slip_rate</span>
        </Block>
      </div>
    </div>
  );
}