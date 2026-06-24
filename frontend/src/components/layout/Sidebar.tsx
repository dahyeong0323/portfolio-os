import {
  BookOpen,
  Boxes,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronRight,
  CircleGauge,
  ClipboardList,
  FileText,
  FlaskConical,
  Layers3,
  NotebookPen,
  PanelLeftClose,
  ReceiptText,
  Scale,
  Settings,
  ShieldCheck,
  ShieldAlert,
  TestTubeDiagonal,
  Workflow,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

type NavItem = { label: string; icon: typeof CircleGauge; to?: string };

const sections: { label: string; items: NavItem[] }[] = [
  {
    label: "OPERATIONS",
    items: [
      { label: "Dashboard", to: "/", icon: CircleGauge },
      { label: "Ledger", to: "/ledger", icon: BookOpen },
      { label: "Reconciliation", to: "/reconciliation", icon: Scale },
      { label: "Risk Engine", to: "/risk", icon: ShieldAlert },
      { label: "Order Tickets", to: "/tickets", icon: ClipboardList },
      { label: "Executions", to: "/executions", icon: ReceiptText },
      { label: "Overrides", to: "/overrides", icon: Workflow },
      { label: "Journal", to: "/journal", icon: NotebookPen },
    ],
  },
  {
    label: "INTELLIGENCE",
    items: [
      { label: "Research Context", to: "/research", icon: FileText },
      { label: "Macro Context", to: "/macro", icon: ChartNoAxesCombined },
      { label: "Senior Memos", to: "/senior-memos", icon: BrainCircuit },
    ],
  },
  {
    label: "GOVERNANCE",
    items: [
      { label: "Model QA", icon: TestTubeDiagonal },
      { label: "Governance Context", to: "/governance", icon: Boxes },
      { label: "Reports Center", to: "/reports", icon: Layers3 },
      { label: "System Boundaries", to: "/system", icon: ShieldCheck },
      { label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open ? <button className="sidebar-backdrop" aria-label="Close sidebar" onClick={onClose} /> : null}
      <aside className={`sidebar ${open ? "sidebar--open" : ""}`} aria-label="Main navigation">
        <div className="brand">
          <div className="brand__mark"><FlaskConical aria-hidden="true" /></div>
          <div><strong>PORTFOLIO OS</strong><span>MISSION CONTROL</span></div>
          <button className="icon-button sidebar__close" onClick={onClose} aria-label="Close sidebar"><X /></button>
        </div>
        <nav>
          {sections.map((section) => (
            <section className="nav-section" key={section.label}>
              <h2>{section.label}</h2>
              {section.items.map((item) => {
                const Icon = item.icon;
                if (!item.to) {
                  return <span className="nav-item nav-item--disabled" key={item.label} aria-disabled="true"><Icon aria-hidden="true" /><span>{item.label}</span><small>SOON</small></span>;
                }
                return <NavLink key={item.label} to={item.to} onClick={onClose} className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}><Icon aria-hidden="true" /><span>{item.label}</span><ChevronRight aria-hidden="true" className="nav-item__arrow" /></NavLink>;
              })}
            </section>
          ))}
        </nav>
        <div className="sidebar__footer"><PanelLeftClose aria-hidden="true" /><div><span>OPERATING MODE</span><strong>RISK GATED</strong></div></div>
      </aside>
    </>
  );
}
