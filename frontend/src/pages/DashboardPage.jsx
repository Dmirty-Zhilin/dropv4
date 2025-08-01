import React, { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Brain, Search, FileText } from 'lucide-react'
import { analyzeDomains, llmAnalyzeDomains } from '../lib/enhanced-api-client'

const DashboardPage = () => {
  const [domainsInput, setDomainsInput] = useState('')
  const [analysisResults, setAnalysisResults] = useState(null)
  const [selectedDomains, setSelectedDomains] = useState([])
  const [llmResults, setLlmResults] = useState(null)
  
  const analyzeMutation = useMutation({
    mutationFn: (domains) => analyzeDomains(domains),
    onSuccess: (data) => setAnalysisResults(data)
  })
  
  const llmMutation = useMutation({
    mutationFn: (domains) => llmAnalyzeDomains(domains),
    onSuccess: (data) => setLlmResults(data)
  })
  
  const handleAnalyze = () => {
    const domains = domainsInput.split('\n').filter(d => d.trim())
    if (domains.length > 0) {
      analyzeMutation.mutate(domains)
    }
  }
  
  const handleDomainSelect = (domain, checked) => {
    if (checked) {
      setSelectedDomains([...selectedDomains, domain])
    } else {
      setSelectedDomains(selectedDomains.filter(d => d !== domain))
    }
  }
  
  const handleLlmAnalyze = () => {
    const selectedData = analysisResults.domains.filter(d => selectedDomains.includes(d.domain))
    llmMutation.mutate(selectedData)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Domain Analysis</CardTitle>
          <CardDescription>Enter domains to analyze, one per line</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea 
            placeholder="example.com&#10;test.com"
            value={domainsInput}
            onChange={(e) => setDomainsInput(e.target.value)}
            rows={5}
          />
          <Button onClick={handleAnalyze} disabled={analyzeMutation.isLoading}>
            <Search className="mr-2 h-4 w-4" />
            {analyzeMutation.isLoading ? 'Analyzing...' : 'Analyze'}
          </Button>
          
          {analysisResults && (
            <div>
              <h3 className="font-semibold mb-2">Analysis Results</h3>
              <div className="space-y-2">
                {analysisResults.domains.map((result, index) => (
                  <div key={index} className="border p-2 rounded">
                    <div className="flex items-center gap-2">
                      <Checkbox 
                        checked={selectedDomains.includes(result.domain)}
                        onCheckedChange={(checked) => handleDomainSelect(result.domain, checked)}
                      />
                      <span>{result.domain}</span>
                    </div>
                    {result.error ? (
                      <p className="text-red-500">{result.error}</p>
                    ) : (
                      <div className="ml-6 text-sm">
                        <p>Quality Score: {result.quality_score}</p>
                        <p>Available: {result.is_available ? 'Yes' : 'No'}</p>
                        {/* Add more details as needed */}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {selectedDomains.length > 0 && (
                <Button onClick={handleLlmAnalyze} disabled={llmMutation.isLoading} className="mt-4">
                  <Brain className="mr-2 h-4 w-4" />
                  {llmMutation.isLoading ? 'Analyzing with LLM...' : 'LLM Analyze Selected'}
                </Button>
              )}
            </div>
          )}
          
          {llmResults && (
            <div className="mt-6">
              <h3 className="font-semibold mb-2">LLM Analysis Results</h3>
              {/* Display LLM results similarly */}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default DashboardPage