import React from 'react';
import { useQuery } from 'react-query';
import { 
  Camera, 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  Clock,
  Activity,
  Users,
  Eye
} from 'lucide-react';
import { dashboardAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatsCard from '../components/StatsCard';
import RecentDetections from '../components/RecentDetections';
import DetectionChart from '../components/DetectionChart';
import SystemHealth from '../components/SystemHealth';

/**
 * Main Dashboard component
 * Displays system overview, statistics, and recent activity
 */
const Dashboard: React.FC = () => {
  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery(
    'dashboard-stats',
    dashboardAPI.getStats,
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  // Fetch recent detections
  const { data: recentDetections, isLoading: detectionsLoading } = useQuery(
    'recent-detections',
    () => dashboardAPI.getRecentDetections({ limit: 10, hours: 24 }),
    {
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  );

  // Fetch detection trends
  const { data: trends } = useQuery(
    'detection-trends',
    () => dashboardAPI.getDetectionTrends({ days: 7 }),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  // Fetch system health
  const { data: systemHealth } = useQuery(
    'system-health',
    dashboardAPI.getSystemHealth,
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading dashboard
            </h3>
            <div className="mt-2 text-sm text-red-700">
              Failed to load dashboard statistics. Please try refreshing the page.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Smart Vehicle License Scanner - System Overview
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <span className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <Activity className="h-4 w-4 mr-2" />
            Live Monitoring
          </span>
        </div>
      </div>

      {/* System Status Alert */}
      {systemHealth && systemHealth.status !== 'healthy' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                System Status: {systemHealth.status}
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                {systemHealth.status === 'no_active_cameras' && 
                  'No cameras are currently active. Please start camera processing.'}
                {systemHealth.status === 'database_error' && 
                  'Database connection issues detected.'}
                {systemHealth.status === 'redis_error' && 
                  'Redis connection issues detected.'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Cameras"
          value={stats?.total_cameras || 0}
          subtitle={`${stats?.active_cameras || 0} active`}
          icon={Camera}
          color="blue"
          trend={stats?.active_cameras > 0 ? 'up' : 'down'}
        />
        
        <StatsCard
          title="License Plates"
          value={stats?.total_plates || 0}
          subtitle={`${stats?.authorized_plates || 0} authorized`}
          icon={Shield}
          color="green"
          trend="up"
        />
        
        <StatsCard
          title="Detections Today"
          value={stats?.detections_today || 0}
          subtitle={`${stats?.detections_this_hour || 0} this hour`}
          icon={Eye}
          color="purple"
          trend={stats?.detections_this_hour > 0 ? 'up' : 'down'}
        />
        
        <StatsCard
          title="Blacklisted Plates"
          value={stats?.blacklisted_plates || 0}
          subtitle="Security alerts"
          icon={AlertTriangle}
          color="red"
          trend="neutral"
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Trends Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Detection Trends (7 Days)
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              License plate detection activity over time
            </p>
          </div>
          <div className="card-body">
            {trends ? (
              <DetectionChart data={trends.daily_detections} />
            ) : (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              System Health
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Current system status and performance
            </p>
          </div>
          <div className="card-body">
            {systemHealth ? (
              <SystemHealth health={systemHealth} />
            ) : (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Recent Detections
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Latest license plate recognitions
              </p>
            </div>
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="h-4 w-4 mr-1" />
              Last 24 hours
            </div>
          </div>
        </div>
        <div className="card-body p-0">
          {detectionsLoading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner />
            </div>
          ) : (
            <RecentDetections detections={recentDetections || []} />
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">
            Quick Actions
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Common system operations
          </p>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <button className="btn btn-primary">
              <Camera className="h-4 w-4 mr-2" />
              Add Camera
            </button>
            <button className="btn btn-secondary">
              <Shield className="h-4 w-4 mr-2" />
              Manage Plates
            </button>
            <button className="btn btn-secondary">
              <TrendingUp className="h-4 w-4 mr-2" />
              View Reports
            </button>
            <button className="btn btn-secondary">
              <Users className="h-4 w-4 mr-2" />
              System Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
