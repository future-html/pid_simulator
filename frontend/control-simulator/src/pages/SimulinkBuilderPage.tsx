import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import axios from "axios";

// ==========================================
// 1. TypeScript Interfaces & Type Defs
// ==========================================

export interface SimulationPayload {
  state_vars: string[];
  state_derivatives: string[];
  targets: string[];
  params: Record<string, number>;
  intermediates: Record<string, string>;
  conditions?: Record<string, Record<string, string>>;
  equations: string[];
  z0: number[];
  t_end: number;
  steps: number;
}

export interface ChartPoint extends Record<string, number> {
  time: number;
}

export interface ApiResponse {
  success: boolean;
  data: ChartPoint[];
  equations: string[];
  initial_state: Record<string, number>;
}

type ModelType = 
  | "Ball & Beam" 
  | "Tank Level (PID)" 
  | "ABS Braking" 
  | "1-DOF Mass-Spring-Damper" 
  | "2-DOF Mass-Spring-Damper";

// ==========================================
// 2. Comprehensive Model Payloads Registry
// ==========================================

const MODEL_BASES: Record<ModelType, SimulationPayload> = {
  "Ball & Beam": {
    state_vars: ["r", "v"],
    state_derivatives: ["v", "a"],
    targets: ["a"],
    params: {
      g: 9.8,
      m: 0.1,
      R: 0.05,
      J: 0.0002,
      Kp: 10.0,
      Kd: 2.0,
      r_target: 0.5,
    },
    intermediates: { theta: "(Kp * (r_target - r) + Kd * (-v))" },
    conditions: {},
    equations: ["a = - (m * g / (J / (R**2) + m)) * theta"],
    z0: [0.0, 0.0],
    t_end: 5.0,
    steps: 500,
  },
  "Tank Level (PID)": {
    state_vars: ["h", "ei"],
    state_derivatives: ["dh_dt", "dei_dt"],
    targets: ["dh_dt", "dei_dt", "q_in"],
    params: { A: 1.0, Cv: 0.5, r: 2.0, Kp: 3.0, Ki: 0.1, Kd: 0.05 },
    intermediates: {},
    conditions: {},
    equations: [
      "dei_dt = (r - h)",
      "q_in = Kp * (r - h) + Ki * ei + Kd * (-dh_dt)",
      "dh_dt = (q_in - Cv * sqrt(h)) / A",
    ],
    z0: [1.0, 0.0],
    t_end: 20.0,
    steps: 500,
  },
  "ABS Braking": {
    state_vars: ["vx", "omega"],
    state_derivatives: ["vx_dot", "omega_dot"],
    targets: ["vx_dot", "omega_dot"],
    params: {
      m: 1500,
      mu: 0.8,
      Fn: 14715,
      R: 0.3,
      Jw: 2.0,
      max_Tb: 4500,
    },
    intermediates: { lambda_val: "(vx - omega * R) / vx" },
    conditions: { Tb: { "lambda_val > 0.2": "0.0", default: "max_Tb" } },
    equations: ["vx_dot = -mu * Fn / m", "omega_dot = (mu * R * Fn - Tb) / Jw"],
    z0: [30.0, 100.0],
    t_end: 3.0,
    steps: 300,
  },
  "1-DOF Mass-Spring-Damper": {
    state_vars: ["x", "v"],
    state_derivatives: ["v", "a"],
    targets: ["a"],
    params: {
      m: 2.0,
      c: 0.5,
      k: 20.0,
      F: 10.0,
    },
    intermediates: {},
    conditions: {},
    equations: ["m * a + c * v + k * x = F"],
    z0: [0.0, 0.0],
    t_end: 10.0,
    steps: 300,
  },
  "2-DOF Mass-Spring-Damper": {
    state_vars: ["x1", "v1", "x2", "v2"],
    state_derivatives: ["v1", "a1", "v2", "a2"],
    targets: ["a1", "a2"],
    params: {
      m1: 1.5,
      m2: 2.5,
      k1: 25.0,
      k2: 15.0,
      c1: 1.2,
      c2: 0.6,
      F1: 15.0,
      F2: 0.0,
    },
    intermediates: {},
    conditions: {},
    equations: [
      "m1 * a1 + (c1 + c2) * v1 - c2 * v2 + (k1 + k2) * x1 - k2 * x2 = F1",
      "m2 * a2 - c2 * v1 + c2 * v2 - k2 * x1 + k2 * x2 = F2",
    ],
    z0: [0.0, 0.0, 0.0, 0.0],
    t_end: 15.0,
    steps: 450,
  },
};

// ==========================================
// 3. React Functional Component Implementation
// ==========================================

const SimulinkBuilderPage: React.FC = () => {
  // State Hook Definitions with Explict Type Guards
  const [modelKey, setModelKey] = useState<ModelType>("Ball & Beam");
  const [payload, setPayload] = useState<SimulationPayload>(MODEL_BASES["Ball & Beam"]);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [equations, setEquations] = useState<string[]>([]);
  const [initialState, setInitialState] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState<boolean>(false);

  // Model Selection Dropdown Handler
  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newKey = e.target.value as ModelType;
    setModelKey(newKey);
    setPayload(MODEL_BASES[newKey]);
    setChartData([]);
    setEquations([]);
    setInitialState({});
  };

  // Parameter Value Mutation Handler
  const handleParamChange = (key: string, value: string) => {
    setPayload((prev) => ({
      ...prev,
      params: {
        ...prev.params,
        [key]: parseFloat(value) || 0,
      },
    }));
  };

  // Run Simulation HTTP Post Call via Axios
  const runSimulation = async () => {
    setLoading(true);
    try {
      const response = await axios.post<ApiResponse>(
        "http://127.0.0.1:3000/api/simulate/universal",
        payload,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      setChartData(response.data.data);
      setEquations(response.data.equations || []);
      setInitialState(response.data.initial_state || {});
    } catch (error) {
      console.error("Simulation Error:", error);
      alert("เกิดข้อผิดพลาดในการจำลอง (อาจเป็น Error ในสมการหรือ API ตีกลับ)");
    } finally {
      setLoading(false);
    }
  };

  // Isolate Line Tracking Variables for Recharts Plotting
  const lineKeys =
    chartData.length > 0
      ? Object.keys(chartData[0]).filter((key) => key !== "time")
      : [];

  const colors = [
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#ff7300",
    "#387908",
    "#a4de6c",
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        ⚙️ Interactive Simulation Lab
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Model Controller & Parameter Workspace Pane */}
        <div className="lg:col-span-3 bg-white p-6 rounded-xl shadow-md h-fit">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              เลือกโมเดล:
            </label>
            <select
              value={modelKey}
              onChange={handleModelChange}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(MODEL_BASES).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <h3 className="font-semibold text-gray-700 mb-3 border-b pb-2">
              ปรับเปลี่ยนค่า Parameters:
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
              {Object.keys(payload.params).map((paramKey) => (
                <div key={paramKey} className="flex flex-col">
                  <label className="text-xs text-gray-500 font-medium mb-1">
                    {paramKey}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={payload.params[paramKey]}
                    onChange={(e) =>
                      handleParamChange(paramKey, e.target.value)
                    }
                    className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={runSimulation}
            disabled={loading}
            className={`w-full py-2.5 rounded-lg text-white font-semibold shadow-md transition-all ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "⏳ กำลังจำลอง..." : "🚀 Run Simulation"}
          </button>
        </div>

        {/* Graphical Response Workspace Panel */}
        <div className="lg:col-span-9 bg-white p-6 rounded-xl shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-700">
              การตอบสนองของระบบ (System Response)
            </h2>
          </div>

          {/* SymPy Substituted System Output Expression Block */}
          {equations.length > 0 && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="text-sm font-semibold text-blue-800 mb-1">
                🧠 สมการที่ถูกแทนที่ค่าจริง (Substituted by SymPy):
              </div>
              <div className="text-xs font-mono text-gray-800 bg-blue-100/50 p-2 rounded border border-blue-100">
                {equations.map((eq, idx) => (
                  <div key={idx}>{eq}</div>
                ))}
              </div>
            </div>
          )}

          {/* Core State Boundary Initialization Metadata */}
          {Object.keys(initialState).length > 0 && (
            <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-md">
              <div className="text-sm font-semibold text-gray-800 mb-1">
                🎯 ค่าเริ่มต้นของ State (Initial Values):
              </div>
              <div className="text-xs font-mono text-gray-800 bg-white p-2 rounded border border-gray-100">
                {JSON.stringify(initialState, null, 2)}
              </div>
            </div>
          )}

          {chartData.length === 0 && !loading ? (
            <div className="h-[400px] flex items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
              กรุณากดปุ่ม "Run Simulation" เพื่อดูกราฟ
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={chartData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  label={{
                    value: "Time (s)",
                    position: "insideBottomRight",
                    offset: -10,
                  }}
                />
                <YAxis
                  label={{
                    value: "Values",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />

                {lineKeys.map((key, index) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulinkBuilderPage;