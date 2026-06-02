// Minimal stroked icons — 16px grid, 1.5 stroke
const Icon = ({ d, size = 16, stroke = 1.5, fill = "none", children, ...p }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill={fill}
       stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" {...p}>
    {d && <path d={d} />}{children}
  </svg>
);

const I = {
  Home:    (p) => <Icon {...p}><path d="M2.5 7 8 2.5 13.5 7v6a.5.5 0 0 1-.5.5h-3v-4h-3v4H3a.5.5 0 0 1-.5-.5z"/></Icon>,
  Graph:   (p) => <Icon {...p}><circle cx="3.5" cy="8" r="1.6"/><circle cx="12.5" cy="3.5" r="1.6"/><circle cx="12.5" cy="12.5" r="1.6"/><path d="M5 7.2l6-3M5 8.8l6 3"/></Icon>,
  Library: (p) => <Icon {...p}><rect x="2.5" y="2.5" width="4" height="11" rx="1"/><rect x="7" y="2.5" width="2.5" height="11" rx="1"/><path d="m11.2 4.2 2.1.7-2.3 8.2-2.1-.7z"/></Icon>,
  Metric:  (p) => <Icon {...p}><path d="M2.5 12.5V8M6 12.5V4M9.5 12.5V7M13 12.5V2.5"/></Icon>,
  Dim:     (p) => <Icon {...p}><rect x="2.5" y="2.5" width="11" height="11" rx="1.5"/><path d="M2.5 6h11M6 2.5v11"/></Icon>,
  Source:  (p) => <Icon {...p}><ellipse cx="8" cy="4" rx="5" ry="1.8"/><path d="M3 4v8c0 1 2.2 1.8 5 1.8s5-.8 5-1.8V4M3 8c0 1 2.2 1.8 5 1.8s5-.8 5-1.8"/></Icon>,
  Event:   (p) => <Icon {...p}><path d="M8 2.5 2.8 8l5.2 5.5L13.2 8z"/></Icon>,
  Plus:    (p) => <Icon {...p}><path d="M8 3v10M3 8h10"/></Icon>,
  Search:  (p) => <Icon {...p}><circle cx="7" cy="7" r="4"/><path d="m10 10 3.5 3.5"/></Icon>,
  Filter:  (p) => <Icon {...p}><path d="M2.5 3h11l-4 5v4l-3 1.5V8z"/></Icon>,
  Sparkle: (p) => <Icon {...p}><path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M4 12l2-2"/></Icon>,
  Chat:    (p) => <Icon {...p}><path d="M2.5 4a1.5 1.5 0 0 1 1.5-1.5h8A1.5 1.5 0 0 1 13.5 4v5a1.5 1.5 0 0 1-1.5 1.5H7l-3 2.5v-2.5H4A1.5 1.5 0 0 1 2.5 9z"/></Icon>,
  Bell:    (p) => <Icon {...p}><path d="M4 11.5V7a4 4 0 0 1 8 0v4.5M2.5 11.5h11M6.5 13.5a1.5 1.5 0 0 0 3 0"/></Icon>,
  Clock:   (p) => <Icon {...p}><circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 1.5"/></Icon>,
  Check:   (p) => <Icon {...p}><path d="m3 8.5 3 3 7-7"/></Icon>,
  Warn:    (p) => <Icon {...p}><path d="M8 2.5 14 13H2z"/><path d="M8 6.5v3M8 11.2v.3"/></Icon>,
  ArrowR:  (p) => <Icon {...p}><path d="M3 8h10M9.5 4.5 13 8l-3.5 3.5"/></Icon>,
  Chevron: (p) => <Icon {...p}><path d="m5 3.5 4 4.5-4 4.5"/></Icon>,
  ChevronD:(p) => <Icon {...p}><path d="m3.5 6 4.5 4 4.5-4"/></Icon>,
  Settings:(p) => <Icon {...p}><circle cx="8" cy="8" r="2"/><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3 3l1.5 1.5M11.5 11.5 13 13M3 13l1.5-1.5M11.5 4.5 13 3"/></Icon>,
  User:    (p) => <Icon {...p}><circle cx="8" cy="5.5" r="2.5"/><path d="M3 13.5c.8-2.3 2.7-3.5 5-3.5s4.2 1.2 5 3.5"/></Icon>,
  X:       (p) => <Icon {...p}><path d="m4 4 8 8M12 4l-8 8"/></Icon>,
  Drag:    (p) => <Icon {...p}><circle cx="6" cy="4" r=".7" fill="currentColor"/><circle cx="10" cy="4" r=".7" fill="currentColor"/><circle cx="6" cy="8" r=".7" fill="currentColor"/><circle cx="10" cy="8" r=".7" fill="currentColor"/><circle cx="6" cy="12" r=".7" fill="currentColor"/><circle cx="10" cy="12" r=".7" fill="currentColor"/></Icon>,
  Link:    (p) => <Icon {...p}><path d="M7 9 9 7M6.5 10.5 5 12a2.5 2.5 0 0 1-3.5-3.5L3 7M9.5 5.5 11 4a2.5 2.5 0 0 1 3.5 3.5L13 9"/></Icon>,
  Branch:  (p) => <Icon {...p}><circle cx="4" cy="3.5" r="1.3"/><circle cx="4" cy="12.5" r="1.3"/><circle cx="12" cy="6" r="1.3"/><path d="M4 5v6M5.3 6c2.5 0 3.7-.4 5.4-1.4"/></Icon>,
  Book:    (p) => <Icon {...p}><path d="M2.5 3.5A1 1 0 0 1 3.5 2.5h10a1 1 0 0 1 1 1v9.5L8 11 1.5 13V3.5z" fill="none"/><path d="M8 4.5v6.5"/></Icon>,
  Eye:     (p) => <Icon {...p}><path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="1.8"/></Icon>,
  Edit:    (p) => <Icon {...p}><path d="M3 13h2.5l7-7-2.5-2.5-7 7z"/><path d="m9 5 2.5 2.5"/></Icon>,
  Copy:    (p) => <Icon {...p}><rect x="5" y="5" width="8.5" height="8.5" rx="1.2"/><path d="M10 5V3.5A1 1 0 0 0 9 2.5H3.5a1 1 0 0 0-1 1V9a1 1 0 0 0 1 1H5"/></Icon>,
};

window.I = I;
window.Icon = Icon;
