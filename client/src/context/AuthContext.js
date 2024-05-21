import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [brandname, setBrandname] = useState("");
  const [mobile, setMoblie] = useState("");
  
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setUsername(localStorage.getItem("username"));
      setBrandname(localStorage.getItem("brandname"));
      setMoblie(localStorage.getItem("mobile"));
      verifyToken(token);
    }
  }, [isLoggedIn]);

  const verifyToken = async (token) => {
    try {
      await axios.get("/verify-token", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setIsLoggedIn(true); // 토큰이 유효하면 로그인 상태로 설정
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`; // 모든 요청에 토큰 설정
    } catch (error) {
      console.error("Token verification failed:", error);
      localStorage.removeItem("token"); // 토큰이 유효하지 않으면 제거
      setIsLoggedIn(false);
    }
  };

  const login = (token, username, brandname, mobile) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('brandname', brandname);
    localStorage.setItem('mobile', mobile);
    setIsLoggedIn(true);
    setUsername(username);
    setBrandname(brandname);
    setMoblie(mobile);
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  };


    
  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("brandname");
    localStorage.removeItem("mobile");
    setIsLoggedIn(false);
    delete axios.defaults.headers.common["Authorization"];
  };

  return (
    <AuthContext.Provider value={{ isLoggedIn, login, logout, username, brandname, mobile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
