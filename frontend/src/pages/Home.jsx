import React from 'react'
import { Link } from 'react-router-dom'
import { 
  UploadIcon, 
  MapIcon, 
  ShieldIcon, 
  ZapIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  GlobeIcon,
  DatabaseIcon
} from 'lucide-react'

const Home = () => {
  const features = [
    {
      icon: DatabaseIcon,
      title: 'Multi-Format Support',
      description: 'Process MBES, SBES, LiDAR, single-beam, and AUV telemetry data',
      color: 'text-blue-600'
    },
    {
      icon: ShieldIcon,
      title: 'Privacy-First Design',
      description: 'Deterministic anonymization with vessel ID hashing and GPS jittering',
      color: 'text-green-600'
    },
    {
      icon: ZapIcon,
      title: 'AI-Powered QC',
      description: 'Machine learning anomaly detection with deterministic rule fallbacks',
      color: 'text-purple-600'
    },
    {
      icon: GlobeIcon,
      title: 'Seabed 2030 Compliant',
      description: 'NetCDF, BAG, and GeoTIFF outputs meeting global standards',
      color: 'text-orange-600'
    }
  ]
  
  const stats = [
    { label: 'Data Formats', value: '5+' },
    { label: 'Output Formats', value: '3' },
    { label: 'Processing Speed', value: '1000 pts/sec' },
    { label: 'Quality Score', value: '95%+' }
  ]
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Transform Ocean Mapping Data for{' '}
          <span className="text-gradient">Seabed 2030</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Convert raw ocean mapping data into standardized, privacy-preserving outputs 
          with AI-powered quality control and environmental overlay capabilities.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="btn-primary px-8 py-3 text-lg inline-flex items-center space-x-2"
          >
            <UploadIcon className="w-5 h-5" />
            <span>Start Processing</span>
          </Link>
          <Link
            to="/map"
            className="btn-outline px-8 py-3 text-lg inline-flex items-center space-x-2"
          >
            <MapIcon className="w-5 h-5" />
            <span>View Map</span>
          </Link>
        </div>
      </div>
      
      {/* Stats Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
        {stats.map((stat, index) => (
          <div key={index} className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">{stat.value}</div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </div>
        ))}
      </div>
      
      {/* Features Section */}
      <div className="mb-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Enterprise-Grade Ocean Mapping Pipeline
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div key={index} className="card p-6 text-center hover:shadow-lg transition-shadow">
                <div className={`w-12 h-12 mx-auto mb-4 rounded-lg bg-gray-100 flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
      
      {/* Process Flow */}
      <div className="mb-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Simple 3-Step Process
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-primary-600">1</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Data</h3>
            <p className="text-gray-600">
              Upload your ocean mapping data files in supported formats (CSV, TXT, LAS, etc.)
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-primary-600">2</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Process & QC</h3>
            <p className="text-gray-600">
              Our AI-powered pipeline processes, validates, and quality-checks your data
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-primary-600">3</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Export & Share</h3>
            <p className="text-gray-600">
              Download Seabed 2030-compliant outputs or upload directly to global databases
            </p>
          </div>
        </div>
      </div>
      
      {/* CTA Section */}
      <div className="bg-gradient-to-r from-primary-600 to-ocean-600 rounded-2xl p-8 md:p-12 text-center text-white">
        <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p className="text-xl mb-8 opacity-90">
          Join the global effort to map the world's oceans by 2030
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center space-x-2"
          >
            <span>Upload Your Data</span>
            <ArrowRightIcon className="w-4 h-4" />
          </Link>
          <a
            href="https://seabed2030.org"
            target="_blank"
            rel="noopener noreferrer"
            className="border border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors inline-flex items-center space-x-2"
          >
            <span>Learn About Seabed 2030</span>
            <ArrowRightIcon className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}

export default Home
