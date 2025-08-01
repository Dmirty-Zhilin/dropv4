import React from 'react'
import { Link, Outlet } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'

const Layout = () => {
  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-xl font-bold">
            Drop Analyzer
          </Link>
          <nav className="space-x-4">
            <Link to="/dashboard" className="text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            <Link to="/reports" className="text-gray-600 hover:text-gray-900">
              Reports
            </Link>
            <Link to="/settings" className="text-gray-600 hover:text-gray-900">
              Settings
            </Link>
            <Link to="/admin" className="text-gray-600 hover:text-gray-900">
              Admin
            </Link>
          </nav>
          <Button variant="ghost" onClick={handleLogout}>
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </header>
      
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <Outlet />
        </div>
      </main>
      
      <footer className="bg-gray-50 border-t py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-600">
          © 2023 Drop Analyzer. All rights reserved.
        </div>
      </footer>
    </div>
  )
}

export default Layout
