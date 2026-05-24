import { useState, useCallback, lazy, Suspense } from "react";
import Header from "./components/layout/Header";
import TabBar from "./components/layout/TabBar";
import StatusBar from "./components/layout/StatusBar";
import RiskTabs from "./components/sections/RiskSection";
import AnalysisModal from "./components/analysis/AnalysisModal";
import LoadingSkeleton from "./components/common/LoadingSkeleton";
import ErrorState from "./components/common/ErrorState";
import EmptyState from "./components/common/EmptyState";
import PriceRangeSelector, { RANGES } from "./components/common/PriceRangeSelector";
import { useStocks } from "./hooks/useStocks";
import type { RecParams } from "./services/api";

const MarketPage = lazy(() => import("./components/pages/MarketPage"));
const ProfilePage = lazy(() => import("./components/pages/ProfilePage"));

function PageLoader() {
  return (
    <div className="px-5 pt-4 space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />
      ))}
    </div>
  );
}

function App() {
  const [tab, setTab] = useState("recommend");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [priceRange, setPriceRange] = useState(0);
  const { data, loading, error, refetch } = useStocks();

  const handlePriceChange = useCallback((index: number) => {
    setPriceRange(index);
    const range = RANGES[index];
    refetch({
      price_min: range.min ?? undefined,
      price_max: range.max ?? undefined,
    });
  }, [refetch]);

  return (
    <>
      <StatusBar />

      <div className="phone-content">
        <Header />

        {tab === "recommend" && (
          <>
            <PriceRangeSelector selected={priceRange} onChange={handlePriceChange} />

            {loading && <LoadingSkeleton />}
            {error && <ErrorState message={error} onRetry={() => handlePriceChange(priceRange)} />}
            {!loading && !error && data && data.sections.length === 0 && <EmptyState />}
            {!loading && !error && data && data.sections.length > 0 && (
              <div className="pb-2">
                <RiskTabs
                  sections={data.sections}
                  onStockTap={setSelectedSymbol}
                />
              </div>
            )}
          </>
        )}

        {tab === "market" && (
          <Suspense fallback={<PageLoader />}>
            <MarketPage />
          </Suspense>
        )}

        {tab === "profile" && (
          <Suspense fallback={<PageLoader />}>
            <ProfilePage />
          </Suspense>
        )}

        <TabBar active={tab} onChange={setTab} />
      </div>

      <AnalysisModal symbol={selectedSymbol} onClose={() => setSelectedSymbol(null)} />
    </>
  );
}

export default App;
