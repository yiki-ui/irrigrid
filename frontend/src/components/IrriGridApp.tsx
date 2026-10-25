"use client";
import React from "react";
import dynamic from "next/dynamic";
import Topbar from "@/components/Layout/Topbar";
import LeftSidebar from "@/components/Layout/Sidebar";
import RightPanel from "@/components/Layout/RightPanel";
import BottomBar from "@/components/Layout/BottomBar";

import StartPanel from "@/components/panels/StartPanel";
import LocationPanel from "@/components/panels/LocationPanel";
import ClimatePanel from "@/components/panels/ClimatePanel";
import RainfallPanel from "@/components/panels/RainfallPanel";
import CropPanel from "@/components/panels/CropPanel";
import SoilPanel from "@/components/panels/SoilPanel";
import WaterPanel from "@/components/panels/WaterPanel";
import SchedulePanel from "@/components/panels/SchedulePanel";
import DesignPanel from "@/components/panels/DesignPanel";
import ResultsPanel from "@/components/panels/ResultsPanel";

import { useAutoPopulate } from "@/lib/useAutoPopulate";

// FarmMap must be client-only (Leaflet requires window)
const FarmMap = dynamic(() => import("@/components/Map/FarmMap"), {
  ssr: false,
  loading: () => (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-main)",
        color: "var(--text-dim)",
        fontSize: "13px",
        fontFamily: "var(--font-mono)",
      }}
    >
      ⟳ Loading satellite imagery &amp; GIS engine…
    </div>
  ),
});

// 2D Field Engineering Layout (Plotly)
const FieldLayout2D = dynamic(() => import("@/components/panels/FieldLayout2DPanel"), {
  ssr: false,
  loading: () => (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-main)",
        color: "var(--primary)",
        fontSize: "13px",
        fontFamily: "var(--font-mono)",
      }}
    >
      ⟳ Loading 2D Precision Engineering Layout Engine…
    </div>
  ),
});


import { useIrriGridStore } from "@/lib/store";

import CropPatternPanel from "@/components/panels/CropPatternPanel";

const STEP_TITLES: Record<number, string> = {
  1: "Start Project", 2: "Rwanda Location Database",
  3: "Climate / ETo - Monthly Data", 4: "Rain & Effective Rain",
  5: "Crop Data - Growth Stages & Kc Values", 6: "Soil Properties & Water Holding Capacity",
  7: "Water Requirements - ETc & NIR", 8: "Irrigation Schedule",
  9: "Crop Pattern & Planting Calendar (Rwanda)", 10: "Drip Irrigation System Design - NSGA-II Optimization",
  11: "2D Field Layout", 12: "Visualize 3D", 13: "Run Analysis",
};

function ActivePanel({ step }: { step: number }) {
  switch (step) {
    case 1: return <StartPanel />;
    case 2: return <LocationPanel />; // also handled by isMapStep below
    case 3: return <ClimatePanel />;
    case 4: return <RainfallPanel />;
    case 5: return <CropPanel />;
    case 6: return <SoilPanel />;
    case 7: return <WaterPanel />;
    case 8: return <SchedulePanel />;
    case 9: return <CropPatternPanel />;
    case 10: return <DesignPanel />;
    // Step 11 is rendered directly in IrriGridApp to avoid the padding wrapper
    case 13: return <ResultsPanel />;
    default: return <StartPanel />;
  }
}

export default function IrriGridApp() {
  const { sidebarStep } = useIrriGridStore();
  const isMapStep = sidebarStep === 2;
  const is2DStep = sidebarStep === 11;
  
  // Orchestrate automated data fetching based on location changes
  useAutoPopulate();

  return (
    <div className="app-container">
      <Topbar />
      <div className="main-content">
        <LeftSidebar />
        
        {/* Center Content */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--bg-main)" }}>
          {!isMapStep && !is2DStep && (
            <div className="panel-header" style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10, background: "var(--bg-widget)" }}>
              <span style={{ color: "var(--primary)", fontSize: 13, lineHeight: 1 }}>■</span>
              <h2 style={{ color: "var(--primary)", fontSize: 14, fontWeight: "bold", letterSpacing: 0.5, margin: 0 }}>
                {STEP_TITLES[sidebarStep] ?? "Panel"}
              </h2>
            </div>
          )}
          <div style={{ flex: 1, overflowY: (isMapStep || is2DStep) ? "hidden" : "auto", display: "flex", flexDirection: "column", height: "100%" }}>
            {isMapStep ? (
              <div style={{ display: "flex", flex: 1, height: "100%", overflow: "hidden" }}>
                 <div style={{ width: 420, minWidth: 380, maxWidth: 440, background: "var(--bg-widget)", borderRight: "1px solid var(--border)", overflowY: "auto" }}>
                   <LocationPanel />
                 </div>
                 <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
                   <FarmMap />
                 </div>
              </div>
            ) : is2DStep ? (
              <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
                <FieldLayout2D />
              </div>
            ) : (
              <div style={{ padding: 20 }}>
                <ActivePanel step={sidebarStep} />
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar */}
        <RightPanel />
      </div>
      <BottomBar />
    </div>
  );
}
