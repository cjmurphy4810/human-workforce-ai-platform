import { NavLink } from 'react-router-dom'
import { Home, Search, BarChart2, Monitor, Activity } from 'lucide-react'
import { useHealth } from '../../hooks/useHealth'

const NAV = [
  { to: '/',          label: 'Home',      icon: Home,      end: true },
  { to: '/research',  label: 'Research',  icon: Search,    end: false },
  { to: '/analytics', label: 'Analytics', icon: BarChart2, end: false },
  { to: '/system',    label: 'System',    icon: Monitor,   end: false },
]

export default function Sidebar() {
  const { data: health } = useHealth()

  const statusColor =
    health?.status === 'healthy'  ? 'bg-green-500' :
    health?.status === 'degraded' ? 'bg-amber-500' :
    health             ? 'bg-red-500' :
                        'bg-slate-600'

  const statusLabel =
    health?.status === 'healthy'  ? 'Connected' :
    health?.status === 'degraded' ? 'Degraded'  :
    health             ? 'Offline'   :
                        'Connecting…'

  return (
    <aside className="w-60 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600/20 border border-blue-600/30 rounded-lg flex items-center justify-center">
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100 leading-tight">HWAI Platform</div>
            <div className="text-xs text-slate-500 leading-tight">Intelligence Dashboard</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-600/25'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800 border border-transparent'
              }`
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Status footer */}
      <div className="px-5 py-4 border-t border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${statusColor}`} />
          <span className="text-xs text-slate-400">{statusLabel}</span>
        </div>
        {health && (
          <div className="text-xs text-slate-600">
            API v{health.version} · {health.sources_configured} sources
          </div>
        )}
      </div>
    </aside>
  )
}
