import styles from "./css/App.module.css";
import Home from "./views/Home";
import { AuthProvider } from "./context/AuthContext";

const App = () => {
  return (
    <AuthProvider>
      <div className={styles.App}>
        <Home></Home>
      </div>
    </AuthProvider>
  );
};

export default App;
