import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { getUserReports, deleteReport, exportReports } from '../lib/enhanced-api-client'
import { FileText, Download, Trash2, Calendar, Filter } from 'lucide-react'

const ReportsPage = () => {
  const [currentPage, setCurrentPage] = React.useState(1)
  const [selectedReports, setSelectedReports] = React.useState([])
  const [exportFormat, setExportFormat] = React.useState('json')
  const [exporting, setExporting] = React.useState(false)
  
  const queryClient = useQueryClient()
  
  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports', currentPage],
    queryFn: () => getUserReports(currentPage, 10),
    keepPreviousData: true
  })
  
  const deleteMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries(['reports'])
      setSelectedReports([])
    }
  })
  
  const handleSelectReport = (reportId, checked) => {
    if (checked) {
      setSelectedReports([...selectedReports, reportId])
    } else {
      setSelectedReports(selectedReports.filter(id => id !== reportId))
    }
  }
  
  const handleSelectAll = (checked) => {
    if (checked && reportsData?.reports) {
      setSelectedReports(reportsData.reports.map(r => r.id))
    } else {
      setSelectedReports([])
    }
  }
  
  const handleDeleteSelected = async () => {
    if (selectedReports.length === 0) return
    
    for (const reportId of selectedReports) {
      await deleteMutation.mutateAsync(reportId)
    }
  }
  
  const handleExport = async () => {
    setExporting(true)
    try {
      const result = await exportReports(exportFormat, selectedReports)
      
      if (exportFormat === 'json') {
        const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `reports_${new Date().toISOString().split('T')[0]}.json`
        a.click()
        URL.revokeObjectURL(url)
      } else if (exportFormat === 'csv') {
        const blob = new Blob([result.data], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `reports_${new Date().toISOString().split('T')[0]}.csv`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setExporting(false)
    }
  }
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  const getReportTypeLabel = (type) => {
    const types = {
      'domain_analysis': 'Анализ домена',
      'batch_analysis': 'Пакетный анализ',
      'llm_analysis': 'LLM анализ'
    }
    return types[type] || type
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Загрузка отчетов...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Отчеты</h1>
          <p className="text-gray-600 mt-1">Управление вашими отчетами анализа доменов</p>
        </div>
        
        <div className="flex gap-2">
          <Select value={exportFormat} onValueChange={setExportFormat}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="csv">CSV</SelectItem>
            </SelectContent>
          </Select>
          
          <Button 
            onClick={handleExport}
            disabled={exporting || selectedReports.length === 0}
            variant="outline"
          >
            <Download className="h-4 w-4 mr-2" />
            {exporting ? 'Экспорт...' : 'Экспорт'}
          </Button>
          
          <Button 
            onClick={handleDeleteSelected}
            disabled={selectedReports.length === 0 || deleteMutation.isLoading}
            variant="destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Удалить
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Ваши отчеты
              </CardTitle>
              <CardDescription>
                Всего отчетов: {reportsData?.total || 0}
              </CardDescription>
            </div>
            
            {reportsData?.reports && reportsData.reports.length > 0 && (
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={selectedReports.length === reportsData.reports.length}
                  onCheckedChange={handleSelectAll}
                />
                <span className="text-sm text-gray-600">Выбрать все</span>
              </div>
            )}
          </div>
        </CardHeader>
        
        <CardContent>
          {!reportsData?.reports || reportsData.reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет отчетов</h3>
              <p className="text-gray-600">
                Создайте ваш первый отчет, проанализировав домен на главной странице.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {reportsData.reports.map((report) => (
                <div key={report.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selectedReports.includes(report.id)}
                        onCheckedChange={(checked) => handleSelectReport(report.id, checked)}
                      />
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium">
                            {getReportTypeLabel(report.type)}
                          </h4>
                          {report.domain && (
                            <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {report.domain}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {formatDate(report.created_at)}
                          </div>
                          <div>ID: {report.id}</div>
                        </div>
                        
                        {report.data && Object.keys(report.data).length > 0 && (
                          <div className="mt-2 p-3 bg-gray-50 rounded text-sm">
                            <pre className="whitespace-pre-wrap">
                              {JSON.stringify(report.data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteMutation.mutate(report.id)}
                      disabled={deleteMutation.isLoading}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              
              {/* Pagination */}
              {reportsData.pages > 1 && (
                <div className="flex justify-center gap-2 mt-6">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    Назад
                  </Button>
                  
                  <span className="flex items-center px-3 text-sm">
                    Страница {currentPage} из {reportsData.pages}
                  </span>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(reportsData.pages, currentPage + 1))}
                    disabled={currentPage === reportsData.pages}
                  >
                    Вперед
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default ReportsPage

