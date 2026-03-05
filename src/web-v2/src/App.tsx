import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll, useTransform, useSpring } from 'framer-motion';
import {
  Clock,
  TrendingDown,
  TrendingUp,
  Activity,
  Zap,
  Activity as ActivityIcon,
  Shield,
  HardDrive,
  Cpu,
  ChevronDown,
  Layers
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// --- Types ---
interface BatteryData {
  percent: number;
  status: string;
  voltage: number;
  temperature: number;
  charge_rate: number;
  health: number;
  time_left: number;
  power_source: string;
  cycle_count: number;
  history: { timestamp: string; percent: number }[];
}

interface DiskData {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  read_bytes_rate: number;
  write_bytes_rate: number;
  daily_growth_gb: number;
  days_to_full: number;
  prediction?: {
    probability: number;
    risk: 'low' | 'medium' | 'high';
  };
  history: { timestamp: string; used_gb: number }[];
}

// --- Components ---

const CustomCursor: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const outlineX = useSpring(0, { damping: 25, stiffness: 300 });
  const outlineY = useSpring(0, { damping: 25, stiffness: 300 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
      outlineX.set(e.clientX - 17);
      outlineY.set(e.clientY - 17);
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (['BUTTON', 'A', 'INPUT'].includes(target.tagName) || target.closest('.interactable') || target.closest('.glass-card')) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseover', handleMouseOver);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, [outlineX, outlineY]);

  return (
    <>
      <div
        className="custom-cursor"
        style={{
          left: mousePos.x - 3,
          top: mousePos.y - 3,
          transform: isHovering ? 'scale(2)' : 'scale(1)',
          opacity: isHovering ? 0 : 1
        }}
      />
      <motion.div
        className="custom-cursor-outline"
        style={{
          left: outlineX,
          top: outlineY,
          scale: isHovering ? 1.8 : 1,
          borderColor: isHovering ? 'var(--accent-color)' : 'rgba(255, 255, 255, 0.2)',
          backgroundColor: isHovering ? 'rgba(0, 243, 255, 0.05)' : 'transparent',
          borderWidth: isHovering ? '2px' : '1px'
        }}
      />
    </>
  );
};

const NeuralBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    const nodes: any[] = [];
    const nodeCount = 80;
    const mouse = { x: -1000, y: -1000 };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 1.5 + 0.5
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      nodes.forEach(node => {
        node.x += node.vx;
        node.y += node.vy;

        const dx = node.x - mouse.x;
        const dy = node.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          const force = (200 - dist) / 200;
          node.x += (dx / dist) * force * 2;
          node.y += (dy / dist) * force * 2;
        }

        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        ctx.fillStyle = 'rgba(0, 243, 255, 0.15)';
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150) {
            ctx.strokeStyle = `rgba(0, 243, 255, ${0.1 * (1 - dist / 150)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(animate);
    };

    animate();
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return <canvas ref={canvasRef} id="neuralNetwork" />;
};

const StatCard: React.FC<{
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  delay?: number;
}> = ({ title, icon, children, className = "", delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
    className={`glass-card ${className}`}
  >
    <div className="card-header">
      <span className="card-title">{title}</span>
      {icon && <span className="card-icon">{icon}</span>}
    </div>
    <div className="card-body">
      {children}
    </div>
  </motion.div>
);

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'battery' | 'disk'>('battery');
  const [batteryData, setBatteryData] = useState<BatteryData | null>(null);
  const [diskData, setDiskData] = useState<DiskData | null>(null);
  const [time, setTime] = useState(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));

  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.3], [1, 0.9]);
  const dashboardY = useTransform(scrollYProgress, [0, 0.4], [100, 0]);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })), 1000);

    const fetchData = async () => {
      try {
        const [bRes, dRes] = await Promise.all([
          fetch('/battery_data.json'),
          fetch('/disk_data.json')
        ]);

        if (bRes.ok) {
          const raw = await bRes.json();
          const mapped: BatteryData = {
            percent: raw.current.psutil.percent,
            status: raw.current.psutil.power_plugged ? 'charging' : 'discharging',
            voltage: raw.current.voltage,
            temperature: raw.current.temperature,
            charge_rate: raw.current.power_draw,
            health: raw.analytics.battery_health_percent,
            time_left: raw.analytics.estimated_runtime_minutes,
            power_source: raw.current.psutil.power_plugged ? 'AC' : 'BAT',
            cycle_count: raw.static.cycle_count,
            history: (raw.history || []).map((h: any) => ({
              timestamp: h.timestamp.split('T')[1].split('.')[0],
              percent: h.psutil.percent
            }))
          };
          setBatteryData(mapped);
        }

        if (dRes.ok) {
          const raw = await dRes.json();
          const mapped: DiskData = {
            total_gb: raw.current.usage.total_bytes / (1024 ** 3),
            used_gb: raw.current.usage.used_bytes / (1024 ** 3),
            free_gb: raw.current.usage.free_bytes / (1024 ** 3),
            read_bytes_rate: raw.current.io_rates.read_bytes_per_sec,
            write_bytes_rate: raw.current.io_rates.write_bytes_per_sec,
            daily_growth_gb: raw.analytics.daily_growth_bytes / (1024 ** 3),
            days_to_full: raw.analytics.estimated_days_to_full,
            prediction: {
              probability: raw.current.failure_probability,
              risk: raw.analytics.neural_health_label.toLowerCase() as any
            },
            history: (raw.history || []).map((h: any) => ({
              timestamp: h.timestamp.split('T')[1].split('.')[0],
              used_gb: h.usage.used_bytes / (1024 ** 3)
            }))
          };
          setDiskData(mapped);
        }
      } catch (e) {
        console.error("Fetch failed", e);
      }
    };

    fetchData();
    const dataTimer = setInterval(fetchData, 5000);

    return () => {
      clearInterval(timer);
      clearInterval(dataTimer);
    };
  }, []);

  return (
    <div className="neural-core">
      <CustomCursor />
      <div className="background-container">
        <NeuralBackground />
      </div>

      <motion.section
        className="hero-section"
        style={{ opacity: heroOpacity, scale: heroScale }}
      >
        <div className="hero-content container">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
            className="hero-badge"
          >
            <Shield size={14} className="highlight" />
            <span>NEURAL CORE V2.0 // ACTIVE</span>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="hero-title"
          >
            INTELLIGENCE <br /> <span className="highlight">REDEFINED</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="hero-subtitle"
          >
            Monitor. Analyze. Predict. Experience the next generation of hardware analytics with the precision of neural architecture.
          </motion.p>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5, duration: 1 }}
            className="scroll-indicator"
          >
            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="mouse-icon"
            >
              <ChevronDown size={20} />
            </motion.div>
            <span>Dive into the core</span>
          </motion.div>
        </div>
      </motion.section>

      <nav className="top-nav glass-effect">
        <div className="container nav-content">
          <div className="nav-brand">
            <Layers size={20} className="highlight" />
            <span>NEURAL CORE</span>
          </div>
          <div className="nav-links">
            <button
              className={`nav-btn ${activeTab === 'battery' ? 'active' : ''}`}
              onClick={() => setActiveTab('battery')}
            >
              01/BATTERY
            </button>
            <button
              className={`nav-btn ${activeTab === 'disk' ? 'active' : ''}`}
              onClick={() => setActiveTab('disk')}
            >
              02/DISK
            </button>
          </div>
          <div className="nav-info">
            <Clock size={16} />
            <span>{time}</span>
          </div>
        </div>
      </nav>

      <motion.main
        className="main-content container"
        style={{ y: dashboardY }}
      >
        <AnimatePresence mode="wait">
          {activeTab === 'battery' ? (
            <motion.div
              key="battery"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.5 }}
              className="dashboard-grid"
            >
              <StatCard title="ENERGY CORE" icon={<Zap className="highlight" />} className="card-large">
                <div className="gauge-viz">
                  <svg viewBox="0 0 200 200" className="gauge-svg">
                    <circle cx="100" cy="100" r="90" className="gauge-track" />
                    <motion.circle
                      cx="100" cy="100" r="90"
                      className="gauge-val"
                      strokeDasharray="565.48"
                      initial={{ strokeDashoffset: 565.48 }}
                      animate={{ strokeDashoffset: 565.48 - (565.48 * (batteryData?.percent || 0) / 100) }}
                      transition={{ duration: 2, ease: "easeOut" }}
                    />
                  </svg>
                  <div className="gauge-content">
                    <span className="val">{batteryData?.percent || '--'}<small>%</small></span>
                    <label>CAPACITY</label>
                  </div>
                </div>
                <div className="card-footer-stats">
                  <div className="footer-item">
                    <label>RUNTIME</label>
                    <span className="highlight">{batteryData?.time_left || '--'} MIN</span>
                  </div>
                  <div className="footer-item">
                    <label>SOURCE</label>
                    <span>{batteryData?.power_source?.toUpperCase() || '--'}</span>
                  </div>
                </div>
              </StatCard>

              <div className="stats-column">
                <StatCard title="SYSTEM STATUS" icon={<Activity />}>
                  <div className="status-badge-container">
                    <div className={`status-badge-premium ${batteryData?.status}`}>
                      <div className="pulse-ring"></div>
                      <span>{batteryData?.status?.toUpperCase() || 'OFFLINE'}</span>
                    </div>
                  </div>
                  <div className="metric-list">
                    <div className="metric-item">
                      <label>Battery Health</label>
                      <span className="val">{batteryData?.health || '--'}%</span>
                    </div>
                    <div className="progress-mini">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${batteryData?.health || 0}%` }}
                        className="progress-fill"
                      />
                    </div>
                    <div className="metric-item" style={{ marginTop: '1rem' }}>
                      <label>Cycle Count</label>
                      <span className="val">{batteryData?.cycle_count || '--'}</span>
                    </div>
                  </div>
                </StatCard>

                <div className="mini-grid">
                  <StatCard title="VOLT" className="mini">
                    <div className="mini-val">{batteryData?.voltage?.toFixed(1) || '--'}V</div>
                  </StatCard>
                  <StatCard title="TEMP" className="mini">
                    <div className="mini-val highlight">{batteryData?.temperature?.toFixed(1) || '--'}°C</div>
                  </StatCard>
                  <StatCard title="DRAW" className="mini">
                    <div className="mini-val">
                      {Math.abs(batteryData?.charge_rate || 0).toFixed(1)}W
                    </div>
                  </StatCard>
                  <StatCard title="FLUX" className="mini">
                    {batteryData && batteryData.charge_rate >= 0 ? <TrendingUp className="highlight" /> : <TrendingDown className="danger" />}
                  </StatCard>
                </div>
              </div>

              <StatCard title="ENERGY FLUX ARCHIVE" className="card-full" icon={<ActivityIcon />}>
                <div className="chart-wrapper">
                  <Line
                    data={{
                      labels: batteryData?.history.map(h => h.timestamp) || [],
                      datasets: [{
                        label: 'CHARGE',
                        data: batteryData?.history.map(h => h.percent) || [],
                        borderColor: '#00f3ff',
                        backgroundColor: (context) => {
                          const ctx = context.chart.ctx;
                          const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                          gradient.addColorStop(0, 'rgba(0, 243, 255, 0.2)');
                          gradient.addColorStop(1, 'rgba(0, 243, 255, 0)');
                          return gradient;
                        },
                        fill: true,
                        tension: 0.5,
                        pointRadius: 0,
                        borderWidth: 2
                      }]
                    }}
                    options={{
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false }, tooltip: { enabled: true, mode: 'index', intersect: false } },
                      scales: {
                        x: { display: false },
                        y: {
                          grid: { color: 'rgba(255,255,255,0.05)' },
                          ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 10, family: 'Inter' } }
                        }
                      }
                    }}
                  />
                </div>
              </StatCard>
            </motion.div>
          ) : (
            <motion.div
              key="disk"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.5 }}
              className="dashboard-grid"
            >
              <StatCard title="STORAGE NEURON" icon={<HardDrive className="highlight" />} className="card-large">
                <div className="gauge-viz">
                  <svg viewBox="0 0 200 200" className="gauge-svg">
                    <circle cx="100" cy="100" r="90" className="gauge-track" />
                    <motion.circle
                      cx="100" cy="100" r="90"
                      className="gauge-val disk"
                      strokeDasharray="565.48"
                      initial={{ strokeDashoffset: 565.48 }}
                      animate={{ strokeDashoffset: 565.48 - (565.48 * (diskData ? (diskData.used_gb / diskData.total_gb) : 0)) }}
                      transition={{ duration: 2, ease: "easeOut" }}
                    />
                  </svg>
                  <div className="gauge-content">
                    <span className="val">{diskData ? ((diskData.used_gb / diskData.total_gb) * 100).toFixed(0) : '--'}<small>%</small></span>
                    <label>SATURATION</label>
                  </div>
                </div>
                <div className="card-footer-stats">
                  <div className="footer-item">
                    <label>TOTAL</label>
                    <span className="highlight">{diskData?.total_gb.toFixed(0) || '--'} GB</span>
                  </div>
                  <div className="footer-item">
                    <label>FREE</label>
                    <span>{diskData?.free_gb.toFixed(1) || '--'} GB</span>
                  </div>
                </div>
              </StatCard>

              <div className="stats-column">
                <StatCard title="PREDICTIVE STABILITY" className={`prediction-card risk-${diskData?.prediction?.risk}`}>
                  <div className="prediction-hero">
                    <div className="risk-indicator">
                      <div className="outer-glow"></div>
                      <ActivityIcon size={32} />
                    </div>
                    <div className="risk-content">
                      <span className="risk-label">PROBABILITY</span>
                      <h3 className="risk-val">{((diskData?.prediction?.probability || 0) * 100).toExponential(3)}%</h3>
                    </div>
                  </div>
                  <div className="prediction-footer">
                    <div className="footer-text">
                      <Shield size={12} className="highlight" />
                      <span>HEALTH STATUS: <span className={`status-${diskData?.prediction?.risk}`}>{diskData?.prediction?.risk?.toUpperCase() || 'UNKNOWN'}</span></span>
                    </div>
                  </div>
                </StatCard>

                <div className="mini-grid">
                  <StatCard title="READ" className="mini">
                    <div className="mini-val">{(diskData?.read_bytes_rate || 0) / (1024 * 1024) > 1 ? `${((diskData?.read_bytes_rate || 0) / (1024 * 1024)).toFixed(1)} MB` : `${((diskData?.read_bytes_rate || 0) / 1024).toFixed(0)} KB`}</div>
                  </StatCard>
                  <StatCard title="WRITE" className="mini">
                    <div className="mini-val highlight">{(diskData?.write_bytes_rate || 0) / (1024 * 1024) > 1 ? `${((diskData?.write_bytes_rate || 0) / (1024 * 1024)).toFixed(1)} MB` : `${((diskData?.write_bytes_rate || 0) / 1024).toFixed(0)} KB`}</div>
                  </StatCard>
                  <StatCard title="GROWTH" className="mini">
                    <div className="mini-val">{(diskData?.daily_growth_gb || 0).toFixed(3)} G</div>
                  </StatCard>
                  <StatCard title="DAYS" className="mini">
                    <div className="mini-val">{diskData?.days_to_full && diskData.days_to_full > 999 ? '∞' : diskData?.days_to_full}</div>
                  </StatCard>
                </div>
              </div>

              <StatCard title="SATURATION DELTA" className="card-full" icon={<Cpu />}>
                <div className="chart-wrapper">
                  <Line
                    data={{
                      labels: diskData?.history.map(h => h.timestamp) || [],
                      datasets: [{
                        label: 'USED GB',
                        data: diskData?.history.map(h => h.used_gb) || [],
                        borderColor: '#ff00c3',
                        backgroundColor: (context) => {
                          const ctx = context.chart.ctx;
                          const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                          gradient.addColorStop(0, 'rgba(255, 0, 195, 0.1)');
                          gradient.addColorStop(1, 'rgba(255, 0, 195, 0)');
                          return gradient;
                        },
                        fill: true,
                        tension: 0.5,
                        pointRadius: 0,
                        borderWidth: 2
                      }]
                    }}
                    options={{
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales: {
                        x: { display: false },
                        y: {
                          grid: { color: 'rgba(255,255,255,0.05)' },
                          ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 10 } }
                        }
                      }
                    }}
                  />
                </div>
              </StatCard>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.main>

      <footer className="main-footer container">
        <div className="footer-content">
          <div className="footer-left">
            <span>TERMINAL ACCESS // L3-RESTRICTED</span>
          </div>
          <div className="footer-right">
            <span>SYSAUDIT: OK</span>
          </div>
        </div>
      </footer>

      <style>{`
        .neural-core {
          min-height: 200vh;
          background-color: var(--bg-color);
        }

        .hero-section {
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          position: sticky;
          top: 0;
          z-index: 1;
        }

        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--glass-border);
          border-radius: 100px;
          font-family: var(--font-display);
          font-size: 0.7rem;
          letter-spacing: 0.2em;
          margin-bottom: 2rem;
        }

        .hero-title {
          font-size: clamp(3rem, 10vw, 7rem);
          line-height: 0.9;
          margin-bottom: 1.5rem;
        }

        .hero-subtitle {
          font-size: 1.1rem;
          color: var(--text-secondary);
          max-width: 600px;
          margin: 0 auto 3rem;
          font-family: var(--font-accent);
        }

        .scroll-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
        }

        .top-nav {
          position: sticky;
          top: 0;
          z-index: 100;
          padding: 1rem 0;
          margin-bottom: 4rem;
        }

        .nav-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .nav-brand {
          display: flex;
          align-items: center;
          gap: 1rem;
          font-family: var(--font-display);
          font-weight: 700;
          letter-spacing: 0.1em;
        }

        .nav-links {
          display: flex;
          gap: 1rem;
          background: rgba(255, 255, 255, 0.03);
          padding: 0.3rem;
          border-radius: 8px;
          border: 1px solid var(--glass-border);
        }

        .nav-btn {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          padding: 0.5rem 1.2rem;
          font-family: var(--font-display);
          font-size: 0.75rem;
          cursor: pointer;
          border-radius: 6px;
          transition: var(--transition-fast);
        }

        .nav-btn.active {
          background: var(--accent-color);
          color: #000;
        }

        .nav-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-family: var(--font-display);
          font-size: 0.8rem;
          color: var(--text-secondary);
        }

        .main-content {
          padding-bottom: 10rem;
          position: relative;
          z-index: 2;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.5rem;
          grid-template-rows: auto auto;
        }

        .card-large {
          grid-column: span 1;
        }

        .stats-column {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .card-full {
          grid-column: span 2;
        }

        .glass-card {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .card-title {
          font-family: var(--font-display);
          font-size: 0.75rem;
          letter-spacing: 0.2em;
          color: var(--text-secondary);
        }

        .gauge-viz {
          position: relative;
          width: 220px;
          height: 220px;
          margin: 0 auto;
        }

        .gauge-svg {
          transform: rotate(-90deg);
        }

        .gauge-track {
          fill: none;
          stroke: rgba(255, 255, 255, 0.05);
          stroke-width: 12;
        }

        .gauge-val {
          fill: none;
          stroke: var(--accent-color);
          stroke-width: 12;
          stroke-linecap: round;
          filter: drop-shadow(0 0 8px var(--accent-glow));
        }

        .gauge-val.disk {
          stroke: var(--accent-secondary);
          filter: drop-shadow(0 0 8px rgba(255, 0, 195, 0.3));
        }

        .gauge-content {
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
        }

        .gauge-content .val {
          font-family: var(--font-display);
          font-size: 3rem;
          font-weight: 800;
          line-height: 1;
        }

        .gauge-content .val small {
          font-size: 1rem;
          color: var(--text-muted);
        }

        .gauge-content label {
          font-size: 0.6rem;
          letter-spacing: 0.3em;
          color: var(--text-secondary);
          margin-top: 0.5rem;
        }

        .card-footer-stats {
          display: flex;
          justify-content: space-around;
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid var(--glass-border);
        }

        .footer-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.3rem;
        }

        .footer-item label {
          font-size: 0.6rem;
          color: var(--text-muted);
          letter-spacing: 0.1em;
        }

        .footer-item span {
          font-family: var(--font-display);
          font-size: 1rem;
        }

        .status-badge-container {
          display: flex;
          justify-content: center;
          margin-bottom: 2rem;
        }

        .status-badge-premium {
          position: relative;
          padding: 0.4rem 1.2rem;
          border-radius: 4px;
          font-family: var(--font-display);
          font-size: 0.75rem;
          letter-spacing: 0.2em;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          overflow: hidden;
        }

        .status-badge-premium.charging { color: var(--success); }
        .status-badge-premium.discharging { color: var(--warning); }

        .pulse-ring {
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          background: currentColor;
          opacity: 0.1;
          animation: badgePulse 2s infinite;
        }

        @keyframes badgePulse {
          0% { transform: scale(0.9); opacity: 0.1; }
          50% { transform: scale(1.1); opacity: 0.2; }
          100% { transform: scale(0.9); opacity: 0.1; }
        }

        .metric-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .metric-item {
          display: flex;
          justify-content: space-between;
          font-size: 0.85rem;
        }

        .metric-item label { color: var(--text-secondary); }
        .metric-item .val { font-family: var(--font-display); }

        .progress-mini {
          height: 4px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
          overflow: hidden;
          margin-top: 0.5rem;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--accent-color), var(--success));
          border-radius: 10px;
        }

        .mini-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }

        .glass-card.mini {
          padding: 1rem;
          align-items: center;
          justify-content: center;
        }

        .mini-val {
          font-family: var(--font-display);
          font-size: 1.1rem;
          font-weight: 600;
        }

        .chart-wrapper {
          height: 300px;
          width: 100%;
        }

        .prediction-card {
          position: relative;
          overflow: hidden;
        }

        .prediction-card::after {
          content: '';
          position: absolute;
          top: 0; right: 0; width: 100px; height: 100px;
          background: radial-gradient(circle at top right, var(--accent-glow), transparent 70%);
          pointer-events: none;
        }

        .prediction-hero {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .risk-indicator {
          position: relative;
          width: 60px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 12px;
          border: 1px solid var(--glass-border);
        }

        .risk-val {
          font-family: var(--font-display);
          font-size: 1.8rem;
          font-weight: 700;
        }

        .risk-label {
          font-size: 0.6rem;
          color: var(--text-secondary);
          letter-spacing: 0.2em;
        }

        .status-low { color: var(--success); }
        .status-medium { color: var(--warning); }
        .status-high { color: var(--danger); }

        .main-footer {
          padding-top: 4rem;
          padding-bottom: 4rem;
          border-top: 1px solid var(--glass-border);
          color: var(--text-muted);
          font-size: 0.7rem;
          font-family: var(--font-display);
          letter-spacing: 0.1em;
        }

        .footer-content {
          display: flex;
          justify-content: space-between;
        }

        .danger { color: var(--danger); }

        @media (max-width: 900px) {
          .dashboard-grid { grid-template-columns: 1fr; }
          .card-full { grid-column: span 1; }
          .hero-title { font-size: 4rem; }
        }
      `}</style>
    </div>
  );
};

export default App;

