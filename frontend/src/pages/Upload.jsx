import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  UploadIcon, 
  FileIcon, 
  AlertCircleIcon, 
  CheckCircleIcon,
  XIcon,
  InfoIcon,
  MapIcon,
  ShieldIcon
} from 'lucide-react'
import axios from 'axios'

const Upload = () => {
  const navigate = useNavigate()
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [formData, setFormData] = useState({
    sensor_type: 'mbes',
    output_format: 'netcdf',
    anonymize: true,
    add_overlay: false,
    qc_mode: 'auto'
  })
  
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      rejectedFiles.forEach(({ file, errors }) => {
        errors.forEach((error) => {
          toast.error(`${file.name}: ${error.message}`)
        })
      })
    }
    
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0
    }))
    
    setFiles(prev => [...prev, ...newFiles])
    toast.success(`${acceptedFiles.length} file(s) added`)
  }, [])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'application/json': ['.json'],
      'application/octet-stream': ['.las', '.laz']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true
  })
  
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }
  
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }
  
  const uploadFiles = async () => {
    if (files.length === 0) {
      toast.error('Please select at least one file')
      return
    }
    
    setUploading(true)
    
    try {
      const uploadPromises = files.map(async (fileObj) => {
        const formDataToSend = new FormData()
        formDataToSend.append('file', fileObj.file)
        formDataToSend.append('sensor_type', formData.sensor_type)
        formDataToSend.append('output_format', formData.output_format)
        formDataToSend.append('anonymize', formData.anonymize)
        formDataToSend.append('add_overlay', formData.add_overlay)
        formDataToSend.append('qc_mode', formData.qc_mode)
        
        const response = await axios.post('/api/v1/ingest/upload', formDataToSend, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setFiles(prev => prev.map(f => 
              f.id === fileObj.id ? { ...f, progress } : f
            ))
          }
        })
        
        return {
          ...fileObj,
          jobId: response.data.job_id,
          status: 'uploaded'
        }
      })
      
      const results = await Promise.all(uploadPromises)
      setFiles(results)
      
      toast.success('All files uploaded successfully!')
      navigate('/jobs')
      
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Ocean Mapping Data</h1>
        <p className="text-gray-600">
          Upload your ocean mapping data files for processing and conversion to Seabed 2030-compliant formats.
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Area */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Files</h2>
            
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <UploadIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              {isDragActive ? (
                <p className="text-lg text-primary-600">Drop the files here...</p>
              ) : (
                <div>
                  <p className="text-lg text-gray-600 mb-2">
                    Drag & drop files here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports CSV, TXT, JSON, LAS, LAZ files (max 100MB each)
                  </p>
                </div>
              )}
            </div>
            
            {/* File List */}
            {files.length > 0 && (
              <div className="mt-6">
                <h3 className="text-md font-semibold text-gray-900 mb-3">Selected Files</h3>
                <div className="space-y-2">
                  {files.map((fileObj) => (
                    <div key={fileObj.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileIcon className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{fileObj.file.name}</p>
                          <p className="text-xs text-gray-500">{formatFileSize(fileObj.file.size)}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {fileObj.status === 'uploading' && (
                          <div className="text-xs text-gray-500">{fileObj.progress}%</div>
                        )}
                        {fileObj.status === 'uploaded' && (
                          <CheckCircleIcon className="w-5 h-5 text-green-500" />
                        )}
                        <button
                          onClick={() => removeFile(fileObj.id)}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <XIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Configuration */}
        <div className="space-y-6">
          {/* Processing Options */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Processing Options</h2>
            
            <div className="space-y-4">
              {/* Sensor Type */}
              <div>
                <label className="label block mb-2">Sensor Type</label>
                <select
                  name="sensor_type"
                  value={formData.sensor_type}
                  onChange={handleInputChange}
                  className="input"
                >
                  <option value="mbes">Multi-Beam Echo Sounder (MBES)</option>
                  <option value="sbes">Single-Beam Echo Sounder (SBES)</option>
                  <option value="lidar">LiDAR</option>
                  <option value="singlebeam">Single-Beam</option>
                  <option value="auv">AUV Telemetry</option>
                </select>
              </div>
              
              {/* Output Format */}
              <div>
                <label className="label block mb-2">Output Format</label>
                <select
                  name="output_format"
                  value={formData.output_format}
                  onChange={handleInputChange}
                  className="input"
                >
                  <option value="netcdf">NetCDF (Seabed 2030)</option>
                  <option value="bag">BAG (Bathymetric Attributed Grid)</option>
                  <option value="geotiff">GeoTIFF (Raster)</option>
                </select>
              </div>
              
              {/* QC Mode */}
              <div>
                <label className="label block mb-2">Quality Control</label>
                <select
                  name="qc_mode"
                  value={formData.qc_mode}
                  onChange={handleInputChange}
                  className="input"
                >
                  <option value="auto">Automatic (AI + Rules)</option>
                  <option value="manual">Manual Review</option>
                  <option value="skip">Skip QC</option>
                </select>
              </div>
            </div>
          </div>
          
          {/* Privacy Options */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <ShieldIcon className="w-5 h-5 mr-2 text-green-600" />
              Privacy Options
            </h2>
            
            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="anonymize"
                  checked={formData.anonymize}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Anonymize vessel data
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="add_overlay"
                  checked={formData.add_overlay}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Add environmental overlays
                </span>
              </label>
            </div>
          </div>
          
          {/* Info Panel */}
          <div className="card p-6 bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <InfoIcon className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-blue-900 mb-2">Processing Information</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Files are processed securely</li>
                  <li>• Quality control is applied automatically</li>
                  <li>• Outputs are Seabed 2030 compliant</li>
                  <li>• Processing typically takes 2-5 minutes</li>
                </ul>
              </div>
            </div>
          </div>
          
          {/* Upload Button */}
          <button
            onClick={uploadFiles}
            disabled={files.length === 0 || uploading}
            className="w-full btn-primary py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'Uploading...' : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Upload
