import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Upload from './pages/Upload'
import Jobs from './pages/Jobs'
import Map from './pages/Map'
import Status from './pages/Status'

function App() {
  return (
    <div className="min-h-screen bg-gradient-ocean">
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/map" element={<Map />} />
          <Route path="/status" element={<Status />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App
