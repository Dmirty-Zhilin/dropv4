import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getDomainDetail } from '../lib/enhanced-api-client'
import { Globe, Calendar, TrendingUp, Archive } from 'lucide-react'

const ReportDetailPage = () => {
  const { domain } = useParams()

  const { data, isLoading, error } = useQuery({
    queryKey: ['domain', domain],
    queryFn: () => getDomainDetail(domain),
    enabled: !!domain,
  })

  // Mock data for demonstration
  const mockData = {
    domain: domain,
    quality_score: 85,
    total_snapshots: 1234,
    years_covered: 15,
    ai_category: 'technology',
    is_good: true,
    recommended: true,
    has_snapshot: true,
    first_snapshot: '2008-03-15',
    last_snapshot: '2023-11-20',
    description: 'This domain shows consistent quality content over many years with good archive coverage.',
    snapshots_by_year: [
      { year: 2023, count: 156 },
      { year: 2022, count: 142 },
      { year: 2021, count: 138 },
      { year: 2020, count: 125 },
      { year: 2019, count: 118 }
    ]
  }

  const domainData = data || mockData

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading domain details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        <p>Error loading domain details. Showing demo data.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{domainData.domain}</h1>
        <p className="mt-2 text-gray-600">
          Detailed analysis and historical data
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{domainData.quality_score}</div>
            <p className="text-xs text-muted-foreground">
              Overall quality rating
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Snapshots</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{domainData.total_snapshots?.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Archive snapshots
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Years Covered</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{domainData.years_covered}</div>
            <p className="text-xs text-muted-foreground">
              Historical coverage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Category</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{domainData.ai_category}</div>
            <p className="text-xs text-muted-foreground">
              AI classification
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Domain Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Domain Information</CardTitle>
            <CardDescription>Basic details and status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Domain Name</label>
              <p className="text-lg font-semibold">{domainData.domain}</p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-500">First Snapshot</label>
              <p className="text-lg">{domainData.first_snapshot || 'N/A'}</p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-500">Last Snapshot</label>
              <p className="text-lg">{domainData.last_snapshot || 'N/A'}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <div className="flex space-x-2 mt-1">
                {domainData.is_good && (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Good Quality
                  </span>
                )}
                {domainData.recommended && (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                    Recommended
                  </span>
                )}
                {domainData.has_snapshot && (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                    Has Snapshots
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analysis Summary</CardTitle>
            <CardDescription>AI-generated insights</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700">
              {domainData.description || 'No description available for this domain.'}
            </p>
            
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2">Key Metrics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Quality Score:</span>
                  <span className="text-sm font-medium">{domainData.quality_score}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Archive Coverage:</span>
                  <span className="text-sm font-medium">{domainData.years_covered} years</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Snapshots:</span>
                  <span className="text-sm font-medium">{domainData.total_snapshots?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Snapshots by Year */}
      {domainData.snapshots_by_year && (
        <Card>
          <CardHeader>
            <CardTitle>Snapshots by Year</CardTitle>
            <CardDescription>Historical snapshot distribution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {domainData.snapshots_by_year.map((yearData) => (
                <div key={yearData.year} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{yearData.year}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(yearData.count / Math.max(...domainData.snapshots_by_year.map(d => d.count))) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600 w-12 text-right">{yearData.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ReportDetailPage

