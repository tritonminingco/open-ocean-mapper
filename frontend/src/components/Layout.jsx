import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  MapIcon, 
  UploadIcon, 
  ListIcon, 
  ActivityIcon,
  HomeIcon,
  GithubIcon,
  ExternalLinkIcon
} from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()
  
  const navigation = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Upload', href: '/upload', icon: UploadIcon },
    { name: 'Jobs', href: '/jobs', icon: ListIcon },
    { name: 'Map', href: '/map', icon: MapIcon },
    { name: 'Status', href: '/status', icon: ActivityIcon },
  ]
  
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-ocean-500 to-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">🌊</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gradient">Open Ocean Mapper</h1>
                  <p className="text-xs text-gray-500">Seabed 2030 Compliant</p>
                </div>
              </Link>
            </div>
            
            {/* Navigation */}
            <nav className="hidden md:flex space-x-8">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-primary-600 bg-primary-50'
                        : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>
            
            {/* External Links */}
            <div className="flex items-center space-x-4">
              <a
                href="https://github.com/tritonminingco/open-ocean-mapper"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <GithubIcon className="w-5 h-5" />
              </a>
              <a
                href="https://seabed2030.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <ExternalLinkIcon className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>
      
      {/* Mobile Navigation */}
      <div className="md:hidden bg-white border-b border-gray-200">
        <div className="px-4 py-2">
          <nav className="flex space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex-1 flex flex-col items-center py-2 px-1 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4 mb-1" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
      
      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-ocean-500 to-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">🌊</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Open Ocean Mapper</h3>
                  <p className="text-sm text-gray-600">Making ocean mapping data accessible and standardized</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Transform raw ocean mapping data into Seabed 2030-compliant outputs with privacy-first design 
                and AI-powered quality control.
              </p>
              <div className="flex space-x-4">
                <a
                  href="https://github.com/tritonminingco/open-ocean-mapper"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <GithubIcon className="w-5 h-5" />
                </a>
                <a
                  href="https://seabed2030.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <ExternalLinkIcon className="w-5 h-5" />
                </a>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><Link to="/upload" className="hover:text-primary-600 transition-colors">Upload Data</Link></li>
                <li><Link to="/jobs" className="hover:text-primary-600 transition-colors">Job Status</Link></li>
                <li><Link to="/map" className="hover:text-primary-600 transition-colors">Map View</Link></li>
                <li><Link to="/status" className="hover:text-primary-600 transition-colors">System Status</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-primary-600 transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-primary-600 transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-primary-600 transition-colors">Contributing</a></li>
                <li><a href="#" className="hover:text-primary-600 transition-colors">Support</a></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-sm text-gray-600">
                © 2024 Triton Mining Co. Licensed under Apache-2.0
              </p>
              <div className="flex space-x-6 mt-4 md:mt-0">
                <a href="#" className="text-sm text-gray-600 hover:text-primary-600 transition-colors">Privacy</a>
                <a href="#" className="text-sm text-gray-600 hover:text-primary-600 transition-colors">Terms</a>
                <a href="#" className="text-sm text-gray-600 hover:text-primary-600 transition-colors">Security</a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
