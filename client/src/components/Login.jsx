import React, { useState } from "react";
import styles from "../css/Login.module.css";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const Login = () => {
  const [userid, setId] = useState("");
  const [userpw, setPw] = useState("");
  const { logout, login, isLoggedIn } = useAuth();

  const handleLogin = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post("/login", {
        userid,
        userpw,
      });
      login(response.data.token); // 로그인 상태 업데이트
    } catch (error) {
      console.error("Login error:", error);
    }
  };
  const handleLogout = async (e) => {
    e.preventDefault();
    await logout();
  };
  if (!isLoggedIn) {
    return (
      <div className={styles.LoginWrap}>
        <h3 className={styles.LoginLogo}>
          <img src="" alt="" />
        </h3>
        <p>
          안녕하세요.
          <br />
        </p>
        <span>서비스 이용을 위해 로그인을 해주세요.</span>

        <form onSubmit={handleLogin} className={styles.LoginFormWrap}>
          <div className={styles.LoginEmailWrap}>
            <input
              type="text"
              placeholder="ID"
              id="loginEmail"
              className={styles.LoginEmail}
              value={userid}
              onChange={(e) => setId(e.target.value)}
            />
          </div>

          <div className={styles.LoginPasswordWrap}>
            <input
              type="password"
              placeholder="PASSWORD"
              id="loginPassword"
              className={styles.LoginPassword}
              value={userpw}
              onChange={(e) => setPw(e.target.value)}
            />
          </div>

          <button type="submit" className={styles.LoginSubmitButton}>
            로그인하기
          </button>
        </form>
      </div>
    );
  } else {
    return (
      <div className={styles.LoginWrap}>
        <h3 className={styles.LoginLogo}>
          <img src="" alt="" />
        </h3>
        <p>
          안녕하세요.
          <br />
          김서준님.
        </p>
        <button className={styles.LogoutButton} onClick={handleLogout}>
          로그아웃하기
        </button>
      </div>
    );
  }
};

export default Login;
