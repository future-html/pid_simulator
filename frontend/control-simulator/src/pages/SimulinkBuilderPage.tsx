import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts';

// ─── API endpoint (CHANGE THIS to your Flask backend) ──────────────
// ❌ This should NOT be your frontend URL (e.g., not 'https://pid-simulator-9pft.vercel.app')
// ✅ Use your Flask server: e.g., 'http://127.0.0.1:3000' or deployed backend URL
const API_BASE = 'http://127.0.0.1:3000'; // ← UPDATE THIS

// ─── System configurations (unchanged) ──────────────────────────────
const SYSTEMS = {
  '1dof': {
    label: '1-DOF Mass-Spring-Damper',
    desc: 'x, dx · m·ddx + c·dx + k·x = F',
    payload: {
      state_vars: ['x', 'dx'],
      state_derivatives: ['dx', 'ddx'],
      targets: ['ddx'],
      equations: ['m*ddx + c*dx + k*x - F'],
      params: { m: 2.0, c: 0.8, k: 25.0, F: 5.0 },
      z0: [0.0, 0.0],
      t_end: 10.0,
      steps: 500,
    },
    colors: ['#64b5f6', '#42e695']
  },
  '2dof': {
    label: '2-DOF Coupled Mass-Spring',
    desc: 'x₁, x₂ · two masses with springs',
    payload: {
      state_vars: ['x1', 'x2', 'dx1', 'dx2'],
      state_derivatives: ['dx1', 'dx2', 'ddx1', 'ddx2'],
      targets: ['ddx1', 'ddx2'],
      equations: [
        'm1*ddx1 + (c1 + c2)*dx1 - c2*dx2 + (k1 + k2)*x1 - k2*x2 - F1',
        'm2*ddx2 - c2*dx1 + c2*dx2 - k2*x1 + k2*x2 - F2'
      ],
      params: { m1: 10.0, m2: 5.0, k1: 100.0, k2: 50.0, c1: 5.0, c2: 2.0, F1: 0.0, F2: 0.0 },
      z0: [1.0, 0.0, 0.0, 0.0],
      t_end: 10.0,
      steps: 1000,
    },
    colors: ['#64b5f6', '#42e695', '#ffb74d', '#ef5350']
  },
  'tank': {
    label: 'Tank Level',
    desc: 'h · A·dh = Qin − Qout',
    payload: {
      state_vars: ['h'],
      state_derivatives: ['dh'],
      targets: ['dh'],
      intermediates: { Qout: 'c * sqrt(h)' },
      conditions: {
        Qin: {
          'h > 3.5': '0.0',
          'default': 'input_flow'
        }
      },
      equations: ['dh - (Qin - Qout) / A'],
      params: { A: 1.5, c: 0.35, input_flow: 0.8 },
      z0: [0.5],
      t_end: 30.0,
      steps: 400,
    },
    colors: ['#42e695']
  },
  'ballbeam': {
    label: 'Ball & Beam (PD)',
    desc: 'r, θ · with PD controller',
    payload: {
      state_vars: ['r', 'theta', 'dr', 'dtheta'],
      state_derivatives: ['dr', 'dtheta', 'ddr', 'ddtheta'],
      targets: ['ddr', 'ddtheta'],
      equations: [
        '1.4 * mb * ddr + mb * g * sin(theta) - mb * r * dtheta**2',
        '(J_beam + mb * r**2) * ddtheta + 2 * mb * r * dr * dtheta + mb * g * r * cos(theta) - tau'
      ],
      intermediates: {
        tau: 'Kp_r * (r_target - r) - Kd_r * dr - Kp_theta * theta - Kd_theta * dtheta'
      },
      params: {
        mb: 0.1,
        J_beam: 0.05,
        g: 9.81,
        r_target: 0.0,
        Kp_r: 2.5,
        Kd_r: 1.2,
        Kp_theta: 5.0,
        Kd_theta: 1.5
      },
      z0: [0.4, 0.1, 0.0, 0.0],
      t_end: 8.0,
      steps: 400,
    },
    colors: ['#ffb74d', '#64b5f6', '#42e695', '#ef5350']
  },
  'abs': {
    label: 'ABS (Anti-lock Braking)',
    desc: 'vx, ω · with slip & friction',
    payload: {
      state_vars: ['vx', 'omega'],
      state_derivatives: ['dvx', 'domega'],
      targets: ['dvx', 'domega'],
      equations: [
        'dvx + Ff / mass',
        'domega - (T_road - Tb) / J'
      ],
      intermediates: {
        lambda_val: '(vx - omega * R) / vx',
        mu: '(1.2801 * (1.0 - exp(-23.99 * lambda_val)) - 0.52 * lambda_val) * exp(-0.03 * vx)',
        Ff: 'mu * mass * g',
        T_road: 'Ff * R'
      },
      conditions: {
        Tb: {
          'lambda_val > 0.20': '0.0',
          'default': 'torque'
        }
      },
      params: {
        mass: 250.0,
        torque: 1200.0,
        J: 1.0,
        R: 0.32,
        g: 9.81
      },
      z0: [30.0, 93.75],
      t_end: 3.0,
      steps: 300,
    },
    colors: ['#64b5f6', '#ef5350']
  }
};

const SYSTEM_KEYS = Object.keys(SYSTEMS);

// ─── API call using axios ────────────────────────────────────────────
async function runSimulation(payload) {
  try {
    const response = await axios.post(`${API_BASE}/api/simulate/universal`, payload, {
      headers: { 'Content-Type': 'application/json' },
    });
    return response.data;
  } catch (error) {
    // Extract error message from axios error response
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errMsg = error.response.data?.error || `HTTP ${error.response.status}`;
      throw new Error(errMsg);
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('No response from server. Please check your network and CORS settings.');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error(error.message || 'Request failed');
    }
  }
}

// ─── Main Component ──────────────────────────────────────────────────
export default function SimulinkBuilderPage() {
  // ... (all state, hooks, and handlers remain exactly the same) ...

  // ── State ──
  const [activeSystem, setActiveSystem] = useState('1dof');
  const [params, setParams] = useState(() => ({ ...SYSTEMS['1dof'].payload.params }));
  const [z0, setZ0] = useState(() => [...SYSTEMS['1dof'].payload.z0]);
  const [tEnd, setTEnd] = useState(SYSTEMS['1dof'].payload.t_end);
  const [steps, setSteps] = useState(SYSTEMS['1dof'].payload.steps);

  const [chartData, setChartData] = useState([]);
  const [stateVars, setStateVars] = useState(SYSTEMS['1dof'].payload.state_vars);
  const [colors, setColors] = useState(SYSTEMS['1dof'].colors);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRunTime, setLastRunTime] = useState(null);

  // ── Load system ──
  const loadSystem = useCallback((key) => {
    const sys = SYSTEMS[key];
    if (!sys) return;
    setActiveSystem(key);
    setParams({ ...sys.payload.params });
    setZ0([...sys.payload.z0]);
    setTEnd(sys.payload.t_end);
    setSteps(sys.payload.steps);
    setStateVars([...sys.payload.state_vars]);
    setColors([...sys.colors]);
    setChartData([]);
    setError(null);
    setLastRunTime(null);
  }, []);

  // ── Handlers ──
  const handleParamChange = useCallback((key, val) => {
    setParams((prev) => ({ ...prev, [key]: val }));
  }, []);

  const handleZ0Change = useCallback((idx, val) => {
    setZ0((prev) => {
      const next = [...prev];
      next[idx] = val;
      return next;
    });
  }, []);

  const resetParams = useCallback(() => {
    const sys = SYSTEMS[activeSystem];
    if (!sys) return;
    setParams({ ...sys.payload.params });
    setZ0([...sys.payload.z0]);
    setTEnd(sys.payload.t_end);
    setSteps(sys.payload.steps);
    setError(null);
  }, [activeSystem]);

  // ── Run simulation ──
  const runSim = useCallback(async () => {
    const sys = SYSTEMS[activeSystem];
    if (!sys) return;

    const payload = {
      state_vars: sys.payload.state_vars,
      state_derivatives: sys.payload.state_derivatives,
      targets: sys.payload.targets,
      equations: sys.payload.equations,
      params: { ...params },
      z0: [...z0],
      t_end: tEnd,
      steps: Math.floor(steps),
    };
    if (sys.payload.intermediates) {
      payload.intermediates = { ...sys.payload.intermediates };
    }
    if (sys.payload.conditions) {
      payload.conditions = { ...sys.payload.conditions };
    }

    setLoading(true);
    setError(null);
    const start = performance.now();

    try {
      const result = await runSimulation(payload);
      if (Array.isArray(result) && result.length > 0) {
        setChartData(result);
        setLastRunTime(((performance.now() - start) / 1000).toFixed(2));
      } else {
        throw new Error('Unexpected response format');
      }
    } catch (err) {
      setError(err.message || 'Simulation failed');
      setChartData([]);
    } finally {
      setLoading(false);
    }
  }, [activeSystem, params, z0, tEnd, steps]);

  // ── Keyboard shortcut ──
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        runSim();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [runSim]);

  // ── Load initial ──
  useEffect(() => {
    loadSystem('1dof');
  }, []);

  // ── Derived ──
  const z0Entries = useMemo(() => {
    const sys = SYSTEMS[activeSystem];
    if (!sys) return [];
    return sys.payload.state_vars.map((name, idx) => ({ name, idx, val: z0[idx] ?? 0 }));
  }, [activeSystem, z0]);

  // ── Custom Tooltip ──
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div className="bg-[#0e151e] border border-[#2a3648] rounded-xl px-4 py-3 text-sm text-[#e8edf5] shadow-2xl">
        <div className="text-[#7a8fa8] mb-1">t = {label.toFixed(3)}</div>
        {payload.map((p, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5 rounded-sm"
              style={{ background: p.color || p.stroke }}
            />
            <span>{p.name}:</span>
            <span className="font-medium text-white">{p.value.toFixed(4)}</span>
          </div>
        ))}
      </div>
    );
  };

  // ─── Render ───
  return (
    <div className="font-sans bg-[#0b0e14] text-[#e8edf5] min-h-screen p-6 max-w-7xl mx-auto">
      <div className="flex flex-col gap-6">

        {/* Header */}
        <header className="flex items-center justify-between flex-wrap gap-4 pb-4 border-b border-[#232a36]">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-[#64b5f6] to-[#42e695] bg-clip-text text-transparent">
            ⚙ Control System Simulator
          </h1>
          <span className="text-sm bg-[#1a2330] px-4 py-1.5 rounded-full text-[#8ba0c0] border border-[#2d3a4a]">
            Flask + React • Recharts
          </span>
        </header>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-[340px_1fr] gap-6">

          {/* ─── LEFT PANEL ─── */}
          <div className="flex flex-col gap-5">

            {/* System Selector */}
            <div className="bg-[#131a24] rounded-2xl border border-[#212b38] p-5">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[#7a8fa8] mb-4">
                <span className="w-2 h-2 rounded-full bg-[#64b5f6] inline-block" />
                System
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                {SYSTEM_KEYS.map((key) => {
                  const sys = SYSTEMS[key];
                  const isActive = activeSystem === key;
                  return (
                    <button
                      key={key}
                      onClick={() => loadSystem(key)}
                      className={`text-center p-3 rounded-xl border-2 transition-all text-sm font-medium leading-tight ${
                        isActive
                          ? 'bg-[#1a2a3e] border-[#64b5f6] text-white shadow-[0_0_20px_rgba(100,181,246,0.08)]'
                          : 'bg-[#1a2330] border-[#252f3e] text-[#b0c4de] hover:bg-[#1f2a3a] hover:border-[#3b4a60]'
                      }`}
                    >
                      {sys.label}
                      <span className={`block text-[10px] font-normal mt-0.5 ${
                        isActive ? 'text-[#8aafd0]' : 'text-[#6a7f98]'
                      }`}>
                        {sys.desc}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Parameters */}
            <div className="bg-[#131a24] rounded-2xl border border-[#212b38] p-5">
              <div className="flex items-center justify-between text-sm font-semibold uppercase tracking-wider text-[#7a8fa8] mb-4">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#ffb74d] inline-block" />
                  Parameters
                </span>
                <button
                  onClick={resetParams}
                  className="text-xs bg-transparent border border-[#2d3a4a] text-[#8ba0c0] px-3 py-1.5 rounded-lg hover:bg-[#1a2330] transition"
                >
                  ↺ Reset
                </button>
              </div>

              <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1 custom-scroll">
                {Object.entries(params).map(([key, val]) => (
                  <div key={key} className="flex items-center gap-2.5 bg-[#0e151e] px-3 py-1.5 rounded-xl border border-[#1e2836]">
                    <label className="text-sm font-medium text-[#b8ccdf] min-w-[54px] font-mono">{key}</label>
                    <input
                      type="number"
                      step="any"
                      value={val}
                      onChange={(e) => {
                        const raw = e.target.value;
                        if (raw === '') {
                          handleParamChange(key, 0);
                        } else {
                          const v = parseFloat(raw);
                          handleParamChange(key, isNaN(v) ? 0 : v);
                        }
                      }}
                      className="flex-1 bg-transparent border-none text-[#e8edf5] text-sm py-1.5 font-mono outline-none min-w-0"
                    />
                    <span className="text-xs text-[#5a7088] min-w-[40px] text-right font-mono">
                      {typeof val === 'number' ? val.toFixed(3) : val}
                    </span>
                  </div>
                ))}
              </div>

              {/* z0 */}
              {z0Entries.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#1a2330]">
                  <div className="text-sm font-medium text-[#7a8fa8] mb-2">Initial conditions (z₀)</div>
                  <div className="flex flex-wrap gap-2">
                    {z0Entries.map(({ name, idx, val }) => (
                      <div key={idx} className="flex items-center gap-1.5 bg-[#0e151e] px-3 py-1 rounded-xl border border-[#1e2836]">
                        <span className="text-xs text-[#b8ccdf] font-mono">{name}</span>
                        <input
                          type="number"
                          step="any"
                          value={val}
                          onChange={(e) => {
                            const raw = e.target.value;
                            if (raw === '') {
                              handleZ0Change(idx, 0);
                            } else {
                              const v = parseFloat(raw);
                              handleZ0Change(idx, isNaN(v) ? 0 : v);
                            }
                          }}
                          className="bg-transparent border-none text-[#e8edf5] text-sm w-16 font-mono outline-none text-right"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* t_end & steps */}
              <div className="flex gap-4 mt-4 pt-4 border-t border-[#1a2330]">
                <div className="flex-1">
                  <label className="text-xs text-[#7a8fa8] block mb-1">t_end</label>
                  <input
                    type="number"
                    step="0.5"
                    value={tEnd}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setTEnd(isNaN(v) ? 1 : v);
                    }}
                    className="w-full bg-[#0e151e] border border-[#1e2836] rounded-xl px-3 py-1.5 text-[#e8edf5] text-sm font-mono outline-none"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs text-[#7a8fa8] block mb-1">steps</label>
                  <input
                    type="number"
                    step="50"
                    min="50"
                    value={steps}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10);
                      setSteps(isNaN(v) ? 100 : Math.max(50, v));
                    }}
                    className="w-full bg-[#0e151e] border border-[#1e2836] rounded-xl px-3 py-1.5 text-[#e8edf5] text-sm font-mono outline-none"
                  />
                </div>
              </div>

              <button
                onClick={runSim}
                disabled={loading}
                className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-[#1a6bc4] to-[#3b8fd9] text-white font-semibold text-sm flex items-center justify-center gap-2.5 transition hover:shadow-lg hover:shadow-[#1a6bc4]/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Running…
                  </>
                ) : (
                  <>
                    ▶ Run Simulation
                    <span className="text-xs opacity-50 font-normal">(⌘⏎)</span>
                  </>
                )}
              </button>

              {error && (
                <div className="mt-3 p-3 bg-[#2a1418] border border-[#5a2830] rounded-xl text-[#ef8a8a] text-sm break-words">
                  ⚠ {error}
                </div>
              )}
            </div>
          </div>

          {/* ─── RIGHT PANEL ─── */}
          <div className="bg-[#131a24] rounded-2xl border border-[#212b38] p-5 overflow-hidden">
            <div className="flex items-center justify-between text-sm font-semibold uppercase tracking-wider text-[#7a8fa8] mb-4">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#42e695] inline-block" />
                Simulation Results
              </span>
              {lastRunTime && (
                <span className="text-xs font-normal text-[#4a5a72]">
                  {chartData.length} pts · {lastRunTime}s
                </span>
              )}
            </div>

            <div className="bg-[#0e151e] rounded-xl p-2 min-h-[380px] flex items-center justify-center">
              {chartData.length === 0 ? (
                <div className="text-center text-[#4a5a72] flex flex-col items-center gap-2">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#3b465a" strokeWidth="1.5">
                    <path d="M3 17L8 12L12 16L21 7" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M3 21H21" strokeLinecap="round" />
                  </svg>
                  <span>Run a simulation to see results</span>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a2330" />
                    <XAxis
                      dataKey="time"
                      stroke="#4a5a72"
                      tick={{ fill: '#6a7f98', fontSize: 11 }}
                      tickLine={false}
                      label={{ value: 'Time (s)', position: 'insideBottom', offset: -6, fill: '#6a7f98', fontSize: 12 }}
                    />
                    <YAxis
                      stroke="#4a5a72"
                      tick={{ fill: '#6a7f98', fontSize: 11 }}
                      tickLine={false}
                      label={{ value: 'State', angle: -90, position: 'insideLeft', fill: '#6a7f98', fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                      wrapperStyle={{ fontSize: '12px', color: '#b0c4de', paddingTop: '8px' }}
                      iconType="circle"
                      iconSize={8}
                    />
                    {stateVars.map((name, idx) => (
                      <Line
                        key={name}
                        type="monotone"
                        dataKey={name}
                        stroke={colors?.[idx % colors.length] || '#64b5f6'}
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 4, strokeWidth: 0 }}
                        isAnimationActive={false}
                      />
                    ))}
                    <ReferenceLine y={0} stroke="#2a3648" strokeDasharray="2 4" />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="flex items-center justify-between flex-wrap gap-3 pt-4 mt-4 border-t border-[#1a2330] text-sm text-[#6a7f98]">
              <div className="flex items-center gap-4 flex-wrap">
                <span>System: <strong className="text-[#b8ccdf]">{SYSTEMS[activeSystem]?.label || '—'}</strong></span>
                <span>States: <strong className="text-[#b8ccdf]">{stateVars.join(', ')}</strong></span>
              </div>
              <div>
                {chartData.length > 0 ? (
                  <span className="text-[#42e695]">✓ Ready</span>
                ) : (
                  <span className="text-[#4a5a72]">○ Idle</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}