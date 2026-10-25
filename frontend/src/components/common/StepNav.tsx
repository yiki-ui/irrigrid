"use client";

import React from "react";
import { useIrriGridStore } from "@/lib/store";
import { ArrowLeft, ArrowRight, CheckCircle } from "lucide-react";

interface StepNavProps {
  onNext?: () => void;
  nextLabel?: string;
  disableNext?: boolean;
}

export default function StepNav({ onNext, nextLabel, disableNext = false }: StepNavProps) {
  const { currentStep, setCurrentStep, sidebarStep, setSidebarStep, markStepComplete } = useIrriGridStore();

  const handleNext = () => {
    markStepComplete(currentStep);
    if (onNext) {
      onNext();
    } else if (currentStep < 13) {
      setCurrentStep(currentStep + 1);
      setSidebarStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setSidebarStep(currentStep - 1);
    }
  };

  return (
    <div className="step-footer">
      <button
        onClick={handlePrev}
        disabled={currentStep === 1}
        className="hud-btn"
      >
        <ArrowLeft size={16} />
        Previous
      </button>

      <button
        onClick={handleNext}
        disabled={disableNext}
        className="hud-btn primary"
      >
        {nextLabel || (currentStep === 13 ? "Finished" : "Next Step")}
        {currentStep === 13 ? <CheckCircle size={16} /> : <ArrowRight size={16} />}
      </button>
    </div>
  );
}
