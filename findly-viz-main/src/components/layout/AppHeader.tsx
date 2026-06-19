import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

import logo from "@/assets/vapt-logo.png";
import { Button } from "@/components/ui/button";

interface AppHeaderProps {
  title: string;
  subtitle: string;
  actions?: ReactNode;
}

export function AppHeader({ title, subtitle, actions }: AppHeaderProps) {
  return (
    <header className="border-b border-border/60 bg-background/70 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <img src={logo} alt="VAPT shield logo" width={36} height={36} className="h-9 w-9" />
          <div className="flex flex-col leading-tight">
            <h1 className="text-sm font-semibold tracking-tight text-foreground">{title}</h1>
            <p className="text-xs text-muted-foreground font-mono">{subtitle}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/">Chat</Link>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/report">Report</Link>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/findings-manager">Findings Manager</Link>
          </Button>
          {actions}
        </div>
      </div>
    </header>
  );
}
