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
        "https://pid-simulator-one.vercel.app/api/simulate/universal",
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

  // Updated colors: pink, seablue, green, and other vibrant tones
  const colors = [
    "#ff4d6d", // pink
    "#00b4d8", // seablue
    "#06d6a0", // green
    "#ffb703", // yellow accent
    "#9b5de5", // purple
    "#f15bb5", // hot pink
  ];

  return (
    <>
      <style>{`
        /* ===== Dark Theme with Seablue, Pink & Green ===== */
        :root {
          --bg-primary: #0a0f1a;
          --bg-card: #1a2332;
          --text-primary: #e2e8f0;
          --text-secondary: #94a3b8;
          --accent-pink: #ff4d6d;
          --accent-seablue: #00b4d8;
          --accent-green: #06d6a0;
          --border-color: #2d3a4e;
          --input-bg: #1e293b;
          --shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        }

        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
          background-color: var(--bg-primary);
          color: var(--text-primary);
        }

        .app-container {
          padding: 2rem;
          max-width: 1400px;
          margin: 0 auto;
          min-height: 100vh;
        }

        /* Gradient header text: pink -> seablue -> green */
        .gradient-header {
          font-size: 2.5rem;
          font-weight: 800;
          margin-bottom: 2rem;
          background: linear-gradient(135deg, var(--accent-pink), var(--accent-seablue), var(--accent-green));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          text-fill-color: transparent;
          letter-spacing: -0.5px;
          line-height: 1.2;
        }

        .grid-container {
          display: grid;
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }

        @media (min-width: 1024px) {
          .grid-container {
            grid-template-columns: 1fr 3fr;
          }
        }

        .card {
          background: var(--bg-card);
          border-radius: 1.25rem;
          padding: 1.5rem;
          box-shadow: var(--shadow);
          border: 1px solid var(--border-color);
          backdrop-filter: blur(10px);
        }

        .control-panel {
          height: fit-content;
        }

        .select-model {
          margin-bottom: 1.5rem;
        }

        .select-model label {
          display: block;
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .model-select {
          width: 100%;
          padding: 0.75rem 1rem;
          border-radius: 0.75rem;
          border: 1px solid var(--border-color);
          background: var(--input-bg);
          color: var(--text-primary);
          font-weight: 500;
          outline: none;
          transition: all 0.2s ease;
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 1rem center;
        }

        .model-select:focus {
          border-color: var(--accent-seablue);
          box-shadow: 0 0 0 3px rgba(0,180,216,0.25);
        }

        .params-section h3 {
          font-size: 1rem;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid var(--border-color);
        }

        .params-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          max-height: 500px;
          overflow-y: auto;
          padding-right: 0.5rem;
        }

        .param-item {
          display: flex;
          flex-direction: column;
        }

        .param-item label {
          font-size: 0.75rem;
          color: var(--text-secondary);
          font-weight: 500;
          margin-bottom: 0.25rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .param-input {
          width: 100%;
          padding: 0.5rem 0.75rem;
          border-radius: 0.5rem;
          border: 1px solid var(--border-color);
          background: var(--input-bg);
          color: var(--text-primary);
          font-size: 0.9rem;
          transition: border 0.2s, box-shadow 0.2s;
        }

        .param-input:focus {
          outline: none;
          border-color: var(--accent-pink);
          box-shadow: 0 0 0 3px rgba(255,77,109,0.25);
        }

        .run-button {
          width: 100%;
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 0.75rem;
          font-weight: 700;
          font-size: 1rem;
          color: #fff;
          cursor: pointer;
          margin-top: 1.5rem;
          background: linear-gradient(135deg, var(--accent-seablue), var(--accent-green));
          box-shadow: 0 4px 15px rgba(0,180,216,0.3);
          transition: all 0.3s ease;
          letter-spacing: 0.5px;
        }

        .run-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(0,180,216,0.4);
          background: linear-gradient(135deg, #00c4e8, #2ecc71);
        }

        .run-button:disabled {
          background: #334155;
          color: #94a3b8;
          cursor: not-allowed;
          box-shadow: none;
        }

        .graph-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .graph-header h2 {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .info-box {
          padding: 1rem;
          border-radius: 0.75rem;
          margin-bottom: 1rem;
          font-size: 0.875rem;
        }

        .equations-box {
          background: rgba(0,180,216,0.1);
          border: 1px solid rgba(0,180,216,0.3);
        }

        .equations-box .label {
          color: #7dd3fc;
          font-weight: 600;
        }

        .initial-box {
          background: rgba(6,214,160,0.1);
          border: 1px solid rgba(6,214,160,0.3);
        }

        .initial-box .label {
          color: #86efac;
          font-weight: 600;
        }

        .mono-text {
          font-family: 'Fira Code', 'Cascadia Code', monospace;
          font-size: 0.8rem;
          background: rgba(0,0,0,0.2);
          padding: 0.5rem;
          border-radius: 0.5rem;
          margin-top: 0.5rem;
        }

        .placeholder-chart {
          height: 400px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          border: 2px dashed var(--border-color);
          border-radius: 0.75rem;
          background: rgba(255,255,255,0.02);
        }

        /* Recharts customization */
        .recharts-cartesian-grid-horizontal line,
        .recharts-cartesian-grid-vertical line {
          stroke: #2d3a4e;
        }
        .recharts-text {
          fill: var(--text-secondary);
        }
        .recharts-default-tooltip {
          background: var(--bg-card) !important;
          border: 1px solid var(--border-color) !important;
          border-radius: 0.5rem !important;
        }
        .recharts-tooltip-label {
          color: var(--text-primary) !important;
        }
      `}</style>

      <div className="app-container">
        <h1 className="gradient-header">
          ⚙️ Interactive Simulation Lab
        </h1>

        <div className="grid-container">
          {/* Model Controller & Parameter Workspace Pane */}
          <div className="card control-panel">
            <div className="select-model">
              <label>เลือกโมเดล:</label>
              <select
                value={modelKey}
                onChange={handleModelChange}
                className="model-select"
              >
                {Object.keys(MODEL_BASES).map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <div className="params-section">
              <h3>ปรับเปลี่ยนค่า Parameters:</h3>
              <div className="params-list">
                {Object.keys(payload.params).map((paramKey) => (
                  <div key={paramKey} className="param-item">
                    <label>{paramKey}</label>
                    <input
                      type="number"
                      step="any"
                      value={payload.params[paramKey]}
                      onChange={(e) =>
                        handleParamChange(paramKey, e.target.value)
                      }
                      className="param-input"
                    />
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="run-button"
            >
              {loading ? "⏳ กำลังจำลอง..." : "🚀 Run Simulation"}
            </button>
          </div>

          {/* Graphical Response Workspace Panel */}
          <div className="card">
            <div className="graph-header">
              <h2>การตอบสนองของระบบ (System Response)</h2>
            </div>

            {/* SymPy Substituted System Output Expression Block */}
            {equations.length > 0 && (
              <div className="info-box equations-box">
                <div className="label">🧠 สมการที่ถูกแทนที่ค่าจริง (Substituted by SymPy):</div>
                <div className="mono-text">
                  {equations.map((eq, idx) => (
                    <div key={idx}>{eq}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Core State Boundary Initialization Metadata */}
            {Object.keys(initialState).length > 0 && (
              <div className="info-box initial-box">
                <div className="label">🎯 ค่าเริ่มต้นของ State (Initial Values):</div>
                <div className="mono-text">
                  {JSON.stringify(initialState, null, 2)}
                </div>
              </div>
            )}

            {chartData.length === 0 && !loading ? (
              <div className="placeholder-chart">
                กรุณากดปุ่ม "Run Simulation" เพื่อดูกราฟ
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3a4e" />
                  <XAxis
                    dataKey="time"
                    stroke="#94a3b8"
                    label={{
                      value: "Time (s)",
                      position: "insideBottomRight",
                      offset: -10,
                      fill: "#94a3b8",
                    }}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    label={{
                      value: "Values",
                      angle: -90,
                      position: "insideLeft",
                      fill: "#94a3b8",
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a2332",
                      border: "1px solid #2d3a4e",
                      borderRadius: "0.5rem",
                      color: "#e2e8f0",
                    }}
                  />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    wrapperStyle={{ color: "#e2e8f0" }}
                  />

                  {lineKeys.map((key, index) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      stroke={colors[index % colors.length]}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 6, strokeWidth: 0 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default SimulinkBuilderPage;