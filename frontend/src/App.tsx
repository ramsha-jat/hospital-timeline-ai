// src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import TimelinePage from "./pages/TimelinePage";
import QueryPage from "./pages/QueryPage";
import ValidationPage from "./pages/ValidationPage";
import EvidencePage from "./pages/EvidencePage";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <main className="flex-1">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/timeline" element={<TimelinePage />} />
              <Route path="/query" element={<QueryPage />} />
              <Route path="/validation" element={<ValidationPage />} />
              <Route path="/evidence" element={<EvidencePage />} />
            </Routes>
          </AnimatePresence>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;