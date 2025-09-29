import React, { useState, useEffect } from 'react'
import { 
  ActivityIcon, 
  ServerIcon, 
  DatabaseIcon, 
  CpuIcon,
  HardDriveIcon,
  WifiIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  XCircleIcon,
  RefreshCwIcon
} from 'lucide-react'
import axios from 'axios'

const Status = () => {
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  
  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])
  
  const fetchSystemStatus = async () => {
    try {
      setLoading(true)
      // Mock system status data
      const mockStatus = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        components: {
          api: {
            status: 'healthy',
            response_time_ms: 45,
            uptime_hours: 72.5
          },
          converter: {
            status: 'healthy',
            active_jobs: 2,
            queue_size: 3
          },
          qc: {
            status: 'healthy',
            ml_model_loaded: true,
            rules_engine_active: true
          },
          storage: {
            status: 'healthy',
            disk_usage_percent: 23.5,
            available_space_gb: 156.8
          }
        },
        metrics: {
          active_jobs: 2,
          completed_jobs: 45,
          failed_jobs: 3,
          total_processing_time_hours: 12.5,
          average_processing_time_minutes: 3.2,
          success_rate: 93.8
        },
        performance: {
          cpu_usage_percent: 25.3,
          memory_usage_mb: 512,
          memory_usage_percent: 45.2,
          network_io_mbps: 12.5
        }
      }
      
      setSystemStatus(mockStatus)
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching system status:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'degraded':
        return <AlertTriangleIcon className="w-5 h-5 text-yellow-500" />
      case 'unhealthy':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      default:
        return <AlertTriangleIcon className="w-5 h-5 text-gray-500" />
    }
  }
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'degraded': return 'text-yellow-600 bg-yellow-100'
      case 'unhealthy': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }
  
  const formatUptime = (hours) => {
    const days = Math.floor(hours / 24)
    const remainingHours = Math.floor(hours % 24)
    return `${days}d ${remainingHours}h`
  }
  
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  if (loading && !systemStatus) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="loading-spinner w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading system status...</p>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">System Status</h1>
            <p className="text-gray-600">
              Monitor the health and performance of the Open Ocean Mapper system.
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <div className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
            <button
              onClick={fetchSystemStatus}
              className="btn-outline px-4 py-2"
            >
              <RefreshCwIcon className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>
      
      {/* Overall Status */}
      <div className="card p-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {getStatusIcon(systemStatus?.status)}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Status</h2>
              <p className="text-gray-600">
                All systems operational - Version {systemStatus?.version}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemStatus?.status)}`}>
              {systemStatus?.status.toUpperCase()}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Uptime: {formatUptime(systemStatus?.components?.api?.uptime_hours || 0)}
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Components Status */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Component Status</h2>
            <div className="space-y-4">
              {Object.entries(systemStatus?.components || {}).map(([name, component]) => (
                <div key={name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(component.status)}
                    <div>
                      <div className="font-medium text-gray-900 capitalize">{name}</div>
                      <div className="text-sm text-gray-600">
                        {name === 'api' && `Response time: ${component.response_time_ms}ms`}
                        {name === 'converter' && `Active jobs: ${component.active_jobs}, Queue: ${component.queue_size}`}
                        {name === 'qc' && `ML model: ${component.ml_model_loaded ? 'Loaded' : 'Not loaded'}`}
                        {name === 'storage' && `Usage: ${component.disk_usage_percent}%`}
                      </div>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                    {component.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Metrics */}
        <div className="space-y-6">
          {/* Job Metrics */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Metrics</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Active Jobs:</span>
                <span className="font-medium text-blue-600">{systemStatus?.metrics?.active_jobs}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completed:</span>
                <span className="font-medium text-green-600">{systemStatus?.metrics?.completed_jobs}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Failed:</span>
                <span className="font-medium text-red-600">{systemStatus?.metrics?.failed_jobs}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Success Rate:</span>
                <span className="font-medium">{systemStatus?.metrics?.success_rate}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg Processing:</span>
                <span className="font-medium">{systemStatus?.metrics?.average_processing_time_minutes}m</span>
              </div>
            </div>
          </div>
          
          {/* Performance Metrics */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">CPU Usage</span>
                  <span className="font-medium">{systemStatus?.performance?.cpu_usage_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${systemStatus?.performance?.cpu_usage_percent}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Memory Usage</span>
                  <span className="font-medium">{systemStatus?.performance?.memory_usage_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${systemStatus?.performance?.memory_usage_percent}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Memory:</span>
                  <span className="font-medium">{formatBytes(systemStatus?.performance?.memory_usage_mb * 1024 * 1024)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Network I/O:</span>
                  <span className="font-medium">{systemStatus?.performance?.network_io_mbps} Mbps</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* System Info */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Information</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Version:</span>
                <span className="font-medium">{systemStatus?.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus?.status)}`}>
                  {systemStatus?.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last Check:</span>
                <span className="font-medium">
                  {systemStatus?.timestamp ? new Date(systemStatus.timestamp).toLocaleTimeString() : 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Status
