import { useState, lazy, Suspense } from "react";
import FilterPanel from "./components/filter/FilterPanel";
import Header from "./components/layout/Header";
import TabBar from "./components/layout/TabBar";
import StatusBar from "./components/layout/StatusBar";
import AIBriefingCard from "./components/home/AIBriefingCard";
import ViewToggle from "./components/home/ViewToggle";
import CompactStockCard from "./components/home/CompactStockCard";
import StarPick from "./components/home/StarPick";
import StockTable from "./components/home/StockTable";
import QuickActions from "./components/home/QuickActions";
import LoadingSkeleton from "./components/common/LoadingSkeleton";
import ErrorState from "./components/common/ErrorState";
import EmptyState from "./components/common/EmptyState";
import { useStocks } from "./hooks/useStocks";
import type { RecParams } from "./services/api";

const MarketPage = lazy(() => import("./components/pages/MarketPage"));
const ProfilePage = lazy(() => import("./components/pages/ProfilePage"));
const StockAnalysis = lazy(() => import("./components/analysis/StockAnalysis"));
const AIChatPage = lazy(() => import("./components/chat/AIChatPage"));
const ComparePage = lazy(() => import("./components/compare/ComparePage"));

function PageLoader() {
  return (
    <div className="px-5 pt-4 space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />
      ))}
    </div>
  );
}

type Page = "home" | "market" | "profile" | "analysis" | "ai-chat" | "compare";

function App() {
  const [tab, setTab] = useState("recommend");
  const [page, setPage] = useState<Page>("home");
  const [viewMode, setViewMode] = useState<"featured" | "list">(() =>
    (localStorage.getItem("stockrec_view") as "featured" | "list") || "featured"
  );
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [compareSymbols, setCompareSymbols] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const { data, loading, error, refetch } = useStocks();

  const allStocks = data?.sections.flatMap(s => s.stocks) ?? [];

  const handleViewChange = (v: "featured" | "list") => {
    setViewMode(v);
    localStorage.setItem("stockrec_view", v);
  };

  const handleStockTap = (symbol: string) => {
    setSelectedSymbol(symbol);
    setPage("analysis");
  };

  const handleCompare = (symbols: string[]) => {
    setCompareSymbols(symbols);
    setPage("compare");
  };

  const goHome = () => setPage("home");

  if (page === "analysis" && selectedSymbol) {
    return (
      <Suspense fallback={<PageLoader />}>
        <StockAnalysis symbol={selectedSymbol!} onBack={goHome} />
      </Suspense>
    );
  }
  if (page === "ai-chat") {
    return (
      <Suspense fallback={<PageLoader />}>
        <AIChatPage onBack={goHome} />
      </Suspense>
    );
  }
  if (page === "compare" && compareSymbols.length > 0) {
    return (
      <Suspense fallback={<PageLoader />}>
        <ComparePage symbols={compareSymbols} onBack={goHome} />
      </Suspense>
    );
  }

  return (
    <>
      <StatusBar />
      <div className="phone-content">
        <Header />

        {tab === "recommend" && (
          <>
            {loading && <LoadingSkeleton />}
            {error && <ErrorState message={error} onRetry={() => refetch()} />}
            {!loading && !error && allStocks.length === 0 && <EmptyState />}
            {!loading && !error && allStocks.length > 0 && (
              <>
                <AIBriefingCard />
                <div className="flex items-center px-4 mb-3">
                  <ViewToggle view={viewMode} onChange={handleViewChange} total={allStocks.length} />
                  <button onClick={() => setFilterOpen(true)}
                    className="ml-auto px-3 py-1.5 rounded-lg text-[10px] font-medium"
                    style={{ background: "rgba(118,118,128,0.16)", color: "#8E8E93" }}>
                    筛选 ▾
                  </button>
                </div>
                {viewMode === "featured" ? (
                  <>
                    <StarPick stock={allStocks[0]} onTap={handleStockTap} />
                    {allStocks.slice(1).map((s, i) => (
                      <CompactStockCard key={s.symbol} stock={s} rank={i + 2} onTap={handleStockTap} />
                    ))}
                    <QuickActions onAIChat={() => setPage("ai-chat")} onAnalysis={() => {}} />
                  </>
                ) : (
                  <StockTable stocks={allStocks} onCompare={handleCompare} onTap={handleStockTap} />
                )}
              </>
            )}
          </>
        )}

        {tab === "market" && (
          <Suspense fallback={<PageLoader />}><MarketPage /></Suspense>
        )}
        {tab === "profile" && (
          <Suspense fallback={<PageLoader />}><ProfilePage /></Suspense>
        )}

        <TabBar active={tab} onChange={setTab} />
      </div>

      <FilterPanel open={filterOpen} onClose={() => setFilterOpen(false)}
        onApply={(params) => {
          refetch(params as RecParams);
        }} />
    </>
  );
}

export default App;
