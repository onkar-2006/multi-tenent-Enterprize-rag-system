import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LaunchpadPage from './pages/LaunchpadPage';
import HRPortalPage from './pages/HRPortalPage';
import ITPortalPage from './pages/ITPortalPage';
import SupportPortalPage from './pages/SupportPortalPage';
import SalesPortalPage from './pages/SalesPortalPage';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LaunchpadPage />} />
        <Route path="/hr" element={<HRPortalPage />} />
        <Route path="/it" element={<ITPortalPage />} />
        <Route path="/support" element={<SupportPortalPage />} />
        <Route path="/sales" element={<SalesPortalPage />} />
      </Routes>
    </Router>
  );
}
