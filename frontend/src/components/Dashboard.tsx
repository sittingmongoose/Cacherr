/**
 * Cacherr Dashboard Component
 * 
 * Main dashboard showing cache statistics, active sessions, and controls.
 */

import React, { useState, useEffect, useCallback } from 'react';
import type {
  CacheStats,
  CacheHealth,
  ActiveSession,
  CachedFile,
  CacheCycleResult,
} from '../types/cache';
import { formatBytes, formatRelativeTime, getHealthColor } from '../types/cache';
import * as api from '../services/api';

// ============================================================
// Sub-components
// ============================================================

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, color }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="text-sm font-medium text-gray-500">{title}</h3>
    <p className="mt-1 text-2xl font-semibold" style={{ color: color || '#1f2937' }}>
      {value}
    </p>
    {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
  </div>
);

interface HealthBadgeProps {
  health: CacheHealth;
}

const HealthBadge: React.FC<HealthBadgeProps> = ({ health }) => {
  const color = getHealthColor(health);
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
      style={{ backgroundColor: `${color}20`, color }}
    >
      {health.toUpperCase()}
    </span>
  );
};

interface SessionCardProps {
  session: ActiveSession;
}

const SessionCard: React.FC<SessionCardProps> = ({ session }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
    <div>
      <p className="font-medium text-gray-900">{session.title}</p>
      <p className="text-sm text-gray-500">
        {session.username} • {session.state}
      </p>
    </div>
    <div className="text-right">
      <p className="text-lg font-semibold text-blue-600">
        {session.progress.toFixed(0)}%
      </p>
    </div>
  </div>
);

interface FileRowProps {
  file: CachedFile;
  onUncache: (path: string) => void;
}

const FileRow: React.FC<FileRowProps> = ({ file, onUncache }) => {
  const fileName = file.path.split('/').pop() || file.path;
  
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2">
        <span className="text-sm font-medium text-gray-900" title={file.path}>
          {fileName}
        </span>
      </td>
      <td className="px-4 py-2">
        <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
          {file.source}
        </span>
      </td>
      <td className="px-4 py-2 text-sm text-gray-500">
        {formatBytes(file.size_bytes)}
      </td>
      <td className="px-4 py-2 text-sm text-gray-500">
        {formatRelativeTime(file.cached_at)}
      </td>
      <td className="px-4 py-2">
        <button
          onClick={() => onUncache(file.path)}
          className="text-red-600 hover:text-red-800 text-sm"
        >
          Remove
        </button>
      </td>
    </tr>
  );
};

// ============================================================
// Main Dashboard Component
// ============================================================

const Dashboard: React.FC = () => {
  // State
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [files, setFiles] = useState<CachedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [lastCycleResult, setLastCycleResult] = useState<CacheCycleResult | null>(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      const [statsRes, sessionsRes, filesRes] = await Promise.all([
        api.getCacheStats(),
        api.getSessions(),
        api.getCachedFiles(),
      ]);

      if (statsRes.success && statsRes.data) {
        setStats(statsRes.data);
      }
      if (sessionsRes.success && sessionsRes.data) {
        setSessions(sessionsRes.data.sessions);
      }
      if (filesRes.success && filesRes.data) {
        setFiles(filesRes.data.files);
      }

      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load and polling
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Action handlers
  const handleRunCycle = async () => {
    setActionLoading(true);
    try {
      const result = await api.runCacheCycle();
      if (result.success && result.data) {
        setLastCycleResult(result.data);
        fetchData();
      } else {
        setError(result.error);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleReconcile = async () => {
    setActionLoading(true);
    try {
      const result = await api.runReconciliation();
      if (result.success) {
        fetchData();
      } else {
        setError(result.error);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleEvict = async () => {
    setActionLoading(true);
    try {
      const result = await api.triggerEviction(false);
      if (result.success) {
        fetchData();
      } else {
        setError(result.error);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleUncache = async (path: string) => {
    if (!confirm(`Remove "${path.split('/').pop()}" from cache?`)) return;
    
    try {
      const result = await api.uncacheFile(path);
      if (result.success) {
        fetchData();
      } else {
        setError(result.error);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to uncache file');
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cacherr</h1>
              <p className="text-sm text-gray-500">Intelligent Plex Media Caching</p>
            </div>
            {stats && <HealthBadge health={stats.health} />}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-sm text-red-600 hover:text-red-800 mt-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Cache Size"
              value={stats.total_size_human}
              subtitle={stats.limit_human !== 'Unlimited' ? `of ${stats.limit_human}` : undefined}
            />
            <StatCard
              title="Used"
              value={`${stats.used_percent}%`}
              color={getHealthColor(stats.health)}
            />
            <StatCard
              title="Files Cached"
              value={stats.file_count}
            />
            <StatCard
              title="Active Sessions"
              value={sessions.length}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={handleRunCycle}
            disabled={actionLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {actionLoading ? 'Running...' : 'Run Cache Cycle'}
          </button>
          <button
            onClick={handleReconcile}
            disabled={actionLoading}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
          >
            Reconcile
          </button>
          <button
            onClick={handleEvict}
            disabled={actionLoading}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            Trigger Eviction
          </button>
        </div>

        {/* Last Cycle Result */}
        {lastCycleResult && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-medium text-green-800">Last Cache Cycle</h3>
            <p className="text-sm text-green-700 mt-1">
              Cached: {lastCycleResult.files_cached} files ({formatBytes(lastCycleResult.bytes_cached)}) •
              Restored: {lastCycleResult.files_restored} files •
              Duration: {lastCycleResult.duration_seconds}s
            </p>
          </div>
        )}

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Sessions */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b">
                <h2 className="text-lg font-medium">Active Sessions</h2>
              </div>
              <div className="p-4 space-y-3">
                {sessions.length === 0 ? (
                  <p className="text-gray-500 text-sm">No active sessions</p>
                ) : (
                  sessions.map((session, i) => (
                    <SessionCard key={i} session={session} />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Cached Files */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b">
                <h2 className="text-lg font-medium">Cached Files ({files.length})</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cached</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {files.slice(0, 20).map((file, i) => (
                      <FileRow key={i} file={file} onUncache={handleUncache} />
                    ))}
                  </tbody>
                </table>
                {files.length > 20 && (
                  <div className="px-4 py-2 text-sm text-gray-500 text-center border-t">
                    Showing 20 of {files.length} files
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
