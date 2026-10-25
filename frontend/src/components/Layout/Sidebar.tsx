"use client";
import React from "react";
import { useIrriGridStore } from "@/lib/store";
import {
  Sprout,
  FolderOpen,
  MapPin,
  CloudSun,
  CloudRain,
  Leaf,
  Layers,
  Droplets,
  CalendarDays,
  Grid2x2,
  Wrench,
  Settings,
  Layout,
  BarChart3,
} from "lucide-react";

const STEPS = [
  { step: 1,  num: "01", label: "Start Project",   Icon: FolderOpen },
  { step: 2,  num: "02", label: "Location",         Icon: MapPin },
  { step: 3,  num: "03", label: "Climate/ET0",      Icon: CloudSun },
  { step: 4,  num: "04", label: "Rainfall",         Icon: CloudRain },
  { step: 5,  num: "05", label: "Crop",             Icon: Leaf },
  { step: 6,  num: "06", label: "Soil",             Icon: Layers },
  { step: 7,  num: "07", label: "Water Req.",       Icon: Droplets },
  { step: 8,  num: "08", label: "Irrig. Sched.",    Icon: CalendarDays },
  { step: 9,  num: "09", label: "Crop Pattern",     Icon: Grid2x2 },
  { step: 10, num: "10", label: "Design System",    Icon: Settings },
  { step: 11, num: "11", label: "2D Layout",        Icon: Layout },
  { step: 13, num: "12", label: "Run Analysis",     Icon: BarChart3 },
];


export default function LeftSidebar() {
  const { sidebarStep, setSidebarStep, setCurrentStep } = useIrriGridStore();

  function handleStepClick(idx: number) {
    setSidebarStep(idx);
    setCurrentStep(idx);
  }

  return (
    <div className="left-nav" style={{ width: 220, minWidth: 220, padding: 0 }}>
      {/* Logo/Title Section */}
      <div style={{
        background: "var(--bg-nav-dark)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.12)",
        padding: "16px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: "10px"
      }}>
         <Sprout size={18} color="#ffffff" />
         <span style={{ color: "#ffffff", fontSize: 15, fontWeight: "bold", letterSpacing: 0.8 }}>
           Irrigrid
         </span>
      </div>

      <div style={{ padding: "12px 0", flex: 1, overflowY: "auto" }}>
        {STEPS.map((s) => {
          const idx = s.step;
          const active = sidebarStep === idx;
          const { Icon } = s;
          return (
            <div
              key={idx}
              className={`step-item${active ? " active" : ""}`}
              onClick={() => handleStepClick(idx)}
              style={{
                 margin: "2px 8px",
                 padding: "9px 12px",
                 borderRadius: 4,
                 cursor: "pointer",
                 color: active ? "#ffffff" : "#c0d6f3",
                 background: active ? "var(--bg-nav-active)" : "transparent",
                 borderLeft: "none",
                 fontSize: 12,
                 fontFamily: "var(--font)",
                 letterSpacing: 0.5,
                 transition: "all 0.15s",
                 display: "flex",
                 alignItems: "center",
                 gap: 10,
              }}
            >
              <Icon
                size={14}
                color={active ? "#ffffff" : "#8eb5de"}
                style={{ flexShrink: 0 }}
              />
              <span style={{ opacity: active ? 1 : 0.8, fontSize: 10, fontFamily: "var(--font-mono)", flexShrink: 0, color: active ? "#ffffff" : "#8fb2d8" }}>
                {s.num}
              </span>
              <span>{s.label}</span>
            </div>
          );
        })}
      </div>

      <div className="nav-footer" style={{ padding: "12px 14px", borderTop: "1px solid rgba(255, 255, 255, 0.12)", color: "#8fb2d8", fontSize: 10, textAlign: "center", lineHeight: 1.4 }}>
        <div>Step {sidebarStep === 13 ? 12 : sidebarStep} of {STEPS.length}</div>
        <div style={{ marginTop: 6, fontSize: 9, opacity: 0.85 }}>Data source: National Institute of Statistics of Rwanda (NISR)</div>
      </div>
    </div>
  );
}
