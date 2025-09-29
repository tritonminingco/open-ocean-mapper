import React, { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import { Icon } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { 
  MapPinIcon, 
  DownloadIcon, 
  EyeIcon,
  InfoIcon,
  ActivityIcon
} from 'lucide-react'
import axios from 'axios'

// Fix for default markers in react-leaflet
delete Icon.Default.prototype._getIconUrl
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const Map = () => {
  const [mapData, setMapData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedJob, setSelectedJob] = useState(null)
  const [mapCenter, setMapCenter] = useState([40.7128, -74.0060]) // Default to NYC
  const [mapZoom, setMapZoom] = useState(10)
  
  useEffect(() => {
    fetchMapData()
  }, [])
  
  const fetchMapData = async () => {
    try {
      setLoading(true)
      // Mock data for demonstration
      const mockData = [
        {
          id: 'job-1',
          filename: 'mbes_survey_001.csv',
          sensor_type: 'mbes',
          status: 'completed',
          latitude: 40.7128,
          longitude: -74.0060,
          depth_range: [10, 150],
          quality_score: 0.95,
          total_points: 1250,
          created_at: '2024-01-15T10:30:00Z'
        },
        {
          id: 'job-2',
          filename: 'lidar_coastal_002.las',
          sensor_type: 'lidar',
          status: 'processing',
          latitude: 40.7589,
          longitude: -73.9851,
          depth_range: [0, 50],
          quality_score: 0.87,
          total_points: 890,
          created_at: '2024-01-15T11:15:00Z'
        },
        {
          id: 'job-3',
          filename: 'sbes_deep_003.txt',
          sensor_type: 'sbes',
          status: 'completed',
          latitude: 40.6892,
          longitude: -74.0445,
          depth_range: [200, 800],
          quality_score: 0.92,
          total_points: 2100,
          created_at: '2024-01-15T12:00:00Z'
        }
      ]
      
      setMapData(mockData)
      
      // Calculate map center from data
      if (mockData.length > 0) {
        const avgLat = mockData.reduce((sum, item) => sum + item.latitude, 0) / mockData.length
        const avgLon = mockData.reduce((sum, item) => sum + item.longitude, 0) / mockData.length
        setMapCenter([avgLat, avgLon])
      }
      
    } catch (error) {
      console.error('Error fetching map data:', error)
    } finally {
      setLoading(false)
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
  
  const getSensorIcon = (sensorType) => {
    switch (sensorType) {
      case 'mbes': return '🌊'
      case 'sbes': return '📡'
      case 'lidar': return '🔍'
      case 'auv': return '🤖'
      default: return '📊'
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
  
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="loading-spinner w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading map data...</p>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Ocean Mapping Data Visualization</h1>
        <p className="text-gray-600">
          Explore processed ocean mapping data on an interactive map with quality metrics and processing status.
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Map */}
        <div className="lg:col-span-3">
          <div className="card p-4 h-96 lg:h-[600px]">
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '100%', width: '100%' }}
              className="rounded-lg"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              {mapData.map((job) => (
                <Marker
                  key={job.id}
                  position={[job.latitude, job.longitude]}
                  eventHandlers={{
                    click: () => setSelectedJob(job)
                  }}
                >
                  <Popup>
                    <div className="p-2">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-lg">{getSensorIcon(job.sensor_type)}</span>
                        <span className="font-semibold text-sm">{job.filename}</span>
                      </div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Sensor:</span>
                          <span className="uppercase">{job.sensor_type}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Points:</span>
                          <span>{job.total_points.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Quality:</span>
                          <span>{(job.quality_score * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="space-y-6">
          {/* Legend */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Legend</h2>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <span className="text-lg">🌊</span>
                <div>
                  <div className="text-sm font-medium">MBES</div>
                  <div className="text-xs text-gray-500">Multi-Beam Echo Sounder</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-lg">📡</span>
                <div>
                  <div className="text-sm font-medium">SBES</div>
                  <div className="text-xs text-gray-500">Single-Beam Echo Sounder</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-lg">🔍</span>
                <div>
                  <div className="text-sm font-medium">LiDAR</div>
                  <div className="text-xs text-gray-500">Light Detection & Ranging</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-lg">🤖</span>
                <div>
                  <div className="text-sm font-medium">AUV</div>
                  <div className="text-xs text-gray-500">Autonomous Underwater Vehicle</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Status Legend */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Status</h2>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm">Completed</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm">Processing</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span className="text-sm">Failed</span>
              </div>
            </div>
          </div>
          
          {/* Selected Job Details */}
          {selectedJob && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h2>
              <div className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">{selectedJob.filename}</div>
                  <div className="text-xs text-gray-500">{formatDate(selectedJob.created_at)}</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Sensor Type:</span>
                    <span className="font-medium uppercase">{selectedJob.sensor_type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(selectedJob.status)}`}>
                      {selectedJob.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total Points:</span>
                    <span className="font-medium">{selectedJob.total_points.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Quality Score:</span>
                    <span className="font-medium">{(selectedJob.quality_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Depth Range:</span>
                    <span className="font-medium">{selectedJob.depth_range[0]}-{selectedJob.depth_range[1]}m</span>
                  </div>
                </div>
                
                <div className="pt-3 border-t border-gray-200">
                  <div className="flex space-x-2">
                    <button className="flex-1 btn-outline py-2 text-sm">
                      <EyeIcon className="w-4 h-4 mr-1" />
                      View
                    </button>
                    <button className="flex-1 btn-primary py-2 text-sm">
                      <DownloadIcon className="w-4 h-4 mr-1" />
                      Download
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Statistics */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Jobs:</span>
                <span className="font-medium">{mapData.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completed:</span>
                <span className="font-medium text-green-600">
                  {mapData.filter(job => job.status === 'completed').length}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Processing:</span>
                <span className="font-medium text-blue-600">
                  {mapData.filter(job => job.status === 'processing').length}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg Quality:</span>
                <span className="font-medium">
                  {(mapData.reduce((sum, job) => sum + job.quality_score, 0) / mapData.length * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Map
