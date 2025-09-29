import React, { useState, useEffect } from 'react'
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  AlertCircleIcon,
  DownloadIcon,
  EyeIcon,
  RefreshCwIcon,
  FilterIcon
} from 'lucide-react'
import axios from 'axios'

const Jobs = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  
  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])
  
  const fetchJobs = async () => {
    try {
      setLoading(true)
      // Mock data for demonstration
      const mockJobs = [
        {
          id: 'job-1',
          filename: 'mbes_survey_001.csv',
          sensor_type: 'mbes',
          output_format: 'netcdf',
          status: 'completed',
          progress: 100,
          created_at: '2024-01-15T10:30:00Z',
          completed_at: '2024-01-15T10:35:00Z',
          quality_score: 0.95,
          total_points: 1250,
          anonymized: true,
          overlay_applied: false,
          qc_mode: 'auto'
        },
        {
          id: 'job-2',
          filename: 'lidar_coastal_002.las',
          sensor_type: 'lidar',
          output_format: 'bag',
          status: 'processing',
          progress: 65,
          created_at: '2024-01-15T11:15:00Z',
          quality_score: 0.87,
          total_points: 890,
          anonymized: true,
          overlay_applied: true,
          qc_mode: 'auto'
        },
        {
          id: 'job-3',
          filename: 'sbes_deep_003.txt',
          sensor_type: 'sbes',
          output_format: 'geotiff',
          status: 'completed',
          progress: 100,
          created_at: '2024-01-15T12:00:00Z',
          completed_at: '2024-01-15T12:08:00Z',
          quality_score: 0.92,
          total_points: 2100,
          anonymized: false,
          overlay_applied: false,
          qc_mode: 'manual'
        },
        {
          id: 'job-4',
          filename: 'auv_mission_004.json',
          sensor_type: 'auv',
          output_format: 'netcdf',
          status: 'failed',
          progress: 0,
          created_at: '2024-01-15T13:30:00Z',
          error_message: 'Invalid file format',
          quality_score: 0.0,
          total_points: 0,
          anonymized: true,
          overlay_applied: false,
          qc_mode: 'auto'
        }
      ]
      
      setJobs(mockJobs)
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'processing':
        return <ClockIcon className="w-5 h-5 text-blue-500" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      default:
        return <AlertCircleIcon className="w-5 h-5 text-gray-500" />
    }
  }
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100'
      case 'processing': return 'text-blue-600 bg-blue-100'
      case 'failed': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  const formatDuration = (startTime, endTime) => {
    if (!endTime) return 'In progress...'
    const start = new Date(startTime)
    const end = new Date(endTime)
    const diffMs = end - start
    const diffMins = Math.floor(diffMs / 60000)
    const diffSecs = Math.floor((diffMs % 60000) / 1000)
    return `${diffMins}m ${diffSecs}s`
  }
  
  const filteredJobs = jobs.filter(job => {
    if (filter === 'all') return true
    return job.status === filter
  })
  
  const sortedJobs = [...filteredJobs].sort((a, b) => {
    const aVal = a[sortBy]
    const bVal = b[sortBy]
    
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })
  
  const handleDownload = (jobId) => {
    // Mock download functionality
    console.log('Downloading job:', jobId)
  }
  
  const handleView = (jobId) => {
    // Mock view functionality
    console.log('Viewing job:', jobId)
  }
  
  const handleRefresh = () => {
    fetchJobs()
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Processing Jobs</h1>
            <p className="text-gray-600">
              Monitor your ocean mapping data processing jobs and download results.
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="btn-outline px-4 py-2"
          >
            <RefreshCwIcon className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>
      
      {/* Filters and Controls */}
      <div className="card p-6 mb-8">
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FilterIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Filter:</span>
            </div>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="all">All Jobs</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Sort by:</span>
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input w-auto"
            >
              <option value="created_at">Created Date</option>
              <option value="filename">Filename</option>
              <option value="status">Status</option>
              <option value="quality_score">Quality Score</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="input w-auto"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Jobs List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="loading-spinner w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading jobs...</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedJobs.length === 0 ? (
            <div className="card p-12 text-center">
              <AlertCircleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
              <p className="text-gray-600">No jobs match your current filter criteria.</p>
            </div>
          ) : (
            sortedJobs.map((job) => (
              <div key={job.id} className="card p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{job.filename}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>Created: {formatDate(job.created_at)}</span>
                          {job.completed_at && (
                            <span>Completed: {formatDate(job.completed_at)}</span>
                          )}
                          <span>Duration: {formatDuration(job.created_at, job.completed_at)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600">Sensor Type</div>
                        <div className="font-medium uppercase">{job.sensor_type}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Output Format</div>
                        <div className="font-medium">{job.output_format}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Total Points</div>
                        <div className="font-medium">{job.total_points.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Quality Score</div>
                        <div className="font-medium">{(job.quality_score * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm">
                      <span className={`px-2 py-1 rounded-full ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                      {job.anonymized && (
                        <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                          Anonymized
                        </span>
                      )}
                      {job.overlay_applied && (
                        <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                          Overlay Applied
                        </span>
                      )}
                      <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
                        QC: {job.qc_mode}
                      </span>
                    </div>
                    
                    {job.error_message && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                        <div className="text-sm text-red-800">
                          <strong>Error:</strong> {job.error_message}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col space-y-2 ml-6">
                    {job.status === 'processing' && (
                      <div className="w-32">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{job.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                    
                    {job.status === 'completed' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleView(job.id)}
                          className="btn-outline px-3 py-1 text-sm"
                        >
                          <EyeIcon className="w-4 h-4 mr-1" />
                          View
                        </button>
                        <button
                          onClick={() => handleDownload(job.id)}
                          className="btn-primary px-3 py-1 text-sm"
                        >
                          <DownloadIcon className="w-4 h-4 mr-1" />
                          Download
                        </button>
                      </div>
                    )}
                    
                    {job.status === 'failed' && (
                      <button
                        onClick={() => handleView(job.id)}
                        className="btn-outline px-3 py-1 text-sm"
                      >
                        <EyeIcon className="w-4 h-4 mr-1" />
                        View Details
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default Jobs
