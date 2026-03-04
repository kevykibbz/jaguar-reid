import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import JaguarReIdPage from "@/pages/JaguarReIdPage";
import JaguarGalleryPage from "@/pages/JaguarGalleryPage";
import ImageDetailPage from "@/pages/ImageDetailPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ReportsPage } from "@/pages/ReportsPage";
import SpeciesAnalysisPage from "@/pages/SpeciesAnalysisPage";
import { ThemeProvider } from "@/contexts/ThemeProvider";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/layout/AppSidebar";

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="wildtrack-theme">
      <Router>
        <SidebarProvider>
          <div className="flex min-h-screen w-full">
            <AppSidebar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/upload" element={<JaguarReIdPage />} />
                <Route path="/gallery" element={<JaguarGalleryPage />} />
                <Route path="/image/:jaguarId" element={<ImageDetailPage />} />
                <Route
                  path="/species-analysis"
                  element={<SpeciesAnalysisPage />}
                />
                <Route path="/reports" element={<ReportsPage />} />
              </Routes>
            </main>
          </div>
        </SidebarProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
