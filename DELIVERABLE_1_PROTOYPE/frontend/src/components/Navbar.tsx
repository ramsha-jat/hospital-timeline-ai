// src/components/Navbar.tsx
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Menu, X, Home, Activity, MessageSquareText,
  ShieldCheck, Link2, Hospital
} from "lucide-react";

const navItems = [
  { path: "/", label: "Home", icon: Home },
  { path: "/timeline", label: "Timeline", icon: Activity },
  { path: "/query", label: "Query", icon: MessageSquareText },
  { path: "/validation", label: "Validate", icon: ShieldCheck },
  { path: "/evidence", label: "Evidence", icon: Link2 },
];

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-primary-300 transition-shadow">
              <Hospital className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-gray-900">Hospital</span>
              <span className="text-lg font-bold text-primary-600">Timeline</span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="relative flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all"
                >
                  {isActive && (
                    <motion.div
                      layoutId="nav-active"
                      className="absolute inset-0 bg-primary-50 border border-primary-200 rounded-lg"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <Icon className={`w-4 h-4 relative z-10 ${isActive ? "text-primary-600" : "text-gray-500"}`} />
                  <span className={`relative z-10 ${isActive ? "text-primary-700" : "text-gray-600 hover:text-gray-900"}`}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </div>

          <div className="hidden md:flex items-center gap-2">
            <span className="px-2.5 py-1 bg-warning-50 border border-warning-500/30 rounded-full text-[10px] font-bold text-warning-600 uppercase">
              Research Only
            </span>
          </div>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden border-t bg-white px-4 pb-4"
        >
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium ${
                  isActive ? "bg-primary-50 text-primary-700" : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            );
          })}
        </motion.div>
      )}
    </nav>
  );
};

export default Navbar;