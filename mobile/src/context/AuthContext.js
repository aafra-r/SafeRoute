import React, { createContext, useState, useContext } from 'react';
import { ApiService, setAuthToken } from '../services/api';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState({
    id: 1,
    full_name: 'Alex Rivera (Demo)',
    email: 'demo@saferoute.app',
    phone: '+1 (555) 019-2834',
    emergency_contacts: [
      { id: 1, name: 'Sarah Rivera (Mother)', phone: '+1 (555) 019-9988', relationship: 'Parent' },
      { id: 2, name: 'Campus Security Dispatch', phone: '+1 (555) 019-1122', relationship: 'Campus Police' }
    ],
    trusted_contacts: [
      { id: 1, name: 'Jordan Lee (Roommate)', phone: '+1 (555) 019-4455' }
    ]
  });
  const [isAuthenticated, setIsAuthenticated] = useState(true); // Default to logged-in demo user for seamless UX
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const res = await ApiService.login(email, password);
      if (res.token) {
        setAuthToken(res.token);
      }
      setUser(res.user || {
        id: 1,
        full_name: 'Alex Rivera (Demo)',
        email: email || 'demo@saferoute.app',
        phone: '+1 (555) 019-2834'
      });
      setIsAuthenticated(true);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const res = await ApiService.register(userData);
      if (res.token) {
        setAuthToken(res.token);
      }
      setUser(res.user);
      setIsAuthenticated(true);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
