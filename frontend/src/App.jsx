import React, { useState, useRef, useCallback, useEffect } from 'react'
import { 
  Play, Square, Loader2, CheckCircle2, ChevronRight, ChevronDown,
  FlaskConical, Search, Target, Lightbulb, Microscope, 
  GitBranch, Brain, RotateCcw, Database, BarChart3, FileSearch
} from 'lucide-react'

// =============================================================================
// Pipeline Configurations
// =============================================================================

const PIPELINES = {
  drug_discovery: {
    id: 'drug_discovery',
    name: 'Drug Discovery Pipeline',
    description: '6-agent hypothesis generation with dynamic routing',
    icon: FlaskConical,
    placeholder: "Enter research question... e.g., 'Can we develop a selective PLK1 inhibitor targeting the polo-box domain?'",
    agents: {
      target_hypothesis: { 
        name: 'Target Hypothesis', 
        role: 'Hypothesis Formulation', 
        Icon: Target,
      },
      literature_evidence: { 
        name: 'Literature Evidence', 
        role: 'Evidence Synthesis', 
        Icon: Search,
      },
      druggability: { 
        name: 'Druggability', 
        role: 'Target Assessment', 
        Icon: FlaskConical,
      },
      novelty: { 
        name: 'Novelty Analysis', 
        role: 'Competitive Intelligence', 
        Icon: Lightbulb,
      },
      preclinical_design: { 
        name: 'Preclinical Design', 
        role: 'Experimental Planning', 
        Icon: Microscope,
      },
      controller: { 
        name: 'Controller', 
        role: 'Decision & Routing', 
        Icon: GitBranch,
      }
    },
    agentOrder: [
      'target_hypothesis',
      'literature_evidence', 
      'druggability',
      'novelty',
      'preclinical_design',
      'controller'
    ],
    hasScores: true,
    hasLoops: true
  },
  research_gap: {
    id: 'research_gap',
    name: 'Research Gap Finder',
    description: 'Identify under-explored areas in scientific literature',
    icon: FileSearch,
    placeholder: "Enter research domain... e.g., 'smoking cessation interventions in emergency departments'",
    agents: {
      query_planner: { 
        name: 'Query Planner', 
        role: 'Search Strategy', 
        Icon: Search,
      },
      data_fetcher: { 
        name: 'Data Fetcher', 
        role: 'Literature Retrieval', 
        Icon: Database,
      },
      aggregator: { 
        name: 'Aggregator', 
        role: 'Statistical Analysis', 
        Icon: BarChart3,
      },
      literature_analyzer: { 
        name: 'Literature Analyzer', 
        role: 'Pattern Recognition', 
        Icon: Brain,
      },
      gap_synthesizer: { 
        name: 'Gap Synthesizer', 
        role: 'Hypothesis Generation', 
        Icon: Lightbulb,
      }
    },
    agentOrder: [
      'query_planner',
      'data_fetcher',
      'aggregator',
      'literature_analyzer',
      'gap_synthesizer'
    ],
    hasScores: false,
    hasLoops: false
  }
}

// =============================================================================
// Components
// =============================================================================

// Pipeline Selector Dropdown
function PipelineSelector({ selectedPipeline, onSelect, disabled }) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  const pipeline = PIPELINES[selectedPipeline]
  const PipelineIcon = pipeline.icon

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`flex items-center gap-3 px-4 py-2 rounded-lg border transition-colors ${
          disabled 
            ? 'bg-zinc-100 border-zinc-200 cursor-not-allowed' 
            : 'bg-white border-zinc-300 hover:border-amber-400 cursor-pointer'
        }`}
      >
        <PipelineIcon size={20} className="text-amber-500" />
        <div className="text-left">
          <div className="text-sm font-medium text-zinc-900">{pipeline.name}</div>
          <div className="text-xs text-zinc-500">{pipeline.description}</div>
        </div>
        <ChevronDown size={16} className={`text-zinc-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-white border border-zinc-200 rounded-lg shadow-lg z-50 overflow-hidden min-w-full">
          {Object.values(PIPELINES).map((p) => {
            const Icon = p.icon
            return (
              <button
                key={p.id}
                onClick={() => {
                  onSelect(p.id)
                  setIsOpen(false)
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-zinc-50 transition-colors text-left ${
                  selectedPipeline === p.id ? 'bg-amber-50' : ''
                }`}
              >
                <Icon size={20} className={selectedPipeline === p.id ? 'text-amber-500' : 'text-zinc-400'} />
                <div className="flex-1 text-left">
                  <div className="text-sm font-medium text-zinc-900">{p.name}</div>
                  <div className="text-xs text-zinc-500">{p.description}</div>
                </div>
                {selectedPipeline === p.id && (
                  <CheckCircle2 size={16} className="text-amber-500 ml-auto flex-shrink-0" />
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

// Left Panel - Agent Step Item
function AgentStep({ agentId, agent, status, thinking, isExpanded, onToggle }) {
  if (!agent) return null
  
  const { Icon } = agent
  
  const getStatusColor = () => {
    if (status === 'complete') return 'text-emerald-500'
    if (status === 'thinking') return 'text-amber-500'
    if (status === 'working') return 'text-blue-500'
    return 'text-zinc-400'
  }

  return (
    <div>
      <button
        onClick={onToggle}
        className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-zinc-100 transition-colors text-left ${
          status !== 'waiting' ? 'bg-zinc-100/50' : ''
        }`}
      >
        <Icon size={18} className={getStatusColor()} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${status === 'waiting' ? 'text-zinc-500' : 'text-zinc-900'}`}>
              {agent.name}
            </span>
            {status !== 'waiting' && status !== 'complete' && (
              <span className={`text-xs ${getStatusColor()}`}>
                {status === 'thinking' ? 'Reasoning...' : 'Generating...'}
              </span>
            )}
          </div>
          <span className="text-xs text-zinc-500">{agent.role}</span>
        </div>
        {status === 'complete' && <CheckCircle2 size={16} className="text-emerald-500" />}
        {(status === 'thinking' || status === 'working') && <Loader2 size={16} className="text-amber-500 animate-spin" />}
        <ChevronRight 
          size={16} 
          className={`text-zinc-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
        />
      </button>
      
      {isExpanded && thinking && (
        <div className="px-4 py-2 ml-6 border-l-2 border-amber-200">
          <div className="flex items-center gap-2 text-xs text-amber-600 mb-1">
            <Brain size={12} />
            <span>Reasoning</span>
          </div>
          <p className="text-xs text-zinc-600 leading-relaxed">
            {thinking}
          </p>
        </div>
      )}
    </div>
  )
}

// Strip markdown formatting from text
function stripMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/^#+\s*/gm, '')
    .replace(/`([^`]+)`/g, '$1')
}

// Right Panel - Output Section
function OutputSection({ agentId, agent, output, isStreaming }) {
  if (!agent || !output) return null
  
  const { Icon } = agent
  const cleanOutput = stripMarkdown(output)

  return (
    <div className="mb-6 pb-6 border-b border-zinc-200 last:border-0">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={18} className="text-amber-500" />
        <h3 className="text-sm font-semibold text-zinc-900">{agent.name}</h3>
        {isStreaming && (
          <span className="text-xs text-blue-500 flex items-center gap-1">
            <Loader2 size={12} className="animate-spin" />
            Generating
          </span>
        )}
      </div>
      <div className="bg-zinc-50 rounded-lg p-4 border border-zinc-200">
        <div className="text-sm text-zinc-700 whitespace-pre-wrap leading-relaxed">
          {cleanOutput}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-amber-500 animate-pulse ml-0.5" />
          )}
        </div>
      </div>
    </div>
  )
}

// Score Pills (Drug Discovery only)
function ScorePill({ label, score }) {
  if (score === null || score === undefined) {
    return (
      <div className="px-2 py-1 rounded text-xs font-mono text-zinc-400 bg-zinc-100">
        {label}: --
      </div>
    )
  }
  const percentage = Math.round(score * 100)
  const color = score >= 0.5 ? 'text-emerald-700 bg-emerald-100' : 'text-amber-700 bg-amber-100'
  
  return (
    <div className={`px-2 py-1 rounded text-xs font-mono ${color}`}>
      {label}: {percentage}%
    </div>
  )
}

// Decision Banner (Drug Discovery)
function DecisionBanner({ decision, scores, iterations, pipelineType }) {
  if (!decision) return null
  
  // For research gap, show completion differently
  if (pipelineType === 'research_gap') {
    return (
      <div className="p-4 rounded-lg border mb-6 bg-emerald-50 border-emerald-300">
        <div className="flex items-center gap-3">
          <CheckCircle2 size={24} className="text-emerald-600" />
          <div>
            <div className="text-lg font-bold text-emerald-700">Analysis Complete</div>
            <div className="text-xs text-zinc-600">
              Research gaps identified • {iterations} iteration{iterations !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>
    )
  }
  
  const isGo = decision.toUpperCase() === 'GO'
  
  return (
    <div className={`p-4 rounded-lg border mb-6 ${
      isGo ? 'bg-emerald-50 border-emerald-300' : 'bg-red-50 border-red-300'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isGo ? (
            <CheckCircle2 size={24} className="text-emerald-600" />
          ) : (
            <div className="w-6 h-6 rounded-full border-2 border-red-600" />
          )}
          <div>
            <div className={`text-lg font-bold ${isGo ? 'text-emerald-700' : 'text-red-700'}`}>
              {isGo ? 'GO' : 'NO-GO'}
            </div>
            <div className="text-xs text-zinc-600">
              {isGo ? 'Approved for experimental validation' : 'Requires refinement'}
              {' • '}{iterations} iteration{iterations > 1 ? 's' : ''}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <ScorePill label="Ev" score={scores.evidence} />
          <ScorePill label="Dr" score={scores.druggability} />
          <ScorePill label="Nv" score={scores.novelty} />
          <ScorePill label="Fe" score={scores.feasibility} />
        </div>
      </div>
    </div>
  )
}

// Loop Notification
function LoopNotification({ loopTo, iteration, agents }) {
  if (!loopTo) return null
  
  const agentName = agents[loopTo]?.name || loopTo
  
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-orange-100 border border-orange-300 rounded-lg text-sm text-orange-700 mb-4">
      <RotateCcw size={14} className="animate-spin" />
      <span>Iteration {iteration}: Looping back to <strong>{agentName}</strong></span>
    </div>
  )
}

// =============================================================================
// Main App
// =============================================================================

export default function App() {
  const [pipelineType, setPipelineType] = useState('research_gap')
  const [question, setQuestion] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [agentStatus, setAgentStatus] = useState({})
  const [agentThinking, setAgentThinking] = useState({})
  const [agentOutputs, setAgentOutputs] = useState({})
  const [outputOrder, setOutputOrder] = useState([])
  const [currentAgent, setCurrentAgent] = useState(null)
  const [expandedAgent, setExpandedAgent] = useState(null)
  const [scores, setScores] = useState({ evidence: null, druggability: null, novelty: null, feasibility: null })
  const [loopTo, setLoopTo] = useState(null)
  const [currentIteration, setCurrentIteration] = useState(0)
  const [finalDecision, setFinalDecision] = useState(null)
  const [error, setError] = useState(null)
  const [userScrolled, setUserScrolled] = useState(false)
  
  const abortControllerRef = useRef(null)
  const outputPanelRef = useRef(null)
  const isAutoScrollingRef = useRef(true)

  // Get current pipeline config
  const pipeline = PIPELINES[pipelineType]

  // Auto-scroll
  useEffect(() => {
    if (outputPanelRef.current && isAutoScrollingRef.current && !userScrolled) {
      outputPanelRef.current.scrollTop = outputPanelRef.current.scrollHeight
    }
  }, [agentOutputs, outputOrder, userScrolled])

  const handleScroll = useCallback(() => {
    if (!outputPanelRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = outputPanelRef.current
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    if (distanceFromBottom > 150) {
      setUserScrolled(true)
      isAutoScrollingRef.current = false
    } else if (distanceFromBottom < 50) {
      setUserScrolled(false)
      isAutoScrollingRef.current = true
    }
  }, [])

  const resetState = useCallback(() => {
    setAgentStatus({})
    setAgentThinking({})
    setAgentOutputs({})
    setOutputOrder([])
    setCurrentAgent(null)
    setExpandedAgent(null)
    setScores({ evidence: null, druggability: null, novelty: null, feasibility: null })
    setLoopTo(null)
    setCurrentIteration(0)
    setFinalDecision(null)
    setError(null)
    setUserScrolled(false)
    isAutoScrollingRef.current = true
  }, [])

  const scrollToBottom = useCallback(() => {
    setUserScrolled(false)
    isAutoScrollingRef.current = true
    if (outputPanelRef.current) {
      outputPanelRef.current.scrollTop = outputPanelRef.current.scrollHeight
    }
  }, [])

  const runPipeline = async () => {
    if (!question.trim() || isRunning) return

    setIsRunning(true)
    resetState()

    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('/api/pipeline/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question,
          pipeline_type: pipelineType
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              handleSSEEvent(data)
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(`Connection error: ${err.message}`)
      }
    }

    setIsRunning(false)
    abortControllerRef.current = null
  }

  const stopPipeline = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  const handleSSEEvent = (data) => {
    const agentOrder = pipeline.agentOrder

    if (data.type === 'iteration_start') {
      setCurrentIteration(data.iteration)
      setLoopTo(null)
    } 
    else if (data.type === 'loop') {
      setLoopTo(data.to)
      const loopIdx = agentOrder.indexOf(data.to)
      if (loopIdx >= 0) {
        const agentsToReset = agentOrder.slice(loopIdx)
        setAgentStatus(prev => {
          const next = { ...prev }
          agentsToReset.forEach(a => { next[a] = 'waiting' })
          return next
        })
      }
    }
    else if (data.type === 'pipeline_complete') {
      setFinalDecision(data.decision || 'COMPLETE')
      setCurrentAgent(null)
      if (data.scores) setScores(prev => ({ ...prev, ...data.scores }))
    } 
    else if (data.agent) {
      const { agent, phase, content, full_output, scores: newScores } = data

      if (phase === 'thinking') {
        setAgentStatus(prev => ({ ...prev, [agent]: 'thinking' }))
        setAgentThinking(prev => ({ ...prev, [agent]: content }))
        setCurrentAgent(agent)
        setExpandedAgent(agent)
        setLoopTo(null)
        
        setOutputOrder(prev => {
          const filtered = prev.filter(a => a !== agent)
          return [...filtered, agent]
        })
        setAgentOutputs(prev => ({ ...prev, [agent]: '' }))
      } 
      else if (phase === 'output') {
        setAgentStatus(prev => ({ ...prev, [agent]: 'working' }))
        setAgentOutputs(prev => ({ ...prev, [agent]: (prev[agent] || '') + content }))
      } 
      else if (phase === 'complete') {
        setAgentStatus(prev => ({ ...prev, [agent]: 'complete' }))
        if (full_output) {
          setAgentOutputs(prev => ({ ...prev, [agent]: full_output }))
        }
        if (newScores) {
          setScores(prev => ({ ...prev, ...newScores }))
        }
      }
    }
  }

  const PipelineIcon = pipeline.icon

  return (
    <div className="h-screen bg-zinc-50 text-zinc-900 flex flex-col">
      {/* Header */}
      <div className="border-b border-zinc-200 px-6 py-4 bg-white">
        <div className="flex items-center justify-between">
          <PipelineSelector 
            selectedPipeline={pipelineType}
            onSelect={(id) => {
              setPipelineType(id)
              resetState()
              setQuestion('')
            }}
            disabled={isRunning}
          />
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            {currentIteration > 0 && (
              <span className="px-2 py-1 bg-zinc-100 rounded">
                Iteration {currentIteration}{pipeline.hasLoops ? '/3' : ''}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Input Bar */}
      <div className="border-b border-zinc-200 px-6 py-4 bg-white">
        <div className="max-w-7xl mx-auto flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={pipeline.placeholder}
            className="flex-1 px-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-amber-400 focus:bg-white transition-colors"
            disabled={isRunning}
            onKeyDown={(e) => e.key === 'Enter' && runPipeline()}
          />
          {isRunning ? (
            <button
              onClick={stopPipeline}
              className="px-4 py-2.5 bg-red-50 text-red-600 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors flex items-center gap-2"
            >
              <Square size={16} />
              Stop
            </button>
          ) : (
            <button
              onClick={runPipeline}
              disabled={!question.trim()}
              className="px-5 py-2.5 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Play size={16} />
              Run Pipeline
            </button>
          )}
        </div>
        {error && (
          <div className="max-w-7xl mx-auto mt-2">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Agent Steps */}
        <div className="w-80 border-r border-zinc-200 flex flex-col bg-white">
          <div className="px-4 py-3 border-b border-zinc-200">
            <h2 className="text-sm font-medium text-zinc-700">Execution Pipeline</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {pipeline.agentOrder.map((agentId) => (
              <AgentStep
                key={agentId}
                agentId={agentId}
                agent={pipeline.agents[agentId]}
                status={agentStatus[agentId] || 'waiting'}
                thinking={agentThinking[agentId]}
                isExpanded={expandedAgent === agentId}
                onToggle={() => setExpandedAgent(expandedAgent === agentId ? null : agentId)}
              />
            ))}
          </div>
          
          {/* Scores Summary (Drug Discovery only) */}
          {pipeline.hasScores && (scores.evidence !== null || scores.druggability !== null || scores.novelty !== null || scores.feasibility !== null) && (
            <div className="border-t border-zinc-200 p-4">
              <div className="text-xs text-zinc-500 mb-2">Current Scores</div>
              <div className="grid grid-cols-2 gap-2">
                <ScorePill label="Evidence" score={scores.evidence} />
                <ScorePill label="Druggability" score={scores.druggability} />
                <ScorePill label="Novelty" score={scores.novelty} />
                <ScorePill label="Feasibility" score={scores.feasibility} />
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Output Canvas */}
        <div className="flex-1 flex flex-col bg-white">
          <div className="px-6 py-3 border-b border-zinc-200 flex items-center justify-between">
            <h2 className="text-sm font-medium text-zinc-700">Analysis Output</h2>
            <div className="flex items-center gap-3">
              {userScrolled && isRunning && (
                <button 
                  onClick={scrollToBottom}
                  className="text-xs text-amber-600 hover:text-amber-700"
                >
                  ↓ Scroll to bottom
                </button>
              )}
              {currentAgent && agentStatus[currentAgent] !== 'complete' && (
                <span className="text-xs text-amber-500 flex items-center gap-1">
                  <Loader2 size={12} className="animate-spin" />
                  {pipeline.agents[currentAgent]?.name} is {agentStatus[currentAgent]}...
                </span>
              )}
            </div>
          </div>
          
          <div 
            ref={outputPanelRef} 
            className="flex-1 overflow-y-auto p-6 bg-zinc-50"
            onScroll={handleScroll}
          >
            {outputOrder.length === 0 && !isRunning ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <PipelineIcon size={48} className="text-zinc-300 mx-auto mb-4" />
                  <p className="text-zinc-500 text-sm">Enter a research question and run the pipeline</p>
                  <p className="text-zinc-400 text-xs mt-1">Agent outputs will appear here</p>
                </div>
              </div>
            ) : (
              <>
                <DecisionBanner 
                  decision={finalDecision} 
                  scores={scores}
                  iterations={currentIteration}
                  pipelineType={pipelineType}
                />
                
                {pipeline.hasLoops && (
                  <LoopNotification 
                    loopTo={loopTo} 
                    iteration={currentIteration}
                    agents={pipeline.agents}
                  />
                )}
                
                {outputOrder.map((agentId) => (
                  <OutputSection
                    key={`${agentId}-${currentIteration}`}
                    agentId={agentId}
                    agent={pipeline.agents[agentId]}
                    output={agentOutputs[agentId]}
                    isStreaming={currentAgent === agentId && agentStatus[agentId] === 'working'}
                  />
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}