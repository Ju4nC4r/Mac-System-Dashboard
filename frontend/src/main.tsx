import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, Battery, Cpu, HardDrive, MemoryStick, RefreshCw, Search, Thermometer, X } from 'lucide-react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import './styles.css'

type Snapshot = { timestamp: number; cpu: { percentage: number; load: number; cores: number }; memory: { total: number; used: number; available: number; percentage: number }; disk: { total: number; used: number; free: number; percentage: number }; battery: { available: boolean; percentage: number | null; charging: boolean } }
type Process = { pid: number; name: string; command: string; cpu: number; memory: number; state: string }
const formatBytes = (value: number) => value >= 1e9 ? `${(value / 1e9).toFixed(1)} GB` : `${Math.round(value / 1e6)} MB`

function MetricCard({ icon, title, value, detail, percentage, tone = 'blue' }: { icon: ReactNode; title: string; value: string; detail: string; percentage: number; tone?: string }) {
  return <section className={`metric-card ${tone}`}><header>{icon}<h2>{title}</h2></header><strong>{value}</strong><p>{detail}</p><div className="progress"><i style={{ width: `${Math.min(100, percentage)}%` }} /></div><small>{percentage.toFixed(0)}% usado</small></section>
}

function Chart({ title, data, keyName, color, formatter }: { title: string; data: Snapshot[]; keyName: 'cpu' | 'memory'; color: string; formatter: (value: number) => string }) {
  const points = data.map(item => ({ time: new Date(item.timestamp).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' }), value: keyName === 'cpu' ? item.cpu.percentage : item.memory.used / 1e9 }))
  return <section className="chart-card"><h2>{title}</h2><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={points}><defs><linearGradient id={`fill-${keyName}`} x1="0" x2="0" y1="0" y2="1"><stop stopColor={color} stopOpacity={.36}/><stop offset="1" stopColor={color} stopOpacity={0}/></linearGradient></defs><XAxis dataKey="time" minTickGap={40}/><YAxis tickFormatter={formatter}/><Tooltip formatter={(value) => formatter(Number(value ?? 0))}/><Area type="monotone" dataKey="value" stroke={color} strokeWidth={2.5} fill={`url(#fill-${keyName})`} /></AreaChart></ResponsiveContainer></div></section>
}

export function App() {
  const [overview, setOverview] = useState<Snapshot | null>(null)
  const [history, setHistory] = useState<Snapshot[]>([])
  const [processes, setProcesses] = useState<Process[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Process | null>(null)
  const [notice, setNotice] = useState('')
  const load = async () => {
    const [current, trend, list] = await Promise.all(['/api/overview', '/api/history', '/api/processes'].map(url => fetch(url).then(res => res.json())))
    setOverview(current); setHistory(trend); setProcesses(list)
  }
  useEffect(() => { load(); const timer = window.setInterval(load, 3000); return () => clearInterval(timer) }, [])
  const filtered = useMemo(() => processes.filter(item => item.name.toLowerCase().includes(query.toLowerCase())).slice(0, 14), [processes, query])
  const act = async (kind: 'terminate' | 'force') => {
    if (!selected || !window.confirm(`${kind === 'force' ? 'Forzar la finalización' : 'Finalizar'} de ${selected.name}? Puede perderse trabajo sin guardar.`)) return
    const response = await fetch(`/api/processes/${selected.pid}/${kind}`, { method: 'POST' }).then(res => res.json())
    setNotice(response.message); setSelected(null); load()
  }
  if (!overview) return <main className="loading">Cargando métricas del Mac…</main>
  const { cpu, memory, disk, battery } = overview
  return <main><nav><div className="brand"><Activity/><div><h1>mac-system-dashboard</h1><p>Monitor local de este Mac</p></div></div><button className="refresh" onClick={load}><RefreshCw/>Actualizar</button></nav>
    <div className="metrics"><MetricCard icon={<Cpu/>} title="CPU" value={`${cpu.percentage}%`} detail={`Carga ${cpu.load} · ${cpu.cores} núcleos`} percentage={cpu.percentage}/><MetricCard icon={<MemoryStick/>} title="Memoria" value={formatBytes(memory.used)} detail={`de ${formatBytes(memory.total)} · ${formatBytes(memory.available)} libre`} percentage={memory.percentage} tone="green"/><MetricCard icon={<HardDrive/>} title="Disco" value={formatBytes(disk.used)} detail={`de ${formatBytes(disk.total)} · ${formatBytes(disk.free)} libre`} percentage={disk.percentage}/><MetricCard icon={battery.available ? <Battery/> : <Thermometer/>} title="Batería" value={battery.available ? `${battery.percentage}%` : 'No disponible'} detail={battery.available ? (battery.charging ? 'Cargando' : 'En batería') : 'Este Mac no informa batería'} percentage={battery.percentage ?? 0} tone="amber"/></div>
    <div className="charts"><Chart title="Uso de CPU" data={history} keyName="cpu" color="#4b9cff" formatter={value => `${value}%`}/><Chart title="Uso de memoria" data={history} keyName="memory" color="#65d46e" formatter={value => `${value} GB`}/></div>
    <section className="process-section"><div className="process-table"><header><div><h2>Procesos</h2><p>Selecciona un proceso para actuar sobre él.</p></div><label><Search/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar proceso"/></label></header><table><thead><tr><th>Proceso</th><th>CPU</th><th>Memoria</th><th>Estado</th></tr></thead><tbody>{filtered.map(item => <tr className={selected?.pid === item.pid ? 'selected' : ''} onClick={() => setSelected(item)} key={item.pid}><td><b>{item.name}</b><small>PID {item.pid}</small></td><td>{item.cpu}%</td><td>{formatBytes(item.memory)}</td><td><span className="state">{item.state}</span></td></tr>)}</tbody></table></div><aside><h2>Acción seleccionada</h2>{selected ? <><h3>{selected.name}</h3><p>PID {selected.pid}. Las acciones requieren confirmación.</p><button className="danger" onClick={() => act('terminate')}><X/>Finalizar proceso</button><button className="outline" onClick={() => act('force')}>Forzar finalización</button></> : <p>Elige un proceso de la tabla para ver las acciones disponibles.</p>}{notice && <p className="notice">{notice}</p>}</aside></section>
  </main>
}
const root = document.getElementById('root')
if (root) createRoot(root).render(<App />)
