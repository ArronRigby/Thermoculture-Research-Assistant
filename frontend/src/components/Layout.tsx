import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import clsx from 'clsx';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: '\u2302' },              // ⌂
  { to: '/samples', label: 'Discourse Browser', icon: '\u2637' }, // ☷
  { to: '/analysis', label: 'Analysis & Insights', icon: '\u2261' }, // ≡
  { to: '/research', label: 'Research Workspace', icon: '\u270E' }, // ✎
  { to: '/collection', label: 'Collection', icon: '\u21BB' },     // ↻
  { to: '/settings', label: 'Settings', icon: '\u2699' },         // ⚙
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-gray-900 text-white transition-transform duration-200 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Brand header */}
        <div className="flex h-16 items-center gap-3 border-b border-gray-700 px-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-lg font-bold text-white">
            T
          </span>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-wide">
              Thermoculture
            </span>
            <span className="text-[10px] uppercase tracking-widest text-gray-400">
              Research Assistant
            </span>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 scrollbar-thin">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-600/20 text-primary-300'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white',
                    )
                  }
                >
                  <span className="w-5 text-center text-lg">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-gray-700 px-4 py-3">
          <p className="text-xs text-gray-500">v1.0.0</p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm lg:px-6">
          {/* Mobile hamburger */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 text-gray-600 hover:bg-gray-100 lg:hidden"
            aria-label="Open sidebar"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          {/* Title (visible on desktop) */}
          <h1 className="hidden text-lg font-semibold text-gray-800 lg:block">
            Thermoculture Research Assistant
          </h1>

          {/* Right side: user menu placeholder */}
          <div className="flex items-center gap-3">
            <button
              className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700 hover:bg-primary-200"
              aria-label="User menu"
            >
              U
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
