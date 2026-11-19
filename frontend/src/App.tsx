import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { StudentPicker } from "./components/StudentPicker";
import { DiagnosisPage } from "./pages/DiagnosisPage";
import { PracticePage } from "./pages/PracticePage";
import { TeacherPage } from "./pages/TeacherPage";
import { StudentProvider } from "./student";

function Logo() {
  return (
    <div className="logo">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" stroke="#8FA8FF" strokeWidth="2" aria-hidden="true">
        <circle cx="6" cy="6" r="3" /><circle cx="22" cy="6" r="3" /><circle cx="14" cy="22" r="3" />
        <path d="M8.5 8 12 19.5M19.5 8 16 19.5M9 6h10" />
      </svg>
      <span>MindLattice</span>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <StudentProvider>
        <div className="layout">
          <nav className="sidebar" aria-label="Main">
            <Logo />
            <NavLink to="/" end className="nav-link">Diagnosis</NavLink>
            <NavLink to="/practice" className="nav-link">Micro exercises</NavLink>
            <NavLink to="/teacher" className="nav-link">Teacher dashboard</NavLink>
            <StudentPicker />
          </nav>
          <main className="content">
            <Routes>
              <Route path="/" element={<DiagnosisPage />} />
              <Route path="/practice" element={<PracticePage />} />
              <Route path="/practice/:conceptId" element={<PracticePage />} />
              <Route path="/teacher" element={<TeacherPage />} />
            </Routes>
          </main>
        </div>
      </StudentProvider>
    </BrowserRouter>
  );
}
