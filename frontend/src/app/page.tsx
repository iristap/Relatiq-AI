'use client';

import { useState, useEffect } from 'react';
import {
  getArticles,
  getNetwork,
  getCompanyAnalysis,
  agentQuery,
  agentInsight,
  getArticleMentions,
  Article,
  GraphData
} from '@/lib/api';
import GraphVisualization from '@/components/GraphVisualization';
import {
  Filter,
  Calendar,
  Share2,
  MessageSquare,
  BrainCircuit,
  Loader2,
  Sun,
  Moon,
  BookOpen,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface AgentResult {
  cypher: string;
  data: any[];
  graph: GraphData;
}

export default function Home() {
  // State
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedArticles, setSelectedArticles] = useState<string[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'graph' | 'timeline' | 'analysis' | 'agent'>('graph');

  // Agent State
  const [query, setQuery] = useState('');
  const [agentResult, setAgentResult] = useState<AgentResult | null>(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [insight, setInsight] = useState('');

  const [insightLoading, setInsightLoading] = useState(false);
  const [analysisType, setAnalysisType] = useState('Summary'); // Summary, Risks, Direction

  // Analysis State
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Reading Mode State
  const [readingMode, setReadingMode] = useState(false);
  const [currentArticleIndex, setCurrentArticleIndex] = useState(0);
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);

  // Filters
  const [minDegree, setMinDegree] = useState(1);

  // Theme
  const [darkMode, setDarkMode] = useState(false);

  // Initial Load
  useEffect(() => {
    loadArticles();
  }, []);

  // Theme Effect
  useEffect(() => {
    // Check local storage on mount. Default to light if not set.
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setDarkMode(true);
    }
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  // Load Graph when selection changes
  useEffect(() => {
    if (activeTab === 'graph') {
      loadGraph();
    } else if (activeTab === 'analysis' && selectedArticles.length > 0) {
      loadAnalysis();
    }
  }, [selectedArticles, minDegree, activeTab]);

  const loadArticles = async () => {
    try {
      const data = await getArticles();
      setArticles(data);
    } catch (error) {
      console.error("Failed to load articles", error);
    }
  };

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await getNetwork({
        article_titles: selectedArticles.length > 0 ? selectedArticles : undefined,
        min_degree: minDegree
      });
      setGraphData(data);
    } catch (error) {
      console.error("Failed to load graph", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      const data = await getCompanyAnalysis(selectedArticles);
      setAnalysisData(data);
    } catch (error) {
      console.error("Failed to load analysis", error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleAgentQuery = async () => {
    if (!query) return;
    setAgentLoading(true);
    try {
      const result = await agentQuery(query);
      setAgentResult(result);
      if (result.graph && result.graph.nodes.length > 0) {
        setGraphData(result.graph); // Update main graph with agent result
      }
    } catch (error) {
      console.error("Agent query failed", error);
    } finally {
      setAgentLoading(false);
    }
  };

  const handleInsight = async () => {
    if (selectedArticles.length === 0) return;
    setInsightLoading(true);
    try {
      const result = await agentInsight(selectedArticles, analysisType);
      setInsight(result.insight);
    } catch (error) {
      console.error("Insight generation failed", error);
    } finally {
      setInsightLoading(false);
    }
  };

  const toggleArticleSelection = (title: string) => {
    setSelectedArticles(prev =>
      prev.includes(title)
        ? prev.filter(t => t !== title)
        : [...prev, title]
    );
  };

  // Reading Mode Logic
  useEffect(() => {
    if (readingMode && selectedArticles.length > 0) {
      const title = selectedArticles[currentArticleIndex];
      if (title) {
        getArticleMentions(title).then(ids => {
          setHighlightedNodes(ids);
        }).catch(err => console.error("Failed to get mentions", err));
      }
    } else {
      setHighlightedNodes([]);
    }
  }, [readingMode, currentArticleIndex, selectedArticles]);

  const handleNextArticle = () => {
    if (currentArticleIndex < selectedArticles.length - 1) {
      setCurrentArticleIndex(prev => prev + 1);
    }
  };

  const handlePrevArticle = () => {
    if (currentArticleIndex > 0) {
      setCurrentArticleIndex(prev => prev - 1);
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-50 font-sans overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col shadow-sm z-10">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-indigo-600" />
            Relatiq AI
          </h1>
          <p className="text-xs text-slate-500 mt-1">Financial Knowledge Graph</p>
        </div>

        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <Filter className="w-4 h-4" /> Filters
          </h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Degree of Separation: {minDegree}</label>
              <input
                type="range"
                min="1"
                max="4"
                value={minDegree}
                onChange={(e) => setMinDegree(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>
          </div>

          {selectedArticles.length > 0 && (
            <div className="p-4 border-b border-slate-200 dark:border-slate-800">
              <button
                onClick={() => {
                  setReadingMode(true);
                  setCurrentArticleIndex(0);
                }}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
              >
                <BookOpen className="w-4 h-4" /> Start Reading Mode
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <Calendar className="w-4 h-4" /> Articles
          </h2>
          <div className="space-y-2">
            {articles.map((article, idx) => (
              <div
                key={idx}
                onClick={() => toggleArticleSelection(article.title)}
                className={clsx(
                  "p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md",
                  selectedArticles.includes(article.title)
                    ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800 shadow-sm"
                    : "bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 hover:border-indigo-100 dark:hover:border-indigo-900"
                )}
              >
                <div className="flex items-start gap-2">
                  <div className={clsx(
                    "w-4 h-4 mt-0.5 rounded border flex items-center justify-center flex-shrink-0",
                    selectedArticles.includes(article.title) ? "bg-indigo-600 border-indigo-600" : "border-slate-300"
                  )}>
                    {selectedArticles.includes(article.title) && <div className="w-2 h-2 bg-white rounded-sm" />}
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-slate-800 dark:text-slate-200 line-clamp-2">{article.title}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{article.date} • {article.source || 'Unknown'}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-950 overflow-hidden">
        {/* Header/Tabs */}
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex items-center justify-between shadow-sm transition-colors">
          <div className="flex items-center gap-6">
            <button
              onClick={() => setActiveTab('graph')}
              className={clsx(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2",
                activeTab === 'graph'
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
            >
              <Share2 className="w-4 h-4" /> Graph View
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={clsx(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2",
                activeTab === 'analysis'
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
            >
              <Filter className="w-4 h-4" /> Company Analysis
            </button>
            <button
              onClick={() => setActiveTab('agent')}
              className={clsx(
                "px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2",
                activeTab === 'agent'
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
            >
              <MessageSquare className="w-4 h-4" /> Agent & Insights
            </button>
          </div>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">

          {activeTab === 'graph' && (
            <div className="h-full flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Network Visualization</h2>
                <div className="flex gap-2">
                  {loading && <span className="text-sm text-slate-500 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading Graph...</span>}
                </div>
              </div>
              <div className="flex-1 min-h-0 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-1 relative">
                <GraphVisualization data={graphData} darkMode={darkMode} highlightedNodes={highlightedNodes} />

                {/* Reading Mode Overlay */}
                {readingMode && selectedArticles.length > 0 && (
                  <div className="absolute bottom-6 left-6 right-6 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6 flex flex-col animate-in slide-in-from-bottom-10">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2 text-xs font-medium text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                        <BookOpen className="w-3 h-3" />
                        Article {currentArticleIndex + 1} of {selectedArticles.length}
                      </div>
                      <button
                        onClick={() => {
                          setReadingMode(false);
                          setHighlightedNodes([]);
                        }}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                      {selectedArticles[currentArticleIndex]}
                    </h3>

                    <div className="flex items-center justify-between mt-4">
                      <button
                        onClick={handlePrevArticle}
                        disabled={currentArticleIndex === 0}
                        className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-600 dark:text-slate-400"
                      >
                        <ChevronLeft className="w-6 h-6" />
                      </button>

                      <div className="text-sm text-slate-500 dark:text-slate-400">
                        Mentions highlighted in graph
                      </div>

                      <button
                        onClick={handleNextArticle}
                        disabled={currentArticleIndex === selectedArticles.length - 1}
                        className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-600 dark:text-slate-400"
                      >
                        <ChevronRight className="w-6 h-6" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="max-w-6xl mx-auto">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4">Company Analysis</h2>
              {selectedArticles.length === 0 ? (
                <div className="p-8 text-center bg-slate-100 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  Select articles from the sidebar to view company analysis.
                </div>
              ) : analysisLoading ? (
                <div className="flex items-center justify-center p-12">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                </div>
              ) : analysisData ? (
                <div className="space-y-6">
                  <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
                      <h3 className="font-semibold text-slate-700 dark:text-slate-200">Companies Mentioned</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-white dark:bg-slate-900 border-b dark:border-slate-800">
                          <tr>
                            <th className="px-6 py-3">Company</th>
                            <th className="px-6 py-3">Article</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analysisData.companies.map((row: any, i: number) => (
                            <tr key={i} className="bg-white dark:bg-slate-900 border-b dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800">
                              <td className="px-6 py-3 font-medium text-slate-900 dark:text-slate-100">{row.Company}</td>
                              <td className="px-6 py-3 text-slate-500 dark:text-slate-400">{row.Article}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
                      <h3 className="font-semibold text-slate-700 dark:text-slate-200">Connections</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-white dark:bg-slate-900 border-b dark:border-slate-800">
                          <tr>
                            <th className="px-6 py-3">Company 1</th>
                            <th className="px-6 py-3">Company 2</th>
                            <th className="px-6 py-3">Relationships</th>
                            <th className="px-6 py-3">Distance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analysisData.connections.map((row: any, i: number) => (
                            <tr key={i} className="bg-white dark:bg-slate-900 border-b dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800">
                              <td className="px-6 py-3 font-medium text-slate-900 dark:text-slate-100">{row.Company1}</td>
                              <td className="px-6 py-3 font-medium text-slate-900 dark:text-slate-100">{row.Company2}</td>
                              <td className="px-6 py-3 text-slate-500 dark:text-slate-400">{row.Relationships.join(', ')}</td>
                              <td className="px-6 py-3 text-slate-500 dark:text-slate-400">{row.Distance}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}

          {activeTab === 'agent' && (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Agent Query Section */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-indigo-600" />
                  Ask the Knowledge Graph
                </h2>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., What companies does OpenAI invest in?"
                    className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    onKeyDown={(e) => e.key === 'Enter' && handleAgentQuery()}
                  />
                  <button
                    onClick={handleAgentQuery}
                    disabled={agentLoading}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {agentLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Ask'}
                  </button>
                </div>

                {agentResult && (
                  <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-top-4">
                    <div className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                      <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Generated Cypher</h3>
                      <pre className="text-xs font-mono text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-800 overflow-x-auto">
                        {agentResult.cypher}
                      </pre>
                    </div>

                    {agentResult.graph && agentResult.graph.nodes.length > 0 && (
                      <div className="h-[400px] bg-slate-900 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
                        <GraphVisualization data={agentResult.graph} darkMode={darkMode} />
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Insight Section */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                      <Share2 className="w-5 h-5 text-emerald-600" />
                      Insight Analysis
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                      Select articles from the sidebar to generate a summary and insights.
                    </p>
                  </div>
                  <button
                    onClick={handleInsight}
                    disabled={insightLoading || selectedArticles.length === 0}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {insightLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Insights'}
                  </button>
                </div>

                {/* Analysis Type Selector */}
                <div className="flex gap-2 mb-4">
                  {['Summary', 'Risks', 'Direction'].map((type) => (
                    <button
                      key={type}
                      onClick={() => setAnalysisType(type)}
                      className={clsx(
                        "px-3 py-1.5 text-xs font-medium rounded-full border transition-colors",
                        analysisType === type
                          ? "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800"
                          : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700 dark:hover:bg-slate-800"
                      )}
                    >
                      {type === 'Direction' ? 'Company Direction' : type}
                    </button>
                  ))}
                </div>

                {selectedArticles.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {selectedArticles.map((title, i) => (
                      <span key={i} className="px-2 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs rounded-md border border-indigo-100 dark:border-indigo-800">
                        {title}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm rounded-lg border border-amber-100 dark:border-amber-800 mb-4">
                    Please select at least one article from the sidebar to analyze.
                  </div>
                )}

                {insight && (
                  <div className="prose prose-sm max-w-none bg-white dark:bg-slate-950 p-6 rounded-lg border border-slate-200 dark:border-slate-800 animate-in fade-in">
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{insight}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
