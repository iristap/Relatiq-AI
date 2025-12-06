'use client';

import { useState, useEffect } from 'react';
import {
  getArticles,
  getNetwork,
  getCompanyAnalysis,
  getSectors,
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
  ChevronRight,
  Search,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Newspaper
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
  const [viewMode, setViewMode] = useState<'selection' | 'analysis'>('selection');
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
  const [dateRange, setDateRange] = useState('30d');
  const [selectedTiers, setSelectedTiers] = useState<string[]>(['Tier A', 'Tier B']);
  const [selectedStatus, setSelectedStatus] = useState<string[]>(['Confirmed News', 'Analysis/Outlook']);
  const [availableSectors, setAvailableSectors] = useState<string[]>([]);
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [entitySearch, setEntitySearch] = useState('');

  // Theme
  const [darkMode, setDarkMode] = useState(false);

  // Initial Load
  useEffect(() => {
    loadSectors();
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
    if (viewMode === 'analysis') {
      if (activeTab === 'graph') {
        loadGraph();
      } else if (activeTab === 'analysis' && selectedArticles.length > 0) {
        loadAnalysis();
      }
    }
  }, [selectedArticles, dateRange, selectedTiers, selectedStatus, selectedSectors, entitySearch, activeTab, viewMode]);

  // Load Articles when filters change
  useEffect(() => {
    loadArticles();
  }, [dateRange, selectedTiers, selectedStatus, selectedSectors, entitySearch]);

  const loadArticles = async () => {
    try {
      const data = await getArticles({
        date_range: dateRange,
        tiers: selectedTiers.length > 0 ? selectedTiers.map(t => t.replace('Tier ', '')) : undefined,
        news_status: selectedStatus.length > 0 ? selectedStatus : undefined,
        sectors: selectedSectors.length > 0 ? selectedSectors : undefined,
        entity_search: entitySearch || undefined
      });
      setArticles(data);
    } catch (error) {
      console.error("Failed to load articles", error);
    }
  };

  const loadSectors = async () => {
    try {
      const data = await getSectors();
      setAvailableSectors(data);
    } catch (error) {
      console.error("Failed to load sectors", error);
    }
  };

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await getNetwork({
        article_titles: selectedArticles.length > 0 ? selectedArticles : undefined,
        date_range: dateRange,
        tiers: selectedTiers.length > 0 ? selectedTiers : undefined,
        news_status: selectedStatus.length > 0 ? selectedStatus : undefined,
        sectors: selectedSectors.length > 0 ? selectedSectors : undefined,
        entity_search: entitySearch || undefined
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

        {viewMode === 'selection' ? (
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex-1 overflow-y-auto min-h-0">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Filter className="w-4 h-4" /> Filters
            </h2>
            <div className="space-y-6">
              {/* News Tier */}
              <div>
                <label className="text-xs font-medium text-slate-500 mb-2 block">News Tier</label>
                <div className="space-y-2">
                  {['Tier A', 'Tier B', 'Tier C'].map(tier => (
                    <label key={tier} className="flex items-center gap-2 cursor-pointer group">
                      <div className={clsx(
                        "w-4 h-4 rounded border flex items-center justify-center transition-colors",
                        selectedTiers.includes(tier)
                          ? "bg-indigo-600 border-indigo-600"
                          : "border-slate-300 dark:border-slate-600 group-hover:border-indigo-400"
                      )}>
                        {selectedTiers.includes(tier) && <CheckCircle2 className="w-3 h-3 text-white" />}
                      </div>
                      <input
                        type="checkbox"
                        className="hidden"
                        checked={selectedTiers.includes(tier)}
                        onChange={() => {
                          setSelectedTiers(prev =>
                            prev.includes(tier) ? prev.filter(t => t !== tier) : [...prev, tier]
                          );
                        }}
                      />
                      <span className="text-sm text-slate-600 dark:text-slate-300">{tier}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* News Status */}
              <div>
                <label className="text-xs font-medium text-slate-500 mb-2 block">News Status</label>
                <div className="space-y-2">
                  {['Confirmed News', 'Speculation', 'Analysis/Outlook'].map(status => (
                    <label key={status} className="flex items-center gap-2 cursor-pointer group">
                      <div className={clsx(
                        "w-4 h-4 rounded border flex items-center justify-center transition-colors",
                        selectedStatus.includes(status)
                          ? "bg-indigo-600 border-indigo-600"
                          : "border-slate-300 dark:border-slate-600 group-hover:border-indigo-400"
                      )}>
                        {selectedStatus.includes(status) && <CheckCircle2 className="w-3 h-3 text-white" />}
                      </div>
                      <input
                        type="checkbox"
                        className="hidden"
                        checked={selectedStatus.includes(status)}
                        onChange={() => {
                          setSelectedStatus(prev =>
                            prev.includes(status) ? prev.filter(s => s !== status) : [...prev, status]
                          );
                        }}
                      />
                      <span className="text-sm text-slate-600 dark:text-slate-300">{status}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-200 dark:border-slate-800 pt-4 space-y-6">
                {/* Date Range */}
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">Date range</label>
                  <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="3m">Last 3 months</option>
                    <option value="all">All time</option>
                  </select>
                </div>

                {/* Entity Search */}
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">Entity Search</label>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      value={entitySearch}
                      onChange={(e) => setEntitySearch(e.target.value)}
                      placeholder="Search companies..."
                      className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>
                </div>

                {/* Sectors */}
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-2 block">Sectors</label>
                  <div className="flex flex-wrap gap-2">
                    {availableSectors.map(sector => (
                      <button
                        key={sector}
                        onClick={() => {
                          setSelectedSectors(prev =>
                            prev.includes(sector) ? prev.filter(s => s !== sector) : [...prev, sector]
                          );
                        }}
                        className={clsx(
                          "px-2 py-1 text-xs rounded-full border transition-colors",
                          selectedSectors.includes(sector)
                            ? "bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-900/50 dark:text-indigo-300 dark:border-indigo-800"
                            : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-indigo-300"
                        )}
                      >
                        {sector}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex-1 overflow-y-auto flex flex-col gap-6 min-h-0">
            <button
              onClick={() => setViewMode('selection')}
              className="w-full py-2 px-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Back to Selection
            </button>

            <div className="space-y-4">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">Analyzing {selectedArticles.length} articles</div>
              <div className="flex flex-wrap gap-2">
                {selectedArticles.slice(0, 5).map((title, i) => (
                  <span key={i} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] rounded border border-slate-200 dark:border-slate-700 truncate max-w-full">
                    {title}
                  </span>
                ))}
                {selectedArticles.length > 5 && (
                  <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] rounded border border-slate-200 dark:border-slate-700">
                    +{selectedArticles.length - 5} more
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-950 overflow-hidden">
        {viewMode === 'selection' ? (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between shadow-sm">
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-indigo-600" />
                Select Articles to Analyze
              </h2>
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  {selectedArticles.length} selected
                </span>
                <button
                  onClick={() => setViewMode('analysis')}
                  disabled={selectedArticles.length === 0}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                >
                  Analyze Selected <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className="p-2 rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
                  title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
                >
                  {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {articles.map((article, idx) => (
                  <div
                    key={idx}
                    onClick={() => toggleArticleSelection(article.title)}
                    className={clsx(
                      "p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md group flex flex-col gap-3",
                      selectedArticles.includes(article.title)
                        ? "bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-800 shadow-sm"
                        : "bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 hover:border-indigo-100 dark:hover:border-indigo-900"
                    )}
                  >
                    <div className="flex justify-between items-start">
                      <div className={clsx(
                        "w-5 h-5 mt-0.5 rounded-full border flex items-center justify-center flex-shrink-0 transition-colors",
                        selectedArticles.includes(article.title)
                          ? "bg-indigo-600 border-indigo-600"
                          : "border-slate-300 dark:border-slate-600 group-hover:border-indigo-400"
                      )}>
                        {selectedArticles.includes(article.title) && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                      </div>
                      <div className="flex gap-1">
                        {article.tier && (
                          <span className={clsx(
                            "text-[10px] px-1.5 py-0.5 rounded font-medium border uppercase tracking-wider",
                            article.tier === 'Tier A' ? "bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800" :
                              article.tier === 'Tier B' ? "bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800" :
                                "bg-slate-50 text-slate-600 border-slate-100 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
                          )}>
                            {article.tier}
                          </span>
                        )}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 leading-snug mb-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
                        {article.title}
                      </h3>

                      {article.status && (
                        <span className={clsx(
                          "inline-block text-[10px] px-1.5 py-0.5 rounded font-medium border uppercase tracking-wider mb-2",
                          article.status === 'Confirmed News' ? "bg-indigo-50 text-indigo-700 border-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800" :
                            article.status === 'Speculation' ? "bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800" :
                              "bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800"
                        )}>
                          {article.status}
                        </span>
                      )}

                      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-auto">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {article.date}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1 truncate max-w-[100px]">
                          <Newspaper className="w-3 h-3" />
                          {article.source || 'Unknown'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
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
            <div className="flex-1 overflow-y-auto p-6 min-h-0">

              {activeTab === 'graph' && (
                <div className="h-full flex flex-col">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Network Visualization</h2>
                    <div className="flex gap-2 items-center">
                      {selectedArticles.length > 0 && !readingMode && (
                        <button
                          onClick={() => setReadingMode(true)}
                          className="text-xs flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400 rounded-full font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
                        >
                          <BookOpen className="w-3 h-3" />
                          Start Reading Mode
                        </button>
                      )}
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
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {analysisData.sentiment && analysisData.sentiment.map((item: any, i: number) => {
                          const total = item.Total;
                          const posPct = (item.Positive / total) * 100;
                          const negPct = (item.Negative / total) * 100;
                          const neuPct = (item.Neutral / total) * 100;

                          return (
                            <div key={i} className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-4 flex flex-col gap-3">
                              <div className="flex justify-between items-start">
                                <h3 className="font-semibold text-slate-800 dark:text-slate-100 truncate" title={item.Entity}>
                                  {item.Entity}
                                </h3>
                                <span className={clsx(
                                  "text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide border",
                                  item.Type === 'Company' ? "bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800" :
                                    item.Type === 'Product' ? "bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800" :
                                      "bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800"
                                )}>
                                  {item.Type}
                                </span>
                              </div>

                              <div className="space-y-1">
                                <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                                  <span>Sentiment Distribution</span>
                                  <span>{total} mentions</span>
                                </div>
                                <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex">
                                  {posPct > 0 && <div style={{ width: `${posPct}%` }} className="bg-emerald-500" title={`Positive: ${item.Positive}`} />}
                                  {neuPct > 0 && <div style={{ width: `${neuPct}%` }} className="bg-slate-400" title={`Neutral: ${item.Neutral}`} />}
                                  {negPct > 0 && <div style={{ width: `${negPct}%` }} className="bg-rose-500" title={`Negative: ${item.Negative}`} />}
                                </div>
                                <div className="flex justify-between text-[10px] text-slate-400">
                                  <span className="text-emerald-600 dark:text-emerald-400">{item.Positive > 0 ? `${Math.round(posPct)}% Pos` : ''}</span>
                                  <span className="text-rose-600 dark:text-rose-400">{item.Negative > 0 ? `${Math.round(negPct)}% Neg` : ''}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
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
          </>
        )}
      </div>
    </div>
  );
}
