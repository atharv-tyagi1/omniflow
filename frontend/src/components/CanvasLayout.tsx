"use client";

import React, { useEffect, useState } from "react";
import Navigation from "./Navigation";

const CANVAS_WIDTH = 1920;
const CANVAS_HEIGHT = 1080;

export default function CanvasLayout({ children }: { children: React.ReactNode }) {
  const [scale, setScale] = useState(1);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    const calculateScale = () => {
      const widthScale = window.innerWidth / CANVAS_WIDTH;
      const heightScale = window.innerHeight / CANVAS_HEIGHT;
      // Fit perfectly in viewport, maintaining 16:9
      const newScale = Math.min(widthScale, heightScale);
      setScale(newScale);
    };

    calculateScale();
    window.addEventListener("resize", calculateScale);
    return () => window.removeEventListener("resize", calculateScale);
  }, []);

  return (
    <div className="fixed inset-0 w-full h-full bg-[#E5E7EB] flex items-center justify-center overflow-hidden z-0">
      <div 
        className="relative bg-background shadow-[0_0_100px_rgba(0,0,0,0.1)] overflow-hidden origin-center transition-transform duration-75 ease-linear"
        style={{
          width: `${CANVAS_WIDTH}px`,
          height: `${CANVAS_HEIGHT}px`,
          transform: mounted ? `scale(${scale})` : 'scale(1)',
        }}
      >
        <Navigation />
        <main className="absolute left-[320px] top-[100px] w-[1600px] h-[980px] overflow-y-auto canvas-scroll bg-background">
          {children}
        </main>
      </div>
    </div>
  );
}
